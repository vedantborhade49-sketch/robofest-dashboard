import logging
import httpx
from typing import Optional, List
from datetime import datetime

from app.data.provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry, TelemetryState
from app.models.system import SystemHealth
from app.models.incident import Incident
from app.models.event import Event
from app.models.detection import Detection
from app.models.report import Report
from app.models.map import MapState

logger = logging.getLogger(__name__)

class APIDataProvider(DataProvider):
    """
    Connects to the Ground Station FastAPI via REST for initial synchronization.
    After initialization, live updates are handled by the RealtimeClient WebSocket.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=2.0)
        
        # Internal cache populated by initial sync
        self._mission: Optional[Mission] = None
        self._drone: Optional[Drone] = None
        self._camera: Optional[Camera] = None
        self._ai: Optional[AIStatus] = None
        self._telemetry: Optional[Telemetry] = None
        self._health: Optional[SystemHealth] = None
        self._incidents: List[Incident] = []
        self._events: List[Event] = []
        self._reports: List[Report] = []
        
        self.sync_initial_state()

    def sync_initial_state(self):
        """Fetches initial state from REST API so the dashboard isn't empty on boot."""
        try:
            # For this step, we fetch what's available. If endpoints don't exist yet, we catch the 404.
            # Example endpoints (based on existing backend architecture)
            
            # Incidents
            try:
                resp = self.client.get(f"{self.base_url}/incidents")
                if resp.status_code == 200:
                    data = resp.json()
                    self._incidents = [Incident(**i) for i in data.get("incidents", data)]
            except Exception as e:
                logger.warning(f"Could not sync initial incidents: {e}")

            # Reports
            try:
                resp = self.client.get(f"{self.base_url}/reports")
                if resp.status_code == 200:
                    data = resp.json()
                    self._reports = [Report(**r) for r in data.get("reports", data)]
            except Exception as e:
                logger.warning(f"Could not sync initial reports: {e}")

            # System Health / Status could be added here
            try:
                resp = self.client.get(f"{self.base_url}/onboard/status")
                if resp.status_code == 200:
                    # Update local caches if needed
                    pass
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to perform REST initial sync: {e}")

    # Standard getters (returning cached objects or empty defaults, as WebSocket updates StateManager directly)
    def get_mission(self) -> Optional[Mission]:
        return self._mission or Mission(
            mission_id="LIVE-MISSION", mission_status="WAITING",
            elapsed_time=0.0, search_progress=0.0, connection_status="DISCONNECTED"
        )

    def get_drone(self) -> Optional[Drone]:
        return self._drone or Drone(
            drone_id="AEROSAR", status="WAITING", battery=0.0,
            altitude=0.0, speed=0.0, heading=0.0, signal_strength=0.0
        )

    def get_camera(self) -> Optional[Camera]:
        return self._camera or Camera(
            connected=False, fps=0.0, latency=0.0, frame_count=0,
            dropped_frames=0, resolution="N/A"
        )

    def get_ai_status(self) -> Optional[AIStatus]:
        return self._ai or AIStatus(
            status="WAITING", model_name="N/A", inference_fps=0.0,
            detections_count=0, device="N/A"
        )

    def get_telemetry(self) -> Optional[Telemetry]:
        return self._telemetry

    def get_system_health(self) -> Optional[SystemHealth]:
        return self._health or SystemHealth(
            cpu_usage=0.0, memory_usage=0.0, temperature=0.0,
            communication_status="WAITING"
        )

    def get_incidents(self) -> List[Incident]:
        return self._incidents

    def get_events(self) -> List[Event]:
        return self._events

    def get_detections(self) -> List[Detection]:
        return []

    def get_map_state(self) -> MapState:
        from app.models.incident import Location
        return MapState(drone_position=Location(latitude=0.0, longitude=0.0, x=0.0, y=0.0, z=0.0))

    def get_telemetry_state(self) -> TelemetryState:
        if self._telemetry:
            return TelemetryState(flight=self._telemetry)
        from app.models.telemetry import FlightTelemetry
        return TelemetryState(flight=FlightTelemetry())

    def get_reports(self) -> List[Report]:
        return self._reports

    def step_simulation(self):
        # We don't simulate anything in live mode
        pass

    def add_incident(self, incident: Incident):
        # Already pushed to backend by operator actions via REST if needed.
        pass

    def update_incident(self, incident: Incident):
        try:
            self.client.put(
                f"{self.base_url}/incidents/{incident.incident_id}/status",
                params={"status": incident.status}
            )
        except Exception as e:
            logger.error(f"Failed to update incident on backend: {e}")

    def add_event(self, event: Event):
        pass
