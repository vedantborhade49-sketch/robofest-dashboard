from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import IncidentCreateRequest, IncidentPatchRequest, IncidentResponse
from app.services.backend_service import BackendService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentResponse], summary="List incidents")
def list_incidents() -> List[IncidentResponse]:
    return [IncidentResponse.model_validate(item.model_dump()) for item in BackendService().get_incidents()]


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Get incident by id")
def get_incident(incident_id: str) -> IncidentResponse:
    incident = BackendService().get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(incident.model_dump())


@router.post("", response_model=IncidentResponse, summary="Create incident")
def create_incident(payload: IncidentCreateRequest) -> IncidentResponse:
    incident = payload.to_incident()
    saved = BackendService().create_incident(incident)
    return IncidentResponse.model_validate(saved.model_dump())


@router.patch("/{incident_id}", response_model=IncidentResponse, summary="Update incident")
def patch_incident(incident_id: str, payload: IncidentPatchRequest) -> IncidentResponse:
    updates = payload.model_dump(exclude_unset=True)
    incident = BackendService().update_incident(incident_id, **updates)
    return IncidentResponse.model_validate(incident.model_dump())
