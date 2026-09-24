# Instructions d'Installation et de Lancement (eTransport)

Ce document explique comment installer et démarrer l'application eTransport en local sur votre machine.

---

## 1. Prérequis

Avant de commencer, assurez-vous d'avoir installé sur votre ordinateur :

- **Docker** (version 24.0 ou supérieure)
- **Docker Compose** (version 2.20 ou supérieure)
- **Git**

---

## 2. Étapes d'installation et de lancement

### Étape 1 : Cloner le dépôt Git
Ouvrez un terminal et exécutez la commande suivante :

```bash
git clone git@github.com:Mardino229/eTransport.git
cd eTransport
```

### Étape 2 : Démarrer l'application avec Docker Compose
Pour construire les images et démarrer tous les conteneurs (PostgreSQL, Redis, Backend, Simulateur et Frontend) :

```bash
docker compose up --build
```

*(Note : Pour lancer l'application avec rechargement automatique des modifications en développement, vous pouvez utiliser `docker compose up --watch`)*

---

## 3. Accès aux interfaces et services

Une fois les conteneurs démarrés, vous pouvez accéder aux services aux adresses suivantes :

| Service | Adresse URL | Description |
|---|---|---|
| **Frontend Web** | [http://localhost:3000](http://localhost:3000) | Carte Leaflet interactive et Tableau de bord Analytics |
| **Backend API (Swagger Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentation interactive FastAPI et test des endpoints |
| **WebSocket live** | `ws://localhost:8000/ws/buses` | Flux temps réel de la position des 35 bus |
| **Base de données PostgreSQL** | `localhost:5433` | PostgreSQL 15 + PostGIS (`user: etransport`, `pass: etransport_pass`) |
| **Cache Redis** | `localhost:6379` | In-memory cache et verrous de réservation |

---

## 4. Tester l'application

1. **Voir la carte des bus en direct** : Allez sur `http://localhost:3000`. Vous verrez les 35 bus se déplacer en temps réel le long des 14 lignes.
2. **Tester la recommandation de bus** : Dans le formulaire de gauche, choisissez votre arrêt de destination (ex: `Campus UAC`) et cliquez sur "Obtenir une recommandation".
3. **Consulter les statistiques et conseils de régulation** : Ouvrez l'onglet "Analytics & Régulation" pour voir le Top 5 des lignes et les suggestions d'optimisation.

---

## 5. Arrêter et réinitialiser l'application

### Arrêter les conteneurs :
Appuyez sur `Ctrl + C` dans le terminal ou lancez :
```bash
docker compose down
```

### Réinitialiser complètement la base de données (si besoin) :
Pour supprimer les données enregistrées et repartir d'une base vierge :
```bash
docker compose down -v
docker compose up --build
```
