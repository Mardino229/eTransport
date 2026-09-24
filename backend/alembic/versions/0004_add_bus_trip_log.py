"""Créer la table bus_trip_log pour journaliser les terminus horodatés

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-24 07:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS bus_trip_log (
            id SERIAL PRIMARY KEY,
            bus_id VARCHAR(50) NOT NULL REFERENCES buses(id),
            route_id VARCHAR(50) NOT NULL REFERENCES routes(id),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_btl_timestamp ON bus_trip_log (timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_btl_bus_id ON bus_trip_log (bus_id)")


def downgrade() -> None:
    op.drop_index("ix_btl_bus_id", table_name="bus_trip_log")
    op.drop_index("ix_btl_timestamp", table_name="bus_trip_log")
    op.drop_table("bus_trip_log")
