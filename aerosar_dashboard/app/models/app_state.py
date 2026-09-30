from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import TelemetryState
from app.models.system import SystemHealth
from app.models.map import MapState
from app.models.detection import Detection
from app.models.incident import Incident
from app.models.report import Report
from app.models.event import Event
from app.models.settings import DashboardSettings
from app.models.spatial import SpatialState

class AppState(BaseModel):
    """
    Centralized, immutable application state representation representing the
    single source of truth for the entire STALLION AEROSAR Ground Station.
    All dashboard views consume slices of this state rather than maintaining
    independent, fragmented mock simulations.
    """
    mission: Mission
    drone: Drone
    camera: Camera
    ai: AIStatus
    telemetry: TelemetryState
    system: SystemHealth
    map_state: MapState
    detections: List[Detection] = Field(default_factory=list)
    incidents: List[Incident] = Field(default_factory=list)
    reports: List[Report] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    spatial: SpatialState = Field(default_factory=SpatialState)
    settings: DashboardSettings = Field(default_factory=DashboardSettings)
    last_updated: datetime = Field(default_factory=datetime.now)
    is_stale: bool = False
