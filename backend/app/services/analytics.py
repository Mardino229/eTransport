"""
Services décisionnels et statistiques analytiques pour eTransport MTDI Bénin.

Fournit les calculs de capacité en temps réel, l'analyse de fréquentation des arrêts,
le classement des lignes et les algorithmes de proposition d'optimisation.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List

import redis as redis_lib
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import PassengerFlux, Bus, Route, Stop, BusTripLog
from app.schemas import (
    BusLiveSchema,
    StopAnalyticsSchema,
    TopRouteSchema,
    OptimizationAction,
    OptimizationSuggestionsResponse,
)


def get_all_buses_live(redis: redis_lib.Redis) -> List[BusLiveSchema]:
    """
    Ce que fait cette fonction :
    -----------------------------
    Lit directement la mémoire Redis en effectuant un `KEYS bus:*` (en excluant les clés de réservation),
    récupère la télémétrie Hash de chaque véhicule et construit la liste des objets `BusLiveSchema`.

    Utilité pour l'application globale :
    ------------------------------------
    Fournit l'API `/api/v1/buses/live` en réponse ultra-rapide (lecture RAM) pour le rafraîchissement
    de la carte GPS et le suivi du taux d'occupation des bus.
    """
    bus_keys = redis.keys("bus:*")
    bus_keys = [k for k in bus_keys if not k.endswith(":reserved_seats")]

    buses = []
    for key in bus_keys:
        raw = redis.hgetall(key)
        if not raw:
            continue
        try:
            capacity = int(raw.get("capacity", 60))
            passengers = int(raw.get("passengers_count", 0))
            available = int(raw.get("available_seats", capacity - passengers))
            occupancy = round((passengers / capacity) * 100, 1) if capacity > 0 else 0.0

            buses.append(
                BusLiveSchema(
                    bus_id=raw.get("bus_id", key.replace("bus:", "")),
                    route_id=raw.get("route_id"),
                    lat=float(raw.get("lat", 0)),
                    lng=float(raw.get("lng", 0)),
                    speed=float(raw.get("speed", 0)),
                    capacity=capacity,
                    passengers_count=passengers,
                    available_seats=available,
                    occupancy_rate=occupancy,
                    next_stop_id=raw.get("next_stop_id"),
                    timestamp=raw.get("timestamp", ""),
                )
            )
        except (ValueError, TypeError):
            continue

    return buses


def get_stop_analytics(stop_id: str, db: Session) -> StopAnalyticsSchema:
    """
    Ce que fait cette fonction :
    -----------------------------
    Interroge la table SQL `passenger_flux` pour un arrêt donné sur la fenêtre des 24 dernières heures,
    calcule la somme des étudiants montés, descendus, le nombre d'étudiants actuellement en attente,
    et estime le temps moyen d'attente à quai.

    Utilité pour l'application globale :
    ------------------------------------
    Permet de suivre en détail la congestion à chaque station universitaire (ex: Campus UAC, Étoile Rouge)
    et de mesurer le temps de prise en charge des étudiants par les bus.
    """
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if stop is None:
        raise ValueError(f"Arrêt '{stop_id}' introuvable.")

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = (
        db.query(
            func.sum(PassengerFlux.boarded_count).label("total_boarded"),
            func.sum(PassengerFlux.alighted_count).label("total_alighted"),
            func.sum(PassengerFlux.waiting_count).label("current_waiting"),
        )
        .filter(
            PassengerFlux.stop_id == stop_id,
            PassengerFlux.timestamp >= since,
        )
        .one()
    )

    total_boarded = result.total_boarded or 0
    total_alighted = result.total_alighted or 0
    current_waiting = result.current_waiting or 0

    avg_wait = min(current_waiting * 0.5, 10.0) if current_waiting > 0 else 0.0

    return StopAnalyticsSchema(
        stop_id=stop_id,
        stop_name=stop.name,
        total_boarded=total_boarded,
        total_alighted=total_alighted,
        current_waiting=current_waiting,
        avg_wait_time_min=round(avg_wait, 1),
    )


def get_top5_routes(db: Session) -> List[TopRouteSchema]:
    """
    Ce que fait cette fonction :
    -----------------------------
    Exécute une requête d'agrégation SQL complexe croisant les tables `buses`, `routes` et `passenger_flux`
    pour extraire les 5 itinéraires ayant enregistré le plus grand nombre de voyageurs sur 24h,
    tout en calculant leur taux de saturation théorique.

    Utilité pour l'application globale :
    ------------------------------------
    Alimente la section "Top 5 des Lignes" du tableau de bord de supervision pour visualiser instantanément
    les axes de transport les plus sollicités de la métropole.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    results = (
        db.query(
            Bus.current_route_id.label("route_id"),
            Route.name.label("route_name"),
            func.sum(PassengerFlux.boarded_count).label("daily_passengers"),
            func.count(func.distinct(PassengerFlux.bus_id)).label("bus_count"),
            func.max(Bus.capacity).label("bus_capacity"),
            # Nombre de rotations effectuées dans les 24 dernières heures par tous les bus de la ligne
            func.count(func.distinct(BusTripLog.id)).label("total_trips"),
        )
        .join(PassengerFlux, PassengerFlux.bus_id == Bus.id)
        .join(Route, Route.id == Bus.current_route_id)
        .outerjoin(
            BusTripLog,
            (BusTripLog.bus_id == Bus.id) & (BusTripLog.timestamp >= since),
        )
        .filter(PassengerFlux.timestamp >= since)
        .group_by(Bus.current_route_id, Route.name)
        .order_by(func.sum(PassengerFlux.boarded_count).desc())
        .limit(5)
        .all()
    )

    top5 = []
    for row in results:
        daily = row.daily_passengers or 0
        total_trips = int(row.total_trips or 0)
        bus_capacity = int(row.bus_capacity or 60)
        if total_trips > 0:
            # Capacité réelle = nombre de rotations effectuées × places disponibles par bus
            max_capacity = total_trips * bus_capacity
        else: 
            # Fallback si le simulateur vient de démarrer et n'a pas encore de rotations enregistrées
            max_capacity = (int(row.bus_count or 1)) * bus_capacity * 8 
        saturation = min((daily / max_capacity) * 100, 100.0) if max_capacity > 0 else 0.0

        top5.append(
            TopRouteSchema(
                route_id=row.route_id or "unknown",
                route_name=row.route_name or "Inconnu",
                daily_passengers=daily,
                saturation_rate=round(saturation, 1),
            )
        )

    return top5


def get_optimization_suggestions(db: Session) -> OptimizationSuggestionsResponse:
    """
    Ce que fait cette fonction :
    -----------------------------
    Analyse l'ensemble des métriques d'affluence SQL sur 24 heures pour :
    1. Détecter les lignes surchargées (proposer d'ajouter des bus ou rapprocher les départs).
    2. Détecter les lignes sous-fréquentées (proposer des réallocations ou fusions).
    3. Identifier les points chauds (hotspots de congestion).
    4. Renvoyer un rapport structuré avec les créneaux de pointe.

    Utilité pour l'application globale :
    ------------------------------------
    Constitue le cœur du cas d'usage n°5 (Optimisation et régulation). Il fournit des recommandations
    chiffrées et exploitables aux régulateurs du transport universitaire pour rééquilibrer la flotte.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Récupération exhaustive sur l'ensemble des 14 lignes du réseau COUS-AC
    line_stats = (
        db.query(
            Route.id.label("route_id"),
            Route.name.label("route_name"),
            func.count(func.distinct(Bus.id)).label("bus_count"),
            func.coalesce(func.max(Bus.capacity), 50).label("bus_capacity"),
            func.coalesce(func.sum(PassengerFlux.boarded_count), 0).label("total_boarded"),
            func.coalesce(func.avg(PassengerFlux.waiting_count), 0.0).label("avg_waiting"),
            func.count(func.distinct(BusTripLog.id)).label("total_trips"),
        )
        .outerjoin(Bus, Bus.current_route_id == Route.id)
        .outerjoin(
            PassengerFlux,
            (PassengerFlux.bus_id == Bus.id) & (PassengerFlux.timestamp >= since),
        )
        .outerjoin(
            BusTripLog,
            (BusTripLog.bus_id == Bus.id) & (BusTripLog.timestamp >= since),
        )
        .group_by(Route.id, Route.name)
        .all()
    )

    stop_stats = (
        db.query(
            Stop.id.label("stop_id"),
            Stop.name.label("stop_name"),
            func.sum(PassengerFlux.waiting_count).label("total_waiting"),
            func.sum(PassengerFlux.boarded_count).label("total_boarded"),
        )
        .join(PassengerFlux, PassengerFlux.stop_id == Stop.id)
        .filter(PassengerFlux.timestamp >= since)
        .group_by(Stop.id, Stop.name)
        .order_by(func.sum(PassengerFlux.waiting_count).desc())
        .limit(5)
        .all()
    )

    suggestions: List[OptimizationAction] = []

    for row in line_stats:
        bus_count = int(row.bus_count or 0)
        bus_capacity = int(row.bus_capacity or 50)
        total_boarded = int(row.total_boarded or 0)
        avg_waiting = float(row.avg_waiting or 0.0)
        total_trips = int(row.total_trips or 0)

        # Estimations réalistes des rotations (fallback à 8 par bus au démarrage du simulateur)
        effective_trips = total_trips if total_trips > 0 else max(1, bus_count) * 8

        # Capacité maximale théorique offerte sur cette ligne (Nombre de bus × Capacité × Rotations par bus)
        trips_per_bus = max(1, effective_trips // max(1, bus_count))
        offered_capacity = max(1, bus_count) * bus_capacity * trips_per_bus

        # Saturation réelle (%) = (Passagers montés / Capacité offerte) * 100
        real_saturation = min((total_boarded / max(1, offered_capacity)) * 100.0, 100.0)

        # Pression d'attente moyenne à quai ramenée par bus affecté à la ligne
        pressure_per_bus = avg_waiting / max(1, bus_count)

        # 1. Cas d'engorgement élevé (Saturation > 80% OU forte pression d'attente > 5 passagers/bus)
        if real_saturation > 80.0 or pressure_per_bus > 5.0:
            suggestions.append(
                OptimizationAction(
                    action_type="add_bus",
                    line_id=row.route_id,
                    description=(
                        f"Ajouter 1 à 2 bus sur la ligne {row.route_name} aux heures de pointe "
                        f"(Saturation : {real_saturation:.0f}%, Pression : {pressure_per_bus:.1f} étudiants/bus en attente)"
                    ),
                    metric_value=round(real_saturation, 1),
                    metric_label=f"Saturation réelle : {real_saturation:.0f}%",
                )
            )
        # 2. Cas de saturation modérée (60% à 80%) -> Réajustement des horaires / fréquences
        elif 60.0 <= real_saturation <= 80.0:
            suggestions.append(
                OptimizationAction(
                    action_type="reschedule",
                    line_id=row.route_id,
                    description=(
                        f"Rapprocher la fréquence de passage sur {row.route_name} "
                        f"(réduire l'intervalle entre départs) pour lisser la charge (Saturation : {real_saturation:.0f}%)"
                    ),
                    metric_value=round(real_saturation, 1),
                    metric_label=f"Taux de saturation : {real_saturation:.0f}%",
                )
            )
        # 3. Cas de sous-fréquentation avec surplus de bus (bus_count >= 2 et saturation < 30%) -> Réallocation
        elif real_saturation < 30.0 and bus_count >= 2:
            suggestions.append(
                OptimizationAction(
                    action_type="reallocate_bus",
                    line_id=row.route_id,
                    description=(
                        f"Sous-fréquentation sur {row.route_name} ({total_boarded} passagers/24h avec {bus_count} bus). "
                        f"Réallouer 1 bus vers une ligne saturée."
                    ),
                    metric_value=round(real_saturation, 1),
                    metric_label=f"Saturation : {real_saturation:.0f}% ({bus_count} bus)",
                )
            )
        # 4. Cas de très faible fréquentation sur ligne solo -> Fusion de lignes
        elif real_saturation < 20.0 and bus_count <= 1 and total_boarded < 50:
            suggestions.append(
                OptimizationAction(
                    action_type="merge_lines",
                    line_id=row.route_id,
                    description=(
                        f"Très faible fréquentation sur {row.route_name} ({total_boarded} passagers/24h). "
                        f"Envisager la fusion avec une ligne voisine."
                    ),
                    metric_value=float(total_boarded),
                    metric_label=f"Passagers/24h : {total_boarded}",
                )
            )

    hotspots = [
        {
            "stop_id": row.stop_id,
            "stop_name": row.stop_name,
            "total_waiting_24h": int(row.total_waiting or 0),
            "total_boarded_24h": int(row.total_boarded or 0),
        }
        for row in stop_stats
    ]

    return OptimizationSuggestionsResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        suggestions=suggestions,
        hotspots=hotspots,
        peak_hours={
            "morning": {"start": "06:30", "end": "08:30", "multiplier": 2.5, "direction": "vers UAC"},
            "evening": {"start": "17:00", "end": "19:30", "multiplier": 3.0, "direction": "depuis UAC"},
        },
    )

