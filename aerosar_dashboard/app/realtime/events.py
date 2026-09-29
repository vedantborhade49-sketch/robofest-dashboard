from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class EventType(str, Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    INCIDENT_STATUS_CHANGED = "INCIDENT_STATUS_CHANGED"
    EVIDENCE_CREATED = "EVIDENCE_CREATED"
    MISSION_UPDATED = "MISSION_UPDATED"
    DRONE_STATUS_UPDATED = "DRONE_STATUS_UPDATED"
    CAMERA_STATUS_UPDATED = "CAMERA_STATUS_UPDATED"
    AI_STATUS_UPDATED = "AI_STATUS_UPDATED"
    SYSTEM_EVENT = "SYSTEM_EVENT"

class RealTimeEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mission_id: Optional[str] = None
    payload: Dict[str, Any]
