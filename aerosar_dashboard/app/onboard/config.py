import os
from typing import Literal, Optional
from pydantic import BaseModel, Field

class OnboardConfig(BaseModel):
    runtime_mode: Literal["development", "onboard", "LAPTOP", "PI"] = "development"
    
    # Providers
    camera_provider: Literal["mock", "webcam", "video", "pi"] = "mock"
    video_file_path: str = "assets/test_video.mp4"
    camera_index: int = 0
    lidar_provider: Literal["mock", "real"] = "mock"
    slam_provider: Literal["mock", "real"] = "mock"
    mavlink_provider: Literal["mock", "real"] = "mock"
    
    # Communication
    communication_enabled: bool = True
    transport_type: Literal["loopback", "websocket"] = "websocket"
    ground_station_url: str = "http://127.0.0.1:8000"
    ground_station_ws_url: str = "ws://127.0.0.1:8000/api/v1/uav/ws"
    vehicle_id: str = "AEROSAR-01"
    mission_id: str = "SAR-001"
    heartbeat_interval_ms: int = 1000
    
    # YOLO Model Loading & Inference
    yolo_model_path: str = "models/best.pt"
    yolo_confidence_threshold: float = 0.5
    yolo_iou_threshold: float = 0.45
    yolo_image_size: int = 640
    yolo_device: str = "cpu"
    yolo_max_detections: int = 100
    
    # Buffer & Storage Constraints
    buffer_enabled: bool = True
    buffer_size: int = 1000
    max_disk_usage_percent: float = 85.0
    
    # Health Monitoring
    health_monitor_enabled: bool = True
    health_monitor_interval_ms: int = 5000
    
    # Resource Thresholds
    cpu_warning_threshold: float = 80.0
    cpu_critical_threshold: float = 95.0
    mem_warning_threshold: float = 80.0
    mem_critical_threshold: float = 95.0
    temp_warning_threshold: float = 75.0
    temp_critical_threshold: float = 85.0
    
    # Update intervals (ms) - FPS Control
    camera_fps: int = 30
    perception_interval_ms: int = 200  # Inference FPS (1000/200 = 5 FPS)
    lidar_interval_ms: int = 100
    telemetry_interval_ms: int = 100
    
    # Lifecycle & Recovery
    service_start_timeout: int = 5000
    service_restart_policy: str = "always"
    max_reconnect_attempts: int = 10
    reconnect_delay_ms: int = 2000

    @classmethod
    def from_env(cls) -> "OnboardConfig":
        """Load configuration from environment variables with safe fallbacks."""
        # This allows injecting config without hardcoding
        return cls(
            runtime_mode=os.getenv("AEROSAR_RUNTIME_MODE", "PI"),
            camera_provider=os.getenv("AEROSAR_CAMERA_PROVIDER", "mock"),
            ground_station_url=os.getenv("AEROSAR_GROUND_URL", "http://127.0.0.1:8000"),
            ground_station_ws_url=os.getenv("AEROSAR_GROUND_WS", "ws://127.0.0.1:8000/api/v1/uav/ws"),
            yolo_model_path=os.getenv("AEROSAR_YOLO_MODEL", "models/best.pt"),
            yolo_device=os.getenv("AEROSAR_YOLO_DEVICE", "cpu")
        )
