from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_session
from app.database.models import AnomalyEventModel
from app.models.anomaly_event import AnomalyEvent, AnomalyEventStatus

class AnomalyEventRepository:
    def _get_session(self) -> Session:
        return next(get_session())

    def _to_pydantic(self, m: AnomalyEventModel) -> AnomalyEvent:
        return AnomalyEvent(
            event_id=m.event_id,
            event_type=m.event_type,
            entity_id=m.entity_id,
            status=m.status,
            first_seen=m.first_seen,
            last_seen=m.last_seen,
            first_frame_id=m.first_frame_id,
            last_frame_id=m.last_frame_id,
            confidence=m.confidence,
            spatial_information=m.spatial_information,
            metadata=m.metadata_json or {},
            created_at=m.created_at,
            updated_at=m.updated_at
        )

    def create_event(self, event: AnomalyEvent) -> AnomalyEvent:
        with self._get_session() as db:
            db_event = AnomalyEventModel(
                event_id=event.event_id,
                event_type=event.event_type,
                entity_id=event.entity_id,
                status=str(event.status.value if hasattr(event.status, 'value') else event.status),
                first_seen=event.first_seen,
                last_seen=event.last_seen,
                first_frame_id=event.first_frame_id,
                last_frame_id=event.last_frame_id,
                confidence=event.confidence,
                spatial_information=event.spatial_information,
                metadata_json=event.metadata,
                created_at=event.created_at,
                updated_at=event.updated_at
            )
            db.add(db_event)
            db.commit()
            db.refresh(db_event)
            return self._to_pydantic(db_event)

    def get_event(self, event_id: str) -> Optional[AnomalyEvent]:
        with self._get_session() as db:
            m = db.query(AnomalyEventModel).filter(AnomalyEventModel.event_id == event_id).first()
            if not m:
                return None
            return self._to_pydantic(m)

    def update_event(self, event: AnomalyEvent) -> AnomalyEvent:
        with self._get_session() as db:
            m = db.query(AnomalyEventModel).filter(AnomalyEventModel.event_id == event.event_id).first()
            if m:
                m.event_type = event.event_type
                m.entity_id = event.entity_id
                m.status = str(event.status.value if hasattr(event.status, 'value') else event.status)
                m.first_seen = event.first_seen
                m.last_seen = event.last_seen
                m.first_frame_id = event.first_frame_id
                m.last_frame_id = event.last_frame_id
                m.confidence = event.confidence
                m.spatial_information = event.spatial_information
                m.metadata_json = event.metadata
                m.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(m)
                return self._to_pydantic(m)
            else:
                return self.create_event(event)

    def find_active_event(self, entity_id: str, event_type: str) -> Optional[AnomalyEvent]:
        with self._get_session() as db:
            m = db.query(AnomalyEventModel).filter(
                AnomalyEventModel.entity_id == entity_id,
                AnomalyEventModel.event_type == event_type,
                AnomalyEventModel.status.in_([AnomalyEventStatus.NEW.value, AnomalyEventStatus.ACTIVE.value, AnomalyEventStatus.UPDATED.value])
            ).order_by(AnomalyEventModel.last_seen.desc()).first()
            if m:
                return self._to_pydantic(m)
            return None

    def list_events(self) -> List[AnomalyEvent]:
        with self._get_session() as db:
            models = db.query(AnomalyEventModel).order_by(AnomalyEventModel.last_seen.desc()).all()
            return [self._to_pydantic(m) for m in models]

    def resolve_event(self, event_id: str) -> Optional[AnomalyEvent]:
        with self._get_session() as db:
            m = db.query(AnomalyEventModel).filter(AnomalyEventModel.event_id == event_id).first()
            if m:
                m.status = AnomalyEventStatus.RESOLVED.value
                m.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(m)
                return self._to_pydantic(m)
            return None
