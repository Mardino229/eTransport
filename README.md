# eTransport MTDI Bénin - Transport Universitaire (COUS-AC)

Application de suivi des bus en temps réel, de recommandation de trajets et d'aide à la décision pour le réseau de transport de l'Université d'Abomey-Calavi (COUS-AC).

---

## Sommaire
1. [Présentation du projet](#présentation-du-projet)
2. [Lancement en local](#lancement-en-local)
3. [Hypothèses et données de simulation](#hypothèses-et-données-de-simulation)
4. [Détail des cas d'usage](#détail-des-cas-dusage)
5. [Pour aller plus loin](#pour-aller-plus-loin)

---

## Lancement en local

### Prérequis
- Docker et Docker Compose installés.

### Commandes pour démarrer

```bash
git clone git@github.com:Mardino229/eTransport.git
cd eTransport
docker compose up --build
```

### URLs des services

- **Frontend (Interface web)** : http://localhost:3000
- **Backend API (Swagger)** : http://localhost:8000/docs
- **WebSocket (Positions GPS)** : ws://localhost:8000/ws/buses

---

## Hypothèses et données de simulation

Pour simuler le réseau sans données réelles au départ, les règles suivantes ont été appliquées :

- **Flotte** : 35 bus en circulation (capacité de 50 à 60 places).
- **Réseau** : 14 lignes et 15 arrêts principaux (UAC Campus, Étoile Rouge, ENEAM, Akpakpa, Godomey, Porto-Novo, Tori, etc.).
- **Télémétrie** : Les bus envoient leur position GPS toutes les 2 secondes vers Redis.
- **Profils d'affluence** : Demande multipliée par 3.0 le matin (06h30-09h10) et par 2.8 le soir (16h00-19h30).

---

## Détail des cas d'usage

### 1. Gestion de capacité
Affiche pour chaque bus le nombre de passagers à bord, la capacité totale et les places restantes.
- Route : `GET /api/v1/buses/live`

### 2. Analyse des arrêts
Calcule pour un arrêt donné le nombre total d'étudiants montés, descendus, en attente et le temps d'attente moyen.
- Route : `GET /api/v1/stops/{stop_id}/analytics`

### 3. Top 5 des itinéraires
Présente les 5 lignes les plus empruntées sur les dernières 24 heures avec leur volume de passagers et leur taux de saturation.
- Route : `GET /api/v1/routes/top5`

### 4. Recommandation intelligente et cas des 200 requêtes simultanées
L'étudiant indique sa position et sa destination. La fonction de score évalue les bus selon 4 critères :
- Temps d'arrivée à l'arrêt (ETA) - poids 0.35
- Distance de marche jusqu'à l'arrêt - poids 0.25
- Durée totale du trajet - poids 0.25
- Taux d'occupation du bus - poids 0.15 (+ une pénalité si le bus nécessite un demi-tour au terminus)

**Cas des 200 requêtes simultanées** : Chaque réservation diminue atomiquement un compteur Redis (`DECR`). Si les places d'un bus sont épuisées pendant les requêtes simultanées, les étudiants suivants sont orientés vers les alternatives suivantes sans conflit.
- Route : `POST /api/v1/recommendation`

### 5. Optimisation d'itinéraire (Aide à la décision)
Analyse les données du réseau et propose des actions chiffrées :
- Ajout de bus si la saturation dépasse 80% ou si la pression d'attente par bus est forte.
- Ajustement des fréquences si la saturation est entre 60% et 80%.
- Réallocation de bus si une ligne est sous-fréquentée avec plusieurs bus en service.
- Fusion de lignes si la fréquentation est inférieure à 50 passagers/jour.
- Route : `GET /api/v1/optimizations/suggestions`

---

## Pour aller plus loin

### 1. Recul sur mes choix

1. **Auto-hébergement du serveur OSRM** : Le projet utilise l'API publique d'OSRM (`router.project-osrm.org`) pour calculer les tracés routiers réels sur la carte et dans le simulateur. Avec plus de temps, héberger une instance OSRM locale dans un conteneur Docker (avec le fichier OpenStreetMap du Bénin) permettrait d'éviter les limites de requêtes de l'API publique et de réduire la latence des trajets à quelques millisecondes.
2. **Gestion du mode hors-ligne web** : Conserver en cache local (LocalStorage / Service Worker) les derniers horaires chargés pour qu'un étudiant sans connexion réseau à l'arrêt puisse toujours consulter les informations de passage.
3. **Option boîtier IoT vs application chauffeur** : Le choix d'un boîtier GPS autonome garantit un envoi continu et passif des positions (toutes les 2s) sans dépendre d'une action du chauffeur. Une application sur tablette chauffeur aurait permis la saisie d'incidents (bouchons, pannes), mais aurait introduit un risque d'oubli d'activation.

### 2. Dette technique

- **Authentification** : Les endpoints de l'API sont actuellement ouverts pour simplifier les tests du prototype. Une gestion par jetons JWT devra être ajoutée pour sécuriser les accès.
- **Modèle de trafic routier** : La vitesse des bus est fixe (32 km/h en moyenne). Le modèle ne prend pas encore en compte les variations fines d'embouteillages par tronçon. De plus les estimations sont faites à partir de données simulés (profils d'affluence) et non de données réelles collectées sur le terrain. Il faudrait d'abord collecter des données réelles pour avoir des estimations plus justes.
- **Tests automatisés** : Les validations ont été effectuées manuellement et via des requêtes de test. L'ajout d'une suite de tests automatisés (Pytest) sécurisera les futures évolutions.

### 3. Passage à l'échelle (50 000 étudiants et 300 bus)

- **Point de blocage principal** : La diffusion en direct des positions par WebSockets depuis un seul serveur FastAPI et la fréquence des écritures en base de données.
- **Solutions envisagées** :
  - Séparer la diffusion WebSocket sur un service dédié (Socket.IO ou Centrifugo).
  - Filtrer les données envoyées par zone géographique pour éviter que chaque étudiant ne reçoive la position de l'ensemble de la flotte.
  - Insérer les flux de passagers par lots (batchs toutes les 15 à 30 secondes) dans PostgreSQL au lieu d'écritures synchrone à chaque arrêt.

### 4. Données manquantes du terrain

1. **Mode d'équipement réel des bus** : On ne sait pas si la flotte du COUS-AC dispose de boîtiers GPS IoT dédiés, d'une application smartphone chauffeur ou d'un fournisseur GPS tiers. Le mode de collecte des positions devra être adapté selon l'équipement réel.
2. **Heure d'arrivée exacte des étudiants à l'arrêt** : Sans système de validation à l'arrêt (ex: scan de QR code à l'arrivée), il est impossible de savoir à quel moment précis un étudiant arrive à la station et combien de temps il y a réellement attendu. Le temps d'attente calculé reste donc une estimation.
4. **Historique des trajets étudiants** : Permettrait d'anticiper la demande par arrêt et de mieux répartir les bus avant la formation des files d'attente.

### 5. Mise en production (Première itération sur le terrain)

1. **Phase 1 (Pilote sur 1 ligne)** : Mettre en place une ou plusieurs lignes tests et équiper les bus sur ces lignes pour obtenir des données réelles. 
2. **Phase 2 (Ajustements)** : En fonction des données collectées améliorer les estimations effectués pour avoir des données plus juste et donc des recommandation pertinentes.
3. **Phase 3 (Déploiement général)** : Étendre le système aux autres lignes une fois la première phase validée. 
