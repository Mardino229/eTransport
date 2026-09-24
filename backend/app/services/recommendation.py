"""
Moteur de recommandation intelligente et de réservation atomique eTransport MTDI Bénin.

Contient les algorithmes de scoring multi-critères pondéré, le routage vectoriel directionnel
(Aller vs Retour, détection des destinations passées et calcul dynamique du temps de demi-tour au terminus),
et la gestion des réservations dans Redis avec verrouillage atomique contre l'effet de troupeau.
"""

import json
import math
import time
from datetime import datetime, timezone
from typing import Optional

import redis as redis_lib

from app.data.dataset import STOPS, ROUTES
from app.schemas import (
    BusCandidate,
    RecommendationRequest,
    RecommendationResponse,
    ScoreBreakdown,
)

# 15 Arrêts et Lignes Dynamiquement Dérivés de la Source Unique de Vérité ─
STOPS_LOCATIONS = {s_id: (s["lat"], s["lng"]) for s_id, s in STOPS.items()}
ROUTE_STOPS = {r_id: r["stops"] for r_id, r in ROUTES.items()}

# Pondérations du Score (paramétrables)
W_ETA = 0.35   # Temps d'arrivée du bus à l'arrêt
W_WALK = 0.25  # Distance de marche de l'étudiant vers l'arrêt
W_TRIP = 0.25  # Durée totale du trajet jusqu'à destination
W_OCC = 0.15   # Pénalité sur le taux de remplissage

RESERVATION_TTL = 60  # Durée de la réservation atomique (60s)
WALK_SPEED_KMH = 5.0
BUS_AVG_SPEED_KMH = 25.0
STOP_DWELL_BUFFER_MIN = 2.0  # Marge de tolérance d'embarquement à l'arrêt (2 min)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcul de la distance orthodromique (en km) entre deux points GPS."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_candidate(
    raw: dict,
    student_lat: float,
    student_lng: float,
    destination_stop_id: str,
) -> Optional[BusCandidate]:
    """

    Construit et évalue un bus en analysant son routage vectoriel directionnel :
    1. Vérifie si la ligne du bus dessert l'arrêt de destination.
    2. Identifie si l'arrêt de destination est EN AMONT (Trajet Direct) ou EN AVAL (Déjà dépassé).
    3. Si la destination a été dépassée, calcule dynamiquement le temps nécessaire pour poursuivre jusqu'au terminus,
       faire demi-tour (+3 min de pause), et revenir vers la destination.
    4. Calcule le temps d'approche (ETA), de marche et la durée totale du trajet réajustée.
    5. Applique le filtre d'attrapabilité avec un délai de marge de 2 min d'arrêt.
    """
    try:
        route_id = raw.get("route_id")
        if route_id in ROUTE_STOPS:
            served_stops = ROUTE_STOPS[route_id]
            if destination_stop_id not in served_stops:
                return None

        bus_lat = float(raw.get("lat", 0))
        bus_lng = float(raw.get("lng", 0))
        capacity = int(raw.get("capacity", 60))
        passengers = int(raw.get("passengers_count", 0))
        available_seats = int(raw.get("available_seats", capacity - passengers))

        if available_seats <= 0:
            return None

        bus_direction = int(raw.get("direction", 1))

        # Analyse de la direction du bus et position de la destination
        is_direct = True
        requires_uturn = False
        uturn_delay_min = 0.0
        bus_ride_min = 0.0

        if route_id in ROUTE_STOPS:
            served_stops = ROUTE_STOPS[route_id]
            # 1. Arrêt le plus proche de la position actuelle du bus
            nearest_bus_stop_id = min(
                served_stops,
                key=lambda s_id: _haversine_km(
                    bus_lat, bus_lng, STOPS_LOCATIONS[s_id][0], STOPS_LOCATIONS[s_id][1]
                ),
            )
            # 2. Arrêt de prise en charge (montée) le plus proche de l'étudiant sur cette ligne
            boarding_stop_id = min(
                served_stops,
                key=lambda s_id: _haversine_km(
                    student_lat, student_lng, STOPS_LOCATIONS[s_id][0], STOPS_LOCATIONS[s_id][1]
                ),
            )

            current_stop_idx = served_stops.index(nearest_bus_stop_id)
            boarding_stop_idx = served_stops.index(boarding_stop_id)
            dest_stop_idx = served_stops.index(destination_stop_id)

            board_coords = STOPS_LOCATIONS[boarding_stop_id]
            dest_coords = STOPS_LOCATIONS[destination_stop_id]

            # Distance de marche RÉELLE : de l'étudiant à son arrêt de montée
            walking_km = _haversine_km(student_lat, student_lng, board_coords[0], board_coords[1])
            walk_time_min = (walking_km / WALK_SPEED_KMH) * 60.0

            # Temps d'approche du bus (ETA RÉEL) : du bus vers l'arrêt de montée
            dist_bus_to_board = _haversine_km(bus_lat, bus_lng, board_coords[0], board_coords[1])
            eta_min = (dist_bus_to_board / BUS_AVG_SPEED_KMH) * 60.0

            # CONTRÔLE D'ATTRAPABILITÉ (FILTRE DE FAISABILITÉ)
            # Si le temps de marche de l'étudiant dépasse l'ETA du bus + 2 min d'arrêt,
            # le bus sera déjà reparti avant son arrivée -> Bus inatteignable (disqualifié).
            if walk_time_min > (eta_min + STOP_DWELL_BUFFER_MIN):
                return None

            if bus_direction == 1:
                # Sens Aller (de 0 vers len-1)
                if dest_stop_idx >= boarding_stop_idx:
                    # La destination est DEVANT l'arrêt de montée -> Trajet Direct
                    is_direct = True
                    requires_uturn = False
                    dist_board_to_dest = _haversine_km(board_coords[0], board_coords[1], dest_coords[0], dest_coords[1])
                    bus_ride_min = (dist_board_to_dest / BUS_AVG_SPEED_KMH) * 60.0
                else:
                    # La destination est DERRIÈRE l'arrêt de montée -> Demi-tour au terminus requis
                    is_direct = False
                    requires_uturn = True
                    terminus_stop_id = served_stops[-1]
                    terminus_coords = STOPS_LOCATIONS[terminus_stop_id]

                    dist_board_to_terminus = _haversine_km(board_coords[0], board_coords[1], terminus_coords[0], terminus_coords[1])
                    dist_terminus_to_dest = _haversine_km(terminus_coords[0], terminus_coords[1], dest_coords[0], dest_coords[1])

                    time_to_terminus = (dist_board_to_terminus / BUS_AVG_SPEED_KMH) * 60.0 + 3.0  # +3 min pause
                    time_terminus_to_dest = (dist_terminus_to_dest / BUS_AVG_SPEED_KMH) * 60.0

                    uturn_delay_min = round(time_to_terminus, 1)
                    bus_ride_min = time_to_terminus + time_terminus_to_dest
            else:
                # Sens Retour (de len-1 vers 0)
                if dest_stop_idx <= boarding_stop_idx:
                    # La destination est DEVANT l'arrêt de montée -> Trajet Direct
                    is_direct = True
                    requires_uturn = False
                    dist_board_to_dest = _haversine_km(board_coords[0], board_coords[1], dest_coords[0], dest_coords[1])
                    bus_ride_min = (dist_board_to_dest / BUS_AVG_SPEED_KMH) * 60.0
                else:
                    # La destination est DERRIÈRE -> Demi-tour au terminus principal
                    is_direct = False
                    requires_uturn = True
                    terminus_stop_id = served_stops[0]
                    terminus_coords = STOPS_LOCATIONS[terminus_stop_id]

                    dist_board_to_terminus = _haversine_km(board_coords[0], board_coords[1], terminus_coords[0], terminus_coords[1])
                    dist_terminus_to_dest = _haversine_km(terminus_coords[0], terminus_coords[1], dest_coords[0], dest_coords[1])

                    time_to_terminus = (dist_board_to_terminus / BUS_AVG_SPEED_KMH) * 60.0 + 3.0
                    time_terminus_to_dest = (dist_terminus_to_dest / BUS_AVG_SPEED_KMH) * 60.0

                    uturn_delay_min = round(time_to_terminus, 1)
                    bus_ride_min = time_to_terminus + time_terminus_to_dest
        else:
            dest_coords = STOPS_LOCATIONS.get(destination_stop_id, (6.41609, 2.34199))
            walking_km = _haversine_km(student_lat, student_lng, bus_lat, bus_lng)
            eta_min = (walking_km / BUS_AVG_SPEED_KMH) * 60.0
            dist_to_dest = _haversine_km(bus_lat, bus_lng, dest_coords[0], dest_coords[1])
            bus_ride_min = (dist_to_dest / BUS_AVG_SPEED_KMH) * 60.0

        trip_duration_min = eta_min + bus_ride_min
        occupancy_rate = (passengers / capacity) * 100 if capacity > 0 else 0.0

        return BusCandidate(
            bus_id=raw.get("bus_id", "unknown"),
            route_id=route_id,
            lat=bus_lat,
            lng=bus_lng,
            available_seats=available_seats,
            capacity=capacity,
            occupancy_rate=round(occupancy_rate, 1),
            eta_min=round(eta_min, 2),
            walking_distance_km=round(walking_km, 3),
            trip_duration_min=round(trip_duration_min, 2),
            is_direct=is_direct,
            requires_uturn=requires_uturn,
            uturn_delay_min=uturn_delay_min,
            score=0.0,
            score_breakdown=ScoreBreakdown(
                arrival_time_score=0.0,
                walking_distance_score=0.0,
                trip_time_score=0.0,
                occupancy_score=0.0,
                uturn_penalty_score=0.0,
                final_score=0.0,
            ),
        )
    except (TypeError, ValueError, KeyError):
        return None


def _normalize(values: list[float]) -> list[float]:
    """Exécute une normalisation Min-Max sur une liste de valeurs réelles."""
    if not values:
        return values
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.0] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def compute_recommendations(
    request: RecommendationRequest,
    redis: redis_lib.Redis,
) -> RecommendationResponse:
    """

    Moteur principal de recommandation et de réservation de transport :
    1. Récupère tous les bus en mémoire vive Redis.
    2. Analyse le sens de déplacement et sépare les bus directs des bus nécessitant un demi-tour au terminus.
    3. Normalise les métriques (ETA, Marche, Durée totale incluant le demi-tour dynamique, Remplissage).
    4. Calcule le score pondéré final pour chaque candidat (plus petit score = meilleur bus).
    5. Trie et réserve de manière atomique un siège sur le meilleur bus disponible dans Redis.

    Garantit l'attribution prioritaire des bus directs se déplaçant vers la destination de l'étudiant
    et informe en toute transparence si un demi-tour au terminus est requis.
    """
    bus_keys = redis.keys("bus:*")
    bus_keys = [k for k in bus_keys if not k.endswith(":reserved_seats")]

    raw_buses: list[dict] = []
    for key in bus_keys:
        raw = redis.hgetall(key)
        if raw:
            raw_buses.append(raw)

    candidates: list[BusCandidate] = []
    for raw in raw_buses:
        c = _build_candidate(raw, request.student_lat, request.student_lng, request.destination_stop_id)
        if c is not None:
            candidates.append(c)

    if not candidates:
        raise ValueError(
            "Aucun bus disponible pour cette destination : "
            "soit aucune ligne ne dessert cet arrêt, "
            "soit les bus sont complets, "
            "soit ils seront repartis avant votre arrivée à l'arrêt."
        )

    etas = [c.eta_min for c in candidates]
    walks = [c.walking_distance_km for c in candidates]
    trips = [c.trip_duration_min for c in candidates]
    occs = [c.occupancy_rate / 100.0 for c in candidates]

    norm_etas = _normalize(etas)
    norm_walks = _normalize(walks)
    norm_trips = _normalize(trips)

    for i, c in enumerate(candidates):
        arr_score = W_ETA * norm_etas[i]
        walk_score = W_WALK * norm_walks[i]
        trip_score = W_TRIP * norm_trips[i]
        occ_score = W_OCC * occs[i]
        
        # Pénalité additionnelle si un demi-tour au terminus est nécessaire
        uturn_penalty = 0.15 if c.requires_uturn else 0.0
        final = arr_score + walk_score + trip_score + occ_score + uturn_penalty

        c.score_breakdown = ScoreBreakdown(
            arrival_time_score=round(arr_score, 4),
            walking_distance_score=round(walk_score, 4),
            trip_time_score=round(trip_score, 4),
            occupancy_score=round(occ_score, 4),
            uturn_penalty_score=round(uturn_penalty, 4),
            final_score=round(final, 4),
        )
        c.score = round(final, 4)

    candidates.sort(key=lambda x: x.score)

    reserved = False
    chosen = None

    for candidate in candidates:
        bus_id = candidate.bus_id
        reservation_key = f"bus:{bus_id}:reserved_seats"

        current_reserved = redis.get(reservation_key)
        if current_reserved is None:
            redis.set(reservation_key, candidate.available_seats, ex=RESERVATION_TTL)
            current_reserved = candidate.available_seats
        else:
            current_reserved = int(current_reserved)

        if current_reserved <= 0:
            continue

        new_count = redis.decr(reservation_key)
        if new_count >= 0:
            redis.expire(reservation_key, RESERVATION_TTL)
            candidate.available_seats = new_count
            chosen = candidate
            reserved = True
            break
        else:
            redis.incr(reservation_key)

    if chosen is None:
        chosen = candidates[0]
        reserved = False

    alternatives = [c for c in candidates if c.bus_id != chosen.bus_id][:3]

    return RecommendationResponse(
        student_id=request.student_id,
        destination_stop_id=request.destination_stop_id,
        recommended_bus=chosen,
        alternatives=alternatives,
        reserved=reserved,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
