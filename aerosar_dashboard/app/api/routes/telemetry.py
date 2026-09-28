from fastapi import APIRouter

from app.services.backend_service import BackendService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("", summary="Read current telemetry state", response_model=dict)
def get_telemetry() -> dict:
    return BackendService().get_telemetry()
