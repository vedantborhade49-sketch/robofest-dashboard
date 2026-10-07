import os
import cv2
import json
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from pathlib import Path

from app.models.detection import Detection, BoundingBox
from app.models.entity import Entity, EntityStatus
from app.database.entity_repository import EntityRepository

class MatchResult:
    def __init__(self, matched: bool, entity_id: Optional[str], confidence: float, reason: str):
        self.matched = matched
        self.entity_id = entity_id
        self.confidence = confidence
        self.reason = reason

class EntityAppearanceMatcher:
    """
    Placeholder for future true Re-ID (e.g., person Re-ID embeddings).
    Currently unavailable in standard YOLO output.
    """
    def match_appearance(self, detection: Detection, candidates: List[Entity]) -> MatchResult:
        return MatchResult(False, None, 0.0, "appearance matcher unavailable")

class EntityMatcher:
    def __init__(self, time_window_seconds: float = 5.0, distance_ratio: float = 0.2):
        self.time_window = time_window_seconds
        self.distance_ratio = distance_ratio
        self.appearance_matcher = EntityAppearanceMatcher()

    def _detection_center(self, bbox: BoundingBox) -> Tuple[float, float]:
        if bbox.x is not None and bbox.y is not None:
            return float(bbox.x), float(bbox.y)
        cx = 0.0
        cy = 0.0
        if bbox.x1 is not None and bbox.x2 is not None:
            cx = (bbox.x1 + bbox.x2) / 2.0
        if bbox.y1 is not None and bbox.y2 is not None:
            cy = (bbox.y1 + bbox.y2) / 2.0
        return float(cx), float(cy)

    def match(self, detection: Detection, candidate_entities: List[Entity], timestamp: Optional[datetime] = None) -> MatchResult:
        """
        Entity matching pipeline:
        1. Try true appearance Re-ID (unavailable)
        2. Fallback to short-term spatial-temporal tracking
        3. If track_id exists (it doesn't in current YOLO), use it.
        """
        now = timestamp or detection.timestamp
        
        # 1. Appearance Match (Future)
        app_result = self.appearance_matcher.match_appearance(detection, candidate_entities)
        if app_result.matched:
            return app_result

        # 2. Track ID (Not available in current model, but this is where it would be checked)
        if hasattr(detection, "track_id") and detection.track_id is not None:
            pass # We would map track_id to entity_id here

        # 3. Spatial-Temporal Heuristic Fallback
        center = self._detection_center(detection.bbox)
        is_normalized = 0.0 <= center[0] <= 1.0 and 0.0 <= center[1] <= 1.0
        img_diag = (1.0 ** 2 + 1.0 ** 2) ** 0.5 if is_normalized else (((detection.image_width ** 2 + detection.image_height ** 2) ** 0.5) or 1.0)

        best_match = None
        best_dist = float('inf')

        for entity in candidate_entities:
            if entity.entity_type != detection.class_name.upper():
                continue
            
            time_diff = (now - entity.last_seen).total_seconds()
            if time_diff > self.time_window or time_diff < -1.0:
                continue

            last_center = entity.metadata.get("last_center")
            if not last_center:
                continue
                
            dist = ((center[0] - last_center[0]) ** 2 + (center[1] - last_center[1]) ** 2) ** 0.5
            if dist <= img_diag * self.distance_ratio:
                if dist < best_dist:
                    best_dist = dist
                    best_match = entity

        if best_match:
            conf = max(0.0, 1.0 - (best_dist / (img_diag * self.distance_ratio)))
            return MatchResult(True, best_match.entity_id, conf, "Spatial-temporal heuristic match")
            
        return MatchResult(False, None, 0.0, "UNKNOWN")


class EntityRegistry:
    def __init__(self, repository: Optional[EntityRepository] = None, data_dir: str = "data/entities"):
        self.repo = repository or EntityRepository()
        self.matcher = EntityMatcher()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load active entities into memory for fast matching
        self._active_entities = {e.entity_id: e for e in self.repo.find_active_entities()}
        
        # Keep track of counters for ID generation
        self._counters = {}
        self._initialize_counters()

    def _initialize_counters(self):
        # Very simple counter initialization based on existing entities
        all_entities = self.repo.list_entities()
        for e in all_entities:
            parts = e.entity_id.split("_")
            if len(parts) == 2 and parts[1].isdigit():
                prefix = parts[0]
                num = int(parts[1])
                if prefix not in self._counters or num > self._counters[prefix]:
                    self._counters[prefix] = num

    def _generate_entity_id(self, entity_type: str) -> str:
        prefix = entity_type.upper()
        if prefix not in self._counters:
            self._counters[prefix] = 0
        self._counters[prefix] += 1
        return f"{prefix}_{self._counters[prefix]:03d}"

    def _get_bbox_area(self, bbox: BoundingBox) -> float:
        if bbox.width is not None and bbox.height is not None:
            return bbox.width * bbox.height
        return 0.0

    def _save_crop_if_better(self, entity: Entity, detection: Detection, frame: Optional[np.ndarray]):
        if frame is None:
            return

        bbox = detection.bbox
        if bbox.x1 is None or bbox.x2 is None or bbox.y1 is None or bbox.y2 is None:
            return

        area = self._get_bbox_area(bbox)
        current_best_area = entity.metadata.get("best_area", 0.0)
        current_best_conf = entity.metadata.get("best_confidence", 0.0)

        # Replace crop if confidence is significantly higher or area is larger (while confidence is decent)
        better_crop = False
        if detection.confidence > current_best_conf + 0.1:
            better_crop = True
        elif detection.confidence >= current_best_conf - 0.05 and area > current_best_area:
            better_crop = True

        if better_crop or entity.image_path is None:
            # Extract crop
            h, w = frame.shape[:2]
            x1 = max(0, int(bbox.x1))
            y1 = max(0, int(bbox.y1))
            x2 = min(w, int(bbox.x2))
            y2 = min(h, int(bbox.y2))

            if x2 > x1 and y2 > y1:
                crop = frame[y1:y2, x1:x2]
                entity_dir = self.data_dir / entity.entity_id
                entity_dir.mkdir(exist_ok=True)
                
                crop_path = entity_dir / "best_crop.jpg"
                cv2.imwrite(str(crop_path), crop)
                
                entity.image_path = str(crop_path)
                entity.metadata["best_area"] = area
                entity.metadata["best_confidence"] = float(detection.confidence)

                # Save metadata json
                meta_path = entity_dir / "metadata.json"
                with open(meta_path, "w") as f:
                    json.dict_meta = {
                        "entity_id": entity.entity_id,
                        "type": entity.entity_type,
                        "best_confidence": float(detection.confidence),
                        "best_area": area,
                        "last_updated": datetime.now().isoformat()
                    }
                    json.dump(json.dict_meta, f, indent=2)

    def resolve(self, detection: Detection, timestamp: datetime, frame_id: int, frame: Optional[np.ndarray] = None) -> Entity:
        """
        Resolves a detection to a persistent Entity (creates or updates).
        """
        candidates = list(self._active_entities.values())
        match_result = self.matcher.match(detection, candidates, timestamp)

        center = self.matcher._detection_center(detection.bbox)

        if match_result.matched and match_result.entity_id and match_result.entity_id in self._active_entities:
            # Update existing
            entity = self._active_entities[match_result.entity_id]
            entity.last_seen = timestamp
            entity.last_frame_id = frame_id
            entity.sighting_count += 1
            # exponential moving average for confidence
            entity.confidence = (entity.confidence * 0.7) + (detection.confidence * 0.3)
            entity.metadata["last_center"] = center
            entity.metadata["last_reason"] = match_result.reason

            self._save_crop_if_better(entity, detection, frame)
            
            # Persist update
            updated_entity = self.repo.update_entity(entity)
            self._active_entities[match_result.entity_id] = updated_entity
            return updated_entity
        else:
            # Create new
            new_id = self._generate_entity_id(detection.class_name)
            entity = Entity(
                entity_id=new_id,
                entity_type=detection.class_name.upper(),
                first_seen=timestamp,
                last_seen=timestamp,
                first_frame_id=frame_id,
                last_frame_id=frame_id,
                sighting_count=1,
                confidence=detection.confidence,
                status=EntityStatus.ACTIVE,
                metadata={"last_center": center, "creation_reason": match_result.reason}
            )
            
            self._save_crop_if_better(entity, detection, frame)
            
            saved_entity = self.repo.create_entity(entity)
            self._active_entities[saved_entity.entity_id] = saved_entity
            return saved_entity

    def process_detections(self, detections: List[Detection], frame: Optional[np.ndarray] = None) -> List[Tuple[Detection, Entity]]:
        """
        Process a list of detections for a single frame.
        Returns a list of (Detection, Entity) tuples.
        """
        results = []
        for det in detections:
            entity = self.resolve(det, det.timestamp, det.frame_id, frame)
            results.append((det, entity))
        return results
