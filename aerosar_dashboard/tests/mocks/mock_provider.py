import random
import math
from datetime import datetime, timedelta
from typing import List, Optional
from app.data.provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import (
    Telemetry, TelemetryState, FlightTelemetry, PositionTelemetry,
    PowerTelemetry, CommunicationTelemetry, SensorStatus,
    FlightControllerStatus, CompanionComputerStatus, TelemetryHistoryPoint
)
from app.models.system import SystemHealth
from app.models.incident import Incident, Location
from app.models.event import Event
from app.models.detection import Detection, BoundingBox
from app.models.map import MapState, SearchBoundary
from app.models.context import RetrievedContext
from app.models.report import Report, IncidentSummary

class MockDataProvider(DataProvider):
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        # Drone position and navigation in LOCAL / SLAM coordinates (meters)
        self._drone_x = 12.4
        self._drone_y = 8.7
        self._drone_z = 14.8
        self._drone_heading = 127.0
        self._drone_speed = 3.2
        self._drone_vertical_speed = 0.4
        self._drone_roll = 0.8
        self._drone_pitch = -1.2
        self._drone_battery = 82.0
        self._drone_voltage = 15.7
        self._drone_current = 8.4

        # Communication link metrics
        self._signal_strength = 87.0
        self._latency = 38.0
        self._packet_loss = 0.2

        # Computing health metrics
        self._sys_cpu = 34.0
        self._sys_mem = 42.0
        self._sys_temp = 51.0
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

        # Initial time-series buffer for historical telemetry graphs (30 past seconds)
        self._telemetry_history: List[TelemetryHistoryPoint] = []
        now = datetime.now()
        for i in range(30, 0, -1):
            t = now - timedelta(seconds=i)
            alt_mock = 14.8 + 0.4 * math.sin(i * 0.35)
            spd_mock = 3.2 + 0.25 * math.cos(i * 0.3)
            bat_mock = 82.0 + (i * 0.015)
            self._telemetry_history.append(TelemetryHistoryPoint(
                timestamp=t,
                altitude=round(alt_mock, 1),
                speed=round(spd_mock, 1),
                battery=round(bat_mock, 1)
            ))

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
        
        now_ev = datetime.now()
        self._events = [
            Event(
                event_id="EVT-0001",
                timestamp=self._start_time,
                level="SUCCESS",
                source="MISSION",
                event_type="MISSION",
                message="Mission SAR-001 initialized",
                mission_id="SAR-001",
                details={"operator": "COMMAND-1", "search_grid": "SECTOR-ALPHA", "boundary": "30x25m"}
            ),
            Event(
                event_id="EVT-0002",
                timestamp=self._start_time + timedelta(seconds=2),
                level="INFO",
                source="SYSTEM",
                event_type="SYSTEM",
                message="Companion computer self-test passed (Raspberry Pi 5)",
                mission_id="SAR-001",
                details={"cpu_status": "NORMAL", "ram_available": "58%", "temperature_c": 51.0}
            ),
            Event(
                event_id="EVT-0003",
                timestamp=self._start_time + timedelta(seconds=4),
                level="SUCCESS",
                source="CAMERA",
                event_type="CAMERA",
                message="Camera-01 optical payload link established (1080p @ 30 FPS)",
                mission_id="SAR-001",
                details={"device": "/dev/video0", "codec": "H264", "resolution": "1920x1080"}
            ),
            Event(
                event_id="EVT-0004",
                timestamp=self._start_time + timedelta(seconds=6),
                level="INFO",
                source="TELEMETRY",
                event_type="TELEMETRY",
                message="ArduPilot flight controller telemetry link established",
                mission_id="SAR-001",
                details={"autopilot": "ARDUPILOT", "mode": "GUIDED", "baud": 115200}
            ),
            Event(
                event_id="EVT-0005",
                timestamp=self._start_time + timedelta(seconds=8),
                level="INFO",
                source="LIDAR",
                event_type="LIDAR",
                message="LiDAR driver calibrated in standby mode",
                mission_id="SAR-001",
                details={"range_max_m": 30.0, "fov_deg": 360, "scan_rate_hz": 15}
            ),
            Event(
                event_id="EVT-0006",
                timestamp=self._start_time + timedelta(seconds=11),
                level="SUCCESS",
                source="SLAM",
                event_type="SLAM",
                message="Local coordinate reference frame (LOCAL / SLAM) locked",
                mission_id="SAR-001",
                details={"reference_frame": "LOCAL / SLAM", "drift_rate": "0.02 m/min", "tracked_features": 420}
            ),
            Event(
                event_id="EVT-0007",
                timestamp=self._start_time + timedelta(seconds=14),
                level="SUCCESS",
                source="AI",
                event_type="AI",
                message="YOLO edge detection model loaded onto neural accelerator",
                mission_id="SAR-001",
                details={"model_file": "yolov8-sar.onnx", "target_classes": ["PERSON"], "batch_size": 1}
            ),
            Event(
                event_id="EVT-0008",
                timestamp=self._start_time + timedelta(seconds=18),
                level="INFO",
                source="MISSION",
                event_type="MISSION",
                message="Search waypoint patrol pattern activated across sector Alpha",
                mission_id="SAR-001",
                details={"waypoints_count": 10, "pattern": "LAWNMOWER_EXPANDING"}
            ),
            Event(
                event_id="EVT-0009",
                timestamp=self._start_time + timedelta(seconds=22),
                level="INFO",
                source="COMMUNICATION",
                event_type="COMMUNICATION",
                message="Telemetry RF uplink verified (Signal: 87%, Latency: 38ms)",
                mission_id="SAR-001",
                details={"signal_percent": 87.0, "latency_ms": 38.0, "packet_loss": 0.2}
            ),
            Event(
                event_id="EVT-0010",
                timestamp=now_ev - timedelta(minutes=2, seconds=11),
                level="INFO",
                source="AI",
                event_type="AI",
                message="Person detected with confidence 94.2% at coordinates (12.4, 8.7, 14.8)",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"confidence": 0.942, "camera": "Camera-01", "frame": 18342, "coords": "X:12.4, Y:8.7, Z:14.8"}
            ),
            Event(
                event_id="EVT-0011",
                timestamp=now_ev - timedelta(minutes=2, seconds=10),
                level="SUCCESS",
                source="INCIDENT",
                event_type="INCIDENT",
                message="Incident INC-001 created automatically by detection engine",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"incident_id": "INC-001", "type": "PERSON DETECTED", "status": "NEW"}
            ),
            Event(
                event_id="EVT-0012",
                timestamp=now_ev - timedelta(minutes=2, seconds=9),
                level="SUCCESS",
                source="DATABASE",
                event_type="DATABASE",
                message="Incident INC-001 stored in mission operational database",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"record_id": "REC-8841", "storage_engine": "SQLite / Local"}
            ),
            Event(
                event_id="EVT-0013",
                timestamp=now_ev - timedelta(minutes=2, seconds=8),
                level="SUCCESS",
                source="BACKEND",
                event_type="BACKEND",
                message="Incident INC-001 synchronized to ground station cache",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"sync_protocol": "IPC_SHARED_MEMORY", "latency_ms": 12}
            ),
            Event(
                event_id="EVT-0014",
                timestamp=now_ev - timedelta(minutes=2, seconds=6),
                level="INFO",
                source="RAG",
                event_type="RAG",
                message="Retrieved 3 contextual intelligence sources for INC-001",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"sources": ["SRC-001", "SRC-002", "SRC-003"], "avg_relevance": 0.88}
            ),
            Event(
                event_id="EVT-0015",
                timestamp=now_ev - timedelta(minutes=2, seconds=5),
                level="SUCCESS",
                source="LLM",
                event_type="LLM",
                message="Incident intelligence report RPT-001 synthesized",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"report_id": "RPT-001", "model": "MOCK-RAG-LLM (SIMULATED)"}
            ),
            Event(
                event_id="EVT-0016",
                timestamp=now_ev - timedelta(minutes=2, seconds=0),
                level="INFO",
                source="INCIDENT",
                event_type="INCIDENT",
                message="Incident INC-001 confirmed by ground station operator",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"operator": "COMMAND-1", "previous_status": "NEW", "new_status": "CONFIRMED"}
            ),
            Event(
                event_id="EVT-0017",
                timestamp=now_ev - timedelta(minutes=1, seconds=55),
                level="SUCCESS",
                source="DASHBOARD",
                event_type="DASHBOARD",
                message="Report RPT-001 marked as REVIEWED by operator",
                mission_id="SAR-001",
                incident_id="INC-001",
                details={"report_id": "RPT-001", "action": "SIGN_OFF"}
            ),
            Event(
                event_id="EVT-0018",
                timestamp=now_ev - timedelta(minutes=1, seconds=20),
                level="WARNING",
                source="COMMUNICATION",
                event_type="COMMUNICATION",
                message="RF signal strength degraded momentarily to 68%",
                mission_id="SAR-001",
                details={"uplink": "DEGRADED", "packet_loss": "2.4%", "rssi": "-78 dBm"}
            ),
            Event(
                event_id="EVT-0019",
                timestamp=now_ev - timedelta(minutes=0, seconds=51),
                level="WARNING",
                source="AI",
                event_type="AI",
                message="Candidate target detected under partial canopy shadow (87.4%)",
                mission_id="SAR-001",
                incident_id="INC-002",
                details={"confidence": 0.874, "camera": "Camera-01", "occlusion": "foliage", "coords": "X:18.2, Y:11.3, Z:13.2"}
            ),
            Event(
                event_id="EVT-0020",
                timestamp=now_ev - timedelta(minutes=0, seconds=50),
                level="WARNING",
                source="INCIDENT",
                event_type="INCIDENT",
                message="Incident INC-002 created for operator review",
                mission_id="SAR-001",
                incident_id="INC-002",
                details={"incident_id": "INC-002", "type": "PERSON DETECTED", "status": "REVIEW"}
            ),
            Event(
                event_id="EVT-0021",
                timestamp=now_ev - timedelta(minutes=0, seconds=45),
                level="INFO",
                source="LLM",
                event_type="LLM",
                message="Incident report RPT-002 generated for INC-002",
                mission_id="SAR-001",
                incident_id="INC-002",
                details={"report_id": "RPT-002", "review_status": "PENDING REVIEW"}
            ),
            Event(
                event_id="EVT-0022",
                timestamp=now_ev - timedelta(minutes=0, seconds=40),
                level="WARNING",
                source="CAMERA",
                event_type="CAMERA",
                message="Camera payload buffer dropped 2 frames under bus load",
                mission_id="SAR-001",
                details={"dropped_frames": 2, "frame_queue_depth": 16, "fps": 28.4}
            ),
            Event(
                event_id="EVT-0023",
                timestamp=now_ev - timedelta(minutes=0, seconds=33),
                level="INFO",
                source="AI",
                event_type="AI",
                message="Unoccluded target detected at coordinates (7.8, 16.5, 12.7)",
                mission_id="SAR-001",
                incident_id="INC-003",
                details={"confidence": 0.912, "camera": "Camera-01", "frame": 19488}
            ),
            Event(
                event_id="EVT-0024",
                timestamp=now_ev - timedelta(minutes=0, seconds=32),
                level="INFO",
                source="INCIDENT",
                event_type="INCIDENT",
                message="Incident INC-003 registered as NEW",
                mission_id="SAR-001",
                incident_id="INC-003",
                details={"incident_id": "INC-003", "type": "PERSON DETECTED", "status": "NEW"}
            ),
            Event(
                event_id="EVT-0025",
                timestamp=now_ev - timedelta(minutes=0, seconds=20),
                level="INFO",
                source="TELEMETRY",
                event_type="TELEMETRY",
                message="Battery capacity at 82.0% (Voltage: 15.7V, Current: 8.4A)",
                mission_id="SAR-001",
                details={"battery_percent": 82.0, "cell_health": "GOOD", "remaining_flight_time_min": 26}
            ),
            Event(
                event_id="EVT-0026",
                timestamp=now_ev - timedelta(minutes=0, seconds=10),
                level="SUCCESS",
                source="COMMUNICATION",
                event_type="COMMUNICATION",
                message="Communication link quality restored to optimal 87%",
                mission_id="SAR-001",
                details={"signal_percent": 87.0, "latency_ms": 38.0, "packet_loss": 0.2}
            )
        ]
        self._sim_step_counter = 0

        # Step 8 Mock Reports & RAG Context
        self._reports = [
            Report(
                report_id="RPT-001",
                incident_id="INC-001",
                mission_id="SAR-001",
                status="REVIEWED",
                generated_at=datetime.now() - timedelta(minutes=2, seconds=5),
                incident_type="PERSON DETECTED",
                confidence=0.942,
                incident_summary=IncidentSummary(
                    incident_id="INC-001",
                    type="PERSON DETECTED",
                    confidence=0.942,
                    timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                    location=Location(x=12.4, y=8.7, z=14.8),
                    status="CONFIRMED"
                ),
                ai_report=(
                    "A person was detected within the surveyed search sector at approximately 14:32:08. "
                    "The visual payload detection was recorded with a high confidence score of 94.2%.\n\n"
                    "The detected target is located at coordinates X: 12.4 m, Y: 8.7 m, Z: 14.8 m relative "
                    "to the current mission reference frame (LOCAL / SLAM). Spatial tracking indicates the "
                    "target has remained stationary across consecutive scan passes.\n\n"
                    "Retrieved context from prior search passes confirms no previous human sightings recorded "
                    "at this position. Visual signature indicates clear human presence. High operational priority."
                ),
                context_sources=[
                    RetrievedContext(
                        source_id="SRC-001",
                        source_type="Previous Observation",
                        content="Person-like silhouette detected near search sector B during optical scan pass.",
                        relevance_score=0.94
                    ),
                    RetrievedContext(
                        source_id="SRC-002",
                        source_type="Mission History",
                        content="Sector B was partially explored during previous search pass (42% area covered).",
                        relevance_score=0.88
                    ),
                    RetrievedContext(
                        source_id="SRC-003",
                        source_type="Incident History",
                        content="No confirmed rescue incident previously recorded at coordinate (12.4, 8.7).",
                        relevance_score=0.82
                    )
                ],
                evidence_image="EV-INC-001.jpg",
                evidence_source="Camera-01 (EO Optical)",
                evidence_frame=18342,
                human_review_status="REVIEWED",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            ),
            Report(
                report_id="RPT-002",
                incident_id="INC-002",
                mission_id="SAR-001",
                status="GENERATED",
                generated_at=datetime.now() - timedelta(minutes=0, seconds=45),
                incident_type="PERSON DETECTED",
                confidence=0.874,
                incident_summary=IncidentSummary(
                    incident_id="INC-002",
                    type="PERSON DETECTED",
                    confidence=0.874,
                    timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                    location=Location(x=18.2, y=11.3, z=13.2),
                    status="REVIEW"
                ),
                ai_report=(
                    "Secondary potential target identified in northeast sector at approximately 14:33:27. "
                    "Confidence score recorded at 87.4% under partial canopy shadow.\n\n"
                    "Target located at X: 18.2 m, Y: 11.3 m, Z: 13.2 m in LOCAL / SLAM coordinates. "
                    "Visual signature indicates a partially occluded human figure.\n\n"
                    "Cross-referencing mission terrain data indicates steep ground gradient nearby. "
                    "Human operator review recommended before classifying as confirmed rescue target."
                ),
                context_sources=[
                    RetrievedContext(
                        source_id="SRC-004",
                        source_type="Terrain Database",
                        content="Sector C contains dense vegetation and uneven terrain slope exceeding 18 degrees.",
                        relevance_score=0.89
                    ),
                    RetrievedContext(
                        source_id="SRC-005",
                        source_type="Mission History",
                        content="Initial flight plan designated Sector C as secondary priority search zone.",
                        relevance_score=0.84
                    )
                ],
                evidence_image="EV-INC-002.jpg",
                evidence_source="Camera-01 (EO Optical)",
                evidence_frame=19120,
                human_review_status="PENDING REVIEW",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            ),
            Report(
                report_id="RPT-003",
                incident_id="INC-003",
                mission_id="SAR-001",
                status="GENERATED",
                generated_at=datetime.now() - timedelta(minutes=0, seconds=25),
                incident_type="PERSON DETECTED",
                confidence=0.912,
                incident_summary=IncidentSummary(
                    incident_id="INC-003",
                    type="PERSON DETECTED",
                    confidence=0.912,
                    timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                    location=Location(x=7.8, y=16.5, z=12.7),
                    status="NEW"
                ),
                ai_report=(
                    "New incident detected in west boundary sector at approximately 14:33:45. "
                    "Automated YOLO detector recorded a 91.2% confidence recognition.\n\n"
                    "Location coordinates are X: 7.8 m, Y: 16.5 m, Z: 12.7 m (LOCAL / SLAM). "
                    "Visual imagery shows unoccluded figure consistent with human survivor.\n\n"
                    "Contextual analysis highlights clear line of sight from primary access route Bravo-2. "
                    "Operator confirmation advised."
                ),
                context_sources=[
                    RetrievedContext(
                        source_id="SRC-006",
                        source_type="Route Analysis",
                        content="Access route Bravo-2 is accessible within 120 meters of coordinates (7.8, 16.5).",
                        relevance_score=0.92
                    ),
                    RetrievedContext(
                        source_id="SRC-007",
                        source_type="Weather & Lighting",
                        content="Ambient solar illumination at 850 lux, low wind speed below 3 m/s.",
                        relevance_score=0.79
                    )
                ],
                evidence_image="EV-INC-003.jpg",
                evidence_source="Camera-01 (EO Optical)",
                evidence_frame=19488,
                human_review_status="PENDING REVIEW",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            ),
            Report(
                report_id="RPT-004",
                incident_id="INC-004",
                mission_id="SAR-001",
                status="PENDING",
                generated_at=datetime.now() - timedelta(seconds=15),
                incident_type="THERMAL ANOMALY",
                confidence=0.760,
                incident_summary=IncidentSummary(
                    incident_id="INC-004",
                    type="THERMAL ANOMALY",
                    confidence=0.760,
                    timestamp=datetime.now() - timedelta(seconds=20),
                    location=Location(x=22.1, y=4.5, z=15.1),
                    status="NEW"
                ),
                ai_report=(
                    "Report generation in progress. RAG retrieval pipeline queued for incident INC-004. "
                    "Context extraction from mission logs and spatial database is currently executing..."
                ),
                context_sources=[
                    RetrievedContext(
                        source_id="SRC-008",
                        source_type="Thermal Calibration",
                        content="Thermal signature delta +4.2°C above ambient background ground temperature.",
                        relevance_score=0.71
                    )
                ],
                evidence_image="EV-INC-004.jpg",
                evidence_source="Camera-02 (IR Thermal)",
                evidence_frame=19612,
                human_review_status="PENDING REVIEW",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            ),
            Report(
                report_id="RPT-005",
                incident_id="INC-005",
                mission_id="SAR-001",
                status="UNAVAILABLE",
                generated_at=datetime.now() - timedelta(minutes=15),
                incident_type="MOTION CLUSTER",
                confidence=0.620,
                incident_summary=IncidentSummary(
                    incident_id="INC-005",
                    type="MOTION CLUSTER",
                    confidence=0.620,
                    timestamp=datetime.now() - timedelta(minutes=15, seconds=20),
                    location=Location(x=2.1, y=2.0, z=14.0),
                    status="RESOLVED"
                ),
                ai_report=(
                    "Report unavailable. Detection confidence (62.0%) was below autonomous reporting "
                    "threshold (75.0%). Incident was dismissed during preliminary filtering pass as "
                    "vegetative wind motion."
                ),
                context_sources=[],
                evidence_image=None,
                evidence_source="Camera-01 (EO Optical)",
                evidence_frame=14102,
                human_review_status="REVIEWED",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            )
        ]

    def _step_drone_simulation(self):
        """Advances the mock drone along its subtle SLAM patrol path."""
        target_x, target_y, target_z = self._waypoints[self._current_wp_idx]
        dx = target_x - self._drone_x
        dy = target_y - self._drone_y
        dist = math.hypot(dx, dy)
        
        if dist < 0.4:
            self._current_wp_idx = (self._current_wp_idx + 1) % len(self._waypoints)
            target_x, target_y, target_z = self._waypoints[self._current_wp_idx]
            dx = target_x - self._drone_x
            dy = target_y - self._drone_y
            dist = math.hypot(dx, dy)

        step = min(0.25, dist)
        if dist > 0.001:
            self._drone_x += (dx / dist) * step
            self._drone_y += (dy / dist) * step
            self._drone_z += (target_z - self._drone_z) * 0.1
            
            rad = math.atan2(dx, dy)
            target_deg = math.degrees(rad) % 360
            diff = (target_deg - self._drone_heading + 180) % 360 - 180
            self._drone_heading = (self._drone_heading + diff * 0.35) % 360

        # Small realistic telemetry fluctuations
        self._drone_speed = max(0.0, 3.2 + random.uniform(-0.15, 0.15))
        self._drone_vertical_speed = round(0.4 + random.uniform(-0.1, 0.1), 2)
        self._drone_roll = round(0.8 + random.uniform(-0.2, 0.2), 1)
        self._drone_pitch = round(-1.2 + random.uniform(-0.2, 0.2), 1)

        # Slow battery depletion
        self._drone_battery = max(10.0, self._drone_battery - 0.004)
        self._drone_voltage = round(14.8 + (self._drone_battery / 100.0) * 1.1, 1)
        self._drone_current = round(8.4 + random.uniform(-0.3, 0.3), 1)

        # Communication fluctuations
        self._signal_strength = round(max(50.0, min(100.0, self._signal_strength + random.uniform(-1.0, 1.0))), 0)
        self._latency = round(max(25.0, min(75.0, self._latency + random.uniform(-2.0, 2.0))), 0)
        self._packet_loss = round(max(0.0, min(2.0, 0.2 + random.uniform(-0.05, 0.05))), 1)

        # Computer metrics
        self._sys_cpu = round(max(15.0, min(90.0, 34.0 + random.uniform(-3.0, 3.0))), 0)
        self._sys_mem = round(max(20.0, min(80.0, 42.0 + random.uniform(-1.0, 1.0))), 0)
        self._sys_temp = round(max(40.0, min(85.0, 51.0 + random.uniform(-0.5, 0.5))), 1)

        # Append to trajectory if moved > 0.4m from last recorded point
        last_pt = self._trajectory[-1]
        if math.hypot(self._drone_x - last_pt.x, self._drone_y - last_pt.y) >= 0.4:
            self._trajectory.append(Location(
                x=round(self._drone_x, 2),
                y=round(self._drone_y, 2),
                z=round(self._drone_z, 2)
            ))
            if len(self._trajectory) > 60:
                self._trajectory.pop(0)

        # Append to time-series history
        self._telemetry_history.append(TelemetryHistoryPoint(
            timestamp=datetime.now(),
            altitude=round(self._drone_z, 1),
            speed=round(self._drone_speed, 1),
            battery=round(self._drone_battery, 1)
        ))
        if len(self._telemetry_history) > 60:
            self._telemetry_history.pop(0)

    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001", mission_status="ACTIVE", elapsed_time=elapsed,
            search_progress=42.0, connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        return Drone(
            drone_id="AEROSAR-01", status="AIRBORNE", battery=round(self._drone_battery, 1),
            altitude=round(self._drone_z, 1), speed=round(self._drone_speed, 1),
            heading=round(self._drone_heading, 1), signal_strength=round(self._signal_strength, 1)
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
            altitude=round(self._drone_z, 1), speed=round(self._drone_speed, 1),
            heading=round(self._drone_heading, 1), battery=round(self._drone_battery, 1), signal=round(self._signal_strength, 1),
            position=Location(x=round(self._drone_x, 1), y=round(self._drone_y, 1), z=round(self._drone_z, 1))
        )
        
    def get_telemetry_state(self) -> TelemetryState:
        """Returns the full structured telemetry state for the Telemetry Page."""
        self._step_drone_simulation()
        
        # Derive battery status
        bat_status = "GOOD"
        if self._drone_battery < 25.0:
            bat_status = "WARNING"
        elif self._drone_battery < 15.0:
            bat_status = "CRITICAL"

        # Derive comm status
        link_st = "CONNECTED"
        if self._signal_strength < 30.0:
            link_st = "DEGRADED"

        power_watts = round(self._drone_voltage * self._drone_current, 1)

        return TelemetryState(
            flight=FlightTelemetry(
                altitude=round(self._drone_z, 1),
                speed=round(self._drone_speed, 1),
                vertical_speed=self._drone_vertical_speed,
                heading=round(self._drone_heading, 1),
                roll=self._drone_roll,
                pitch=self._drone_pitch,
                yaw=round(self._drone_heading, 1)
            ),
            position=PositionTelemetry(
                x=round(self._drone_x, 1),
                y=round(self._drone_y, 1),
                z=round(self._drone_z, 1),
                frame="LOCAL / SLAM",
                heading=round(self._drone_heading, 1)
            ),
            power=PowerTelemetry(
                battery_percent=round(self._drone_battery, 1),
                voltage=self._drone_voltage,
                current=self._drone_current,
                power_watts=power_watts,
                status=bat_status
            ),
            communication=CommunicationTelemetry(
                link_status=link_st,
                signal_percent=round(self._signal_strength, 0),
                latency_ms=round(self._latency, 0),
                packet_loss_percent=self._packet_loss,
                uplink="CONNECTED",
                downlink="CONNECTED"
            ),
            sensors=SensorStatus(
                imu="READY",
                barometer="READY",
                camera="READY",
                lidar="STANDBY",
                gps="NOT REQUIRED",
                slam="STANDBY"
            ),
            flight_controller=FlightControllerStatus(
                status="CONNECTED",
                autopilot="ARDUPILOT",
                mode="GUIDED",
                armed=False,
                link="CONNECTED"
            ),
            companion_computer=CompanionComputerStatus(
                device="RASPBERRY PI 5",
                status="ONLINE",
                cpu_percent=self._sys_cpu,
                ram_percent=self._sys_mem,
                temperature_c=self._sys_temp,
                ai_status="READY",
                camera_status="READY",
                lidar_status="STANDBY"
            ),
            history=list(self._telemetry_history)
        )

    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=self._sys_cpu, memory_usage=self._sys_mem, temperature=self._sys_temp, communication_status="CONNECTED"
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

    def get_event(self, event_id: str) -> Optional[Event]:
        for e in self._events:
            if e.event_id == event_id:
                return e
        return None
        
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

    def step_simulation(self):
        """Advances the physical and sensor simulation state by one cycle."""
        self._frame_count += random.randint(14, 16)
        self._det_x += random.uniform(-0.005, 0.005)
        self._det_y += random.uniform(-0.005, 0.005)
        self._det_x = max(0.15, min(0.85, self._det_x))
        self._det_y = max(0.15, min(0.85, self._det_y))

    def add_incident(self, incident: Incident):
        """Adds a new incident at the top of the mock incident list."""
        self._incidents.insert(0, incident)

    def update_incident(self, incident: Incident):
        """Updates an existing incident matching incident_id."""
        for idx, inc in enumerate(self._incidents):
            if inc.incident_id == incident.incident_id:
                self._incidents[idx] = incident
                break

    def get_map_state(self) -> MapState:
        self._step_drone_simulation()
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

    def get_reports(self) -> List[Report]:
        """Returns all mock incident intelligence reports."""
        return self._reports

    def get_report(self, report_id: str) -> Optional[Report]:
        """Returns a specific report by report_id."""
        for r in self._reports:
            if r.report_id == report_id:
                return r
        return None

    def get_report_by_incident_id(self, incident_id: str) -> Optional[Report]:
        """Returns a specific report by incident_id."""
        for r in self._reports:
            if r.incident_id == incident_id:
                return r
        return None

    def review_report(self, report_id: str) -> bool:
        """
        Marks an incident intelligence report as REVIEWED by human operator.
        Updates review status locally and logs an audit event.
        No flight control or arming commands are issued.
        """
        report = self.get_report(report_id)
        if report:
            report.human_review_status = "REVIEWED"
            if report.status in ("GENERATED", "PENDING"):
                report.status = "REVIEWED"
            self.add_event(Event(
                timestamp=datetime.now(),
                event_type="REPORT",
                message=f"Report {report.report_id} ({report.incident_id}) marked as REVIEWED by operator",
                severity="INFO"
            ))
            return True
        return False

