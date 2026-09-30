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

from app.models.spatial import Pose, OccupancyGrid, TrajectoryPoint

@router.get("/pose", response_model=Optional[Pose])
async def get_pose():
    state = StateManager.instance().get_state()
    if state and state.spatial and state.spatial.current_pose:
        return state.spatial.current_pose
    raise HTTPException(status_code=404, detail="No Pose available")

@router.get("/map", response_model=Optional[OccupancyGrid])
async def get_map():
    state = StateManager.instance().get_state()
    if state and state.spatial and state.spatial.local_map:
        return state.spatial.local_map
    raise HTTPException(status_code=404, detail="No Map available")

@router.get("/trajectory", response_model=List[TrajectoryPoint])
async def get_trajectory():
    state = StateManager.instance().get_state()
    if state and state.spatial:
        return state.spatial.trajectory
    return []

slam_router = APIRouter(prefix="/slam", tags=["slam"])

@slam_router.get("/status")
async def get_slam_status():
    state = StateManager.instance().get_state()
    if state and state.spatial:
        return {
            "status": state.spatial.slam_status,
            "quality": state.spatial.slam_quality,
            "pose_available": state.spatial.current_pose is not None
        }
    return {"status": "DISABLED", "quality": "N/A", "pose_available": False}

