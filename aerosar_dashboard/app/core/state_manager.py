from typing import Optional, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from app.models.app_state import AppState
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import TelemetryState
from app.models.system import SystemHealth
from app.models.map import MapState
from app.models.detection import Detection
from app.models.incident import Incident
from app.models.report import Report, IncidentSummary
from app.models.context import RetrievedContext
from app.models.event import Event
from app.models.settings import DashboardSettings
from app.data.provider import DataProvider

class StateManager(QObject):
    """
    Centralized State Manager for the STALLION AEROSAR Ground Station.
    Serves as the Single Source of Truth (SSoT) for all mission, telemetry,
    camera, perception, incident, report, and system event data.
    Emits granular Qt signals whenever any slice of state is updated.
    """
    # Granular Qt signals for reactive UI updates
    mission_updated = Signal(object)       # Mission
    drone_updated = Signal(object)         # Drone
    camera_updated = Signal(object)        # Camera
    ai_updated = Signal(object)            # AIStatus
    telemetry_updated = Signal(object)     # TelemetryState
    system_updated = Signal(object)        # SystemHealth
    map_updated = Signal(object)           # MapState
    detections_updated = Signal(object)    # List[Detection]
    incidents_updated = Signal(object)     # List[Incident]
    incident_added = Signal(object)        # Incident
    incident_updated = Signal(object)      # Incident
    reports_updated = Signal(object)       # List[Report]
    report_added = Signal(object)          # Report
    report_updated = Signal(object)        # Report
    events_updated = Signal(object)        # List[Event]
    event_added = Signal(object)           # Event
    settings_updated = Signal(object)      # DashboardSettings
    state_updated = Signal(object)         # AppState
    spatial_updated = Signal(object)       # SpatialState

    _instance: Optional["StateManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._state: Optional[AppState] = None
        self._initialized = True

    @classmethod
    def instance(cls) -> "StateManager":
        """Convenience method returning the singleton StateManager instance."""
        if cls._instance is None:
            cls._instance = StateManager()
        return cls._instance

    def initialize_from_provider(self, provider: DataProvider, settings: Optional[DashboardSettings] = None):
        """Initializes the central AppState using baseline data from the provider."""
        self._state = AppState(
            mission=provider.get_mission(),
            drone=provider.get_drone(),
            camera=provider.get_camera(),
            ai=provider.get_ai_status(),
            telemetry=provider.get_telemetry_state(),
            system=provider.get_system_health(),
            map_state=provider.get_map_state(),
            detections=provider.get_detections() or [],
            incidents=list(provider.get_incidents() or []),
            reports=list(provider.get_reports() or []),
            events=list(provider.get_events() or []),
            settings=settings or DashboardSettings(),
            last_updated=datetime.now(),
            is_stale=False
        )
        self.state_updated.emit(self._state)

    def sync_from_provider(self, provider: DataProvider):
        """
        Synchronizes live telemetry, navigation, and perception from the provider
        into central AppState and emits granular signals.
        """
        if self._state is None:
            self.initialize_from_provider(provider)
            return

        # 1. Mission
        m = provider.get_mission()
        if m and m != self._state.mission:
            self._state.mission = m
            self.mission_updated.emit(m)

        # 2. Drone
        d = provider.get_drone()
        if d:
            self._state.drone = d
            self.drone_updated.emit(d)

        # 3. Camera
        c = provider.get_camera()
        if c:
            self._state.camera = c
            self.camera_updated.emit(c)

        # 4. AI Perception
        ai = provider.get_ai_status()
        if ai:
            self._state.ai = ai
            self.ai_updated.emit(ai)

        # 5. Detections
        det = provider.get_detections()
        if det is not None:
            self._state.detections = det
            self.detections_updated.emit(det)

        # 6. Telemetry State
        telem = provider.get_telemetry_state()
        if telem:
            self._state.telemetry = telem
            self.telemetry_updated.emit(telem)

        # 7. System Health
        sys_h = provider.get_system_health()
        if sys_h:
            self._state.system = sys_h
            self.system_updated.emit(sys_h)

        # 8. Map State
        map_st = provider.get_map_state()
        if map_st:
            self._state.map_state = map_st
            self.map_updated.emit(map_st)

    def update_spatial(self, spatial_state):
        if self._state:
            self._state.spatial = spatial_state
            self.spatial_updated.emit(spatial_state)
            self.state_updated.emit(self._state)

        # Timestamp & fresh status
        self._state.last_updated = datetime.now()
        if self._state.is_stale:
            self._state.is_stale = False

        self.state_updated.emit(self._state)

    # -------------------------------------------------------------
    # GETTERS (Single Source of Truth)
    # -------------------------------------------------------------
    def get_state(self) -> Optional[AppState]:
        return self._state

    def get_mission(self) -> Optional[Mission]:
        return self._state.mission if self._state else None

    def get_drone(self) -> Optional[Drone]:
        return self._state.drone if self._state else None

    def get_camera(self) -> Optional[Camera]:
        return self._state.camera if self._state else None

    def get_ai(self) -> Optional[AIStatus]:
        return self._state.ai if self._state else None

    def get_telemetry(self) -> Optional[TelemetryState]:
        return self._state.telemetry if self._state else None

    def get_system(self) -> Optional[SystemHealth]:
        return self._state.system if self._state else None

    def get_map_state(self) -> Optional[MapState]:
        return self._state.map_state if self._state else None

    def get_detections(self) -> List[Detection]:
        return self._state.detections if self._state else []

    def get_incidents(self) -> List[Incident]:
        return self._state.incidents if self._state else []

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        if not self._state:
            return None
        for inc in self._state.incidents:
            if inc.incident_id == incident_id:
                return inc
        return None

    def get_reports(self) -> List[Report]:
        return self._state.reports if self._state else []

    def get_report(self, report_id: str) -> Optional[Report]:
        if not self._state:
            return None
        for r in self._state.reports:
            if r.report_id == report_id:
                return r
        return None

    def get_report_by_incident_id(self, incident_id: str) -> Optional[Report]:
        if not self._state:
            return None
        for r in self._state.reports:
            if r.incident_id == incident_id:
                return r
        return None

    def get_events(self) -> List[Event]:
        if not self._state:
            return []
        return sorted(self._state.events, key=lambda e: e.timestamp, reverse=True)

    def get_event(self, event_id: str) -> Optional[Event]:
        if not self._state:
            return None
        for ev in self._state.events:
            if ev.event_id == event_id:
                return ev
        return None

    def get_settings(self) -> DashboardSettings:
        return self._state.settings if self._state else DashboardSettings()

    # -------------------------------------------------------------
    # ACTION & MUTATION METHODS (Reactive Multi-System Cascades)
    # -------------------------------------------------------------
    def add_incident(self, incident: Incident, auto_create_event_and_report: bool = True):
        """
        Adds a new incident to central state.
        Automatically links an Event Log entry and generates an initial draft
        Report so Incidents, Map, Overview, Event Log, and Reports are 100% coherent.
        """
        if not self._state:
            return

        # Insert at front
        self._state.incidents.insert(0, incident)
        self.incident_added.emit(incident)
        self.incidents_updated.emit(self._state.incidents)

        if auto_create_event_and_report:
            # 1. Automatic linked Event
            inc_type = getattr(incident, "type", "TARGET")
            ev = Event(
                event_id=f"EVT-{incident.incident_id.replace('INC-', '')}",
                timestamp=incident.timestamp,
                level="WARNING",
                source="AI",
                event_type="INCIDENT",
                message=f"Autonomous target detected: {inc_type} (Confidence: {int(incident.confidence * 100)}%)",
                mission_id="SAR-001",
                incident_id=incident.incident_id,
                details={
                    "class": inc_type,
                    "confidence": f"{int(incident.confidence * 100)}%",
                    "pos_x": f"{incident.location.x:.1f}m",
                    "pos_y": f"{incident.location.y:.1f}m",
                    "pos_z": f"{incident.location.z:.1f}m"
                }
            )
            self.add_event(ev)

            # 2. Automatic linked Report
            rpt_num = incident.incident_id.replace("INC-", "")
            rpt = Report(
                report_id=f"RPT-{rpt_num}",
                incident_id=incident.incident_id,
                mission_id="SAR-001",
                status="GENERATED",
                generated_at=incident.timestamp,
                incident_type=inc_type,
                confidence=incident.confidence,
                incident_summary=IncidentSummary(
                    incident_id=incident.incident_id,
                    type=inc_type,
                    confidence=incident.confidence,
                    timestamp=incident.timestamp,
                    location=incident.location,
                    status=incident.status
                ),
                ai_report=f"Automated intelligence synthesis for incident {incident.incident_id}. Primary optical and SLAM sensors confirmed high-probability detection of {inc_type}.",
                context_sources=[
                    RetrievedContext(
                        source_id=f"CTX-YOLO-{rpt_num}",
                        source_type="YOLO Bounding Box",
                        content=f"Primary optical sensor identified {inc_type} with {int(incident.confidence * 100)}% detection certainty at coordinates ({incident.location.x:.1f}, {incident.location.y:.1f}, {incident.location.z:.1f}).",
                        relevance_score=incident.confidence
                    )
                ],
                evidence_image=incident.evidence_image,
                evidence_source="EO/IR GIMBAL CAM-01",
                evidence_frame=12400 + (int(rpt_num) if rpt_num.isdigit() else 80),
                human_review_status="PENDING REVIEW",
                model_name="MOCK-RAG-LLM (SIMULATED)"
            )
            self.add_report(rpt)

        self.state_updated.emit(self._state)

    def update_incident(self, incident: Incident):
        """Updates an existing incident and emits signals."""
        if not self._state:
            return
        for idx, inc in enumerate(self._state.incidents):
            if inc.incident_id == incident.incident_id:
                self._state.incidents[idx] = incident
                self.incident_updated.emit(incident)
                self.incidents_updated.emit(self._state.incidents)
                self.state_updated.emit(self._state)
                break

    def update_incident_status(self, incident_id: str, new_status: str):
        """Centralized lifecycle transition validation and event emission for incident status changes."""
        incident = self.get_incident(incident_id)
        if incident is None:
            return None
        from app.models.incident import IncidentStatus
        if not IncidentStatus.validate_transition(incident.status, new_status):
            raise ValueError(f"Invalid status transition from {incident.status} to {new_status}")
        previous_status = incident.status
        incident.status = new_status
        self.update_incident(incident)
        ev = Event(
            event_id=f"EVT-{incident.incident_id.replace('INC-', '')}-{new_status}",
            timestamp=datetime.now(),
            level="SUCCESS" if new_status in {"CONFIRMED", "RESOLVED"} else "INFO",
            source="INCIDENT",
            event_type="INCIDENT_STATUS",
            message=f"Incident {incident.incident_id} moved from {previous_status} to {new_status} by operator.",
            mission_id=incident.mission_id,
            incident_id=incident.incident_id,
            details={"previous_status": previous_status, "new_status": new_status},
        )
        self.add_event(ev)
        return incident

    def add_event(self, event: Event):
        """Adds an event to central state and emits signals."""
        if not self._state:
            return
        self._state.events.append(event)
        self.event_added.emit(event)
        self.events_updated.emit(self._state.events)
        self.state_updated.emit(self._state)

    def add_report(self, report: Report):
        """Adds a synthesized incident report to central state."""
        if not self._state:
            return
        self._state.reports.insert(0, report)
        self.report_added.emit(report)
        self.reports_updated.emit(self._state.reports)
        self.state_updated.emit(self._state)

    def update_report(self, report: Report):
        """Updates an existing report (e.g. human review) and emits signals."""
        if not self._state:
            return
        for idx, r in enumerate(self._state.reports):
            if r.report_id == report.report_id:
                self._state.reports[idx] = report
                self.report_updated.emit(report)
                self.reports_updated.emit(self._state.reports)
                self.state_updated.emit(self._state)
                break

    def update_settings(self, settings: DashboardSettings):
        """Updates dashboard configuration settings."""
        if not self._state:
            return
        self._state.settings = settings
        self.settings_updated.emit(settings)
        self.state_updated.emit(self._state)

    def set_stale(self, is_stale: bool):
        """Sets communication staleness status."""
        if self._state and self._state.is_stale != is_stale:
            self._state.is_stale = is_stale
            self.state_updated.emit(self._state)
