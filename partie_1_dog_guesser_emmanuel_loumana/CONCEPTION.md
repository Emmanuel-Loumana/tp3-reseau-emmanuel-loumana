# Conception de Dog Guesser

## Ce que je voulais réaliser

J’ai limité le projet à la partie I du TP. Je voulais un jeu agréable à regarder, facile à lancer et dont le code reste adapté à mon niveau. J’ai demandé de soigner l’interface sans multiplier les fonctionnalités ni compliquer l’installation.

J’ai utilisé l’IA pour proposer une organisation des fichiers, générer le code et effectuer des vérifications. De mon côté, j’ai précisé les attentes, essayé le jeu et validé le résultat. Après cet essai, j’ai préféré garder cette version plutôt que d’ajouter des fonctions qui n’étaient pas nécessaires au TP.

## Les choix du projet

L’application utilise Tkinter pour rester en Python. L’interface laisse une grande place à la photo, avec quatre réponses et une correction immédiate. Pillow sert à afficher les images sans les déformer ni couper le chien. Les appels à Dog CEO utilisent requests et les échanges avec le serveur de records passent par websockets.

Une partie comporte dix manches de vingt secondes. Une bonne réponse rapporte des points, avec un bonus pour la rapidité et les bonnes réponses consécutives. Le chrono commence une fois la photo chargée.

Les parties sont enregistrées dans un fichier JSON sur le PC du joueur. Le serveur conserve les records dans un autre fichier et les transmet aux joueurs connectés. Cela suffit pour ce projet, sans installer de base de données. Les téléchargements et la connexion au serveur fonctionnent en arrière-plan pour que la fenêtre reste utilisable.

## Essai et lancement

J’ai testé le jeu et validé son fonctionnement général. J’ai aussi demandé un README avec des instructions courtes pour que le projet puisse être lancé après téléchargement. Le fichier launch.py démarre le serveur local et la fenêtre avec une seule commande.

## Limites

Il faut une connexion Internet pour récupérer les photos. Certaines races gardent leur nom anglais. Le serveur est prévu pour un usage sur un réseau privé : il n’y a pas de compte utilisateur et les scores envoyés par le jeu ne sont pas protégés contre la triche.
