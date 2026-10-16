import json
import queue
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game import points, read_json, write_json
from server import Leaderboard
from network import RecordsClient
from websockets.sync.server import serve
from websockets.sync.client import connect


class GameTests(unittest.TestCase):
    def test_points_and_combo(self):
        self.assertEqual(points(False, 1, 0), 0)
        self.assertEqual(points(True, 0, 1), 300)
        self.assertEqual(points(True, 10, 2), 225)
        self.assertEqual(points(True, 20, 10), 200)
        self.assertEqual(points(True, 0, 10), 400)

    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'data'/'scores.json'
            self.assertEqual(read_json(path), [])
            write_json(path, [{'name':'Émilie', 'score':123}])
            self.assertEqual(read_json(path)[0]['name'], 'Émilie')
            path.write_text('broken')
            self.assertEqual(read_json(path), [])

    def test_two_clients_live_records_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'records.json'
            board = Leaderboard(path)
            with serve(board.handle, '127.0.0.1', 0) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                port = server.socket.getsockname()[1]
                with connect(f'ws://127.0.0.1:{port}') as a, connect(f'ws://127.0.0.1:{port}') as b:
                    self.assertEqual(json.loads(a.recv())['records'], [])
                    b.recv()
                    a.send(json.dumps({'type':'score','name':'Émilie','score':800,'correct':4}))
                    self.assertEqual(json.loads(a.recv())['records'][0]['score'],800)
                    self.assertEqual(json.loads(a.recv())['type'],'saved')
                    self.assertEqual(json.loads(b.recv(timeout=2))['records'][0]['name'],'Émilie')
                    b.send(json.dumps({'type':'score','name':'Émilie','score':200,'correct':1}))
                    self.assertEqual(json.loads(a.recv())['records'][0]['score'],800)
                    b.recv(); b.recv()
                    a.send('[]')
                    self.assertEqual(json.loads(a.recv())['type'],'error')
                    a.send(json.dumps({'type':'score','name':'X','score':999999,'correct':10}))
                    self.assertEqual(json.loads(a.recv())['type'],'error')
                server.shutdown()
            self.assertEqual(Leaderboard(path).records[0]['score'],800)

    def test_network_pending_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            board = Leaderboard(Path(directory)/'records.json')
            with serve(board.handle,'127.0.0.1',0) as server:
                threading.Thread(target=server.serve_forever,daemon=True).start()
                client = RecordsClient(f'ws://127.0.0.1:{server.socket.getsockname()[1]}',queue.Queue())
                client.submit({'name':'Alice','score':600,'correct':3})
                client.submit({'name':'Bob','score':1200,'correct':5})
                deadline=time.monotonic()+5
                while time.monotonic()<deadline and len(board.records)<2:
                    time.sleep(0.05)
                self.assertEqual([r['name'] for r in board.records],['Bob','Alice'])
                client.stopped.set()
                client.thread.join(timeout=3)
                server.shutdown()


if __name__=='__main__':
    unittest.main()
