"""Lancement local : serveur, navigateur et client dans le terminal."""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def main():
    process = None
    try:
        import requests
        from client import run
        url = 'http://127.0.0.1:8000'
        # On réutilise un serveur du tableau déjà ouvert, s'il existe.
        def available():
            try:
                response = requests.get(url + '/config', timeout=1)
                data = response.json()
                return response.status_code == 200 and data.get('width') == 1000 and 'ws_port' in data
            except (requests.RequestException, ValueError, AttributeError):
                return False
        if not available():
            process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('server.py'))])
            for _ in range(30):
                if available():
                    break
                if process.poll() is not None:
                    raise RuntimeError('Le serveur n’a pas démarré. Consulte le message ci-dessus.')
                time.sleep(0.2)
            else:
                raise RuntimeError('Le serveur ne répond pas sur le port 8000.')
        print('Le tableau s’ouvre dans le navigateur : ' + url)
        webbrowser.open(url)
        run(url)
    except ImportError:
        print('Installe les dépendances : python -m pip install -r requirements.txt')
        raise SystemExit(1)
    except (RuntimeError, KeyboardInterrupt) as error:
        print(error)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


if __name__ == '__main__':
    main()
