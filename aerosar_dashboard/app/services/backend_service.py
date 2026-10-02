from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database.database import init_db
from app.database.repository import Repository
from app.models.ai import AIStatus
from app.models.camera import Camera
from app.models.drone import Drone
from app.models.event import Event
from app.models.incident import Incident
from app.models.mission import Mission
from app.models.report import Report
from app.models.context import RetrievedContext
from app.models.system import SystemHealth
from app.models.telemetry import TelemetryState
from app.models.evidence import Evidence
from app.services.incident_service import IncidentService
from app.services.evidence_service import EvidenceService


class BackendService:
    def __init__(self, repository: Optional[Repository] = None):
        init_db()
        self.repository = repository or Repository()
        self.incident_service = IncidentService(self.repository)
        self.evidence_service = EvidenceService()

    def get_system_status(self) -> Dict[str, Any]:
        try:
            init_db()
            db_status = "connected"
        except Exception:
            db_status = "error"

        return {
            "backend": "online",
            "database": db_status,
            "environment": "development",
            "version": "0.1.0",
        }

    def get_health(self) -> Dict[str, str]:
        return {"status": "ok", "service": "aerosar-backend"}

    def create_mission(self, mission_id: str, mission_name: str) -> Mission:
        mission = Mission(
            mission_id=mission_id,
            mission_name=mission_name,
            mission_status="ACTIVE",
            elapsed_time=0.0,
            search_progress=0.0,
            connection_status="CONNECTED",
            status="ACTIVE",
            start_time=datetime.now(),
            end_time=None,
        )
        self.repository.save_mission(mission)
        return mission

    def get_missions(self) -> List[Mission]:
        return self.repository.get_missions()

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        return self.repository.get_mission(mission_id)

    def create_incident(self, incident: Incident) -> Incident:
        return self.incident_service.create_incident(incident)

    def get_incidents(self) -> List[Incident]:
        return self.incident_service.list_incidents()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incident_service.get_incident(incident_id)

    def update_incident(self, incident_id: str, **updates: Any) -> Incident:
        incident = self.get_incident(incident_id)
        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        for field, value in updates.items():
            if field == "status":
                incident = self.incident_service.update_status(incident_id, str(value))
                continue
            if hasattr(incident, field) and field != "incident_id":
                setattr(incident, field, value)
        self.repository.save_incident(incident)
        return incident

    def update_incident_status(self, incident_id: str, status: str) -> Incident:
        return self.incident_service.update_status(incident_id, status)

    def attach_evidence(self, incident_id: str, evidence: Evidence) -> Incident:
        return self.incident_service.attach_evidence(incident_id, evidence)

    def get_incident_evidence(self, incident_id: str) -> List[Evidence]:
        return self.incident_service.get_evidence(incident_id)

    def create_report(self, report: Report) -> Report:
        self.repository.save_report(report)
        return report

    def get_reports(self) -> List[Report]:
        return self.repository.get_reports()

    def get_report(self, report_id: str) -> Optional[Report]:
        return self.repository.get_report(report_id)

    def create_context(self, report_id: str, context: RetrievedContext) -> RetrievedContext:
        self.repository.save_context(report_id, context)
        return context

    def get_context_for_report(self, report_id: str) -> List[RetrievedContext]:
        return self.repository.get_context_for_report(report_id)

    def create_event(self, event: Event) -> Event:
        self.repository.save_event(event)
        return event

    def get_events(self, level: Optional[str] = None, source: Optional[str] = None, mission_id: Optional[str] = None, incident_id: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        events = self.repository.get_events()
        if level:
            events = [item for item in events if str(item.level).upper() == str(level).upper()]
        if source:
            events = [item for item in events if str(item.source).upper() == str(source).upper()]
        if mission_id:
            events = [item for item in events if item.mission_id == mission_id]
        if incident_id:
            events = [item for item in events if item.incident_id == incident_id]
        if limit is not None:
            events = events[:limit]
        return events

    def get_telemetry(self) -> Dict[str, float]:
        from app.core.state_manager import StateManager
        state = StateManager.instance().get_telemetry()
        if not state:
            return {"altitude": 0.0, "speed": 0.0, "battery": 0.0, "heading": 0.0, "signal": 0.0}
        return {
            "altitude": state.flight.altitude,
            "speed": state.flight.speed,
            "battery": state.power.battery_percent,
            "heading": state.flight.heading,
            "signal": state.communication.signal_percent,
        }

    def get_drone_status(self) -> Dict[str, Any]:
        from app.core.state_manager import StateManager
        state = StateManager.instance().get_drone()
        if not state:
            return {
                "drone_id": "N/A",
                "connection": "DISCONNECTED",
                "flight_state": "UNKNOWN",
                "battery": 0.0,
                "altitude": 0.0,
            }
        return {
            "drone_id": state.drone_id,
            "connection": "CONNECTED" if state.status != "DISCONNECTED" else "DISCONNECTED",
            "flight_state": state.status,
            "battery": state.battery,
            "altitude": state.altitude,
        }

    def get_camera_status(self) -> Dict[str, Any]:
        from app.core.state_manager import StateManager
        state = StateManager.instance().get_camera()
        if not state:
            return {
                "camera_id": "CAM-01",
                "status": "DISCONNECTED",
                "fps": 0.0,
                "resolution": "N/A",
            }
        return {
            "camera_id": "CAM-01",
            "status": "CONNECTED" if state.connected else "DISCONNECTED",
            "fps": round(state.fps, 1),
            "resolution": state.resolution,
        }

    def get_ai_status(self) -> Dict[str, Any]:
        from app.core.state_manager import StateManager
        state = StateManager.instance().get_ai()
        if not state:
            return {
                "model": "N/A",
                "status": "WAITING",
                "inference_fps": 0.0,
                "latency_ms": 0.0,
            }
        return {
            "model": state.model_name,
            "status": state.status,
            "inference_fps": round(state.inference_fps, 1),
            "latency_ms": getattr(state, "inference_time_ms", 0.0),
        }

    def get_drone_position(self) -> Dict[str, float]:
        from app.core.state_manager import StateManager
        state = StateManager.instance().get_telemetry()
        if not state or not state.position:
            return {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "heading": 0.0,
            }
        return {
            "x": state.position.x,
            "y": state.position.y,
            "z": state.position.z,
            "heading": state.position.heading,
        }

    def get_database_status(self) -> str:
        try:
            init_db()
            return "connected"
        except Exception:
            return "error"
