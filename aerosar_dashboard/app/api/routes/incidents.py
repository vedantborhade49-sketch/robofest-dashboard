from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.schemas import EvidenceResponse, IncidentCreateRequest, IncidentPatchRequest, IncidentResponse, IncidentStatusUpdateRequest
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


@router.patch("/{incident_id}/status", response_model=IncidentResponse, summary="Update incident status")
def update_incident_status(incident_id: str, payload: IncidentStatusUpdateRequest) -> IncidentResponse:
    try:
        incident = BackendService().update_incident_status(incident_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IncidentResponse.model_validate(incident.model_dump())


@router.get("/{incident_id}/evidence", response_model=List[EvidenceResponse], summary="Get evidence for an incident")
def list_incident_evidence(incident_id: str) -> List[EvidenceResponse]:
    evidence = BackendService().get_incident_evidence(incident_id)
    return [EvidenceResponse.from_model(item) for item in evidence]


@router.get("/{incident_id}/evidence/file", summary="Serve incident evidence image")
def get_incident_evidence_file(incident_id: str):
    evidence = BackendService().get_incident_evidence(incident_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    target = evidence[0]
    if BackendService().evidence_service.is_invalid_path(target.file_path):
        raise HTTPException(status_code=400, detail="Invalid evidence path")
    return FileResponse(path=target.file_path, media_type=target.mime_type)
