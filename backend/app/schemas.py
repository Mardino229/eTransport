from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Bus Schemas

class BusLiveSchema(BaseModel):
    bus_id: str
    route_id: Optional[str] = None
    lat: float
    lng: float
    speed: float
    capacity: int
    passengers_count: int
    available_seats: int
    occupancy_rate: float
    next_stop_id: Optional[str] = None
    timestamp: str


# Stop Analytics Schemas

class StopAnalyticsSchema(BaseModel):
    stop_id: str
    stop_name: str
    total_boarded: int
    total_alighted: int
    current_waiting: int
    avg_wait_time_min: float


# Route / Top 5 Schemas 

class TopRouteSchema(BaseModel):
    route_id: str
    route_name: str
    daily_passengers: int
    saturation_rate: float  # percentage (0-100)


# Recommendation Schemas 

class RecommendationRequest(BaseModel):
    student_id: str = Field(..., example="STU_123")
    student_lat: float = Field(..., example=6.368)
    student_lng: float = Field(..., example=2.412)
    destination_stop_id: str = Field(..., example="STOP_UAC")


class ScoreBreakdown(BaseModel):
    arrival_time_score: float = Field(..., description="Contribution du temps d'arrivée (poids 0.35)")
    walking_distance_score: float = Field(..., description="Contribution de la distance de marche (poids 0.25)")
    trip_time_score: float = Field(..., description="Contribution du temps de trajet total (poids 0.25)")
    occupancy_score: float = Field(..., description="Contribution du taux de remplissage (poids 0.15)")
    uturn_penalty_score: float = Field(0.0, description="Pénalité de demi-tour au terminus (+0.15 si requis)")
    final_score: float = Field(..., description="Score final (plus faible = meilleur)")



class BusCandidate(BaseModel):
    bus_id: str
    route_id: Optional[str] = None
    lat: float
    lng: float
    available_seats: int
    capacity: int
    occupancy_rate: float
    eta_min: float = Field(..., description="Temps d'arrivée estimé à l'arrêt le plus proche (minutes)")
    walking_distance_km: float
    trip_duration_min: float
    is_direct: bool = Field(True, description="True si le bus se dirige directement vers la destination sans demi-tour préalable")
    requires_uturn: bool = Field(False, description="True si le bus doit d'abord effectuer un demi-tour au terminus")
    uturn_delay_min: float = Field(0.0, description="Temps additionnel dynamique causé par le détour/demi-tour au terminus")
    score: float
    score_breakdown: ScoreBreakdown


class RecommendationResponse(BaseModel):
    student_id: str
    destination_stop_id: str
    recommended_bus: BusCandidate
    alternatives: List[BusCandidate]
    reserved: bool = Field(..., description="True si un siège a été réservé atomiquement dans Redis")
    timestamp: str


# Optimization Schemas

class OptimizationAction(BaseModel):
    action_type: str   # 'add_bus', 'reschedule', 'new_stop', 'merge_lines'
    line_id: Optional[str] = None
    description: str
    metric_value: float
    metric_label: str  # ex: "Taux de saturation moyen: 92%"


class OptimizationSuggestionsResponse(BaseModel):
    generated_at: str
    suggestions: List[OptimizationAction]
    hotspots: List[Dict[str, Any]]
    peak_hours: Dict[str, Any]
