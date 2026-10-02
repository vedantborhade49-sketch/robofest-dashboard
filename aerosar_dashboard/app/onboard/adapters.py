import time
import logging
import threading
from typing import Dict, Any, Optional

from app.onboard.service_manager import OnboardService
from app.onboard.communication import CommunicationService
from app.onboard.config import OnboardConfig

from app.perception.camera import VideoSource, WebcamSource, VideoFileSource, PiCameraSource, MockVideoSource
from app.spatial.service import SpatialService
from app.telemetry.service import TelemetryService
from app.models.incident import Incident, Location
from app.communication.frame_sender import FrameSender

logger = logging.getLogger(__name__)

class PerceptionAdapterService(OnboardService):
    """Headless camera streamer that captures frames and sends them over Wi-Fi to the PC."""
    def __init__(self, config: OnboardConfig, comms: CommunicationService, incident_engine=None):
        self.config = config
        self.comms = comms
        # incident_engine is kept for backward compatibility with runtime.py signature but ignored
        
        self.source = self._create_source()
        
        # We start the FrameSender server so the PC can connect to it and receive frames
        # We bind to 0.0.0.0 on port 5000 by default.
        self.sender = FrameSender(host="0.0.0.0", port=5000, camera_id="pi_cam_1", jpeg_quality=70)
        
        self._running = False
        self._camera_thread = None
        self._status = "INIT"
        
        self._camera_frame_count = 0
        self._last_fps_time = time.time()
        self._current_camera_fps = 0.0

    def _create_source(self) -> VideoSource:
        if self.config.camera_provider == "webcam":
            return WebcamSource(self.config.camera_index)
        elif self.config.camera_provider == "video":
            return VideoFileSource(self.config.video_file_path)
        elif self.config.camera_provider == "pi":
            return PiCameraSource(self.config.camera_index)
        elif self.config.camera_provider == "mock":
            return MockVideoSource()
        else:
            raise NotImplementedError("PROVIDER NOT IMPLEMENTED: Camera provider must be explicitly selected.")

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
        self.sender.start()
        
        self._camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self._camera_thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.sender.stop()
        if self._camera_thread:
            self._camera_thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        return self._status

    def get_health(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "camera_fps": round(self._current_camera_fps, 1),
            "streaming": self.sender._client_socket is not None
        }

    def _camera_loop(self):
        """Continuously pulls frames to keep buffer empty and track FPS."""
        # For video files we might want to sleep to match FPS, but for webcams we pull as fast as possible
        target_delay = 1.0 / self.config.camera_fps
        
        while self._running:
            start_time = time.time()
            
            try:
                if not self.source.is_open():
                    logger.warning("Camera source lost, attempting reconnect...")
                    time.sleep(self.config.reconnect_delay_ms / 1000.0)
                    self.source.open()
                    continue
            except AttributeError:
                pass # is_opened not implemented on some mocks
            
            frame = self.source.read()
            if frame is not None:
                self.sender.send_frame(frame)
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
            self._camera_frame_count = 0
            self._last_fps_time = now




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
