from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.spatial import SpatialState, LiDARScan, Obstacle
from app.core.state_manager import StateManager

router = APIRouter(prefix="/spatial", tags=["spatial"])

@router.get("/state", response_model=SpatialState)
async def get_spatial_state():
    state = StateManager.instance().get_state()
    if state and state.spatial:
        return state.spatial
    return SpatialState()

@router.get("/lidar", response_model=Optional[LiDARScan])
async def get_lidar_scan():
    state = StateManager.instance().get_state()
    if state and state.spatial and state.spatial.latest_scan:
        return state.spatial.latest_scan
    raise HTTPException(status_code=404, detail="No LiDAR scan available")

@router.get("/obstacles", response_model=List[Obstacle])
async def get_obstacles():
    state = StateManager.instance().get_state()
    if state and state.spatial:
        return state.spatial.obstacles
    return []
