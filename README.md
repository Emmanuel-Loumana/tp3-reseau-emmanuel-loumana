# Dog Guesser

Projet Python réalisé pour la partie I du TP3. Le principe : reconnaître la race d’un chien parmi quatre propositions à partir d’une photo de [Dog CEO](https://dog.ceo/dog-api/).

## Installation et lancement

Il faut Python 3.10 ou plus récent et une connexion Internet.

1. Télécharger le projet avec **Code → Download ZIP**, puis le décompresser.
2. Ouvrir un terminal dans le dossier contenant `launch.py`.
3. Installer les dépendances, puis lancer le jeu :

```bash
python -m pip install -r requirements.txt
python launch.py
```

Sous Windows, remplacer `python` par `py` si nécessaire. Une fois les dépendances installées, un double-clic sur `lancer.bat` permet aussi de jouer.

VS Code et PyCharm conviennent : ouvrir le dossier du projet et saisir les mêmes commandes dans le terminal de l’éditeur.

Tkinter est normalement fourni avec Python sous Windows, avec l’option Tcl/Tk de l’installateur. Sous Ubuntu ou Debian, installer `python3-tk` s’il manque.

## Jouer

Saisir un pseudo, puis cliquer sur **C’est parti**. Chaque partie compte dix photos, avec vingt secondes pour répondre à chacune. Le chrono démarre après le chargement de l’image.

Cliquer sur une réponse ou utiliser les touches **1 à 4**. Après la correction, cliquer sur le bouton suivant ou appuyer sur Entrée.

Une bonne réponse rapporte 100 points, auxquels s’ajoutent :
- un bonus de vitesse : dix points par seconde restante, arrondi à l’entier inférieur ;
- un bonus de série : 25 points par bonne réponse consécutive après la première, jusqu’à 100 points.

Une erreur ou un temps écoulé rapporte zéro et remet la série à zéro. Une photo qui ne charge pas peut être retentée sans pénalité.

## Scores et records

À la fin des dix manches, cliquer sur **Voir mon résultat** pour enregistrer la partie dans `data/scores.json`. Le serveur conserve les dix meilleurs records, avec un seul score par pseudo, dans `data/records.json`. Le podium est actualisé dans les fenêtres connectées.

Ces fichiers sont créés automatiquement. Si le serveur est indisponible, le jeu reste utilisable et le résultat est sauvegardé sur le PC. L’envoi au serveur attend la reconnexion tant que la fenêtre reste ouverte.

## Tester les records avec deux fenêtres

Démarrer le serveur dans un terminal :

```bash
python server.py
```

Puis lancer `python main.py` dans deux autres terminaux. Les nouveaux records apparaissent dans les deux fenêtres. Pour arrêter le serveur, utiliser Ctrl+C.

Sur deux PC du même réseau, démarrer le serveur avec :

```bash
python server.py --host 0.0.0.0
```

Sur chaque PC, lancer le jeu en remplaçant l’adresse ci-dessous par l’adresse IP du PC serveur :

```bash
python main.py --server ws://ADRESSE_IP_DU_SERVEUR:8765
```

Autoriser Python sur le réseau privé si le pare-feu le demande. Les deux PC doivent avoir accès à Internet pour les photos.

## Organisation

- `main.py` : interface et déroulement d’une partie.
- `game.py` : appels à Dog CEO, calcul des points et sauvegardes locales.
- `server.py` : serveur des records.
- `network.py` : connexion du jeu au serveur.
- `launch.py` : lancement du serveur local et du jeu.
- `CONCEPTION.md` : choix du projet et utilisation de l’IA.

Pour exécuter les tests :

```bash
python -m unittest discover -s tests -v
```

Le serveur est prévu pour un réseau privé et ne dispose pas d’authentification. Certaines races conservent leur nom anglais.
