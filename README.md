# Agent de Sécurité UPHF

Bienvenue sur le dépôt du projet de chatbot d'éveil à la cybersécurité de l'UPHF. 

## 🌿 Git Flow : Comment travailler sur ce projet

Nous utilisons **Git Flow** pour organiser notre travail et éviter les conflits. 

### Les branches principales
* **`main`** : Contient uniquement le code stable et fonctionnel (production).
* **`develop`** : Branche d'intégration continue. C'est ici que toutes les nouvelles fonctionnalités sont fusionnées.

### Créer une nouvelle fonctionnalité
Ne travaillez **jamais** directement sur `main` ou `develop`. 
Pour chaque tâche, créez une branche `feature` depuis `develop` :

1. Démarrer la fonctionnalité :
```bash
   git flow feature start nom-de-ma-tache