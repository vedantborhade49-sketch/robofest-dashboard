from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_session
from app.database.models import EntityModel
from app.models.entity import Entity, EntityStatus

class EntityRepository:
    def _get_session(self) -> Session:
        return next(get_session())

    def _to_pydantic(self, m: EntityModel) -> Entity:
        return Entity(
            entity_id=m.entity_id,
            entity_type=m.entity_type,
            first_seen=m.first_seen,
            last_seen=m.last_seen,
            first_frame_id=m.first_frame_id,
            last_frame_id=m.last_frame_id,
            sighting_count=m.sighting_count,
            confidence=m.confidence,
            status=m.status,
            image_path=m.image_path,
            metadata=m.metadata_json or {},
            created_at=m.created_at,
            updated_at=m.updated_at
        )

    def create_entity(self, entity: Entity) -> Entity:
        with self._get_session() as db:
            db_entity = EntityModel(
                entity_id=entity.entity_id,
                entity_type=entity.entity_type,
                first_seen=entity.first_seen,
                last_seen=entity.last_seen,
                first_frame_id=entity.first_frame_id,
                last_frame_id=entity.last_frame_id,
                sighting_count=entity.sighting_count,
                confidence=entity.confidence,
                status=str(entity.status.value if hasattr(entity.status, 'value') else entity.status),
                image_path=entity.image_path,
                metadata_json=entity.metadata,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )
            db.add(db_entity)
            db.commit()
            db.refresh(db_entity)
            return self._to_pydantic(db_entity)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        with self._get_session() as db:
            m = db.query(EntityModel).filter(EntityModel.entity_id == entity_id).first()
            if not m:
                return None
            return self._to_pydantic(m)

    def update_entity(self, entity: Entity) -> Entity:
        with self._get_session() as db:
            m = db.query(EntityModel).filter(EntityModel.entity_id == entity.entity_id).first()
            if m:
                m.entity_type = entity.entity_type
                m.first_seen = entity.first_seen
                m.last_seen = entity.last_seen
                m.first_frame_id = entity.first_frame_id
                m.last_frame_id = entity.last_frame_id
                m.sighting_count = entity.sighting_count
                m.confidence = entity.confidence
                m.status = str(entity.status.value if hasattr(entity.status, 'value') else entity.status)
                m.image_path = entity.image_path
                m.metadata_json = entity.metadata
                m.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(m)
                return self._to_pydantic(m)
            else:
                return self.create_entity(entity)

    def list_entities(self) -> List[Entity]:
        with self._get_session() as db:
            models = db.query(EntityModel).order_by(EntityModel.last_seen.desc()).all()
            return [self._to_pydantic(m) for m in models]

    def find_active_entities(self) -> List[Entity]:
        with self._get_session() as db:
            models = db.query(EntityModel).filter(EntityModel.status == EntityStatus.ACTIVE.value).all()
            return [self._to_pydantic(m) for m in models]

    def mark_inactive(self, entity_id: str) -> Optional[Entity]:
        with self._get_session() as db:
            m = db.query(EntityModel).filter(EntityModel.entity_id == entity_id).first()
            if m:
                m.status = EntityStatus.INACTIVE.value
                m.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(m)
                return self._to_pydantic(m)
            return None
