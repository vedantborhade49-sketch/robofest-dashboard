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

class SpatialTarget(BaseModel):
    """
    Target position in a specific coordinate frame.
    """
    target_id: str
    frame_id: str
    x: float
    y: float
    z: float
    range: float
    timestamp: datetime = Field(default_factory=datetime.now)
    position_confidence: float = 0.0
    source: str = "LiDAR+Camera"

class CameraGeometry(BaseModel):
    """
    Abstraction for camera intrinsics and resolution.
    """
    image_width: int = 1280
    image_height: int = 720
    fx: float = 640.0
    fy: float = 640.0
    cx: float = 640.0
    cy: float = 360.0

class DetectionGeometry(BaseModel):
    """
    Structured representation of detection geometry.
    """
    center_x: float
    center_y: float
    width: float
    height: float
    bottom_center_x: float
    bottom_center_y: float

class Pose(BaseModel):
    """
    Vehicle pose in a given coordinate frame.
    x, y, z in meters. roll, pitch, yaw in radians.
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    frame_id: str = "map"

class TrajectoryPoint(BaseModel):
    """
    A single point in a historical trajectory.
    """
    x: float
    y: float
    yaw: float
    timestamp: datetime = Field(default_factory=datetime.now)

class OccupancyGrid(BaseModel):
    """
    2D Occupancy Grid map representation.
    cells: 0=unknown, 1=free, 2=occupied.
    """
    width: int
    height: int
    resolution: float = 0.05
    origin_x: float = 0.0
    origin_y: float = 0.0
    cells: List[int] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    frame_id: str = "map"

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
    
    # SLAM additions
    current_pose: Optional[Pose] = None
    trajectory: List[TrajectoryPoint] = Field(default_factory=list)
    local_map: Optional[OccupancyGrid] = None
    slam_status: str = "DISABLED" # DISABLED, INITIALIZING, TRACKING, LOST, ERROR
    slam_quality: str = "N/A"

class SpatialAssociation(BaseModel):
    """
    Matches a detection to a specific spatial state in time.
    """
    spatial_state: Optional[SpatialState] = None
    association_timestamp: datetime = Field(default_factory=datetime.now)
    temporal_error_ms: Optional[float] = None
    available: bool = False
