from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid

from app.models.detection import Detection, BoundingBox
from app.models.incident import Incident, Location
from app.models.spatial import SpatialState
from app.models.settings import DashboardSettings


class IncidentEngine:
    """Converts Detection objects into Incident objects using simple rule-based logic.

    Responsibilities:
    - validate detection
    - apply confidence threshold
    - map class -> incident type
    - suppress duplicates (simple spatial + temporal)
    - produce Incident objects (not persist)
    """

    def __init__(self, settings: Optional[DashboardSettings] = None):
        self.settings = settings or DashboardSettings()
        # active incidents cache: list of (incident_id, type, bbox_center, timestamp)
        self._active: List[Tuple[str, str, Tuple[float, float], datetime]] = []
        # configuration
        # default windows (ms) can be overridden via settings dict keys
        self.dup_time_window = getattr(self.settings, "detection_duplicate_time_window_ms", 5000) / 1000.0
        self.dup_center_distance_ratio = getattr(self.settings, "detection_duplicate_center_ratio", 0.2)

    def _generate_incident_id(self) -> str:
        return f"INC-{uuid.uuid4().hex[:8].upper()}"

    def _detection_center(self, bbox: BoundingBox) -> Tuple[float, float]:
        if bbox.x is not None and bbox.y is not None:
            return float(bbox.x), float(bbox.y)
        # fallback to x1/x2 center
        cx = 0.0
        cy = 0.0
        if bbox.x1 is not None and bbox.x2 is not None:
            cx = (bbox.x1 + bbox.x2) / 2.0
        if bbox.y1 is not None and bbox.y2 is not None:
            cy = (bbox.y1 + bbox.y2) / 2.0
        return float(cx), float(cy)

    def _center_distance(self, c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5

    def _is_duplicate(self, det: Detection) -> Optional[str]:
        # simple rule: same class and center distance relative to image size within ratio and recent time
        now = det.timestamp
        center = self._detection_center(det.bbox)
        for inc_id, inc_type, inc_center, inc_time in list(self._active):
            if (now - inc_time).total_seconds() > self.dup_time_window:
                # expire
                self._active.remove((inc_id, inc_type, inc_center, inc_time))
                continue
            if inc_type != self._map_class_to_type(det.class_name):
                continue
            # normalize distance by image diagonal
            # If detection centers are normalized (0..1) use normalized diagonal, else use pixel diagonal
            is_normalized = 0.0 <= center[0] <= 1.0 and 0.0 <= center[1] <= 1.0
            if is_normalized:
                img_diag = (1.0 ** 2 + 1.0 ** 2) ** 0.5
            else:
                img_diag = ((det.image_width ** 2 + det.image_height ** 2) ** 0.5) or 1.0
            dist = self._center_distance(center, inc_center)
            if dist <= img_diag * self.dup_center_distance_ratio:
                return inc_id
        return None

    def _map_class_to_type(self, class_name: str) -> str:
        cls = class_name.lower() if class_name else ""
        if cls in ("person", "human"):
            return "PERSON_DETECTED"
        return "UNKNOWN_HAZARD"

    def process_detection(self, det: Detection, spatial_state: Optional[SpatialState] = None) -> Optional[Incident]:
        # validate
        if not det or det.confidence is None:
            return None

        # confidence threshold
        thresh = getattr(self.settings, "confidence_threshold", 0.5)
        if det.confidence < thresh:
            return None

        inc_type = self._map_class_to_type(det.class_name)

        # duplicate suppression
        dup = self._is_duplicate(det)
        if dup:
            # update timestamp of active incident
            for idx, (iid, itype, icenter, itime) in enumerate(self._active):
                if iid == dup:
                    self._active[idx] = (iid, itype, icenter, det.timestamp)
                    break
            return None

        # create incident
        incident_id = self._generate_incident_id()
        bbox = det.bbox
        
        location = None
        spatial_status = "UNAVAILABLE"
        pos_frame = None
        rng = None
        s_conf = None
        src_sensor = None
        
        if spatial_state:
            from app.spatial.locator import SpatialLocator
            locator = SpatialLocator()
            
            center_x, center_y = self._detection_center(bbox)
            if bbox.x1 is not None and bbox.x2 is not None and bbox.y2 is not None:
                bottom_x = (bbox.x1 + bbox.x2) / 2.0
                bottom_y = float(bbox.y2)
            else:
                bottom_x = center_x
                bottom_y = center_y
                
            base_target, map_target = locator.locate_target(incident_id, bottom_x, bottom_y, spatial_state)
            
            if map_target:
                location = Location(x=map_target.x, y=map_target.y, z=map_target.z)
                spatial_status = "ESTIMATED"
                pos_frame = map_target.frame_id
                rng = map_target.range
                s_conf = map_target.position_confidence
                src_sensor = map_target.source
            elif base_target:
                location = Location(x=base_target.x, y=base_target.y, z=base_target.z)
                spatial_status = "ESTIMATED"
                pos_frame = base_target.frame_id
                rng = base_target.range
                s_conf = base_target.position_confidence
                src_sensor = base_target.source

        inc = Incident(
            incident_id=incident_id,
            mission_id=getattr(det, "mission_id", "SAR-001"),
            type=inc_type,
            confidence=det.confidence,
            timestamp=det.timestamp,
            bbox=bbox,
            location=location,
            spatial_status=spatial_status,
            position_frame=pos_frame,
            range=rng,
            spatial_confidence=s_conf,
            source_sensor=src_sensor,
            evidence_image=getattr(det, "evidence_image", None),
            status="NEW",
        )

        # register as active
        center = self._detection_center(bbox)
        self._active.append((incident_id, inc_type, center, det.timestamp))
        return inc

    def process_detections(self, detections: List[Detection], spatial_state: Optional[SpatialState] = None) -> List[Incident]:
        created: List[Incident] = []
        for det in detections or []:
            inc = self.process_detection(det, spatial_state)
            if inc:
                created.append(inc)
        return created
