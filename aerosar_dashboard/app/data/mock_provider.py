from .provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Location

class MockDataProvider(DataProvider):
    """Provides mock data for UI development and testing."""
    
    def get_mission(self) -> Mission:
        return Mission(
            mission_id="M-2026-ALPHA",
            mission_status="IN_PROGRESS",
            elapsed_time=1240.5,
            search_progress=45.0,
            connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        return Drone(
            drone_id="STALLION-01",
            status="FLYING",
            battery=78.5,
            altitude=45.2,
            speed=12.4,
            heading=275.0,
            signal_strength=92.0
        )

    def get_camera(self) -> Camera:
        return Camera(
            connected=True,
            fps=30.0,
            latency=120.0
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="ACTIVE",
            model_name="aerosar-yolo-v8-opt",
            inference_fps=15.0,
            detections_count=3
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=45.2,
            speed=12.4,
            heading=275.0,
            battery=78.5,
            signal=92.0,
            position=Location(x=10.5, y=20.1, z=45.2)
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=45.0,
            memory_usage=60.0,
            temperature=55.0,
            communication_status="NOMINAL"
        )
