from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import MissionCreateRequest, MissionResponse
from app.services.backend_service import BackendService

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=List[MissionResponse], summary="List missions")
def list_missions() -> List[MissionResponse]:
    return [MissionResponse.model_validate(m.model_dump()) for m in BackendService().get_missions()]


@router.get("/{mission_id}", response_model=MissionResponse, summary="Get mission by id")
def get_mission(mission_id: str) -> MissionResponse:
    mission = BackendService().get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission.model_dump())


@router.post("", response_model=MissionResponse, summary="Create mission")
def create_mission(payload: MissionCreateRequest) -> MissionResponse:
    mission = BackendService().create_mission(payload.mission_id, payload.mission_name)
    return MissionResponse.model_validate(mission.model_dump())
