from typing import Literal
from pydantic import BaseModel, Field

class OnboardConfig(BaseModel):
    runtime_mode: Literal["development", "onboard"] = "development"
    
    # Providers
    camera_provider: Literal["mock", "real"] = "mock"
    lidar_provider: Literal["mock", "real"] = "mock"
    slam_provider: Literal["mock", "real"] = "mock"
    mavlink_provider: Literal["mock", "real"] = "mock"
    
    # Communication
    communication_mode: Literal["connected", "degraded", "offline"] = "connected"
    ground_station_url: str = "http://127.0.0.1:8000"
    
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
