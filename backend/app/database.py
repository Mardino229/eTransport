"""
Gestionnaire de connexions aux bases de données PostgreSQL et Redis pour eTransport MTDI Bénin.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import redis as redis_lib
from app.config import settings

# Engine SQLAlchemy (PostgreSQL + PostGIS)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Client Redis synchrone pour les dépendances FastAPI
redis_client = redis_lib.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_db():
    """
    Ce que fait cette fonction :
    -----------------------------
    Générateur de dépendance (Dependency Provider) FastAPI pour les sessions de base de données.
    Instancie une nouvelle session SQLAlchemy `SessionLocal()`, la met à disposition de l'endpoint,
    et garantit sa fermeture automatique (`db.close()`) une fois le traitement terminé.

    Utilité pour l'application globale :
    ------------------------------------
    Assure une gestion propre, sécurisée et sans fuite de connexions à la base de données relationnelle PostgreSQL.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """
    Ce que fait cette fonction :
    -----------------------------
    Fournisseur de dépendance FastAPI qui retourne l'instance partagée du client Redis synchrone.

    Utilité pour l'application globale :
    ------------------------------------
    Permet aux endpoints API (recommandation, capacité live) d'accéder instantanément au cache en mémoire vive Redis.
    """
    return redis_client
