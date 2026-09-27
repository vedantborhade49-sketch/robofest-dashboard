from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.detection import BoundingBox

class Location(BaseModel):
    x: float
    y: float
    z: float

class Incident(BaseModel):
    incident_id: str
    mission_id: str = "SAR-001"
    type: str
    confidence: float
    timestamp: datetime
    bbox: Optional[BoundingBox] = None
    location: Location
    evidence_image: Optional[str] = None
    status: str = "NEW"  # NEW | REVIEW | CONFIRMED | RESOLVED
