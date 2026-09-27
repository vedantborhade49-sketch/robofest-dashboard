from abc import ABC, abstractmethod
from typing import Optional
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth

class DataProvider(ABC):
    """Abstract base class for all data providers."""
    
    @abstractmethod
    def get_mission(self) -> Optional[Mission]:
        pass

    @abstractmethod
    def get_drone(self) -> Optional[Drone]:
        pass

    @abstractmethod
    def get_camera(self) -> Optional[Camera]:
        pass

    @abstractmethod
    def get_ai_status(self) -> Optional[AIStatus]:
        pass
        
    @abstractmethod
    def get_telemetry(self) -> Optional[Telemetry]:
        pass
        
    @abstractmethod
    def get_system_health(self) -> Optional[SystemHealth]:
        pass
