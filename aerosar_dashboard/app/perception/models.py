from pydantic import BaseModel
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
