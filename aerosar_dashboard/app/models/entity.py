from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class EntityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"

class Entity(BaseModel):
    """
    Persistent model for observed physical entities (e.g., PERSON_001, VEHICLE_001).
    """
    entity_id: str
    entity_type: str
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    first_frame_id: int = 0
    last_frame_id: int = 0
    sighting_count: int = 1
    confidence: float = 0.0
    status: EntityStatus | str = EntityStatus.ACTIVE
    image_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
