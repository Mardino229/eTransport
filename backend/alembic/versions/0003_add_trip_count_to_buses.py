"""Ajouter trip_count à la table buses pour comptabiliser les rotations réelles

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-24 07:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajout de la colonne trip_count avec valeur par défaut 0
    # IF NOT EXISTS = idempotent si la colonne existe déjà
    op.execute("""
        ALTER TABLE buses
        ADD COLUMN IF NOT EXISTS trip_count INTEGER NOT NULL DEFAULT 0
    """)


def downgrade() -> None:
    op.drop_column("buses", "trip_count")
