"""Initial schema + seed data for eTransport

Revision ID: 0001
Revises: 
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from app.data.dataset import STOPS, ROUTES, BUSES

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Activation de PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Table stops
    op.create_table(
        "stops",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("zone_name", sa.String(100), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
    )

    # Table routes
    op.create_table(
        "routes",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "path",
            geoalchemy2.types.Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True,
        ),
    )

    # Table buses
    op.create_table(
        "buses",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("registration_number", sa.String(20), nullable=False, unique=True),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="60"),
        sa.Column("current_route_id", sa.String(50), sa.ForeignKey("routes.id"), nullable=True),
    )

    # Table passenger_flux
    op.create_table(
        "passenger_flux",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("stop_id", sa.String(50), sa.ForeignKey("stops.id"), nullable=False),
        sa.Column("bus_id", sa.String(50), sa.ForeignKey("buses.id"), nullable=False),
        sa.Column("boarded_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("alighted_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("waiting_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_pf_stop_id", "passenger_flux", ["stop_id"])
    op.create_index("ix_pf_bus_id", "passenger_flux", ["bus_id"])
    op.create_index("ix_pf_timestamp", "passenger_flux", ["timestamp"])

    # 1. SEED : Arrêts de bus (Réseau COUS-AC UAC)
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

    # 2. SEED : 14 Lignes Officiels COUS-AC
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

    # 3. SEED : Flotte de 35 Bus COUS-AC
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
    op.drop_table("passenger_flux")
    op.drop_table("buses")
    op.drop_table("routes")
    op.drop_table("stops")
    op.execute("DROP EXTENSION IF EXISTS postgis")
