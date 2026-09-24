"""
Point d'entrée principal de l'application backend FastAPI eTransport MTDI Bénin.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """

    Gestionnaire du cycle de vie de l'application (Lifespan Context Manager).
    Au démarrage (`startup`), elle vérifie et crée les tables dans PostgreSQL si elles n'existent pas encore.
    À l'arrêt (`shutdown`), elle libère les ressources et connexions actives.

    Garantit que la base de données relationnelle est prête à recevoir des requêtes dès que le serveur Web s'allume.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[WARNING] Impossible de créer les tables : {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API REST + WebSocket pour le système de transport universitaire MTDI Bénin. "
        "Suivi GPS temps réel, gestion des capacités, recommandation intelligente et optimisation des lignes."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuration des autorisations CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes API et WebSocket
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="")


@app.get("/", tags=["Health"])
def root():
    """

    Contrôleur de la route racine HTTP GET `/`.
    Renvoie un document JSON synthétique avec le statut "running" du serveur backend et les URLs d'accès aux endpoints.

    Sert de test de santé (Health Check) pour vérifier la disponibilité de l'API et accéder à la documentation OpenAPI Swagger (`/docs`).
    """
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
        "buses_live": f"{settings.API_V1_STR}/buses/live",
        "recommendation": f"{settings.API_V1_STR}/recommendation",
        "optimizations": f"{settings.API_V1_STR}/optimizations/suggestions",
    }
