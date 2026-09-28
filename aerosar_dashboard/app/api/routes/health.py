from fastapi import APIRouter

from app.services.backend_service import BackendService

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check", description="Returns the backend health status.")
def health() -> dict:
    return BackendService().get_health()
