from __future__ import annotations

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.detection import BoundingBox


class IncidentStatus(str, Enum):
    NEW = "NEW"
    REVIEW = "REVIEW"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

    @classmethod
    def _valid_transitions(cls) -> dict["IncidentStatus", set["IncidentStatus"]]:
        return {
            cls.NEW: {cls.REVIEW},
            cls.REVIEW: {cls.CONFIRMED, cls.DISMISSED},
            cls.CONFIRMED: {cls.RESOLVED},
            cls.RESOLVED: set(),
            cls.DISMISSED: set(),
        }

    @classmethod
    def validate_transition(cls, current: "IncidentStatus | str", target: "IncidentStatus | str") -> bool:
        if current in (None, ""):
            return True
        current_value = cls(current)
        target_value = cls(target)
        if current_value == target_value:
            return True
        return target_value in cls._valid_transitions().get(current_value, set())


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
    evidence_id: Optional[str] = None
    evidence_image: Optional[str] = None
    status: IncidentStatus | str = IncidentStatus.NEW  # NEW | REVIEW | CONFIRMED | RESOLVED | DISMISSED

    def can_transition_to(self, new_status: "IncidentStatus | str") -> bool:
        return IncidentStatus.validate_transition(self.status, new_status)
