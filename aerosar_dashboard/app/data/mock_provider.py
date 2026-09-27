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
from app.models.detection import Detection, BoundingBox

class MockDataProvider(DataProvider):
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        self._drone_altitude = 14.8
        self._drone_speed = 3.2
        self._drone_battery = 82.0
        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        self._frame_count = 12482
        self._dropped_frames = 0
        self._det_x = 0.4
        self._det_y = 0.5
        
        self._incidents = [
            Incident(
                incident_id="INC-001", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.94,
                timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                status="CONFIRMED", location=Location(x=12.4, y=8.7, z=14.8),
                evidence_image="mock_evidence_001.jpg"
            ),
            Incident(
                incident_id="INC-002", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                status="REVIEW", location=Location(x=18.2, y=11.3, z=13.2),
                evidence_image="mock_evidence_002.jpg"
            ),
            Incident(
                incident_id="INC-003", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.91,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                status="NEW", location=Location(x=7.8, y=16.5, z=12.7),
                evidence_image="mock_evidence_003.jpg"
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected", severity="WARNING")
        ]
        
    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001", mission_status="ACTIVE", elapsed_time=elapsed,
            search_progress=42.0, connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        self._drone_altitude += random.uniform(-0.2, 0.2)
        self._drone_speed += random.uniform(-0.1, 0.1)
        self._drone_speed = max(0.0, self._drone_speed)
        return Drone(
            drone_id="AEROSAR-01", status="AIRBORNE", battery=self._drone_battery,
            altitude=round(self._drone_altitude, 1), speed=round(self._drone_speed, 1),
            heading=127.0, signal_strength=98.0
        )

    def get_camera(self) -> Camera:
        self._frame_count += int(random.uniform(28, 30))
        if random.random() < 0.05:
            self._dropped_frames += 1
        return Camera(
            connected=True, fps=random.uniform(27.0, 30.0), latency=random.uniform(35.0, 55.0),
            frame_count=self._frame_count, dropped_frames=self._dropped_frames, resolution="1280x720"
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="READY", model_name="YOLO-PERSON-V1", inference_fps=random.uniform(27.0, 29.0),
            detections_count=len(self._incidents), device="MOCK / CPU"
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=round(self._drone_altitude, 1), speed=round(self._drone_speed, 1),
            heading=127.0, battery=self._drone_battery, signal=98.0,
            position=Location(x=10.5, y=20.1, z=self._drone_altitude)
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=32.0, memory_usage=41.0, temperature=48.0, communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_events(self) -> List[Event]:
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        
    def get_detections(self) -> List[Detection]:
        self._det_x += random.uniform(-0.01, 0.01)
        self._det_y += random.uniform(-0.01, 0.01)
        self._det_x = max(0.1, min(0.9, self._det_x))
        self._det_y = max(0.1, min(0.9, self._det_y))
        
        return [
            Detection(
                detection_id="DET-1029", class_name="PERSON", confidence=random.uniform(0.85, 0.98),
                bbox=BoundingBox(x=self._det_x, y=self._det_y, width=0.15, height=0.25), timestamp=datetime.now()
            )
        ]
