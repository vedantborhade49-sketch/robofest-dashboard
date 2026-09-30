import time
import logging
import threading
from typing import Dict, Any, Optional

from app.onboard.service_manager import OnboardService
from app.onboard.communication import CommunicationService
from app.onboard.config import OnboardConfig

# Domain imports
from app.perception.perception_service import PerceptionService
from app.perception.camera import VideoSource, MockCameraSource, WebcamSource, VideoFileSource, PiCameraSource
from app.spatial.service import SpatialService
from app.telemetry.service import TelemetryService
from app.services.incident_engine import IncidentEngine
from app.models.incident import Incident, Location
from app.models.detection import Detection

logger = logging.getLogger(__name__)

class PerceptionAdapterService(OnboardService):
    """Headless wrapper for the existing PerceptionService and Camera."""
    def __init__(self, config: OnboardConfig, comms: CommunicationService, incident_engine: IncidentEngine):
        self.config = config
        self.comms = comms
        self.incident_engine = incident_engine
        
        self.source = self._create_source()
        self.perception = PerceptionService(source=self.source) 
        
        self._running = False
        self._camera_thread = None
        self._inference_thread = None
        self._status = "INIT"
        
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        
        self._camera_frame_count = 0
        self._inference_frame_count = 0
        self._last_fps_time = time.time()
        self._current_camera_fps = 0.0
        self._current_inference_fps = 0.0

    def _create_source(self) -> VideoSource:
        if self.config.camera_provider == "webcam":
            return WebcamSource(self.config.camera_index)
        elif self.config.camera_provider == "video":
            return VideoFileSource(self.config.video_file_path)
        elif self.config.camera_provider == "pi":
            return PiCameraSource(self.config.camera_index)
        else:
            return MockCameraSource()

    def initialize(self) -> bool:
        if not self.source.open():
            logger.error("Failed to open camera source")
            self._status = "ERROR"
            return False
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self.perception.start()
        
        self._camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self._inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        
        self._camera_thread.start()
        self._inference_thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.perception.stop()
        if self._camera_thread:
            self._camera_thread.join(timeout=2.0)
        if self._inference_thread:
            self._inference_thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        return self._status

    def get_health(self) -> Dict[str, Any]:
        return {
            "inference_time_ms": self.perception.status.inference_time_ms,
            "running": self.perception.running,
            "error": self.perception.status.error,
            "camera_fps": round(self._current_camera_fps, 1),
            "inference_fps": round(self._current_inference_fps, 1),
            "detections": self.perception.status.detection_count,
            "model_loaded": self.perception.status.model_loaded
        }

    def _camera_loop(self):
        """Continuously pulls frames to keep buffer empty and track FPS."""
        # For video files we might want to sleep to match FPS, but for webcams we pull as fast as possible
        target_delay = 1.0 / self.config.camera_fps
        
        while self._running:
            start_time = time.time()
            
            frame = self.source.read()
            if frame is not None:
                with self._frame_lock:
                    self._latest_frame = frame
                self._camera_frame_count += 1
            
            self._update_fps()
            
            elapsed = time.time() - start_time
            sleep_time = target_delay - elapsed
            if sleep_time > 0 and self.config.camera_provider in ["video", "mock"]:
                time.sleep(sleep_time)

    def _update_fps(self):
        now = time.time()
        if now - self._last_fps_time >= 1.0:
            self._current_camera_fps = self._camera_frame_count / (now - self._last_fps_time)
            self._current_inference_fps = self._inference_frame_count / (now - self._last_fps_time)
            self._camera_frame_count = 0
            self._inference_frame_count = 0
            self._last_fps_time = now

    def _inference_loop(self):
        interval = self.config.perception_interval_ms / 1000.0
        while self._running:
            try:
                frame = None
                with self._frame_lock:
                    if self._latest_frame is not None:
                        frame = self._latest_frame.copy()
                        
                if frame is not None:
                    detections, _ = self.perception.process_single_frame(frame)
                    self._inference_frame_count += 1
                    
                    if detections:
                        # Pass to incident engine locally
                        mock_loc = Location(x=0.0, y=0.0, z=0.0, lat=0.0, lon=0.0, alt=0.0)
                        for d_dict in detections:
                            # d_dict is a dictionary from the existing YOLO detector, we need to convert it
                            det = Detection(**d_dict) if isinstance(d_dict, dict) else d_dict
                            incident = self.incident_engine.process_detection(
                                detection=det,
                                current_location=mock_loc
                            )
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
