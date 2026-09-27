import random
from datetime import datetime, timedelta
from typing import List
from .provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Incident, Location
from app.models.event import Event

class MockDataProvider(DataProvider):
    """Provides mock data for UI development and testing with simulated live updates."""
    
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        # State variables for simulation
        self._drone_altitude = 14.8
        self._drone_speed = 3.2
        self._drone_battery = 82.0
        
        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        
        # Static mock lists
        self._incidents = [
            Incident(
                incident_id="INC-001", type="PERSON", confidence=0.94,
                timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                status="DETECTED", location=Location(x=10.5, y=20.1, z=14.8)
            ),
            Incident(
                incident_id="INC-002", type="PERSON", confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                status="REVIEW", location=Location(x=12.2, y=19.8, z=14.5)
            ),
            Incident(
                incident_id="INC-003", type="PERSON", confidence=0.91,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                status="CONFIRMED", location=Location(x=15.1, y=22.4, z=14.2)
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission started", severity="INFO"),
            Event(timestamp=self._start_time + timedelta(seconds=6), event_type="NETWORK", message="Camera connection established", severity="INFO"),
            Event(timestamp=self._start_time + timedelta(seconds=20), event_type="AI", message="AI inference started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=10), event_type="MISSION", message="Incident INC-001 created", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=0, seconds=38), event_type="SYSTEM", message="Evidence image stored", severity="INFO")
        ]
        
    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001",
            mission_status="ACTIVE",
            elapsed_time=elapsed,
            search_progress=42.0,
            connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        self._drone_altitude += random.uniform(-0.2, 0.2)
        self._drone_speed += random.uniform(-0.1, 0.1)
        self._drone_speed = max(0.0, self._drone_speed)
        
        return Drone(
            drone_id="AEROSAR-01",
            status="AIRBORNE",
            battery=self._drone_battery,
            altitude=round(self._drone_altitude, 1),
            speed=round(self._drone_speed, 1),
            heading=127.0,
            signal_strength=98.0
        )

    def get_camera(self) -> Camera:
        return Camera(
            connected=True,
            fps=random.uniform(28.0, 30.0),
            latency=random.uniform(110.0, 130.0)
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="READY",
            model_name="aerosar-yolo-v8-opt",
            inference_fps=15.0,
            detections_count=len(self._incidents)
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=round(self._drone_altitude, 1),
            speed=round(self._drone_speed, 1),
            heading=127.0,
            battery=self._drone_battery,
            signal=98.0,
            position=Location(x=10.5, y=20.1, z=self._drone_altitude)
        )
        
    def get_system_health(self) -> SystemHealth:
        self._sys_cpu += random.uniform(-2.0, 2.0)
        self._sys_cpu = max(10.0, min(100.0, self._sys_cpu))
        self._sys_mem += random.uniform(-0.5, 0.5)
        self._sys_mem = max(20.0, min(100.0, self._sys_mem))
        
        return SystemHealth(
            cpu_usage=round(self._sys_cpu, 1),
            memory_usage=round(self._sys_mem, 1),
            temperature=48.0,
            communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_events(self) -> List[Event]:
        # Return events sorted by timestamp descending
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
