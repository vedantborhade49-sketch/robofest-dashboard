from typing import Optional, List
from datetime import datetime
from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider
from app.models.incident import Incident
from app.models.event import Event

class DataService:
    _instance: Optional["DataService"] = None

    def __new__(cls, provider: Optional[DataProvider] = None):
        # Singleton pattern so view updates share the same provider state and event log
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._provider = provider or MockDataProvider()
        elif provider is not None:
            cls._instance._provider = provider
        return cls._instance

    def get_mission_data(self): return self._provider.get_mission()
    def get_drone_data(self): return self._provider.get_drone()
    def get_telemetry_data(self): return self._provider.get_telemetry()
    def get_camera_data(self): return self._provider.get_camera()
    def get_ai_data(self): return self._provider.get_ai_status()
    def get_system_health(self): return self._provider.get_system_health()
    def get_incidents(self) -> List[Incident]: return self._provider.get_incidents()
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        if hasattr(self._provider, "get_incident"):
            return self._provider.get_incident(incident_id)
        for inc in self.get_incidents():
            if inc.incident_id == incident_id:
                return inc
        return None
        
    def get_events(self) -> List[Event]: return self._provider.get_events()
    def get_detections(self): return self._provider.get_detections()
    def get_map_state(self): return self._provider.get_map_state()
    
    def add_event(self, event: Event):
        self._provider.add_event(event)

    def log_event(self, message: str, event_type: str = "INCIDENT", severity: str = "INFO"):
        self.add_event(Event(
            timestamp=datetime.now(),
            event_type=event_type,
            message=message,
            severity=severity
        ))
