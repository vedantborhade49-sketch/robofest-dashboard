from typing import Optional, List
from datetime import datetime
from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider
from app.models.incident import Incident
from app.models.event import Event
from app.models.report import Report

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
    def get_event(self, event_id: str) -> Optional[Event]:
        if hasattr(self._provider, "get_event"):
            return self._provider.get_event(event_id)
        for e in self.get_events():
            if e.event_id == event_id:
                return e
        return None
    def get_detections(self): return self._provider.get_detections()
    def get_map_state(self): return self._provider.get_map_state()
    def get_telemetry_state(self): return self._provider.get_telemetry_state()

    def get_reports(self) -> List[Report]:
        if hasattr(self._provider, "get_reports"):
            return self._provider.get_reports()
        return []

    def get_report(self, report_id: str) -> Optional[Report]:
        if hasattr(self._provider, "get_report"):
            return self._provider.get_report(report_id)
        for r in self.get_reports():
            if r.report_id == report_id:
                return r
        return None

    def get_report_by_incident_id(self, incident_id: str) -> Optional[Report]:
        if hasattr(self._provider, "get_report_by_incident_id"):
            return self._provider.get_report_by_incident_id(incident_id)
        for r in self.get_reports():
            if r.incident_id == incident_id:
                return r
        return None

    def review_report(self, report_id: str) -> bool:
        if hasattr(self._provider, "review_report"):
            return self._provider.review_report(report_id)
        return False
    
    def add_event(self, event: Event):
        self._provider.add_event(event)

    def log_event(
        self,
        message: str,
        event_type: str = "INCIDENT",
        severity: str = "INFO",
        source: str = "SYSTEM",
        level: Optional[str] = None,
        mission_id: Optional[str] = "SAR-001",
        incident_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        eff_level = level or severity
        self.add_event(Event(
            timestamp=datetime.now(),
            level=eff_level,
            source=source,
            event_type=event_type,
            message=message,
            severity=eff_level,
            mission_id=mission_id,
            incident_id=incident_id,
            details=details
        ))


