from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    FRAME = "FRAME"
    ANNOTATED_FRAME = "ANNOTATED_FRAME"
    CROP = "CROP"


class Evidence(BaseModel):
    evidence_id: str = Field(default="EV-0001")
    incident_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: EvidenceType = EvidenceType.ANNOTATED_FRAME
    file_path: str
    mime_type: str = "image/jpeg"
    frame_id: Optional[int] = None
    source: str = "camera-01"
    description: Optional[str] = None
