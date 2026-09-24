# 🚌 eTransport MTDI Bénin — Transport Universitaire (COUS-AC)

> **Projet de Test Technique** — Application de suivi des bus en temps réel, de réservation de siège et d'aide à la décision pour le réseau de transport de l'Université d'Abomey-Calavi (COUS-AC).

---

## 📋 Sommaire
1. [Présentation du Projet](#-présentation-du-projet)
2. [Comment Lancer le Projet en Local](#-comment-lancer-le-projet-en-local)
3. [Données et Hypothèses de Simulation](#-données-et-hypothèses-de-simulation)
4. [Explication des 5 Cas d'Usage](#-explication-des-5-cas-dusage)
5. [Pour aller plus loin](#-pour-aller-plus-loin)

---

## 🌟 Présentation du Projet

Le but de cette application est de résoudre deux problèmes fréquents dans le transport universitaire :
1. **Pour les étudiants** : Savoir exactement quel bus prendre, dans combien de temps il arrive, et s'il reste de la place à bord.
2. **Pour les gestionnaires du réseau** : Identifier les lignes surchargées aux heures de pointe et savoir où ajouter des bus.

---

## 💻 Comment Lancer le Projet en Local

### 1. Prérequis
Vous devez simplement avoir **Docker** et **Docker Compose** installés sur votre machine.

### 2. Procédure rapide

```bash
# 1. Cloner le projet depuis GitHub
git clone git@github.com:Mardino229/eTransport.git
cd eTransport

# 2. Démarrer toute l'application avec Docker
docker compose up --build
```

### 3. Accès aux pages

| Élément | Adresse | Description |
|---|---|---|
| **Site Web (Frontend)** | [http://localhost:3000](http://localhost:3000) | La carte en direct et le tableau de bord |
| **Documentation API (Backend)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Liste et test de toutes les routes de l'API |

---

## 📊 Données et Hypothèses de Simulation (Section 2.1)

Comme aucune donnée réelle n'était fournie, un simulateur génère automatiquement le déplacement des bus et l'affluence des étudiants :

- **35 bus** en circulation (de 50 à 60 places chacun).
- **14 lignes** desservant **15 arrêts** principaux (UAC Campus, Étoile Rouge, ENEAM, Akpakpa, Godomey, Porto-Novo, Tori, etc.).
- **Télémétrie automatique** : Les bus envoient leur position GPS toutes les **2 secondes** (comme des boîtiers GPS embarqués).
- **Heures de pointe** : L'affluence d'étudiants est multipliée par **3 le matin (06h30–09h10)** vers les cours et par **2.8 le soir (16h00–19h30)** vers les logements.

---

## 🎯 Explication des 5 Cas d'Usage

### 1. Gestion de Capacité
- **Ce que ça fait** : Affiche pour chaque bus le nombre de places libres, le nombre de passagers à bord et le pourcentage de remplissage.
- **Endpoint API** : `GET /api/v1/buses/live`

### 2. Analyse des Arrêts
- **Ce que ça fait** : Calcule pour un arrêt donné le nombre total d'étudiants qui sont montés, descendus, ceux qui restent à quai et le temps d'attente moyen.
- **Endpoint API** : `GET /api/v1/stops/{stop_id}/analytics`

### 3. Top 5 des Itinéraires
- **Ce que ça fait** : Donne les 5 lignes les plus utilisées de la journée avec le nombre d'étudiants transportés et leur niveau d'occupation.
- **Endpoint API** : `GET /api/v1/routes/top5`

### 4. Recommandation Intelligente & Cas des 200 Étudiants Simultanés
- **Ce que ça fait** : L'étudiant entre sa position et sa destination. Le système calcule une note pour chaque bus selon 4 critères :
  - Le temps d'arrivée à l'arrêt (ETA).
  - La distance de marche jusqu'à l'arrêt.
  - La durée totale du trajet.
  - Le niveau de remplissage du bus (+ une pénalité si le bus doit faire un demi-tour au terminus).
- **Cas des 200 étudiants simultanés** : Pour éviter que 200 étudiants réservent la même place au même moment, nous utilisons un compteur de places réservables dans **Redis**. Dès qu'un étudiant choisit un bus, une place est bloquée pendant 60 secondes. Si le bus devient plein, le 201ᵉ étudiant est automatiquement orienté vers le bus suivant.
- **Endpoint API** : `POST /api/v1/recommendation`

### 5. Optimisation d'Itinéraire (Aide à la Décision)
- **Ce que ça fait** : Analyse le réseau et propose 4 types d'actions concrètes avec des chiffres à l'appui :
  - **Ajouter des bus** sur une ligne si elle est saturée ($>80\%$) ou si l'attente est trop forte.
  - **Rapprocher les départs** si la charge est modérée ($60\%$ à $80\%$).
  - **Réallouer un bus** vers une autre ligne si une ligne a trop de bus pour peu de voyageurs.
  - **Fusionner des lignes** si une ligne est presque vide ($<50$ passagers/jour).
- **Endpoint API** : `GET /api/v1/optimizations/suggestions`

---

## 🚀 Pour aller plus loin

### 1. Recul sur mes choix
*Ce que j'aurais fait différemment avec un peu plus d'expérience ou de temps :*

1. **Utiliser une vraie carte routière (OSRM / OpenStreetMap)** : Actuellement, les bus avancent en ligne droite simulée entre les arrêts. En intégrant un moteur de carte routière comme OSRM, les temps de trajet calculés tiendraient compte des vrais tournants et des rues de Cotonou et Calavi.
2. **Gestion du mode hors-ligne sur mobile** : Si un étudiant perd sa connexion 4G à l'arrêt de bus, l'application devrait garder en mémoire les derniers horaires chargés pour qu'il ne se retrouve pas sans information.
3. **Application Chauffeur vs Boîtier GPS** :
   - *Choix actuel (Boîtier GPS autonome)* : Envoie la position automatiquement sans que le chauffeur n'ait rien à faire. C'est simple et fiable.
   - *Alternative (Écran/Application Chauffeur)* : Si le chauffeur avait une application sur tablette, il pourrait signaler manuellement des pannes ou des bouchons, mais il y aurait un risque qu'il oublie d'allumer l'application.

---

### 2. Dette technique
*Les simplifications acceptées pour rendre le projet dans les temps :*

- **Pas de système de connexion (Login / Mot de passe)** : Pour ce test, les endpoints sont ouverts. En situation réelle, il faudrait ajouter une connexion avec token (JWT).
- **Données simulées basiques pour le trafic** : La vitesse des bus est fixe (32 km/h). Dans la réalité, la circulation varie selon les embouteillages.
- **Tests automatisés simples** : Le projet a été testé manuellement. Il faudrait ajouter des tests unitaires (avec Pytest) pour vérifier automatiquement le code avant chaque mise à jour.

---

### 3. Passage à l'échelle (50 000 étudiants et 300 bus)

#### Ce qui risquerait de bloquer en premier :
1. **Les notifications en direct (WebSockets)** : Envoyer la position de 300 bus en même temps à 50 000 étudiants sur un seul serveur va ralentir l'application.
2. **La base de données PostgreSQL** : Si 300 bus enregistrent des passages en même temps, la base de données risque d'être submergée par les écritures.

#### Solutions simples à mettre en place :
- **Séparer les serveurs** : Utiliser un serveur dédié uniquement à la diffusion des positions GPS (ex: Socket.IO ou Centrifugo).
- **Filtrer par zone géographique** : Un étudiant situé à Abomey-Calavi n'a pas besoin de recevoir les positions des bus qui circulent à Porto-Novo.
- **Regrouper les écritures en base** : Au lieu d'écrire dans PostgreSQL à chaque seconde, regrouper les données en mémoire et les sauvegarder toutes les 15 ou 30 secondes.

---

### 4. Données manquantes du terrain

Pour rendre le système encore plus précis sur le terrain, je demanderais :

1. **Les emplois du temps officiels de l'UAC** : Pour savoir à quelle heure précise les cours et les examens finissent, et envoyer des bus juste avant la sortie des amphis.
2. **L'historique des cartes d'étudiants** : Pour connaître les trajets les plus fréquents (ex: combien d'étudiants font le trajet Godomey $\rightarrow$ UAC tous les matins).
3. **Les données de météo locale** : Lorsqu'il pleut à Cotonou ou Calavi, l'affluence aux arrêts couverts augmente fortement.

---

### 5. Mise en production (Première itération sur le terrain)

Si je devais tester l'application en vrai avec des étudiants et des chauffeurs, voici comment je procèderais en **3 étapes simples** :

1. **Étape 1 : Tester sur une seule ligne (ex: Ligne Akpakpa $\rightarrow$ UAC avec 5 bus)**
   - Équiper 5 bus avec des boîtiers GPS bas coût.
   - Demander à 100 étudiants de cette ligne de tester l'application pendant 2 semaines.
2. **Étape 2 : Recueillir les avis et corriger les bugs**
   - Vérifier si les temps d'arrivée affichés (ETA) correspondent bien à la réalité.
   - Demander aux étudiants si les bus recommandés avaient bien des places libres.
3. **Étape 3 : Déployer progressivement sur tout le réseau**
   - Ajouter les 13 autres lignes et les 30 autres bus une fois que la première ligne fonctionne parfaitement.
