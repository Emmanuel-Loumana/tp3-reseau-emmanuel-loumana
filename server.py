"""Serveur de records partagé : python server.py [--host 0.0.0.0]."""
import argparse
import json
import threading
from pathlib import Path

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed

from game import read_json, write_json


class Leaderboard:
    def __init__(self, path):
        self.path = Path(path)
        self.records = read_json(path)
        self.clients = set()
        self.lock = threading.RLock()

    def message(self):
        return json.dumps({'type': 'records', 'records': self.records}, ensure_ascii=False)

    def add(self, record):
        name = record.get('name')
        score = record.get('score')
        correct = record.get('correct')
        if (not isinstance(name, str) or not 1 <= len(name.strip()) <= 20
                or type(score) is not int or not 0 <= score <= 4000
                or type(correct) is not int or not 0 <= correct <= 10):
            raise ValueError('Score invalide.')
        entry = {'name': name.strip(), 'score': score, 'correct': correct}
        # Un seul record par pseudo, pour que le classement reste lisible.
        previous = next((r for r in self.records if r['name'] == entry['name']), None)
        if previous and previous['score'] >= score:
            return
        self.records = [r for r in self.records if r['name'] != entry['name']]
        self.records.append(entry)
        self.records.sort(key=lambda r: (-r['score'], r['name'].casefold()))
        self.records = self.records[:10]
        write_json(self.path, self.records)

    def handle(self, socket):
        with self.lock:
            self.clients.add(socket)
            socket.send(self.message())
        try:
            for raw in socket:
                try:
                    data = json.loads(raw)
                    if not isinstance(data, dict) or data.get('type') != 'score':
                        raise ValueError('Message inconnu.')
                    with self.lock:
                        self.add(data)
                        message = self.message()
                        for client in list(self.clients):
                            try:
                                client.send(message)
                            except ConnectionClosed:
                                self.clients.discard(client)
                        socket.send(json.dumps({'type': 'saved'}))
                except (ValueError, TypeError, AttributeError):
                    socket.send(json.dumps({'type': 'error', 'message': 'Score invalide.'}))
        except ConnectionClosed:
            pass
        finally:
            with self.lock:
                self.clients.discard(socket)


def main():
    parser = argparse.ArgumentParser(description='Serveur de records Dog Guesser')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    board = Leaderboard(Path(__file__).resolve().parent / 'data' / 'records.json')
    try:
        with serve(board.handle, args.host, args.port, max_size=4096) as server:
            print(f'Records : ws://{args.host}:{args.port} — Ctrl+C pour quitter')
            server.serve_forever()
    except OSError as error:
        print(f'Impossible de lancer le serveur : {error}')


if __name__ == '__main__':
    main()
