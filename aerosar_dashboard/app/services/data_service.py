from typing import Optional, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from app.data.provider import DataProvider
from app.data.api_provider import APIDataProvider
# mock provider removed
from app.models.incident import Incident
from app.models.event import Event
from app.models.report import Report
from app.models.app_state import AppState
from app.core.state_manager import StateManager
from app.core.update_loop import CentralUpdateLoop
from app.ui.realtime_client import RealtimeClient

class DataService(QObject):
    """
    Centralized data service façade for the STALLION AEROSAR Ground Station.
    Connects the active DataProvider (Mock or future Live), the central StateManager
    (Single Source of Truth), and the CentralUpdateLoop.
    Exposes reactive Qt signals to UI pages and provides synchronized data access.
    """
    _instance: Optional["DataService"] = None

    # Expose StateManager signals through DataService for clean view consumption
    mission_updated = Signal(object)
    drone_updated = Signal(object)
    camera_updated = Signal(object)
    ai_updated = Signal(object)
    telemetry_updated = Signal(object)
    system_updated = Signal(object)
    map_updated = Signal(object)
    detections_updated = Signal(object)
    incidents_updated = Signal(object)
    incident_added = Signal(object)
    incident_updated = Signal(object)
    reports_updated = Signal(object)
    report_added = Signal(object)
    report_updated = Signal(object)
    events_updated = Signal(object)
    event_added = Signal(object)
    settings_updated = Signal(object)
    state_updated = Signal(object)
    spatial_updated = Signal(object)
    realtime_status_updated = Signal(str)

    def __new__(cls, provider: Optional[DataProvider] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, provider: Optional[DataProvider] = None):
        if getattr(self, "_initialized", False):
            if provider is not None and provider is not self._provider:
                self.set_provider(provider)
            return

        super().__init__()
        self._provider: DataProvider = provider or APIDataProvider()
        self._state_manager = StateManager.instance()
        self._state_manager.initialize_from_provider(self._provider)

        # Handle Mock Mode for WebSocket
        is_mock = type(self._provider).__name__ == "MockDataProvider"

        # --- DATABASE & PERSISTENCE ---
        from app.database.database import init_db
        from app.database.repository import Repository
        import logging
        
        db_initialized = init_db()
        self._repository = Repository()
        
        # Merge persistent historical data into StateManager
        state = self._state_manager.get_state()
        if state and db_initialized:
            try:
                db_incidents = self._repository.get_incidents()
                db_reports = self._repository.get_reports()
                db_events = self._repository.get_events()
                
                existing_inc_ids = {i.incident_id for i in state.incidents}
                for i in db_incidents:
                    if i.incident_id not in existing_inc_ids:
                        state.incidents.append(i)
                        
                existing_rep_ids = {r.report_id for r in state.reports}
                for r in db_reports:
                    if r.report_id not in existing_rep_ids:
                        state.reports.append(r)
                        
                existing_evt_ids = {e.event_id for e in state.events}
                for e in db_events:
                    if e.event_id not in existing_evt_ids:
                        state.events.append(e)
                
                # Re-sort events by timestamp descending
                state.events = sorted(state.events, key=lambda ev: ev.timestamp, reverse=True)
                
                
                self._state_manager.state_updated.emit(state)
            except Exception as e:
                logging.error(f"Failed to load historical data from database: {e}")

        # Wire StateManager signals to Repository for persistence
        self._state_manager.incident_added.connect(self._safe_save_incident)
        self._state_manager.incident_updated.connect(self._safe_save_incident)
        self._state_manager.report_added.connect(self._safe_save_report)
        self._state_manager.report_updated.connect(self._safe_save_report)
        self._state_manager.event_added.connect(self._safe_save_event)

        # Wire StateManager signals to DataService signals
        self._state_manager.mission_updated.connect(self.mission_updated.emit)
        self._state_manager.drone_updated.connect(self.drone_updated.emit)
        self._state_manager.camera_updated.connect(self.camera_updated.emit)
        self._state_manager.ai_updated.connect(self.ai_updated.emit)
        self._state_manager.telemetry_updated.connect(self.telemetry_updated.emit)
        self._state_manager.system_updated.connect(self.system_updated.emit)
        self._state_manager.map_updated.connect(self.map_updated.emit)
        self._state_manager.detections_updated.connect(self.detections_updated.emit)
        self._state_manager.incidents_updated.connect(self.incidents_updated.emit)
        self._state_manager.incident_added.connect(self.incident_added.emit)
        self._state_manager.incident_updated.connect(self.incident_updated.emit)
        self._state_manager.reports_updated.connect(self.reports_updated.emit)
        self._state_manager.report_added.connect(self.report_added.emit)
        self._state_manager.report_updated.connect(self.report_updated.emit)
        self._state_manager.events_updated.connect(self.events_updated.emit)
        self._state_manager.event_added.connect(self.event_added.emit)
        self._state_manager.settings_updated.connect(self.settings_updated.emit)
        self._state_manager.state_updated.connect(self.state_updated.emit)
        self._state_manager.spatial_updated.connect(self.spatial_updated.emit)

        # Spatial Service
        from app.spatial.provider import LiDARProvider
        from app.spatial.slam_provider import SLAMProvider
        from app.spatial.service import SpatialService
        
        class StubLiDAR(LiDARProvider):
            def start(self): pass # HARDWARE NOT AVAILABLE: LiDAR
            def stop(self): pass
            def get_scan(self): return None
            def is_connected(self): return False
            
        class StubSLAM(SLAMProvider):
            def start(self): pass # HARDWARE NOT AVAILABLE: SLAM
            def stop(self): pass
            def update(self, scan): pass
            def get_pose(self): return None
            def get_map(self): return None
            def get_trajectory(self): return []
            def is_initialized(self): return False
            def get_status(self): return "OFFLINE"
            def get_quality(self): return "UNKNOWN"
            def reset(self): pass

        self.spatial_service = SpatialService(
            provider=StubLiDAR(),
            slam_provider=StubSLAM()
        )
        
        from app.spatial.history import SpatialStateHistory
        from app.spatial.qt_worker import SpatialWorker
        from PySide6.QtCore import QThread, QTimer
        
        self.spatial_history = SpatialStateHistory(max_history_size=100, max_age_seconds=2.0)
        self.spatial_worker = SpatialWorker(self.spatial_service, self.spatial_history)
        self._spatial_thread = QThread()
        self.spatial_worker.moveToThread(self._spatial_thread)
        
        self._spatial_thread.started.connect(self.spatial_worker.start)
        self.spatial_worker.stopped.connect(self._spatial_thread.quit)
        
        # We need a timer to tick the spatial worker
        # Timer MUST be created in the main thread and signal the worker, 
        # or created in the worker thread. Since it's DataService in UI thread,
        # we create it here and connect to the slot.
        self._spatial_timer = QTimer()
        self._spatial_timer.timeout.connect(self.spatial_worker.process_update)
        
        def _on_spatial_state_updated(state):
            # Update state manager and publish event
            self._state_manager.update_spatial(state)
            # Publish to real-time event flow
            from app.realtime.event_bus import event_bus
            from app.realtime.events import EventType
            try:
                payload = {
                    "sensor_status": state.sensor_status,
                    "slam_status": state.slam_status,
                    "slam_quality": state.slam_quality,
                }
                if state.current_pose:
                    payload["pose"] = state.current_pose.dict()
                event_bus.publish(EventType.SPATIAL_UPDATE, payload=payload)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not publish spatial event: {e}")
                
        self.spatial_worker.spatial_state_updated.connect(_on_spatial_state_updated)
        
        self._spatial_thread.start()
        self._spatial_timer.start(500) # 500ms heartbeat


        # Central update loop (500ms heartbeat)
        self._update_loop = CentralUpdateLoop(
            state_manager=self._state_manager,
            provider=self._provider,
            interval_ms=500,
            spatial_service=self.spatial_service
        )
        self._update_loop.start()

        # Optional perception integration (worker managed by UI but we allow programmatic hook)
        self._perception_worker = None

        # Connect settings service updates to central loop and state
        from app.services.settings_service import SettingsService
        self._settings_service = SettingsService()
        self._settings_service.settings_updated.connect(self._on_settings_updated)

        # Real-time WebSocket Client
        self._realtime_client = RealtimeClient("ws://127.0.0.1:8000/api/v1/ws")
        self._realtime_client.set_mock_mode(is_mock)
        self._realtime_client.event_received.connect(self._on_realtime_event)
        
        def handle_connected():
            if not getattr(self._realtime_client, "_mock_mode", False):
                self.realtime_status_updated.emit("CONNECTED")
                
        def handle_disconnected():
            if not getattr(self._realtime_client, "_mock_mode", False):
                self.realtime_status_updated.emit("DISCONNECTED")
                
        self._realtime_client.connected.connect(handle_connected)
        self._realtime_client.disconnected.connect(handle_disconnected)
        
        if is_mock:
            self.realtime_status_updated.emit("MOCK")
        else:
            self._realtime_client.connect_to_server()

        self._initialized = True

    def _on_realtime_event(self, event_data: dict):
        try:
            event_type = event_data.get("event_type")
            payload = event_data.get("payload", {})
            
            if event_type == "TELEMETRY_UPDATE":
                from app.models.telemetry import TelemetryState, Telemetry
                # payload is likely a telemetry dump, or partial
                if "flight" in payload:
                    telem = Telemetry(**payload["flight"])
                    # State manager doesn't have a direct "update_telemetry" usually it relies on the loop.
                    # Wait, StateManager has state.telemetry
                    if self._state_manager._state:
                        # Construct a full TelemetryState or just update the flight part
                        if not self._state_manager._state.telemetry:
                            self._state_manager._state.telemetry = TelemetryState(flight=telem)
                        else:
                            self._state_manager._state.telemetry.flight = telem
                        self._state_manager.telemetry_updated.emit(self._state_manager._state.telemetry)
            
            elif event_type == "INCIDENT_CREATED":
                # Ensure it's a full incident or just payload
                incident_data = payload.get("incident", payload)
                if incident_data:
                    from app.models.incident import Incident
                    incident = Incident(**incident_data)
                    self._state_manager.add_incident(incident, auto_create_event_and_report=False)
            
            elif event_type == "INCIDENT_UPDATED" or event_type == "INCIDENT_STATUS_CHANGED":
                incident_data = payload.get("incident", payload)
                if isinstance(incident_data, dict) and "incident_id" in incident_data:
                    from app.models.incident import Incident
                    incident = Incident(**incident_data)
                    self._state_manager.update_incident(incident)
                else:
                    # Fallback for old INCIDENT_STATUS_CHANGED format
                    incident_id = payload.get("incident_id")
                    new_status = payload.get("new_status")
                    if incident_id and new_status:
                        incident = self._state_manager.get_incident(incident_id)
                        if incident:
                            incident.status = new_status
                            self._state_manager.update_incident(incident)
                            
            elif event_type == "SPATIAL_UPDATE":
                if self._state_manager._state:
                    from app.models.map import MapState
                    map_state = MapState(**payload)
                    self._state_manager._state.map_state = map_state
                    self._state_manager.map_updated.emit(map_state)

            elif event_type == "PERCEPTION_STATUS" or event_type == "PERCEPTION_STATUS_UPDATE":
                if self._state_manager._state:
                    from app.models.ai import AIStatus
                    ai_status = AIStatus(**payload)
                    self._state_manager._state.ai = ai_status
                    self._state_manager.ai_updated.emit(ai_status)
                    
            elif event_type == "HEALTH_UPDATE":
                if self._state_manager._state:
                    from app.models.system import SystemHealth
                    health = SystemHealth(**payload)
                    self._state_manager._state.system = health
                    self._state_manager.system_updated.emit(health)
                    
            elif event_type == "SYSTEM_EVENT":
                from app.models.event import Event
                ev = Event(**payload)
                self._state_manager.add_event(ev)

            elif event_type == "REPORT_GENERATED":
                report_id = payload.get("report_id") or payload.get("report", {}).get("report_id")
                if report_id:
                    import threading
                    import httpx
                    import logging
                    def _fetch_report():
                        try:
                            url = f"http://127.0.0.1:8000/api/v1/reports/{report_id}"
                            with httpx.Client() as client:
                                resp = client.get(url)
                                resp.raise_for_status()
                                report_data = resp.json()
                                from app.models.report import Report
                                report = Report(**report_data)
                                self._state_manager.add_report(report)
                        except Exception as e:
                            logging.error(f"Failed to fetch generated report {report_id}: {e}")
                    threading.Thread(target=_fetch_report, daemon=True).start()
        except Exception as e:
            import logging
            logging.error(f"Error handling realtime event: {e}")

    def _on_settings_updated(self, settings):
        self._state_manager.update_settings(settings)
        self._update_loop.set_interval(settings.refresh_interval_ms)

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def update_loop(self) -> CentralUpdateLoop:
        return self._update_loop

    def set_provider(self, provider: DataProvider):
        """Allows switching between Mock and future Live providers without UI changes."""
        self._provider = provider
        self._update_loop.set_provider(provider)
        self._state_manager.initialize_from_provider(provider)
        
        is_mock = type(provider).__name__ == "MockDataProvider"
        if hasattr(self, "_realtime_client"):
            self._realtime_client.set_mock_mode(is_mock)
            if not is_mock:
                self.realtime_status_updated.emit("DISCONNECTED")
                self._realtime_client.connect_to_server()
            else:
                self.realtime_status_updated.emit("MOCK")

    # -------------------------------------------------------------
    # GETTERS — Guaranteed Single Source of Truth from StateManager
    # -------------------------------------------------------------
    def get_state(self) -> Optional[AppState]:
        return self._state_manager.get_state()
        
    def get_spatial_history(self):
        return getattr(self, "spatial_history", None)

    def get_mission_data(self):
        return self._state_manager.get_mission()

    def get_drone_data(self):
        return self._state_manager.get_drone()

    def get_telemetry_data(self):
        telem = self._state_manager.get_telemetry()
        return telem.flight if telem else None

    def get_telemetry_state(self):
        return self._state_manager.get_telemetry()

    def get_camera_data(self):
        return self._state_manager.get_camera()

    def get_ai_data(self):
        return self._state_manager.get_ai()

    def get_system_health(self):
        return self._state_manager.get_system()

    def get_map_state(self):
        return self._state_manager.get_map_state()

    def get_detections(self):
        return self._state_manager.get_detections()

    def get_settings(self):
        return self._state_manager.get_settings()

    def attach_perception_worker(self, worker):
        """Attach a PerceptionWorker (Qt QObject) to propagate detections and status into central state."""
        if worker is None:
            return
        self._perception_worker = worker
        try:
            worker.detections_ready.connect(self._on_detections_from_worker)
            worker.status_updated.connect(self._on_status_from_worker)
        except Exception:
            pass

    def _on_detections_from_worker(self, detections):
        # Update central state and emit signals
        try:
            if self._state_manager._state:
                self._state_manager._state.detections = detections
                self._state_manager.detections_updated.emit(detections)
                self.detections_updated.emit(detections)
        except Exception:
            pass

    def _on_status_from_worker(self, status):
        try:
            # convert PerceptionStatus to AIStatus-like structure if needed
            if self._state_manager._state:
                self._state_manager._state.ai = status
                self._state_manager.ai_updated.emit(status)
                self.ai_updated.emit(status)
        except Exception:
            pass

    def get_incidents(self) -> List[Incident]:
        return self._state_manager.get_incidents()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self._state_manager.get_incident(incident_id)

    def get_reports(self) -> List[Report]:
        return self._state_manager.get_reports()

    def get_report(self, report_id: str) -> Optional[Report]:
        return self._state_manager.get_report(report_id)

    def get_report_by_incident_id(self, incident_id: str) -> Optional[Report]:
        return self._state_manager.get_report_by_incident_id(incident_id)

    def get_events(self) -> List[Event]:
        return self._state_manager.get_events()

    def get_event(self, event_id: str) -> Optional[Event]:
        return self._state_manager.get_event(event_id)

    # -------------------------------------------------------------
    # ACTION & MUTATION METHODS
    # -------------------------------------------------------------
    def add_incident(self, incident: Incident, auto_create_event_and_report: bool = True):
        """
        Adds a new incident. Automatically propagates to StateManager (triggering
        linked event and report generation) and synchronizes with provider.
        """
        from app.data.api_provider import APIDataProvider
        if isinstance(self._provider, APIDataProvider):
            auto_create_event_and_report = False
            
        if hasattr(self._provider, "add_incident"):
            self._provider.add_incident(incident)
        self._state_manager.add_incident(incident, auto_create_event_and_report=auto_create_event_and_report)

    def review_report(self, report_id: str) -> bool:
        """Marks a report as reviewed in provider and StateManager."""
        prov_ok = False
        if hasattr(self._provider, "review_report"):
            prov_ok = self._provider.review_report(report_id)

        rep = self._state_manager.get_report(report_id)
        if rep:
            rep.human_review_status = "REVIEWED"
            if rep.status in ("GENERATED", "PENDING"):
                rep.status = "REVIEWED"
            self._state_manager.update_report(rep)
            self._state_manager.add_event(Event(
                timestamp=datetime.now(),
                event_type="REPORT",
                message=f"Report {rep.report_id} ({rep.incident_id}) marked as REVIEWED by operator",
                severity="INFO",
                incident_id=rep.incident_id
            ))
            return True
        return prov_ok

    def request_report_generation(self, incident_id: str):
        """Requests the backend to generate a report for the given incident via REST API."""
        # For a full implementation we would make a non-blocking HTTP request here.
        # We can use QNetworkAccessManager or a background thread.
        import threading
        import httpx
        import logging
        
        def _do_request():
            try:
                # Use httpx to make synchronous call inside a thread
                url = f"http://127.0.0.1:8000/api/v1/incidents/{incident_id}/generate-report"
                # If mock mode, maybe bypass? No, let it hit the backend to test full pipeline
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url)
                    resp.raise_for_status()
                    logging.info(f"Report generated successfully for incident {incident_id}")
            except Exception as e:
                logging.error(f"Failed to request report generation for {incident_id}: {e}")
                
        # Run in thread so UI doesn't freeze
        threading.Thread(target=_do_request, daemon=True).start()

    def add_event(self, event: Event):
        """Adds an event to provider and StateManager."""
        if hasattr(self._provider, "add_event"):
            self._provider.add_event(event)
        self._state_manager.add_event(event)

    def log_event(
        self,
        message: str,
        event_type: str = "INCIDENT",
        severity: str = "INFO",
        source: str = "SYSTEM",
        level: Optional[str] = None,
        mission_id: Optional[str] = "SAR-001",
        incident_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Convenience method for creating and logging a structured Event."""
        eff_level = level or severity
        ev = Event(
            timestamp=datetime.now(),
            level=eff_level,
            source=source,
            event_type=event_type,
            message=message,
            severity=eff_level,
            mission_id=mission_id,
            incident_id=incident_id,
            details=details
        )
        self.add_event(ev)

    def _safe_save_incident(self, incident: Incident):
        try:
            self._repository.save_incident(incident)
        except Exception as e:
            import logging
            logging.error(f"Failed to persist incident {incident.incident_id}: {e}")

    def _safe_save_report(self, report: Report):
        try:
            self._repository.save_report(report)
        except Exception as e:
            import logging
            logging.error(f"Failed to persist report {report.report_id}: {e}")

    def _safe_save_event(self, event: Event):
        try:
            self._repository.save_event(event)
        except Exception as e:
            import logging
            logging.error(f"Failed to persist event {event.event_id}: {e}")

