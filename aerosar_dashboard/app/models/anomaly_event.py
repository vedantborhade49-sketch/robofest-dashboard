from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class AnomalyEventStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"

class AnomalyEvent(BaseModel):
    """
    Persistent model for CV Anomaly Events linking an entity to a specific anomalous behavior.
    """
    event_id: str
    event_type: str
    entity_id: str
    status: AnomalyEventStatus | str = AnomalyEventStatus.NEW
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    first_frame_id: int = 0
    last_frame_id: int = 0
    confidence: float = 0.0
    spatial_information: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
