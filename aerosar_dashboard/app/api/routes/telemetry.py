from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.state_manager import StateManager

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

def _get_telem():
    state = StateManager.instance().get_telemetry()
    if not state:
        raise HTTPException(status_code=404, detail="Telemetry not available")
    return state

@router.get("", summary="Read current complete telemetry state")
def get_telemetry() -> dict:
    return _get_telem().model_dump()

@router.get("/position", summary="Read current position telemetry")
def get_position() -> dict:
    return _get_telem().position.model_dump()

@router.get("/flight", summary="Read current flight telemetry")
def get_flight() -> dict:
    return _get_telem().flight.model_dump()

@router.get("/attitude", summary="Read current attitude telemetry")
def get_attitude() -> dict:
    flight = _get_telem().flight
    return {
        "roll": flight.roll,
        "pitch": flight.pitch,
        "yaw": flight.yaw,
        "heading": flight.heading
    }

@router.get("/power", summary="Read current power telemetry")
def get_power() -> dict:
    return _get_telem().power.model_dump()

@router.get("/connection", summary="Read current connection telemetry")
def get_connection() -> dict:
    return _get_telem().communication.model_dump()

@router.get("/vehicle", summary="Read current vehicle controller status")
def get_vehicle() -> dict:
    return _get_telem().flight_controller.model_dump()

@router.get("/gps", summary="Read current GPS telemetry")
def get_gps() -> dict:
    return _get_telem().gps.model_dump()
