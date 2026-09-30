from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class DeliveryClass(str, Enum):
    BEST_EFFORT = "BEST_EFFORT"
    RELIABLE = "RELIABLE"

class UAVMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = "AEROSAR-01"
    mission_id: Optional[str] = None
    message_type: str
    schema_version: str = "1.0"
    sequence_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    delivery_class: DeliveryClass = DeliveryClass.BEST_EFFORT
    payload: Dict[str, Any]
