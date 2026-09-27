import random
import math
from datetime import datetime, timedelta
from typing import List, Optional
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
from app.models.map import MapState, SearchBoundary

class MockDataProvider(DataProvider):
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        # Drone position and navigation in LOCAL / SLAM coordinates (meters)
        self._drone_x = 12.4
        self._drone_y = 8.7
        self._drone_z = 14.8
        self._drone_heading = 127.0
        self._drone_speed = 3.2
        self._drone_battery = 82.0

        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        self._frame_count = 12482
        self._dropped_frames = 0
        self._det_x = 0.4
        self._det_y = 0.5
        
        # Subtle predefined patrol path for realistic mock SLAM movement
        self._waypoints = [
            (12.4, 8.7, 14.8),
            (14.8, 10.2, 14.9),
            (17.5, 12.6, 15.0),
            (19.8, 15.2, 14.9),
            (21.4, 18.0, 14.8),
            (18.5, 20.2, 14.7),
            (14.8, 19.0, 14.6),
            (11.2, 16.5, 14.7),
            (8.5, 13.0, 14.8),
            (10.0, 10.0, 14.8)
        ]
        self._current_wp_idx = 1
        
        # Initial trajectory path (P0 -> P1 -> P2 -> P3 -> P4)
        self._trajectory: List[Location] = [
            Location(x=3.5, y=4.2, z=14.2),
            Location(x=6.2, y=5.5, z=14.4),
            Location(x=9.0, y=7.0, z=14.6),
            Location(x=11.0, y=8.0, z=14.7),
            Location(x=12.4, y=8.7, z=14.8)
        ]

        # Primary mock incidents specified in Step 5 & 6 requirements
        self._incidents = [
            Incident(
                incident_id="INC-001",
                mission_id="SAR-001",
                type="PERSON DETECTED",
                confidence=0.94,
                timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                bbox=BoundingBox(x=0.48, y=0.52, width=0.18, height=0.32),
                status="CONFIRMED",
                location=Location(x=12.4, y=8.7, z=14.8),
                evidence_image="EV-INC-001.jpg"
            ),
            Incident(
                incident_id="INC-002",
                mission_id="SAR-001",
                type="PERSON DETECTED",
                confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                bbox=BoundingBox(x=0.62, y=0.40, width=0.14, height=0.28),
                status="REVIEW",
                location=Location(x=18.2, y=11.3, z=13.2),
                evidence_image="EV-INC-002.jpg"
            ),
            Incident(
                incident_id="INC-003",
                mission_id="SAR-001",
                type="PERSON DETECTED",
                confidence=0.91,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                bbox=BoundingBox(x=0.35, y=0.65, width=0.16, height=0.30),
                status="NEW",
                location=Location(x=7.8, y=16.5, z=12.7),
                evidence_image="EV-INC-003.jpg"
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission SAR-001 started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected at 12.4, 8.7, 14.8", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=0), event_type="INCIDENT", message="Incident INC-001 confirmed by operator", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=0, seconds=50), event_type="INCIDENT", message="Incident INC-002 created for review", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=0, seconds=32), event_type="INCIDENT", message="Incident INC-003 created [NEW]", severity="WARNING")
        ]

    def _step_drone_simulation(self):
        """Advances the mock drone along its subtle SLAM patrol path."""
        target_x, target_y, target_z = self._waypoints[self._current_wp_idx]
        dx = target_x - self._drone_x
        dy = target_y - self._drone_y
        dist = math.hypot(dx, dy)
        
        if dist < 0.4:
            # Switch to next waypoint in cyclic path
            self._current_wp_idx = (self._current_wp_idx + 1) % len(self._waypoints)
            target_x, target_y, target_z = self._waypoints[self._current_wp_idx]
            dx = target_x - self._drone_x
            dy = target_y - self._drone_y
            dist = math.hypot(dx, dy)

        # Move small increment (e.g. 0.25 meters per tick)
        step = min(0.25, dist)
        if dist > 0.001:
            self._drone_x += (dx / dist) * step
            self._drone_y += (dy / dist) * step
            self._drone_z += (target_z - self._drone_z) * 0.1
            
            # Heading: 0° = North (+Y), 90° = East (+X)
            rad = math.atan2(dx, dy)
            target_deg = math.degrees(rad) % 360
            # Smooth heading transition
            diff = (target_deg - self._drone_heading + 180) % 360 - 180
            self._drone_heading = (self._drone_heading + diff * 0.35) % 360

        # Append to trajectory if moved > 0.4m from last recorded point
        last_pt = self._trajectory[-1]
        if math.hypot(self._drone_x - last_pt.x, self._drone_y - last_pt.y) >= 0.4:
            self._trajectory.append(Location(
                x=round(self._drone_x, 2),
                y=round(self._drone_y, 2),
                z=round(self._drone_z, 2)
            ))
            # Keep trajectory history bounded
            if len(self._trajectory) > 60:
                self._trajectory.pop(0)

    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001", mission_status="ACTIVE", elapsed_time=elapsed,
            search_progress=42.0, connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        self._drone_speed = round(3.2 + random.uniform(-0.1, 0.1), 1)
        return Drone(
            drone_id="AEROSAR-01", status="AIRBORNE", battery=self._drone_battery,
            altitude=round(self._drone_z, 1), speed=self._drone_speed,
            heading=round(self._drone_heading, 1), signal_strength=98.0
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
            altitude=round(self._drone_z, 1), speed=self._drone_speed,
            heading=round(self._drone_heading, 1), battery=self._drone_battery, signal=98.0,
            position=Location(x=round(self._drone_x, 1), y=round(self._drone_y, 1), z=round(self._drone_z, 1))
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=32.0, memory_usage=41.0, temperature=48.0, communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        for inc in self._incidents:
            if inc.incident_id == incident_id:
                return inc
        return None

    def get_events(self) -> List[Event]:
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        
    def add_event(self, event: Event):
        self._events.append(event)
        
    def get_detections(self) -> List[Detection]:
        self._det_x += random.uniform(-0.01, 0.01)
        self._det_y += random.uniform(-0.01, 0.01)
        self._det_x = max(0.1, min(0.9, self._det_x))
        self._det_y = max(0.1, min(0.9, self._det_y))
        
        return [
            Detection(
                detection_id="DET-1029",
                class_name="PERSON",
                confidence=random.uniform(0.85, 0.98),
                bbox=BoundingBox(x=self._det_x, y=self._det_y, width=0.15, height=0.25),
                timestamp=datetime.now()
            )
        ]

    def get_map_state(self) -> MapState:
        # Step simulation forward on query
        self._step_drone_simulation()
        
        # Explored polygon (mock ~42% explored sector of 30x25m area)
        explored_poly = [
            Location(x=0.0, y=0.0, z=0.0),
            Location(x=20.5, y=0.0, z=0.0),
            Location(x=22.8, y=13.5, z=0.0),
            Location(x=17.2, y=21.0, z=0.0),
            Location(x=0.0, y=19.5, z=0.0)
        ]
        
        return MapState(
            drone_position=Location(
                x=round(self._drone_x, 1),
                y=round(self._drone_y, 1),
                z=round(self._drone_z, 1)
            ),
            drone_heading=round(self._drone_heading, 1),
            trajectory=list(self._trajectory),
            search_boundary=SearchBoundary(min_x=0.0, max_x=30.0, min_y=0.0, max_y=25.0),
            explored_percentage=42.0,
            explored_polygon=explored_poly,
            map_status="READY",
            coordinate_frame="LOCAL / SLAM"
        )
