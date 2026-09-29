from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PerceptionStatus:
    running: bool = False
    model_loaded: bool = False
    model_name: str = "AEROSAR YOLO"
    input_source: str = "unknown"
    fps: float = 0.0
    inference_time_ms: float = 0.0
    frame_count: int = 0
    detection_count: int = 0
    last_frame_timestamp: Optional[datetime] = None
    error: Optional[str] = None
    source_type: str = "mock"
    camera_connected: bool = False
    device: str = "CPU"


@dataclass
class DetectorConfig:
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: str = "cpu"
    image_size: int = 640
    target_classes: Optional[list[str]] = None
    input_source: str = "video"
