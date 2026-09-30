from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot
from typing import Optional
from app.perception.perception_service import PerceptionService
from app.services.data_service import DataService
from app.incidents.incident_engine import IncidentEngine


class PerceptionWorker(QObject):
    started = Signal()
    stopped = Signal()
    frame_ready = Signal(object)  # frame (numpy array)
    detections_ready = Signal(object)  # list of Detection
    status_updated = Signal(object)  # PerceptionStatus

    def __init__(self, service: Optional[PerceptionService] = None):
        super().__init__()
        self.service = service or PerceptionService()
        self._running = False
        # incident engine for converting detections -> incidents
        self._incident_engine = IncidentEngine()

    @Slot()
    def start(self):
        self._running = True
        self.service.start()
        self.started.emit()

    @Slot()
    def stop(self):
        self._running = False
        self.service.stop()
        self.stopped.emit()

    @Slot()
    def capture_and_process(self):
        if not self._running:
            return
        detections, frame = self.service.run_once()
        if frame is not None:
            self.frame_ready.emit(frame)
        self.detections_ready.emit(detections)
        self.status_updated.emit(self.service.status)

        # Convert detections to incidents and persist via DataService
        try:
            if detections:
                ds = DataService()
                state = ds.get_state()
                spatial_state = state.spatial if state else None
                incidents = self._incident_engine.process_detections(detections, spatial_state)
                for inc in incidents:
                    try:
                        ds.add_incident(inc)
                        ds.log_event(
                            message=f"Incident {inc.incident_id} created",
                            event_type="INCIDENT_CREATED",
                            incident_id=inc.incident_id,
                        )
                    except Exception:
                        # swallow per-incident persistence/logging errors
                        pass
        except Exception:
            # ensure perception loop continues even if engine fails
            pass
