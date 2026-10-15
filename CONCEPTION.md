# Conception — Dog Guesser

## Intentions données à l'IA

Le cahier des charges personnel était de faire uniquement la partie I, avec un rendu visuel soigné, un lancement facile et du code compréhensible par un étudiant. L'IA a été sollicitée pour lire le sujet, proposer une organisation, écrire le code et le vérifier. Le code n'a donc pas été rédigé intégralement à la main par l'étudiant.

## Choix retenus

- **Python uniquement** : Tkinter pour la fenêtre, plutôt qu'un site HTML/JavaScript. Le Canvas permet de dessiner une interface personnalisée sans ajouter de framework graphique.
- **Une présentation sobre** : fond crème, vert foncé et orange, grande photo, quatre boutons et une correction immédiate. L'image est conservée entière pour ne pas couper les détails utiles.
- **Un jeu court** : dix manches de vingt secondes. La précision rapporte la base des points ; la vitesse et les séries ajoutent un bonus.
- **Des outils limités** : `requests` et `websockets`, présents dans le cours réseau. Pillow a été ajouté pour lire et redimensionner les photos JPEG dans Tkinter. Tkinter appartient à la bibliothèque standard de Python ; ces deux choix graphiques restent à vérifier avec les outils autorisés par l'enseignant.
- **Deux fichiers JSON distincts** : les parties sur le PC du joueur, les records sur le serveur. Pas de base de données pour ce petit projet.
- **Des tâches en arrière-plan** : les photos et les messages réseau ne doivent pas figer les boutons ou le chrono. Une file transmet les résultats à la fenêtre.

## Validation et rendu

Un essai du jeu a été validé. Le projet est fourni dans un dépôt GitHub public avec les instructions de lancement. Avant la présentation, il reste à relire les fonctions de score, les appels à l’API et les messages WebSocket pour pouvoir expliquer leur fonctionnement.

## Limites assumées

Le jeu dépend d'Internet et de la qualité des photos de Dog CEO. Le serveur est destiné à un réseau privé ; un client modifié pourrait envoyer un score inventé. Ajouter des comptes ou une protection contre la triche compliquerait inutilement ce TP.
