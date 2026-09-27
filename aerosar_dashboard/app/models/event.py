from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, Dict, Any

class Event(BaseModel):
    """
    Structured model for ground station mission and subsystem events.
    Represents an immutable record of chronological mission and operational activity.
    """
    event_id: str = Field(default="EVT-0000")
    timestamp: datetime = Field(default_factory=datetime.now)
    level: str = "INFO"          # INFO | WARNING | ERROR | SUCCESS
    source: str = "SYSTEM"       # MISSION | CAMERA | AI | INCIDENT | DATABASE | BACKEND | COMMUNICATION | TELEMETRY | SLAM | LIDAR | RAG | LLM | SYSTEM | DASHBOARD
    event_type: str = "SYSTEM"   # Sub-category or classification
    message: str
    severity: str = "INFO"       # Backward-compatible alias matching level
    mission_id: Optional[str] = "SAR-001"
    incident_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def sync_level_and_severity(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Synchronize severity and level
            if "severity" in data and "level" not in data:
                sev = str(data["severity"]).upper()
                data["level"] = "ERROR" if sev in ("ERROR", "CRITICAL") else sev
            elif "level" in data and "severity" not in data:
                data["severity"] = data["level"]
            elif "level" in data and "severity" in data:
                # If severity was passed as something else, ensure consistency
                pass
            else:
                data["level"] = "INFO"
                data["severity"] = "INFO"

            # Auto-assign event_id if default or empty
            if "event_id" not in data or not data["event_id"] or data["event_id"] == "EVT-0000":
                import random
                data["event_id"] = f"EVT-{random.randint(1000, 9999)}"
        return data
