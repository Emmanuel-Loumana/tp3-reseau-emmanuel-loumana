"""Lance le serveur local et la fenêtre avec une seule commande."""
import socket
import subprocess
import sys
from pathlib import Path


def main():
    server = None
    try:
        try:
            with socket.create_connection(('127.0.0.1', 8765), timeout=1):
                pass  # Un serveur est déjà lancé : les fenêtres partagent les records.
        except OSError:
            server = subprocess.Popen([sys.executable, str(Path(__file__).with_name('server.py'))])
        from main import main as run_game
        run_game()
    except ImportError as error:
        print(f'Dépendance manquante : {error}')
        print('Installe les dépendances : python -m pip install -r requirements.txt')
        input('Entrée pour fermer…')
    finally:
        if server is not None:
            server.terminate()
            server.wait()


if __name__ == '__main__':
    main()
