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


class BackendService:
    def __init__(self, repository: Optional[Repository] = None):
        init_db()
        self.repository = repository or Repository()

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
        self.repository.save_incident(incident)
        return incident

    def get_incidents(self) -> List[Incident]:
        return self.repository.get_incidents()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        incidents = self.get_incidents()
        for item in incidents:
            if item.incident_id == incident_id:
                return item
        return None

    def update_incident(self, incident_id: str, **updates: Any) -> Incident:
        incident = self.get_incident(incident_id)
        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        for field, value in updates.items():
            if hasattr(incident, field) and field != "incident_id":
                setattr(incident, field, value)
        self.repository.save_incident(incident)
        return incident

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
        from app.data.mock_provider import MockDataProvider
        provider = MockDataProvider()
        telemetry = provider.get_telemetry_state()
        return {
            "altitude": telemetry.flight.altitude,
            "speed": telemetry.flight.speed,
            "battery": telemetry.power.battery_percent,
            "heading": telemetry.flight.heading,
            "signal": telemetry.communication.signal_percent,
        }

    def get_drone_status(self) -> Dict[str, Any]:
        from app.data.mock_provider import MockDataProvider
        provider = MockDataProvider()
        drone = provider.get_drone()
        return {
            "drone_id": drone.drone_id,
            "connection": "SIMULATED",
            "flight_state": drone.status,
            "battery": drone.battery,
            "altitude": drone.altitude,
        }

    def get_camera_status(self) -> Dict[str, Any]:
        from app.data.mock_provider import MockDataProvider
        provider = MockDataProvider()
        camera = provider.get_camera()
        return {
            "camera_id": "CAM-01",
            "status": "SIMULATED",
            "fps": round(camera.fps, 1),
            "resolution": camera.resolution,
        }

    def get_ai_status(self) -> Dict[str, Any]:
        from app.data.mock_provider import MockDataProvider
        provider = MockDataProvider()
        ai = provider.get_ai_status()
        return {
            "model": ai.model_name,
            "status": ai.status,
            "inference_fps": round(ai.inference_fps, 1),
            "latency_ms": 54.2,
        }

    def get_drone_position(self) -> Dict[str, float]:
        from app.data.mock_provider import MockDataProvider
        provider = MockDataProvider()
        telemetry = provider.get_telemetry_state()
        return {
            "x": telemetry.position.x,
            "y": telemetry.position.y,
            "z": telemetry.position.z,
            "heading": telemetry.position.heading,
        }

    def get_database_status(self) -> str:
        try:
            init_db()
            return "connected"
        except Exception:
            return "error"
