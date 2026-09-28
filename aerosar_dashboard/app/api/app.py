from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.missions import router as missions_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.reports import router as reports_router
from app.api.routes.events import router as events_router
from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.status import router as status_router

app = FastAPI(
    title="STALLION AEROSAR Backend",
    version="0.1.0",
    description="Backend communication layer for the AEROSAR search-and-rescue system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(missions_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(telemetry_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")
