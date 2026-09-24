"""Upsert COUS-AC dataset for UAC (15 stops, 14 routes, 35 buses)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22 15:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from app.data.dataset import STOPS, ROUTES, BUSES

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Upsert des 15 Arrêts UAC COUS-AC depuis la Source Unique de Vérité
    for stop_id, s in STOPS.items():
        name_clean = s["name"].replace("'", "''")
        zone_clean = s["zone"].replace("'", "''")
        op.execute(f"""
            INSERT INTO stops (id, name, zone_name, location)
            VALUES ('{stop_id}', '{name_clean}', '{zone_clean}', ST_SetSRID(ST_MakePoint({s['lng']}, {s['lat']}), 4326))
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                zone_name = EXCLUDED.zone_name,
                location = EXCLUDED.location
        """)

    # 2. Upsert des 14 Lignes Officiels COUS-AC
    for route_id, r in ROUTES.items():
        name_clean = r["name"].replace("'", "''")
        wps = r.get("waypoints", [])
        if wps:
            wps_sql = ", ".join(f"ST_MakePoint({lng}, {lat})" for lat, lng in wps)
            path_sql = f"ST_SetSRID(ST_MakeLine(ARRAY[{wps_sql}]), 4326)"
        else:
            path_sql = "NULL"

        op.execute(f"""
            INSERT INTO routes (id, code, name, path)
            VALUES ('{route_id}', '{r["code"]}', '{name_clean}', {path_sql})
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                name = EXCLUDED.name,
                path = EXCLUDED.path
        """)

    # 3. Upsert de la flotte des 35 Bus UAC
    for b in BUSES:
        reg_num = b.get("registration_number", f"RB-{b['id']}")
        op.execute(f"""
            INSERT INTO buses (id, registration_number, capacity, current_route_id)
            VALUES ('{b["id"]}', '{reg_num}', {b["capacity"]}, '{b["route_id"]}')
            ON CONFLICT (id) DO UPDATE SET
                capacity = EXCLUDED.capacity,
                current_route_id = EXCLUDED.current_route_id
        """)


def downgrade() -> None:
    pass
