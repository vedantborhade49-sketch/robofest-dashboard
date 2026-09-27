from pydantic import BaseModel
from datetime import datetime

class BoundingBox(BaseModel):
    x: float # Center X, Normalized 0.0 to 1.0
    y: float # Center Y, Normalized 0.0 to 1.0
    width: float # Normalized 0.0 to 1.0
    height: float # Normalized 0.0 to 1.0

class Detection(BaseModel):
    detection_id: str
    class_name: str
    confidence: float
    bbox: BoundingBox
    timestamp: datetime
