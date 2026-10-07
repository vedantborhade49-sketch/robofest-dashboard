import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from app.models.detection import Detection
from app.models.entity import Entity
from app.models.anomaly_event import AnomalyEvent, AnomalyEventStatus
from app.database.anomaly_event_repository import AnomalyEventRepository

logger = logging.getLogger(__name__)

from app.perception.anomaly_engine import AnomalyEngine

class EventRegistry:
    def __init__(self, repository: Optional[AnomalyEventRepository] = None):
        self.repo = repository or AnomalyEventRepository()
        self.engine = AnomalyEngine()
        
        self.resolve_grace_period = timedelta(seconds=10) # 10 seconds of no sightings = resolved
        self._active_events = {}
        self._load_active_events()

    def _load_active_events(self):
        events = self.repo.list_events()
        for e in events:
            if e.status in (AnomalyEventStatus.NEW, AnomalyEventStatus.ACTIVE, AnomalyEventStatus.UPDATED):
                self._active_events[e.event_id] = e

    def _generate_event_id(self) -> str:
        import uuid
        return f"EVENT_{uuid.uuid4().hex[:6].upper()}"

    def process_entities(self, entity_pairs: List[Tuple[Detection, Entity]]) -> List[Tuple[Detection, Entity, AnomalyEvent]]:
        """
        Takes (Detection, Entity) pairs and registers/updates anomaly events.
        """
        results = []
        now = datetime.utcnow()
        
        # 1. Process new updates
        for det, entity in entity_pairs:
            event_types = self.engine.evaluate(det, entity)
            
            for event_type in event_types:
                # Find active event for this entity + event_type
                active_event = self.repo.find_active_event(entity.entity_id, event_type)
                
                if active_event:
                    # Update existing
                    active_event.last_seen = det.timestamp
                    active_event.last_frame_id = det.frame_id
                    active_event.confidence = max(active_event.confidence, det.confidence)
                    active_event.status = AnomalyEventStatus.UPDATED
                    
                    # Update spatial if available (we will let spatial association augment this later,
                    # but we can capture basic bbox metadata here)
                    if not active_event.metadata:
                        active_event.metadata = {}
                    active_event.metadata["last_bbox"] = det.bbox.model_dump()
                    
                    updated = self.repo.update_event(active_event)
                    self._active_events[updated.event_id] = updated
                    results.append((det, entity, updated))
                else:
                    # Create new
                    new_event = AnomalyEvent(
                        event_id=self._generate_event_id(),
                        event_type=event_type,
                        entity_id=entity.entity_id,
                        status=AnomalyEventStatus.NEW,
                        first_seen=det.timestamp,
                        last_seen=det.timestamp,
                        first_frame_id=det.frame_id,
                        last_frame_id=det.frame_id,
                        confidence=det.confidence,
                        metadata={"last_bbox": det.bbox.model_dump()}
                    )
                    saved = self.repo.create_event(new_event)
                    self._active_events[saved.event_id] = saved
                    results.append((det, entity, saved))

        # 2. Cleanup stale events (Resolve)
        # Note: In a real system this might run on a timer, but doing it per frame is fine
        # if we just check timestamps. We'll use the latest timestamp in the batch as 'now', 
        # or just actual wall-clock.
        if entity_pairs:
            batch_time = max(det.timestamp for det, _ in entity_pairs)
            stale_ids = []
            for event_id, event in self._active_events.items():
                if (batch_time - event.last_seen) > self.resolve_grace_period:
                    stale_ids.append(event_id)
            
            for eid in stale_ids:
                self.repo.resolve_event(eid)
                del self._active_events[eid]
                
        return results
