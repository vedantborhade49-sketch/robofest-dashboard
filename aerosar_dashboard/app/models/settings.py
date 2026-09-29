from pydantic import BaseModel, Field, field_validator
from typing import Optional

class DashboardSettings(BaseModel):
    """
    Pydantic model representing non-flight-critical configuration for the
    STALLION AEROSAR ground station dashboard software stack.
    """
    # 1. GENERAL
    ground_station_name: str = "AEROSAR Ground Station"
    mission_id: str = "SAR-001"
    refresh_interval_ms: int = Field(default=500, gt=0, description="UI update interval in milliseconds")
    time_format: str = "24-hour"

    # 2. DISPLAY
    dark_theme: bool = True
    show_detection_boxes: bool = True
    show_trajectory: bool = True
    show_grid: bool = True
    compact_telemetry: bool = False
    show_system_notifications: bool = True

    # 3. AI / PERCEPTION
    detection_model: str = "person_detector"
    confidence_threshold: float = Field(default=0.50, ge=0.0, le=1.0, description="Minimum confidence for detection")
    max_detections: int = Field(default=20, gt=0, description="Maximum detection count per frame")
    show_detection_labels: bool = True

    # 4. CAMERA
    camera_source: str = "Mock Camera"
    camera_resolution: str = "1280 × 720"
    camera_fps: int = Field(default=30, gt=0, description="Target frame rate")
    mirror_preview: bool = False
    detection_overlay: bool = True
    # Perception runtime
    perception_enabled: bool = True
    perception_camera_index: int = 0

    # 5. MAP
    map_show_grid: bool = True
    map_show_drone: bool = True
    map_show_trajectory: bool = True
    map_show_incidents: bool = True
    map_show_search_boundary: bool = True
    map_show_explored_area: bool = True

    # 6. BACKEND / DATA CONNECTION
    backend_mode: str = "MOCK"
    backend_url: str = "http://localhost:8000"
    auto_reconnect: bool = True

    # 7. COMMUNICATION
    communication_mode: str = "SIMULATED"
    transport: str = "LOCAL"
    update_interval_ms: int = Field(default=500, gt=0)
    connection_timeout_ms: int = Field(default=3000, gt=0)

    # 8. LOGGING
    event_logging_enabled: bool = True
    log_level: str = "INFO"
    max_stored_events: int = Field(default=1000, gt=0)
    console_logging: bool = False

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return round(v, 2)

    @field_validator("refresh_interval_ms")
    @classmethod
    def validate_refresh(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Refresh interval must be a positive integer")
        return v

    @field_validator("max_detections")
    @classmethod
    def validate_max_detections(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Maximum detections must be greater than zero")
        return v

    @field_validator("backend_url")
    @classmethod
    def validate_backend_url(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Backend URL cannot be empty")
        return clean
