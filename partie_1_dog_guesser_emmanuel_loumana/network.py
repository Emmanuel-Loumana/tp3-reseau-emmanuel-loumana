"""Le réseau tourne dans un thread ; seule l'interface modifie les widgets."""
import json
import threading
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed


class RecordsClient:
    def __init__(self, url, events):
        self.url = url
        self.events = events
        self.pending = []
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def submit(self, record):
        with self.lock:
            self.pending.append({'type': 'score', **record})

    def run(self):
        while not self.stopped.is_set():
            try:
                with connect(self.url, open_timeout=3, max_size=16384) as socket:
                    self.events.put(('connection', True))
                    outgoing = None
                    while not self.stopped.is_set():
                        if outgoing is None:
                            with self.lock:
                                outgoing = self.pending[0] if self.pending else None
                            if outgoing:
                                socket.send(json.dumps(outgoing))
                        # Attendre l'accusé avant de retirer un score de la file.
                        while not self.stopped.is_set():
                            try:
                                data = json.loads(socket.recv(timeout=0.2))
                            except TimeoutError:
                                break
                            if data.get('type') == 'records':
                                self.events.put(('records', data['records']))
                            elif data.get('type') in ('saved', 'error'):
                                if outgoing:
                                    with self.lock:
                                        self.pending.pop(0)
                                    outgoing = None
                                self.events.put(('sync', data.get('type') == 'saved'))
                        self.stopped.wait(0.1)
            except (OSError, ConnectionClosed, ValueError, TimeoutError):
                self.events.put(('connection', False))
                self.stopped.wait(3)
