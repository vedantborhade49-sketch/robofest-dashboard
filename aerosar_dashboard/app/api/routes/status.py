from fastapi import APIRouter

from app.services.backend_service import BackendService

router = APIRouter(tags=["status"])


@router.get("/system/status", summary="System status", response_model=dict)
def system_status() -> dict:
    return BackendService().get_system_status()


@router.get("/drone/status", summary="Drone status", response_model=dict)
def drone_status() -> dict:
    return BackendService().get_drone_status()


@router.get("/camera/status", summary="Camera status", response_model=dict)
def camera_status() -> dict:
    return BackendService().get_camera_status()


@router.get("/ai/status", summary="AI status", response_model=dict)
def ai_status() -> dict:
    return BackendService().get_ai_status()


@router.get("/drone/position", summary="Drone position", response_model=dict)
def drone_position() -> dict:
    return BackendService().get_drone_position()
