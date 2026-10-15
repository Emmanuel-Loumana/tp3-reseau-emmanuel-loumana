# Dog Guesser

Une photo de chien, quatre races et 20 secondes pour répondre. Projet Python — TP3, partie I uniquement.

## Installer et jouer

Python **3.10 ou plus récent**, avec Tkinter, et une connexion Internet sont nécessaires.
Depuis le dossier décompressé, ouvrir un terminal :

```bash
python -m pip install -r requirements.txt
python launch.py
```

Sous Windows, `py` peut remplacer `python`. Après installation, un double-clic sur `lancer.bat` lance aussi le jeu. Tkinter est fourni avec l'installation classique de Python sous Windows (option Tcl/Tk). Sous Ubuntu/Debian, installer `python3-tk` si nécessaire.

Entrer un pseudo et cliquer sur **C’est parti**. Répondre en cliquant ou avec les touches **1 à 4**. Entrée permet de passer à la photo suivante après correction.

## Règles

- 10 photos, 20 secondes chacune. Le chrono démarre après le chargement.
- Bonne réponse : 100 points + 10 points par seconde restante (arrondis à l'entier inférieur).
- Série : +25 points par bonne réponse consécutive après la première, jusqu'à +100.
- Erreur ou temps écoulé : 0 point, la série retombe à zéro.
- Le résultat est sauvegardé à la fin des dix manches dans `data/scores.json`.
- Le serveur garde le meilleur score de chaque pseudo et les dix premiers dans `data/records.json`. Le podium se met à jour sans relancer le jeu.

Une photo qui ne charge pas peut être retentée sans pénalité. Si le serveur est indisponible, le jeu continue : le résultat reste local et attend la reconnexion tant que la fenêtre reste ouverte.

## Essayer avec deux joueurs

Sur un même PC : garder un serveur ouvert avec `python server.py`, puis ouvrir deux terminaux et lancer `python main.py` dans chacun. Les deux fenêtres reçoivent les mêmes nouveaux records. Arrêter avec Ctrl+C dans le terminal du serveur.

Sur deux PC du même réseau : sur le premier, lancer `python server.py --host 0.0.0.0`. Sur chaque PC, lancer `python main.py --server ws://ADRESSE_IP_DU_SERVEUR:8765` en remplaçant l'adresse. Autoriser Python sur le réseau privé si Windows le demande. Chaque PC doit avoir accès à Internet pour les photos.

## Fichiers

- `main.py` : interface Tkinter et déroulement de la partie.
- `game.py` : API Dog CEO, règles de score et sauvegarde locale.
- `server.py` : serveur WebSocket et fichier des records.
- `network.py` : connexion aux records en arrière-plan.
- `launch.py` : démarrage local en une commande.
- `CONCEPTION.md` : choix du projet et utilisation de l'IA.

Les sauvegardes se créent automatiquement. Aucun compte, clé d'API ni fichier `.env` n'est nécessaire. Aucun environnement virtuel n'est inclus.

Pour lancer les vérifications : `python -m unittest discover -s tests -v`.

Photos et liste des races : [Dog CEO](https://dog.ceo/dog-api/). Certaines races peu courantes conservent leur nom anglais. Le serveur de records est prévu pour un TP sur un réseau privé : il ne dispose pas d'authentification et les scores sont calculés par le client.
