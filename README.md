# Test Technique MTDI Bénin — Optimisation du Transport Universitaire (COUS-AC)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostGIS](https://img.shields.io/badge/PostGIS-15--3.3-336791?logo=postgresql)](https://postgis.net)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis)](https://redis.io)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com)

> **Projet de Test Technique**
---

## 💻 Instructions d'Installation et Lancement en Local

### 1. Préréquis
- **Docker** ($\ge 24.0$) et **Docker Compose** ($\ge 2.20$)
- **Git**

### 2. Procédure de lancement

```bash
# 1. Cloner le dépôt
git clone <URL_DU_REPO>
cd etransport

# 2. Lancer l'ensemble des services via Docker Compose
docker compose up --build
```

### 3. Accès aux interfaces et APIs

| Service | URL | Description |
|---|---|---|
| **Tableau de Bord Frontend** | [http://localhost:3000](http://localhost:3000) | Application React + Leaflet (Carte live & Analytics) |
| **Documentation API (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Endpoints REST interactifs |
| **WebSocket Temps Réel** | `ws://localhost:8000/ws/buses` | Flux direct de télémétrie des bus |

---

## 📊 Hypothèses de Simulation & Données (Section 2.1)

Le réseau universitaire de référence est modélisé à partir de la cartographie réelle du **COUS-AC (Université d'Abomey-Calavi)** :

| Paramètre | Valeur simulée | Justification & Détails |
|---|---|---|
| **Flotte de bus** | **35 bus** (Capacité : 50 à 60 places) | Adapté à la taille de la flotte universitaire du COUS-AC. |
| **Réseau routier** | **14 lignes** desservant **15 arrêts** | Couvre Abomey-Calavi, Cotonou (ENEAM, Akpakpa, Ganhi, Fidjrossè), Godomey, Porto-Novo, Tori, etc. |
| **Fréquence de rafraîchissement** | Télémétrie GPS toutes les **2 secondes** | Assure une expérience temps réel fluide sur la carte sans engorger le réseau. |
| **Mode de télémétrie** | **Boîtier IoT autonome** (GPS/4G) | Télémétrie passive émise automatiquement sans intervention humaine du chauffeur (2s). |
| **Volumétrie moyenne** | **~5 000 passagers / jour** | Hypothèse de charge quotidienne basée sur la population étudiante active. |
| **Profils d'affluence (Rush)** | **Matin (06h30–09h10)** : $\times 3.0$<br>**Soir (16h00–19h30)** : $\times 2.8$ | Modélise les départs vers les amphis le matin et le retour vers les logements le soir. |

---

## 🎯 Validation des 5 Cas d'Usage Métier

### Cas d'Usage 1 — Gestion de Capacité
- **Endpoint** : `GET /api/v1/buses/live`
- **Mécanisme** : Pour chaque bus, le système calcule le taux de remplissage ($\frac{\text{passagers}}{\text{capacité}} \times 100$) et les places restantes en temps réel depuis Redis.

### Cas d'Usage 2 — Analyse des Arrêts
- **Endpoint** : `GET /api/v1/stops/{stop_id}/analytics`
- **Mécanisme** : Calcule les flux cumulés sur 24h (montés, descendus, en attente) et le temps moyen d'attente estimé à quai.

### Cas d'Usage 3 — Top 5 des Itinéraires
- **Endpoint** : `GET /api/v1/routes/top5`
- **Mécanisme** : Requête d'agrégation SQL identifiant les 5 lignes les plus empruntées avec leur nombre de passagers et leur taux d'occupation.

### Cas d'Usage 4 — Recommandation Intelligente & Cas Limite
- **Endpoint** : `POST /api/v1/recommendation`
- **Fonction de Score Explicite (Score le plus petit = Meilleur bus)** :
  $$\text{Score} = 0.35 \times \hat{\text{ETA}} + 0.25 \times \hat{\text{Marche}} + 0.25 \times \hat{\text{Trajet}} + 0.15 \times \text{Remplissage} + \text{Pénalité}_{\text{demi-tour}}$$
  - **Pondérations** : L'ETA ($0.35$) et les contraintes de déplacement ($0.50$) sont prioritaires pour l'étudiant.
  - **Gestion dynamique** : Détecte si le bus va vers la destination ou nécessite un demi-tour au terminus ($+0.15$ de pénalité).
- **Traitement du cas limite (200 requêtes simultanées — Herding Effect)** :  
  L'attribution de siège utilise un `DECR` **atomique dans Redis** (`bus:<id>:reserved_seats`, TTL 60s). Si le compteur tombe à 0, le système bascule automatiquement et de manière transparente le 201ᵉ étudiant vers le bus candidat alternatif suivant.

### Cas d'Usage 5 — Optimisation d'Itinéraire
- **Endpoint** : `GET /api/v1/optimizations/suggestions`
- **Mécanisme** : Analyse la saturation réelle ($\frac{\text{passagers}}{\text{capacité offerte}}$) et la pression par bus ($\frac{\text{attente}}{\text{nombre de bus}}$) pour générer des actions chiffrées :
  - `add_bus` : Si Saturation $> 80\%$ ou Pression $> 5$ étudiants/bus.
  - `reschedule` : Si Saturation entre $60\%$ et $80\%$.
  - `reallocate_bus` : Si Saturation $< 30\%$ et flotte $\ge 2$ bus.
  - `merge_lines` : Si très faible fréquentation ($< 50$ passagers/24h).

---

## 🚀 Pour aller plus loin

### 1. Recul sur vos choix
*Qu'aurions-nous fait différemment dès le départ, en connaissant ce que nous savons maintenant ?*

1. **Architecture de Messagerie IoT (Redis Streams vs Pub/Sub)** :  
   Nous avons utilisé Redis Pub/Sub pour diffuser les positions GPS. Pub/Sub étant un mode *fire-and-forget* éphémère, nous utiliserions **Redis Streams** ou **NATS** pour garantir la persistance des séries temporelles GPS et faciliter le rejeu de données en cas de coupure du backend.
2. **Calcul d'itinéraires sur graphe routier (OSRM / pgRouting)** :  
   Les ETAs et trajectoires entre arrêts s'appuient sur une interpolation Haversine. Dès le départ, l'intégration du réseau OpenStreetMap de la métropole béninoise via un moteur OSRM dédié aurait permis d'obtenir des temps de parcours tenant compte du réseau routier réel.
3. **Isolation des conteneurs de simulation** :  
   Au lieu d'un simulateur unique gérant les 35 bus dans une boucle `asyncio`, nous isolerions les bus sous forme de micro-services indépendants pour modéliser plus fidèlement des boîtiers IoT autonomes.
4. **Choix du mode de Géolocalisation (Boîtier IoT autonome vs Écran/App Chauffeur)** :  
   - **Architecture retenue (Boîtier IoT autonome embarqué)** : La position GPS est émise de façon 100% passive et automatique dès le démarrage du bus. Cela garantit une haute fréquence constante (2s) et zéro dépendance vis-à-vis d'une manipulation humaine.
   - **Impact si la géolocalisation provenait d'un écran/smartphone Chauffeur** :
     - *Compromis & Risques* : Dépendance humaine (risque d'oubli d'activation de l'app, batterie faible, fermeture accidentelle) et baisse de fréquence GPS (5–15s pour préserver la batterie).
     - *Opportunités métier* : Permettrait en contrepartie au chauffeur d'enrichir les données en déclarant manuellement les départs de terminus, les pannes, les bouchons ou la prise en charge des étudiants.

---

### 2. Dette technique
*Quelles dettes techniques avons-nous volontairement acceptées ?*

| Dette Technique | Justification métier / Arbitrage | Plan d'amélioration |
|---|---|---|
| **Absence d'Authentification (JWT)** | Focalisation sur la logique algorithmique (recommandation & régulation). | Ajouter un middleware FastAPI OAuth2 / JWT. |
| **Heuristique d'attente à quai** | Estimation du temps d'attente basée sur le nombre de personnes bloquées. | Remplacer par un modèle de file d'attente M/M/1. |
| **Plafond de fallback des rotations** | Gérer le démarrage à froid avant l'enregistrement du premier trajet. | Initialiser les rotations d'après la grille horaire officielle. |
| **Couverture de tests unitaires** | Tests de bout en bout manuels validés. | Mettre en place des tests Pytest et Jest automatisés dans la CI/CD. |

---

### 3. Passage à l'échelle
*Comment la solution tiendrait-elle à 50 000 étudiants et 300 bus en heure de pointe ? Qu'est-ce qui casserait en premier ?*

#### Ce qui casserait en premier :
1. **La connexion WebSocket FastAPI (single-process)** : Gérer 50 000 connexions ouvertes simultanément ferait exploser la RAM du conteneur Backend lors du broadcast des positions.
2. **La base de données PostgreSQL lors des écritures de flux** : Les insertions synchrones dans `passenger_flux` créeraient une contention de verrous d'écriture sur le disque.

#### Architecture cible pour passer la charge :
- **Découplage des WebSockets** : Utiliser un cluster **Centrifugo** ou **Socket.IO** dédié avec système de "Rooms" par zone géographique (les étudiants ne reçoivent que les bus de leur secteur).
- **Ingestion Asynchrone par File de Messages (NATS / Kafka)** : Tamponner les insertions de flux voyageurs et écrire par micro-batches toutes les 15 secondes en base.
- **Cluster Redis Shardé** : Répartition des clés de réservation et de télémétrie sur un cluster Redis à 3 nœuds masters.

---

### 4. Données manquantes
*Quelles données supplémentaires demanderiez-vous au terrain, et quelle décision permettraient-elles de prendre ?*

1. **Matrice Origine-Destination (OD) réelle des étudiants** :  
   *Collecte* : Sondage via l'application mobile et données d'inscription par faculté.  
   *Décision* : Réallouer la flotte entre les lignes avant même le début du semestre.
2. **Données de congestion routière temps réel (Trafic)** :  
   *Collecte* : Intégration d'une API de trafic (Google Maps / HERE / Waze).  
   *Décision* : Ajuster dynamiquement les ETAs selon les embouteillages de l'axe Akpakpa–Godomey.
3. **Comptage automatique aux portes des bus (Capteurs APC)** :  
   *Collecte* : Capteurs optiques ou infrarouges installés aux portes des bus.  
   *Décision* : Obtenir le taux d'occupation réel exact sans passer par une estimation de simulation.
4. **Emplois du temps & Calendrier des examens universitaires** :  
   *Collecte* : API des services académiques de l'UAC.  
   *Décision* : Anticiper la sortie massive des étudiants à la fin d'un examen et pré-positionner des bus de réserve 15 minutes avant.

---

### 5. Mise en production
*Quelle serait votre première itération avec de vrais étudiants et de vrais chauffeurs ?*

#### Périmètre du Pilote (MVP — 4 semaines)
- **Ligne test** : Ligne 1 (Akpakpa $\leftrightarrow$ Campus UAC).
- **Ressources** : 5 bus équipés de smartphones/boîtiers GPS bas coût, 500 étudiants bêta-testeurs.

#### Étapes du Déploiement :
1. **Semaine 1 (Chauffeurs)** : Installation des boîtiers GPS sur les 5 bus et mise à disposition d'une interface chauffeur simplifiée (départ terminus, déclaration d'avarie).
2. **Semaine 2 (Étudiants)** : Déploiement du frontend sous forme de **PWA (Progressive Web App)** accessible via QR Code aux arrêts sans installation lourde.
3. **Semaine 3–4 (Expérimentation & Calibrage)** : Mesure du taux de conversion (étudiants ayant suivi la recommandation) et ajustement des poids du score de recommandation.
4. **Indicateurs de Succès (KPIs)** :
   - Réduction de **20%** du temps d'attente moyen à l'arrêt Akpakpa.
   - Augmentation du taux de remplissage des bus de la Ligne 1 de **60% à 80%**.
# eTransport
