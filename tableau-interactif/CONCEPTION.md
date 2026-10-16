# Conception du tableau interactif

## L’objectif

Pour cette deuxième partie, j’ai demandé de garder le même équilibre que pour le jeu : une interface soignée, des fichiers faciles à comprendre et un lancement court. J’ai aussi demandé que les deux projets restent distincts dans le dépôt.

L’IA a aidé à organiser cette partie, à écrire le code et à vérifier les échanges réseau. Les consignes que j’ai données ont surtout porté sur la simplicité d’utilisation et le niveau de complexité. Les vérifications portent sur le fonctionnement du client, de l’API et de la synchronisation entre les tableaux.

## L’organisation retenue

Le client Python demande le type de forme, les positions, les dimensions et la couleur. Il utilise requests pour envoyer les données à POST /draw, avec les noms de champs du sujet. Les tuples RGB donnés dans les exemples deviennent des listes dans le JSON.

Le serveur utilise le module http.server de Python pour l’API et les fichiers de la page, puis websockets pour transmettre les formes aux navigateurs. Deux ports séparent HTTP et WebSocket. Le tableau découvre automatiquement le port WebSocket auprès du serveur, ce qui évite de modifier le JavaScript au lancement.

Le navigateur affiche les formes sur un Canvas de 1000 × 640. Cette taille reste fixe pour que tous les utilisateurs retrouvent les mêmes positions, même avec des fenêtres de tailles différentes. Les formes se superposent dans leur ordre d’arrivée.

## Les ajouts utiles

Le serveur garde le dessin en mémoire pour qu’un nouvel onglet retrouve le tableau courant. Une reconnexion recharge aussi ce dessin. Il n’y a pas de fichier de sauvegarde ni de base de données : arrêter le serveur termine la session.

Le client propose un dessin d’exemple composé des formes du sujet. L’interface permet de masquer les repères, d’exporter une image et d’effacer le tableau après confirmation. Ces ajouts facilitent l’essai sans changer le principe client HTTP → serveur → tableaux WebSocket.

## Les vérifications et les limites

Les tests couvrent les cinq formes, les requêtes incorrectes, deux tableaux connectés, les envois simultanés, le retour du dessin après reconnexion et l’effacement. Le client en terminal est également lancé avec des saisies pour vérifier son fonctionnement.

Le projet est destiné à un réseau privé. Il n’y a pas d’authentification et tous les utilisateurs peuvent effacer le tableau. La limite de 2000 formes évite de conserver indéfiniment des dessins en mémoire.
