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
                    
                # process_associations might drop some detections (duplicates).
                # To easily map back, we'll manually check what was created.
                created_incidents_with_det = []
                for det, assoc in associations:
                    inc = self._incident_engine.process_detection(det, None, assoc=assoc)
                    if inc:
                        created_incidents_with_det.append((inc, det))

                for inc, det in created_incidents_with_det:
                    try:
                        import os
                        import cv2
                        import json
                        
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
                        date_path = inc.timestamp.strftime("%Y/%m/%d")
                        evidence_dir = os.path.join(project_root, "evidence", date_path, inc.incident_id)
                        os.makedirs(evidence_dir, exist_ok=True)
                        
                        frame_name = f"frame_{det.frame_id:06d}.jpg"
                        frame_path = os.path.join(evidence_dir, frame_name)
                        
                        if frame is not None:
                            # Convert RGB to BGR before saving because OpenCV uses BGR
                            if len(frame.shape) == 3 and frame.shape[2] == 3:
                                # A simple check: YOLO output is usually RGB for this project, let's just save via cv2.imwrite which assumes BGR. 
                                # Wait, PerceptionService handles BGR internally? The frame comes from cv2.VideoCapture so it is BGR!
                                pass
                            
                            cv2.imwrite(frame_path, frame)
                            inc.evidence_image = frame_path
                            
                            meta_path = os.path.join(evidence_dir, "metadata.json")
                            meta_data = {
                                "incident_id": inc.incident_id,
                                "frame_id": det.frame_id,
                                "timestamp": inc.timestamp.isoformat(),
                                "camera_id": getattr(det, "camera_id", "webcam_0"),
                                "event_type": inc.type,
                                "bounding_box": det.bbox.model_dump(mode="json") if det.bbox else None,
                                "confidence": det.confidence,
                                "image_path": frame_path,
                                "detection": det.model_dump(mode="json")
                            }
                            with open(meta_path, "w") as f:
                                json.dump(meta_data, f, indent=2)

                    except Exception as e:
                        print("Error saving evidence:", e)
                        pass
                        
                    ds.add_incident(inc)
                    ds.log_event(
                        message=f"Incident {inc.incident_id} created",
                        event_type="INCIDENT_CREATED",
                        incident_id=inc.incident_id,
                    )
        except Exception:
            # ensure perception loop continues even if engine fails
            pass
