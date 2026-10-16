# Partie II — Tableau interactif

**Atelier commun** est un tableau partagé dans le navigateur. Un client Python demande les formes en terminal, les envoie par HTTP, puis le serveur les diffuse en temps réel aux tableaux ouverts par WebSocket.

Ce dossier est indépendant du jeu Dog Guesser de la partie I.

## Installer et lancer

Il faut Python 3.10 ou plus récent et un navigateur récent. Ouvrir un terminal **dans ce dossier**, puis lancer :

```bash
python -m pip install -r requirements.txt
python launch.py
```

Sous Windows, `py` peut remplacer `python`. Après l’installation, un double-clic sur `lancer.bat` convient aussi. Dans VS Code ou PyCharm, ouvrir ce dossier et utiliser le terminal de l’éditeur.

Le navigateur s’ouvre sur **http://127.0.0.1:8000**. Le menu de dessin reste dans le terminal : choisir une forme, saisir ses coordonnées, ses dimensions et sa couleur. Pour essayer rapidement, choisir **6 — Dessin d’exemple**. Choisir **0** pour quitter ; le serveur démarré par le lanceur s’arrête aussi.

Si le navigateur ne s’ouvre pas automatiquement, saisir son adresse à la main. Internet n’est plus nécessaire après l’installation des dépendances.

## Utiliser le tableau

- Le tableau mesure 1000 × 640. L’origine `(0,0)` est en haut à gauche.
- Pour un cercle, `x` et `y` indiquent son centre. Pour un rectangle ou un carré, ils indiquent le coin supérieur gauche.
- Les couleurs sont saisies en RGB, par exemple `120,200,102`. Entrée conserve la couleur proposée.
- Les nouvelles formes se placent au-dessus des précédentes. Ce qui dépasse du tableau est masqué.
- **Repères** affiche ou masque la grille ; **Enregistrer l’image** exporte le dessin en PNG.
- **Effacer le tableau** efface le dessin pour tous, après confirmation.

Le dessin est conservé en mémoire tant que le serveur tourne. Un nouvel onglet ou une reconnexion retrouve le dessin courant. Un redémarrage du serveur remet le tableau à zéro. La limite est de 2000 formes par tableau.

## Plusieurs clients

Pour laisser le serveur ouvert indépendamment du lanceur :

```bash
python server.py
```

Ouvrir **http://127.0.0.1:8000** dans deux onglets, puis lancer `python client.py` dans un autre terminal. Plusieurs clients Python peuvent envoyer des formes en même temps. Ctrl+C arrête le serveur.

Sur plusieurs PC du même réseau, lancer le serveur avec `python server.py --host 0.0.0.0`. Les autres PC ouvrent `http://IP_DU_SERVEUR:8000` et utilisent `python client.py --server http://IP_DU_SERVEUR:8000`. Remplacer `IP_DU_SERVEUR` par l’adresse du PC serveur et autoriser les ports **8000 et 8766** sur le réseau privé si le pare-feu le demande.

Les ports peuvent être changés : `python server.py --port 8001 --ws-port 8767`. Dans ce cas, ouvrir le tableau sur le port HTTP choisi et utiliser le même port avec `client.py --server`.

## API du sujet

Chaque forme est envoyée avec **POST /draw** et un corps JSON. Les cinq exemples suivants sont acceptés :

```json
{"shape":"point","x":30,"y":30,"color":[120,200,102]}
{"shape":"line","x1":30,"y1":30,"x2":60,"y2":60,"color":[210,110,200]}
{"shape":"circle","x":40,"y":40,"radius":20,"color":[220,140,210]}
{"shape":"rectangle","x":40,"y":40,"width":200,"height":100,"color":[120,220,210]}
{"shape":"square","x":30,"y":30,"cote":80,"color":[210,110,200]}
```

La couleur est une liste de trois entiers en JSON : un tuple Python est converti en liste par `requests`. Une requête valide reçoit un statut HTTP 200 ; une saisie invalide reçoit un statut 400 avec un message d’erreur. **POST /clear** est un ajout pour effacer le tableau.

## Fichiers et vérifications

- `server.py` : API HTTP, validation et diffusion WebSocket.
- `client.py` : saisie des formes et envoi au serveur.
- `web/` : page HTML, styles et affichage Canvas.
- `launch.py` : démarrage local en une commande.
- `CONCEPTION.md` : choix du projet et aide de l’IA.

Vérifications : `python -m unittest discover -s tests -v`.

Le projet est prévu pour un usage local ou sur un réseau privé, sans compte utilisateur. Aucun environnement virtuel ni fichier `.env` n’est fourni.
