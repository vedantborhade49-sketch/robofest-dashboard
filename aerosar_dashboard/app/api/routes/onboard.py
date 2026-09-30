from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.models.onboard import OnboardStatus, OnboardSystemHealth
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

router = APIRouter()

# In a real setup, this would be a global reference or injected dependency
# For now we'll mock the status for ground station
mock_onboard_status = OnboardStatus()

@router.get("/status", response_model=OnboardStatus)
async def get_onboard_status():
    """Returns the overall status of the onboard runtime."""
    return mock_onboard_status

@router.get("/health", response_model=OnboardSystemHealth)
async def get_onboard_health():
    """Returns the latest health report from the onboard system."""
    # Return mock data if running on ground station
    return OnboardSystemHealth(
        cpu_percent=12.5,
        memory_percent=45.2,
        temperature_c=42.1,
        disk_percent=33.3,
        is_pi=True,
        os="Linux"
    )

@router.post("/ingest")
async def ingest_onboard_event(event_wrapper: Dict[str, Any]):
    """
    Receives an event from the onboard companion computer.
    This is where structured incidents and telemetry are pushed.
    """
    event_type_str = event_wrapper.get("event_type")
    payload = event_wrapper.get("payload", {})
    
    # We could route these directly into the ground station's StateManager
    # or just broadcast them over the event bus for the dashboard to catch.
    try:
        # Just broadcast to websocket clients
        event_type = EventType(event_type_str)
        event_bus.publish(event_type, payload)
    except ValueError:
        pass # Ignore unknown events
        
    return {"status": "accepted"}
