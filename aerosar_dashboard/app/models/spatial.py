from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LocalPosition(BaseModel):
    """
    Local position relative to the drone's origin (0, 0, 0)
    Uses a standard robotics coordinate frame:
    x = forward (meters)
    y = left (meters)
    z = up (meters)
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

class LiDARPoint(BaseModel):
    """
    A single valid LiDAR measurement point.
    """
    angle: float          # Radians
    distance: float       # Meters
    x: float              # Cartesian X (forward)
    y: float              # Cartesian Y (left)
    intensity: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class LiDARScan(BaseModel):
    """
    A complete scan from the LiDAR sensor.
    """
    scan_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    points: List[LiDARPoint] = Field(default_factory=list)
    min_range: float = 0.0
    max_range: float = 12.0
    angle_min: float = 0.0
    angle_max: float = 6.28318530718 # 2 * PI
    angle_increment: float = 0.01
    sensor_frame: str = "laser"

class Obstacle(BaseModel):
    """
    Extracted obstacle derived from spatial data.
    """
    obstacle_id: str
    x: float
    y: float
    distance: float
    size_estimate: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class SpatialState(BaseModel):
    """
    The current spatial state of the environment.
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    latest_scan: Optional[LiDARScan] = None
    obstacles: List[Obstacle] = Field(default_factory=list)
    local_position: Optional[LocalPosition] = None
    coordinate_frame: str = "base_link"
    sensor_status: str = "DISCONNECTED" # CONNECTED, DISCONNECTED, ERROR, STALE
