from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class Stop(Base):
    """Un arrêt de bus avec sa position géospatiale (PostGIS)."""
    __tablename__ = "stops"

    id = Column(String(50), primary_key=True)             
    name = Column(String(100), nullable=False)             
    zone_name = Column(String(100), nullable=False)        
    location = Column(Geometry("POINT", srid=4326), nullable=False)

    flux_records = relationship("PassengerFlux", back_populates="stop")


class Route(Base):
    """Une ligne de bus avec son tracé géospatial."""
    __tablename__ = "routes"

    id = Column(String(50), primary_key=True)              
    code = Column(String(20), nullable=False)             
    name = Column(String(100), nullable=False)            
    path = Column(Geometry("LINESTRING", srid=4326), nullable=True)

    buses = relationship("Bus", back_populates="route")


class Bus(Base):
    """Un bus avec sa capacité et sa ligne actuelle."""
    __tablename__ = "buses"

    id = Column(String(50), primary_key=True)             
    registration_number = Column(String(20), nullable=False, unique=True)
    capacity = Column(Integer, default=60, nullable=False)
    current_route_id = Column(String(50), ForeignKey("routes.id"), nullable=True)
    trip_count = Column(Integer, default=0, nullable=False)  # Nombre de rotations complètes effectuées

    route = relationship("Route", back_populates="buses")
    flux_records = relationship("PassengerFlux", back_populates="bus")


class PassengerFlux(Base):
    """Snapshot du flux de passagers à un arrêt pour un bus donné."""
    __tablename__ = "passenger_flux"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stop_id = Column(String(50), ForeignKey("stops.id"), nullable=False)
    bus_id = Column(String(50), ForeignKey("buses.id"), nullable=False)
    boarded_count = Column(Integer, default=0, nullable=False)
    alighted_count = Column(Integer, default=0, nullable=False)
    waiting_count = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    stop = relationship("Stop", back_populates="flux_records")
    bus = relationship("Bus", back_populates="flux_records")


class BusTripLog(Base):
    """
    Journal horodaté de chaque terminus atteint par un bus.

    Contrairement à Bus.trip_count (compteur cumulatif global), cette table
    permet de compter les rotations sur n'importe quelle fenêtre temporelle
    (ex : dernières 24h) en filtrant sur `timestamp`, exactement comme PassengerFlux.
    """
    __tablename__ = "bus_trip_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bus_id = Column(String(50), ForeignKey("buses.id"), nullable=False)
    route_id = Column(String(50), ForeignKey("routes.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    bus = relationship("Bus")
    route = relationship("Route")

