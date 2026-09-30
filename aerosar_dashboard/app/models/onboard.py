from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class ServiceStatus(BaseModel):
    status: str
    health: Dict[str, Any] = Field(default_factory=dict)

class OnboardStatus(BaseModel):
    state: str = "OFFLINE"
    communication_mode: str = "OFFLINE"
    buffer_count: int = 0
    uptime_seconds: float = 0.0
    services: Dict[str, ServiceStatus] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class OnboardSystemHealth(BaseModel):
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    temperature_c: float = 0.0
    is_pi: bool = False
    os: str = "Unknown"
    timestamp: datetime = Field(default_factory=datetime.now)
