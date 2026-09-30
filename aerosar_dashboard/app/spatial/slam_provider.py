import time
import math
import logging
from typing import Optional, Tuple, List
from datetime import datetime

from app.models.spatial import Pose, OccupancyGrid, TrajectoryPoint, LiDARScan

logger = logging.getLogger(__name__)

class SLAMProvider:
    """
    Abstract interface for a SLAM provider.
    """
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def update(self, scan: LiDARScan):
        raise NotImplementedError

    def get_pose(self) -> Optional[Pose]:
        raise NotImplementedError

    def get_map(self) -> Optional[OccupancyGrid]:
        raise NotImplementedError

    def get_trajectory(self) -> List[TrajectoryPoint]:
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def is_initialized(self) -> bool:
        raise NotImplementedError
        
    def get_status(self) -> str:
        raise NotImplementedError
        
    def get_quality(self) -> str:
        raise NotImplementedError

class MockSLAMProvider(SLAMProvider):
    """
    Simulated SLAM provider that processes LiDAR scans to build a local occupancy map
    and estimates pose. Includes simulated drift to distinguish estimate from ground truth.
    """
    def __init__(self, map_width=600, map_height=500, resolution=0.05):
        self._is_running = False
        self._is_initialized = False
        self._status = "DISABLED"
        
        self.map_width = map_width
        self.map_height = map_height
        self.resolution = resolution
        
        # Origin at center of map
        self.origin_x = (map_width * resolution) / 2.0
        self.origin_y = (map_height * resolution) / 2.0
        
        self._pose = Pose(x=0.0, y=0.0, yaw=0.0)
        self._trajectory: List[TrajectoryPoint] = []
        self._map = OccupancyGrid(
            width=self.map_width, 
            height=self.map_height, 
            resolution=self.resolution,
            origin_x=self.origin_x,
            origin_y=self.origin_y,
            cells=[0] * (self.map_width * self.map_height)
        )
        
        self._last_update_time = None
        self._accumulated_drift_x = 0.0
        self._accumulated_drift_y = 0.0
        self._accumulated_drift_yaw = 0.0

    def start(self):
        self._is_running = True
        self._status = "INITIALIZING"
        self._last_update_time = time.time()
        logger.info("MockSLAMProvider started.")

    def stop(self):
        self._is_running = False
        self._status = "DISABLED"
        logger.info("MockSLAMProvider stopped.")

    def update(self, scan: LiDARScan):
        if not self._is_running:
            return
            
        current_time = time.time()
        dt = current_time - self._last_update_time if self._last_update_time else 0.1
        self._last_update_time = current_time
        
        if not self._is_initialized:
            # First scan, set origin
            self._pose = Pose(x=0.0, y=0.0, yaw=0.0)
            self._trajectory.append(TrajectoryPoint(x=0.0, y=0.0, yaw=0.0))
            self._is_initialized = True
            self._status = "TRACKING"
            
        # 1. Pose Estimation (Mock)
        # Instead of real ICP, we simulate odometry from the mock provider's ground truth movement
        # by extracting a "velocity" and adding noise.
        # Since we don't have access to ground truth directly here, we will just simulate 
        # a forward movement with some turning, simulating the drone exploring.
        # Wait, the MockLiDARProvider generates scans based on its internal ground truth.
        # If we just move arbitrarily here, the LiDAR points won't match our movement!
        # For a truly robust mock, we should calculate the shift between consecutive LiDAR scans.
        # But for this step, we can use a simplified matching: 
        # We'll just assume the drone is moving at v=0.5 m/s, w=0.1 rad/s (circle) 
        # which matches the MockLiDARProvider's ground truth we will implement.
        
        # Simulated estimation drift
        self._accumulated_drift_x += dt * 0.01  # 1cm/s drift
        self._accumulated_drift_y += dt * -0.005
        self._accumulated_drift_yaw += dt * 0.002
        
        v = 0.5
        w = 0.1
        
        # Update pose estimate
        self._pose.yaw += (w * dt) + self._accumulated_drift_yaw * dt
        self._pose.x += (v * math.cos(self._pose.yaw)) * dt + self._accumulated_drift_x * dt
        self._pose.y += (v * math.sin(self._pose.yaw)) * dt + self._accumulated_drift_y * dt
        self._pose.timestamp = datetime.now()
        
        # Add to trajectory (downsampled)
        if len(self._trajectory) == 0 or self._distance(self._pose, self._trajectory[-1]) > 0.5:
            self._trajectory.append(TrajectoryPoint(x=self._pose.x, y=self._pose.y, yaw=self._pose.yaw))
            if len(self._trajectory) > 500:
                self._trajectory.pop(0)
                
        # 2. Map Update (Ray tracing)
        self._update_occupancy_grid(scan)
        
    def _distance(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)
        
    def _update_occupancy_grid(self, scan: LiDARScan):
        """Ray tracing from estimated pose to lidar points to update occupancy grid."""
        # Drone position in grid
        px = self._pose.x
        py = self._pose.y
        
        gx0, gy0 = self._world_to_grid(px, py)
        
        for pt in scan.points:
            # Transform point to world coordinates based on estimated pose
            world_x = px + pt.distance * math.cos(self._pose.yaw + pt.angle)
            world_y = py + pt.distance * math.sin(self._pose.yaw + pt.angle)
            
            gx1, gy1 = self._world_to_grid(world_x, world_y)
            
            # Very basic Bresenham's line algorithm to mark free space
            self._mark_line_free(gx0, gy0, gx1, gy1)
            
            # Mark endpoint as occupied
            if 0 <= gx1 < self.map_width and 0 <= gy1 < self.map_height:
                self._map.cells[gy1 * self.map_width + gx1] = 2
                
        self._map.timestamp = datetime.now()

    def _world_to_grid(self, wx: float, wy: float) -> Tuple[int, int]:
        gx = int((wx + self.origin_x) / self.resolution)
        gy = int((wy + self.origin_y) / self.resolution)
        return gx, gy

    def _mark_line_free(self, x0: int, y0: int, x1: int, y1: int):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    idx = y * self.map_width + x
                    if self._map.cells[idx] != 2: # Don't overwrite existing obstacles immediately
                        self._map.cells[idx] = 1
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    idx = y * self.map_width + x
                    if self._map.cells[idx] != 2:
                        self._map.cells[idx] = 1
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

    def get_pose(self) -> Optional[Pose]:
        return self._pose

    def get_map(self) -> Optional[OccupancyGrid]:
        return self._map

    def get_trajectory(self) -> List[TrajectoryPoint]:
        return self._trajectory

    def reset(self):
        self._pose = Pose(x=0.0, y=0.0, yaw=0.0)
        self._trajectory.clear()
        self._map.cells = [0] * (self.map_width * self.map_height)
        self._is_initialized = False
        self._status = "INITIALIZING" if self._is_running else "DISABLED"
        self._accumulated_drift_x = 0.0
        self._accumulated_drift_y = 0.0
        self._accumulated_drift_yaw = 0.0

    def is_initialized(self) -> bool:
        return self._is_initialized
        
    def get_status(self) -> str:
        return self._status
        
    def get_quality(self) -> str:
        return "GOOD" if self._is_initialized else "N/A"
