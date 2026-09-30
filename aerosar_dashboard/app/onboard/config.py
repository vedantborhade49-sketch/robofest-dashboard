from typing import Literal
from pydantic import BaseModel, Field

class OnboardConfig(BaseModel):
    runtime_mode: Literal["development", "onboard"] = "development"
    
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
    
    # Buffer
    buffer_enabled: bool = True
    buffer_size: int = 1000
    
    # Health Monitoring
    health_monitor_enabled: bool = True
    health_monitor_interval_ms: int = 5000
    
    # Update intervals (ms)
    camera_fps: int = 15
    perception_interval_ms: int = 200
    lidar_interval_ms: int = 100
    telemetry_interval_ms: int = 100
    
    # Lifecycle
    service_start_timeout: int = 5000
    service_restart_policy: str = "always"
