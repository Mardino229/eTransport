"""
Simulateur IoT eTransport MTDI Bénin (Université d'Abomey-Calavi).

Simule le déplacement en temps réel de 35 bus universitaires COUS-AC sur 14 lignes
desservant Cotonou, Abomey-Calavi, Porto-Novo, Tori, Godomey, etc., et publie la télémétrie
dans Redis et PostgreSQL.
"""

import asyncio
import json
import math
import os
import random
import urllib.request
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as aioredis

from data import (
    BUSES,
    ROUTES,
    STOPS,
    GPS_UPDATE_INTERVAL,
    BUS_SPEED_KMH,
    PEAK_MORNING,
    PEAK_EVENING,
)
 
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://etransport:etransport_pass@db:5432/etransport",
)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Cette fonction calcule la distance orthodromique (en kilomètres) à vol d'oiseau entre deux coordonnées
    géographiques (latitude/longitude) en utilisant la formule trigonométrique de Haversine. 

    Elle est essentielle pour déterminer la position exacte d'un bus par rapport aux 15 arrêts du réseau COUS-AC,
    calculer les distances de marche pour l'étudiant et détecter l'arrivée d'un véhicule à une station.
    """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def interpolate(p1: tuple, p2: tuple, frac: float) -> tuple:
    """
    Cette fonction calcule un point GPS intermédiaire par interpolation linéaire entre deux points (p1 et p2)
    selon une fraction de progression comprise entre 0.0 (départ) et 1.0 (arrivée).
   
    Elle permet de simuler un déplacement fluide et continu des bus le long du tracé des 14 lignes universitaires
    à chaque rafraîchissement GPS (toutes les 2 secondes).
    """
    lat = p1[0] + (p2[0] - p1[0]) * frac
    lng = p1[1] + (p2[1] - p1[1]) * frac
    return (lat, lng)


def get_demand_factor() -> float:
    """
    Cette fonction examine l'heure courante du système et retourne un coefficient de multiplication de l'affluence :
    - Peak Matin (06:30 - 09:10) : x3.0 (rush vers le campus UAC)
    - Peak Soir  (16:00 - 19:30) : x2.8 (rush retour vers les logements)
    - Heures creuses : 1.0

    Elle reproduit théorique le comportement réel des flux d'étudiants de l'UAC afin de tester la robustesse
    du système, la saturation des bus et l'algorithme d'optimisation d'itinéraires sous forte charge.
    """ 
    now = datetime.now()
    h, m = now.hour, now.minute
    total_min = h * 60 + m

    pm_start = PEAK_MORNING["start_h"] * 60 + PEAK_MORNING["start_m"]
    pm_end = PEAK_MORNING["end_h"] * 60 + PEAK_MORNING["end_m"]
    pe_start = PEAK_EVENING["start_h"] * 60 + PEAK_EVENING["start_m"]
    pe_end = PEAK_EVENING["end_h"] * 60 + PEAK_EVENING["end_m"]

    if pm_start <= total_min <= pm_end:
        return PEAK_MORNING["factor"]
    elif pe_start <= total_min <= pe_end:
        return PEAK_EVENING["factor"]
    return 1.0


class BusState:
    """
    Classe représentant l'état dynamique en mémoire vive d'un bus du réseau COUS-AC.
    """

    def __init__(self, config: dict):
        """
        Ce que fait cette méthode :
        -----------------------------
        Initialise les attributs du bus (ID, ligne, capacité de 60 ou 45 places, nombre initial
        de passagers, waypoints du trajet et position de départ aléatoire).

        Utilité pour l'application globale :
        ------------------------------------
        Instancie individuellement chacun des 35 bus officiels pour suivre leur état
        en temps réel.
        """
        self.bus_id = config["id"]
        self.route_id = config["route_id"]
        self.capacity = config["capacity"]
        self.passengers = random.randint(0, self.capacity // 3)
        self.route = ROUTES[self.route_id]
        self.waypoints = self.route["waypoints"]
        self.stops = self.route["stops"]
        self.wp_index = random.randint(0, len(self.waypoints) - 2)
        self.progress = random.random()
        midpoint = len(self.waypoints) // 2
        self.direction = 1 if self.wp_index < midpoint else -1
        self.lat, self.lng = self.waypoints[self.wp_index]
        self.trip_count = 0          # Rotations complètes (aller-retour) depuis le démarrage
        self._pending_trip_count = 0  # Incréments à persister en DB au prochain flush

    @property
    def available_seats(self) -> int:
        """
        Ce que fait cette propriété :
        -----------------------------
        Retourne le nombre actuel de sièges vacants à bord du bus (`capacité - passagers`).

        Utilité pour l'application globale :
        ------------------------------------
        Fournit l'information essentielle transmise au moteur de recommandation Redis pour garantir
        qu'un étudiant ne se voie proposer que des bus ayant des places libres.
        """
        return max(0, self.capacity - self.passengers)

    @property
    def occupancy_rate(self) -> float:
        """
        Ce que fait cette propriété :
        -----------------------------
        Calcule le taux de remplissage en pourcentage (`(passagers / capacité) * 100`).

        Utilité pour l'application globale :
        ------------------------------------
        Alimente le code couleur des bus sur la carte (Vert < 70%, Orange < 90%, Rouge >= 90%)
        et sert d'indicateur pour les rapports de gestion du COUS-AC.
        """
        return round((self.passengers / self.capacity) * 100, 1)

    def _get_stop_wp_index(self, stop_id: str) -> int:
        """
        Trouve l'index de waypoint le plus proche d'un arrêt officiel donné.
        """
        stop_data = STOPS.get(stop_id)
        if not stop_data:
            return 0
        s_lat, s_lng = stop_data["lat"], stop_data["lng"]
        best_idx = 0
        min_d = float("inf")
        for i, (w_lat, w_lng) in enumerate(self.waypoints):
            d = haversine_km(s_lat, s_lng, w_lat, w_lng)
            if d < min_d:
                min_d = d
                best_idx = i
        return best_idx

    def _find_next_stop(self) -> str:
        """
        Identifie avec précision le code de l'arrêt officiel vers lequel le bus se déplace actuellement.
        Prend en compte la position continue le long du tracé (wp_index + progress) et le sens (direction).
        """
        if not self.stops or len(self.stops) == 0:
            return "—"

        if self.direction == 1:
            current_wp = self.wp_index + self.progress
            for stop_id in self.stops:
                stop_wp = self._get_stop_wp_index(stop_id)
                if stop_wp >= (current_wp - 0.05):
                    return stop_id
            return self.stops[-1]
        else:
            current_wp = self.wp_index - self.progress
            reversed_stops = list(reversed(self.stops))
            for stop_id in reversed_stops:
                stop_wp = self._get_stop_wp_index(stop_id)
                if stop_wp <= (current_wp + 0.05):
                    return stop_id
            return reversed_stops[-1]

    def advance(self, delta_km: float) -> bool:
        """
        Ce que fait cette méthode :
        -----------------------------
        Met à jour la position GPS du bus en le faisant avancer de `delta_km` le long des waypoints.
        Gère le demi-tour aux terminus et renvoie `True` si le bus est arrivé à un arrêt (distance < 150m).

        Utilité pour l'application globale :
        ------------------------------------
        Constitue le moteur de physique spatiale du simulateur, déclenchant l'enregistrement des montées/descentes.
        """
        p1 = self.waypoints[self.wp_index]
        p2 = (
            self.waypoints[self.wp_index + self.direction]
            if (0 <= self.wp_index + self.direction < len(self.waypoints))
            else p1
        )

        seg_dist = haversine_km(p1[0], p1[1], p2[0], p2[1])
        if seg_dist == 0:
            seg_dist = 0.01

        self.progress += delta_km / seg_dist
        arrived_at_stop = False

        while self.progress >= 1.0:
            self.progress -= 1.0
            self.wp_index += self.direction

            if self.wp_index >= len(self.waypoints) - 1:
                self.wp_index = len(self.waypoints) - 2
                self.direction = -1
                arrived_at_stop = True
                self.trip_count += 1          # Un terminus = une demi-rotation comptabilisée
                self._pending_trip_count += 1
            elif self.wp_index <= 0:
                self.wp_index = 1
                self.direction = 1
                arrived_at_stop = True
                self.trip_count += 1
                self._pending_trip_count += 1
            else:
                current_pos = self.waypoints[self.wp_index]
                for stop_id, stop_data in STOPS.items():
                    d = haversine_km(
                        current_pos[0], current_pos[1], stop_data["lat"], stop_data["lng"]
                    )
                    if d < 0.15:
                        arrived_at_stop = True
                        break

        next_idx = self.wp_index + self.direction
        next_idx = max(0, min(next_idx, len(self.waypoints) - 1))
        pos = interpolate(
            self.waypoints[self.wp_index], self.waypoints[next_idx], self.progress
        )
        self.lat, self.lng = pos

        return arrived_at_stop

    def simulate_boarding(self, factor: float) -> tuple[int, int, int]:
        """
        Ce que fait cette méthode :
        -----------------------------
        Simule les opérations de montée et de descente des étudiants lors de l'arrêt du bus.
        Prend en compte le coefficient d'affluence et la capacité disponible.

        Utilité pour l'application globale :
        ------------------------------------
        Génère les données de flux de voyageurs (`boarded`, `alighted`, `waiting`) enregistrées en SQL
        pour calculer le taux de fréquentation et alimenter le panneau d'optimisation décisionnelle.
        """
        alighted = min(self.passengers, random.randint(3, max(4, self.passengers // 3)))
        self.passengers -= alighted

        waiting = int(random.randint(0, 15) * factor)
        can_board = min(waiting, self.available_seats)
        boarded = can_board
        self.passengers += boarded
        remaining_waiting = waiting - boarded

        return boarded, alighted, remaining_waiting

    def to_redis_dict(self) -> dict:
        """
        Ce que fait cette méthode :
        -----------------------------
        Formate l'état du bus en un dictionnaire prêt à être sérialisé dans Redis.

        Utilité pour l'application globale :
        ------------------------------------
        Standardise la structure de la trame IoT diffusée en temps réel via WebSocket au frontend React.
        """
        return {
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "speed": round(BUS_SPEED_KMH + random.uniform(-5, 5), 1),
            "capacity": self.capacity,
            "passengers_count": self.passengers,
            "available_seats": self.available_seats,
            "occupancy_rate": round(self.occupancy_rate, 1),
            "next_stop_id": self._find_next_stop(),
            "direction": self.direction,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def simulate_bus(bus_state: BusState, redis: aioredis.Redis, db_pool: asyncpg.Pool):
    """
    Ce que fait cette coroutine :
    -----------------------------
    Gère la boucle de vie d'un bus en tâche de fond asynchrone :
    1. Avance la position du bus toutes les 2 secondes.
    2. Met à jour la mémoire vive Redis (`bus:<id>`) et publie dans le canal `bus_updates`.
    3. Persiste les événements de flux de passagers dans PostgreSQL lors des arrêts.

    Permet la simulation parallèle, fluide et sans blocage des 35 bus simultanément sur le réseau UAC.
    """
    await asyncio.sleep(random.uniform(0, 2))
    delta_km_per_tick = (BUS_SPEED_KMH / 3600) * GPS_UPDATE_INTERVAL

    while True:
        factor = get_demand_factor()
        arrived = bus_state.advance(delta_km_per_tick)

        data = bus_state.to_redis_dict()

        await redis.hset(f"bus:{bus_state.bus_id}", mapping=data)
        payload = json.dumps(data)
        await redis.publish("bus_updates", payload)

        if arrived:
            boarded, alighted, waiting = bus_state.simulate_boarding(factor)
            nearest_stop = min(
                STOPS.items(),
                key=lambda kv: haversine_km(
                    bus_state.lat, bus_state.lng, kv[1]["lat"], kv[1]["lng"]
                ),
            )
            stop_id = nearest_stop[0]

            try:
                async with db_pool.acquire() as conn:
                    # Enregistrement du flux passager à l'arrêt
                    await conn.execute(
                        """
                        INSERT INTO passenger_flux
                            (stop_id, bus_id, boarded_count, alighted_count, waiting_count, timestamp)
                        VALUES ($1, $2, $3, $4, $5, now())
                        """,
                        stop_id,
                        bus_state.bus_id,
                        boarded,
                        alighted,
                        waiting,
                    )
                    # À chaque terminus : journaliser la rotation avec timestamp
                    # → permet de compter les rotations sur une fenêtre 24h exacte
                    if bus_state._pending_trip_count > 0:
                        for _ in range(bus_state._pending_trip_count):
                            await conn.execute(
                                """
                                INSERT INTO bus_trip_log (bus_id, route_id, timestamp)
                                VALUES ($1, $2, now())
                                """,
                                bus_state.bus_id,
                                bus_state.route_id,
                            )
                        # Mise à jour du compteur cumulatif global (stats lifetime du bus)
                        await conn.execute(
                            """
                            UPDATE buses
                            SET trip_count = trip_count + $1
                            WHERE id = $2
                            """,
                            bus_state._pending_trip_count,
                            bus_state.bus_id,
                        )
                        bus_state._pending_trip_count = 0
            except Exception as e:
                print(f"[SIMULATOR] Erreur PostgreSQL pour {bus_state.bus_id} @ {stop_id}: {e}")

        await asyncio.sleep(GPS_UPDATE_INTERVAL)


async def seed_database(db_pool: asyncpg.Pool):
    """

    Exécute des requêtes SQL `INSERT ... ON CONFLICT DO UPDATE` pour peupler ou mettre à jour
    les tables `stops`, `routes` et `buses` dans PostgreSQL avec les 15 arrêts et 14 lignes réelles.

    Garantit l'existence et la cohérence de la base de données relationnelle au démarrage du système,
    évitant toute erreur de contrainte de clé étrangère (`foreign key error`).
    """
    print("[SIMULATOR] Synchronisation des arrêts, lignes et bus COUS-AC dans PostgreSQL...")
    try:
        async with db_pool.acquire() as conn:
            for stop_id, s in STOPS.items():
                zone = s["name"].split("(")[0].strip()
                await conn.execute(
                    """
                    INSERT INTO stops (id, name, zone_name, location)
                    VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
                    ON CONFLICT (id) DO UPDATE
                    SET name = EXCLUDED.name,
                        zone_name = EXCLUDED.zone_name,
                        location = EXCLUDED.location
                    """,
                    stop_id,
                    s["name"],
                    zone,
                    s["lng"],
                    s["lat"],
                )

            for r_id, r in ROUTES.items():
                code = r["name"].split(":")[0].replace("Ligne ", "L").strip()
                wps = r.get("waypoints", [])
                if wps:
                    wps_sql = ", ".join(f"ST_MakePoint({lng}, {lat})" for lat, lng in wps)
                    path_sql = f"ST_SetSRID(ST_MakeLine(ARRAY[{wps_sql}]), 4326)"
                else:
                    path_sql = "NULL"

                await conn.execute(
                    f"""
                    INSERT INTO routes (id, code, name, path)
                    VALUES ($1, $2, $3, {path_sql})
                    ON CONFLICT (id) DO UPDATE
                    SET code = EXCLUDED.code,
                        name = EXCLUDED.name,
                        path = EXCLUDED.path
                    """,
                    r_id,
                    code,
                    r["name"],
                )

            for b in BUSES:
                reg_num = f"RB-{b['id']}"
                await conn.execute(
                    """
                    INSERT INTO buses (id, registration_number, capacity, current_route_id)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET capacity = EXCLUDED.capacity,
                        current_route_id = EXCLUDED.current_route_id
                    """,
                    b["id"],
                    reg_num,
                    b["capacity"],
                    b["route_id"],
                )
        print("[SIMULATOR] Base de données PostgreSQL synchronisée avec succès.")
    except Exception as e:
        print(f"[SIMULATOR] Avertissement lors de la synchronisation DB: {e}")


def fetch_osrm_waypoints_sync(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Interroge l'API OSRM de façon synchrone pour obtenir les waypoints routiers OpenStreetMap.
    """
    if not points or len(points) < 2:
        return points
    coords_str = ";".join([f"{lng},{lat}" for lat, lng in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "eTransport-Simulator/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") == "Ok" and data.get("routes"):
                geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                return [(lat, lng) for lng, lat in geojson_coords]
    except Exception as e:
        print(f"[OSRM] Avertissement chargement OSRM: {e}")
    return points


async def enrich_routes_with_osrm():
    """
    Enrichit les waypoints des 14 lignes avec le tracé routier exact d'OpenStreetMap (OSRM).
    """
    print("[SIMULATOR] Chargement des géométries routières OSRM OpenStreetMap pour les 14 lignes...")
    loop = asyncio.get_running_loop()
    for route_id, route_data in ROUTES.items():
        wps = route_data.get("waypoints", [])
        if len(wps) >= 2:
            try:
                osrm_wps = await loop.run_in_executor(None, fetch_osrm_waypoints_sync, wps)
                if osrm_wps and len(osrm_wps) >= 2:
                    route_data["waypoints"] = osrm_wps
                    print(f"  ✓ {route_id}: {len(osrm_wps)} coordonnées routières OSRM chargées")
            except Exception as e:
                print(f"  ⚠ {route_id}: Erreur OSRM ({e})")


async def main():
    """

    Point d'entrée principal du module simulateur. Démarre la connexion Redis, le pool PostgreSQL,
    lance `enrich_routes_with_osrm()`, `seed_database()`, instancie les 35 bus et lance les coroutines en parallèle.

    Orchestre l'ensemble de la couche de simulation.
    """
    print("[SIMULATOR] Démarrage du simulateur...")
    print(f"[SIMULATOR] {len(BUSES)} bus simulés sur {len(ROUTES)} lignes")
    print(f"[SIMULATOR] Rafraîchissement GPS : toutes les {GPS_UPDATE_INTERVAL}s")

    await enrich_routes_with_osrm()

    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

    await seed_database(db_pool)

    bus_states = [BusState(cfg) for cfg in BUSES]
    tasks = [simulate_bus(state, redis, db_pool) for state in bus_states]

    print(f"[SIMULATOR] {len(tasks)} coroutines bus démarrées. En attente...")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
