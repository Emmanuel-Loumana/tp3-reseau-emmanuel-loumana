import concurrent.futures
import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path

import requests
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import App, validate_shape
from client import example


def receive(socket, kind):
    for _ in range(30):
        message = json.loads(socket.recv(timeout=3))
        if message['type'] == kind:
            return message
    raise AssertionError(f'Message {kind} non reçu')


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App(port=0, ws_port=0)
        cls.app.start()
        cls.url = f'http://127.0.0.1:{cls.app.port}'
        cls.ws = f'ws://127.0.0.1:{cls.app.ws_port}'

    @classmethod
    def tearDownClass(cls):
        cls.app.stop()

    def setUp(self):
        requests.post(self.url + '/clear', timeout=3).raise_for_status()

    def test_five_shapes_reach_two_boards(self):
        shapes = [
            {'shape':'point', 'x':30, 'y':30, 'color':[120,200,102]},
            {'shape':'line', 'x1':30, 'y1':30, 'x2':60, 'y2':60, 'color':[210,110,200]},
            {'shape':'circle', 'x':40, 'y':40, 'radius':20, 'color':[220,140,210]},
            {'shape':'rectangle', 'x':40, 'y':40, 'width':200, 'height':100, 'color':[120,220,210]},
            {'shape':'square', 'x':30, 'y':30, 'cote':80, 'color':[210,110,200]},
        ]
        with connect(self.ws) as first, connect(self.ws) as second:
            self.assertEqual(receive(first,'snapshot')['shapes'], [])
            receive(second,'snapshot')
            for count,shape in enumerate(shapes,1):
                response = requests.post(self.url + '/draw', json=shape, timeout=3)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['count'],count)
                self.assertEqual(receive(first,'shape')['shape'],shape)
                self.assertEqual(receive(second,'shape')['shape'],shape)
        with connect(self.ws) as reconnected:
            self.assertEqual(receive(reconnected,'snapshot')['shapes'],shapes)
            requests.post(self.url + '/clear',timeout=3)
            self.assertEqual(receive(reconnected,'clear'),{'type':'clear'})
        self.assertEqual(requests.get(self.url + '/status',timeout=3).json()['shapes'],0)

    def test_invalid_messages_do_not_break_server(self):
        valid = {'shape':'point','x':1,'y':1,'color':[0,0,0]}
        cases = [None, [], {}, {'shape':[]}, {**valid,'x':-1},
                 {**valid,'x':float('inf')}, {**valid,'x':True},
                 {**valid,'x':10**500}, {**valid,'color':[256,0,0]},
                 {**valid,'color':[True,0,0]}, {**valid,'shape':'triangle'},
                 {'shape':'circle','x':5,'y':5,'radius':0,'color':[0,0,0]}]
        for case in cases:
            response = requests.post(self.url+'/draw', data=json.dumps(case),timeout=3)
            self.assertEqual(response.status_code,400,(case,response.text))
        self.assertEqual(requests.post(self.url+'/draw',data='{oops',timeout=3).status_code,400)
        self.assertEqual(requests.post(self.url+'/draw',data='x'*5000,timeout=3).status_code,413)
        self.assertEqual(requests.post(self.url+'/unknown',json=valid,timeout=3).status_code,404)
        self.assertEqual(requests.post(self.url+'/draw',json=valid,timeout=3).status_code,200)

    def test_simultaneous_http_clients(self):
        def draw(i):
            return requests.post(self.url+'/draw',json={'shape':'point','x':i,'y':i,
                                 'color':[0,0,0]},timeout=5).status_code
        with connect(self.ws) as first, connect(self.ws) as second:
            receive(first,'snapshot'); receive(second,'snapshot')
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                self.assertEqual(list(pool.map(draw,range(20))),[200]*20)
            a=[receive(first,'shape') for _ in range(20)]
            b=[receive(second,'shape') for _ in range(20)]
            self.assertEqual(a,b)
            self.assertEqual([m['count'] for m in a],list(range(1,21)))

    def test_python_client_interactive_and_example(self):
        # Une saisie erronée, puis un carré complet et le dessin d'exemple.
        answers='5\nnon\n40\n50\n80\n300,0,0\n100,120,140\n6\n0\n'
        result=subprocess.run([sys.executable,str(ROOT/'client.py'),'--server',self.url],
                              input=answers,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Forme envoyée',result.stdout)
        self.assertIn('12 forme(s) envoyée(s)',result.stdout)
        with connect(self.ws) as board:
            shapes=receive(board,'snapshot')['shapes']
            self.assertEqual(len(shapes),13)
            self.assertEqual(shapes[0],{'shape':'square','x':40,'y':50,'cote':80,'color':[100,120,140]})
            self.assertEqual(shapes[1:],example())

    def test_web_files_and_config(self):
        for path,content_type in [('/','text/html'),('/style.css','text/css'),('/app.js','text/javascript')]:
            response=requests.get(self.url+path,timeout=3)
            self.assertEqual(response.status_code,200)
            self.assertIn(content_type,response.headers['Content-Type'])
        self.assertEqual(requests.get(self.url+'/config',timeout=3).json()['ws_port'],self.app.ws_port)
        self.assertEqual(requests.get(self.url+'/missing',timeout=3).status_code,404)


if __name__ == '__main__':
    unittest.main()
