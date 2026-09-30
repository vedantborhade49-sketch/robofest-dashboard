import time
import logging
import threading
from typing import Dict, Any, Optional

from app.onboard.service_manager import OnboardService
from app.onboard.communication import CommunicationService
from app.onboard.config import OnboardConfig

# Domain imports
from app.perception.perception_service import PerceptionService
from app.perception.camera import VideoSource
from app.spatial.service import SpatialService
from app.telemetry.service import TelemetryService
from app.services.incident_engine import IncidentEngine
from app.models.incident import Incident

logger = logging.getLogger(__name__)

class PerceptionAdapterService(OnboardService):
    """Headless wrapper for the existing PerceptionService and Camera."""
    def __init__(self, config: OnboardConfig, comms: CommunicationService, incident_engine: IncidentEngine):
        self.config = config
        self.comms = comms
        self.incident_engine = incident_engine
        
        # Initialize domain service
        # In a real setup, we configure the VideoSource based on config.camera_provider
        self.perception = PerceptionService() 
        
        self._running = False
        self._thread = None
        self._status = "INIT"

    def initialize(self) -> bool:
        # We would inject Mock or Real providers here based on self.config
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self.perception.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.perception.stop()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        return self._status

    def get_health(self) -> Dict[str, Any]:
        return {
            "inference_time_ms": self.perception.status.inference_time_ms,
            "running": self.perception.running,
            "error": self.perception.status.error
        }

    def _loop(self):
        interval = self.config.perception_interval_ms / 1000.0
        while self._running:
            try:
                detections, _ = self.perception.run_once()
                if detections:
                    # Pass to incident engine locally
                    for d in detections:
                        incident = self.incident_engine.process_detection(d)
                        if incident:
                            # Send structured incident to ground station
                            self.comms.send_event("INCIDENT_CREATED", incident.model_dump())
            except Exception as e:
                logger.error(f"Perception loop error: {e}")
            time.sleep(interval)


class SpatialAdapterService(OnboardService):
    """Headless wrapper for SpatialService (LiDAR + SLAM)."""
    def __init__(self, config: OnboardConfig, comms: CommunicationService, spatial_service: SpatialService):
        self.config = config
        self.comms = comms
        self.spatial = spatial_service
        self._running = False
        self._thread = None
        self._status = "INIT"

    def initialize(self) -> bool:
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self.spatial.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.spatial.stop()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        return self._status

    def get_health(self) -> Dict[str, Any]:
        return {
            "sensor_status": self.spatial.state.sensor_status,
            "slam_status": self.spatial.state.slam_status
        }

    def _loop(self):
        interval = self.config.lidar_interval_ms / 1000.0
        while self._running:
            try:
                state = self.spatial.update()
                # Send periodic spatial updates if configured, or just on significant changes
                # self.comms.send_event("SPATIAL_UPDATE", state.model_dump())
            except Exception as e:
                logger.error(f"Spatial loop error: {e}")
            time.sleep(interval)


class TelemetryAdapterService(OnboardService):
    """Headless wrapper for TelemetryService (MAVLink)."""
    def __init__(self, config: OnboardConfig, comms: CommunicationService, telemetry_service: TelemetryService):
        self.config = config
        self.comms = comms
        self.telemetry = telemetry_service
        self._running = False
        self._thread = None
        self._status = "INIT"

    def initialize(self) -> bool:
        self.telemetry.provider.connect()
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.telemetry.provider.disconnect()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        return self._status

    def get_health(self) -> Dict[str, Any]:
        return {
            "link_status": self.telemetry.state.communication.link_status,
            "heartbeat_age": self.telemetry.state.communication.heartbeat_age
        }

    def _loop(self):
        interval = self.config.telemetry_interval_ms / 1000.0
        while self._running:
            try:
                if not self.telemetry.provider.is_connected():
                    self.telemetry.provider.connect()
                    time.sleep(1.0)
                    continue
                    
                state = self.telemetry.update()
                if state:
                    self.comms.send_event("TELEMETRY_UPDATE", state.model_dump())
            except Exception as e:
                logger.error(f"Telemetry loop error: {e}")
            time.sleep(interval)
