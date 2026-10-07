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
        
        # Phase 2: Entity and Event Registries
        from app.perception.entity_registry import EntityRegistry
        from app.incidents.event_registry import EventRegistry
        self._entity_registry = EntityRegistry()
        self._event_registry = EventRegistry()

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
                history = ds.get_spatial_history()
                
                from app.models.spatial import SpatialAssociation
                
                # 1. Entity Tracking
                entity_pairs = self._entity_registry.process_detections(detections, frame)
                
                # 2. Anomaly Event Registry
                event_triplets = self._event_registry.process_entities(entity_pairs)
                
                # 3. Spatial Association
                associations = []
                for det, entity, event in event_triplets:
                    assoc = SpatialAssociation(available=False, association_timestamp=det.timestamp)
                    if history:
                        state = history.get_state_at(det.timestamp)
                        if state:
                            assoc.spatial_state = state
                            assoc.temporal_error_ms = abs((state.timestamp - det.timestamp).total_seconds()) * 1000.0
                            assoc.available = True
                    associations.append((det, assoc))
                    
                incidents = self._incident_engine.process_associations(associations)

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
