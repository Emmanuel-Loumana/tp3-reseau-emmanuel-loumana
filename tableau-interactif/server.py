"""API HTTP et diffusion WebSocket du tableau interactif."""
import argparse
import json
import math
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed

WIDTH, HEIGHT = 1000, 640
MAX_SHAPES = 2000
WEB = Path(__file__).resolve().parent / 'web'
FIELDS = {
    'point': ('x', 'y'),
    'line': ('x1', 'y1', 'x2', 'y2'),
    'circle': ('x', 'y', 'radius'),
    'rectangle': ('x', 'y', 'width', 'height'),
    'square': ('x', 'y', 'cote'),
}


def validate_shape(data):
    if not isinstance(data, dict) or not isinstance(data.get('shape'), str):
        raise ValueError('Le champ shape doit indiquer le type de forme.')
    kind = data['shape']
    if kind not in FIELDS:
        raise ValueError('Forme inconnue : point, line, circle, rectangle ou square attendu.')
    color = data.get('color')
    if (not isinstance(color, list) or len(color) != 3
            or any(type(n) is not int or not 0 <= n <= 255 for n in color)):
        raise ValueError('color doit contenir trois entiers RGB entre 0 et 255.')
    shape = {'shape': kind, 'color': color}
    for field in FIELDS[kind]:
        value = data.get(field)
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            raise ValueError(f'{field} doit être un nombre fini.')
        limit = HEIGHT if field in ('y', 'y1', 'y2', 'height') else WIDTH
        minimum = 0 if field in ('x', 'y', 'x1', 'y1', 'x2', 'y2') else 0.01
        if not minimum <= value <= limit:
            raise ValueError(f'{field} doit être compris entre {minimum} et {limit}.')
        shape[field] = value
    return shape


class Board:
    def __init__(self):
        self.shapes = []
        self.clients = set()
        self.lock = threading.RLock()

    def broadcast(self, message):
        # Les modifications et leur diffusion gardent le même ordre pour tous.
        raw = json.dumps(message, allow_nan=False)
        for socket in list(self.clients):
            try:
                socket.send(raw)
            except (ConnectionClosed, OSError):
                self.clients.discard(socket)

    def draw(self, shape):
        with self.lock:
            if len(self.shapes) >= MAX_SHAPES:
                raise ValueError('Tableau plein. Effacez-le avant de continuer.')
            self.shapes.append(shape)
            self.broadcast({'type': 'shape', 'shape': shape, 'count': len(self.shapes)})
            return len(self.shapes)

    def clear(self):
        with self.lock:
            self.shapes.clear()
            self.broadcast({'type': 'clear'})

    def handle_socket(self, socket):
        with self.lock:
            self.clients.add(socket)
            try:
                socket.send(json.dumps({'type': 'snapshot', 'shapes': self.shapes,
                                        'clients': len(self.clients)}))
                self.broadcast({'type': 'clients', 'count': len(self.clients)})
            except (ConnectionClosed, OSError):
                self.clients.discard(socket)
                return
        try:
            # Les dessins arrivent par HTTP. Ce canal sert à diffuser le tableau.
            for _ in socket:
                pass
        except ConnectionClosed:
            pass
        finally:
            with self.lock:
                self.clients.discard(socket)
                self.broadcast({'type': 'clients', 'count': len(self.clients)})


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, board, ws_port, **kwargs):
        self.board = board
        self.ws_port = ws_port
        super().__init__(*args, **kwargs)

    def send_data(self, status, content, content_type='application/json; charset=utf-8'):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/config':
            self.send_data(200, {'ws_port': self.ws_port, 'width': WIDTH, 'height': HEIGHT})
        elif path == '/status':
            with self.board.lock:
                self.send_data(200, {'status': 'ok', 'shapes': len(self.board.shapes),
                                     'clients': len(self.board.clients)})
        elif path in ('/', '/index.html', '/style.css', '/app.js'):
            filename = 'index.html' if path == '/' else path.lstrip('/')
            types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript'}
            try:
                content = (WEB / filename).read_bytes()
                self.send_data(200, content, types[Path(filename).suffix] + '; charset=utf-8')
            except OSError:
                self.send_data(500, {'error': 'Fichier de l’interface introuvable.'})
        else:
            self.send_data(404, {'error': 'Adresse inconnue.'})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ('/draw', '/clear'):
            self.send_data(404, {'error': 'Adresse inconnue.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 4096:
                self.send_data(413, {'error': 'Requête trop volumineuse.'})
                return
            raw = self.rfile.read(length)
            if path == '/clear':
                self.board.clear()
                self.send_data(200, {'status': 'ok'})
                return
            shape = validate_shape(json.loads(raw))
            count = self.board.draw(shape)
            self.send_data(200, {'status': 'ok', 'count': count})
        except (ValueError, UnicodeDecodeError) as error:
            self.send_data(400, {'error': str(error)})

    def log_message(self, format, *args):
        # Le terminal reste disponible pour les messages de lancement.
        pass


class App:
    def __init__(self, host='127.0.0.1', port=8000, ws_port=8766):
        self.board = Board()
        self.ws = serve(self.board.handle_socket, host, ws_port, max_size=4096,
                        max_queue=8, open_timeout=5)
        self.ws_port = self.ws.socket.getsockname()[1]
        try:
            self.http = ThreadingHTTPServer((host, port),
                partial(Handler, board=self.board, ws_port=self.ws_port))
        except OSError:
            self.ws.shutdown()
            raise
        self.http.daemon_threads = True
        self.port = self.http.server_address[1]
        self.threads = []

    def start(self):
        for target in (self.ws.serve_forever, self.http.serve_forever):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self.threads.append(thread)

    def stop(self):
        self.http.shutdown()
        self.http.server_close()
        self.ws.shutdown()
        for thread in self.threads:
            thread.join(timeout=3)


def main():
    parser = argparse.ArgumentParser(description='Serveur du tableau interactif')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--ws-port', type=int, default=8766)
    args = parser.parse_args()
    try:
        app = App(args.host, args.port, args.ws_port)
    except OSError as error:
        print(f'Le serveur ne peut pas démarrer : {error}')
        raise SystemExit(1)
    app.start()
    address = '127.0.0.1' if args.host == '0.0.0.0' else args.host
    print(f'Tableau : http://{address}:{app.port}')
    print(f'WebSocket : port {app.ws_port} · Ctrl+C pour arrêter')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print('\nArrêt du serveur.')
    finally:
        app.stop()


if __name__ == '__main__':
    main()
