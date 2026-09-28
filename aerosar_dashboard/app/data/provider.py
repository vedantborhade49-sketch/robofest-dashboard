from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Incident
from app.models.event import Event
from app.models.detection import Detection
from app.models.report import Report

class DataProvider(ABC):
    """Abstract base class for all data providers."""
    @abstractmethod
    def get_mission(self) -> Optional[Mission]: pass
    @abstractmethod
    def get_drone(self) -> Optional[Drone]: pass
    @abstractmethod
    def get_camera(self) -> Optional[Camera]: pass
    @abstractmethod
    def get_ai_status(self) -> Optional[AIStatus]: pass
    @abstractmethod
    def get_telemetry(self) -> Optional[Telemetry]: pass
    @abstractmethod
    def get_system_health(self) -> Optional[SystemHealth]: pass
    @abstractmethod
    def get_incidents(self) -> List[Incident]: pass
    @abstractmethod
    def get_events(self) -> List[Event]: pass
    def get_event(self, event_id: str) -> Optional[Event]: return None
    @abstractmethod
    def get_detections(self) -> List[Detection]: pass
    def add_event(self, event: Event): pass
    def get_map_state(self): pass
    def get_telemetry_state(self): pass
    def get_reports(self) -> List[Report]: return []
    def get_report(self, report_id: str) -> Optional[Report]: return None
    def step_simulation(self):
        """Advances the physical and sensor simulation state by one cycle."""
        pass

    def add_incident(self, incident: Incident):
        """Adds a new incident to the provider."""
        pass

    def update_incident(self, incident: Incident):
        """Updates an existing incident."""
        pass




