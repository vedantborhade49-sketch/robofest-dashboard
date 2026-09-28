from typing import List, Optional

from fastapi import APIRouter, Query

from app.api.schemas import EventCreateRequest, EventResponse
from app.services.backend_service import BackendService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=List[EventResponse], summary="List events")
def list_events(
    level: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    mission_id: Optional[str] = Query(default=None),
    incident_id: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1),
) -> List[EventResponse]:
    events = BackendService().get_events(level=level, source=source, mission_id=mission_id, incident_id=incident_id, limit=limit)
    return [EventResponse.model_validate(item.model_dump()) for item in events]


@router.post("", response_model=EventResponse, summary="Create event")
def create_event(payload: EventCreateRequest) -> EventResponse:
    event = payload.to_event()
    saved = BackendService().create_event(event)
    return EventResponse.model_validate(saved.model_dump())
