"""
Routes et Endpoints de l'API FastAPI eTransport MTDI Bénin.

Expose les contrôleurs HTTP REST (Capacité, Analytics, Recommandation, Optimisation)
et l'endpoint WebSocket pour la diffusion temps réel.
"""

import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, get_redis
from app.schemas import (
    BusLiveSchema,
    RecommendationRequest,
    RecommendationResponse,
    StopAnalyticsSchema,
    TopRouteSchema,
    OptimizationSuggestionsResponse,
)
from app.data.dataset import STOPS, ROUTES, BUSES
from app.services import analytics as analytics_svc
from app.services.recommendation import compute_recommendations

import redis as redis_lib

router = APIRouter()


@router.get(
    "/network/stops",
    tags=["Arrêts"],
    summary="Retourne la liste complète des arrêts officiels avec leurs coordonnées GPS",
)
def get_network_stops():
    return list(STOPS.values())


@router.get(
    "/network/routes",
    tags=["Itinéraires"],
    summary="Retourne la configuration des 14 lignes avec arrêts et waypoints",
)
def get_network_routes():
    return ROUTES


@router.get(
    "/buses/live",
    response_model=list[BusLiveSchema],
    tags=["Capacité"],
    summary="Retourne tous les bus en temps réel avec positions GPS, places disponibles et taux de remplissage",
)
def get_buses_live(redis: redis_lib.Redis = Depends(get_redis)):
    """

    Point d'entrée REST HTTP GET `/api/v1/buses/live`.
    Interroge Redis et retourne la liste instantanée des bus avec positions GPS, vitesses,
    places disponibles et taux de remplissage.

    Permet le chargement initial de la carte interactive et sert de système de secours (polling)
    si la connexion WebSocket réseau est interrompue.
    """
    buses = analytics_svc.get_all_buses_live(redis)
    return buses


@router.get(
    "/stops/{stop_id}/analytics",
    response_model=StopAnalyticsSchema,
    tags=["Arrêts"],
    summary="Montées, descentes, personnes en attente et temps d'attente moyen à un arrêt",
)
def get_stop_analytics(stop_id: str, db: Session = Depends(get_db)):
    """

    Point d'entrée REST HTTP GET `/api/v1/stops/{stop_id}/analytics`.
    Reçoit un identifiant d'arrêt (ex: `STOP_UAC`) et retourne les statistiques agrégées des flux
    de voyageurs enregistrés sur les dernières 24 heures.

    Alimente les fiches analytiques par station dans le tableau de bord de gestion du COUS-AC.
    """
    try:
        return analytics_svc.get_stop_analytics(stop_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/routes/top5",
    response_model=list[TopRouteSchema],
    tags=["Itinéraires"],
    summary="Top 5 des lignes les plus fréquentées avec volume journalier et taux de saturation",
)
def get_top5_routes(db: Session = Depends(get_db)):
    """

    Point d'entrée REST HTTP GET `/api/v1/routes/top5`.
    Calcule et renvoie le classement des 5 lignes de transport universitaire les plus fréquentées.

    Fournit les données visualisées sous forme de graphique à barres dans la section Analytics du dashboard.
    """
    return analytics_svc.get_top5_routes(db)


@router.post(
    "/recommendation",
    response_model=RecommendationResponse,
    tags=["Recommandation"],
    summary="Recommande le meilleur bus disponible pour un étudiant (score pondéré + réservation atomique Redis)",
)
def get_recommendation(
    request: RecommendationRequest,
    redis: redis_lib.Redis = Depends(get_redis),
):
    """

    Point d'entrée REST HTTP POST `/api/v1/recommendation`.
    Traite la demande d'un étudiant (position GPS, arrêt de destination), calcule le bus optimal,
    effectue la réservation atomique d'un siège et renvoie le résultat accompagné de 3 bus alternatifs.

    Forme l'interface d'entrée du moteur de guidage personnalisé pour les étudiants de l'UAC.
    """
    try:
        return compute_recommendations(request, redis)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.get(
    "/optimizations/suggestions",
    response_model=OptimizationSuggestionsResponse,
    tags=["Optimisation"],
    summary="Suggestions d'optimisation chiffrées basées sur l'analyse des données historiques",
)
def get_optimization_suggestions(db: Session = Depends(get_db)):
    """

    Point d'entrée REST HTTP GET `/api/v1/optimizations/suggestions`.
    Génère un rapport synthétique contenant les actions d'optimisation préconisées
    (ajout de bus, réajustement des départs, fusion de lignes) et les zones de congestion (hotspots).

    Alimente le panneau décisionnel d'aide à la régulation pour les autorités du transport universitaire.
    """
    return analytics_svc.get_optimization_suggestions(db)


@router.websocket("/ws/buses")
async def websocket_buses(websocket: WebSocket):
    """

    Endpoint WebSocket `/ws/buses`.
    Accepte la connexion du navigateur, transmet immédiatement la liste complète de tous les bus en circulation (`snapshot`),
    puis s'abonne au canal Redis Pub/Sub `bus_updates` pour pousser en direct chaque déplacement de véhicule.

    Permet l'affichage dynamique fluide et en temps réel de la flotte sur la carte Leaflet sans aucun rafraîchissement de page.
    """
    await websocket.accept()
    r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    try:
        bus_keys = await r.keys("bus:*")
        bus_keys = [k for k in bus_keys if not k.endswith(":reserved_seats")]
        snapshot = []
        for key in bus_keys:
            raw = await r.hgetall(key)
            if raw and "bus_id" in raw:
                snapshot.append(raw)
        if snapshot:
            await websocket.send_text(json.dumps({"type": "snapshot", "buses": snapshot}))
    except Exception as e:
        print(f"[WS] Erreur lors de l'envoi du snapshot initial: {e}")

    pubsub = r.pubsub()
    await pubsub.subscribe("bus_updates")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("bus_updates")
        await r.aclose()
