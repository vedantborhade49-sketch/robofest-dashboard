from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class Detection(BaseModel):
    detection_id: str
    timestamp: datetime
    frame_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    source: str
    image_width: int
    image_height: int
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None

# --- New CV Boundary Models ---

class DetectionResult(BaseModel):
    """Normalized CV output for a single object detection."""
    class_name: str
    confidence: float
    bbox: BBox
    class_id: Optional[int] = None
    track_id: Optional[str] = None
    metadata: Optional[dict] = None

class CVResult(BaseModel):
    """Structured result of processing a single NetworkFrame."""
    frame_id: int
    timestamp: datetime
    detections: list[DetectionResult] = Field(default_factory=list)
    processing_time: Optional[float] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None
