#!/bin/sh
set -e

echo "[entrypoint] Attente de PostgreSQL..."
until pg_isready -h "${POSTGRES_SERVER:-db}" -U "${POSTGRES_USER:-etransport}"; do
  echo "[entrypoint] PostgreSQL non disponible, nouvelle tentative dans 2s..."
  sleep 2
done

echo "[entrypoint] PostgreSQL disponible. Exécution des migrations Alembic..."
alembic upgrade head

echo "[entrypoint] Démarrage de l'API FastAPI avec Uvicorn (--reload)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
