import math
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.spatial import LiDARScan, Pose, SpatialState, CameraGeometry, DetectionGeometry, SpatialTarget

class CameraToLiDARTransform:
    """
    Synthetic calibration for Simulation.
    Assume Camera is mounted slightly above and forward of LiDAR, looking forward.
    For simplicity, camera optical axis (Z) is forward (X in LiDAR frame), 
    camera X is right (-Y in LiDAR frame), camera Y is down (-Z in LiDAR frame).
    """
    def __init__(self, offset_x=0.1, offset_y=0.0, offset_z=0.05):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.offset_z = offset_z

    def camera_ray_to_lidar_ray(self, ray_x: float, ray_y: float, ray_z: float) -> Tuple[float, float, float]:
        """
        Transforms a direction vector from Camera frame to LiDAR frame.
        Camera frame: Z forward, X right, Y down.
        LiDAR frame: X forward, Y left, Z up.
        """
        l_x = ray_z
        l_y = -ray_x
        l_z = -ray_y
        return l_x, l_y, l_z

class SpatialLocator:
    """
    Calculates spatial information for visual detections.
    """
    def __init__(self, camera_geom: Optional[CameraGeometry] = None, transform: Optional[CameraToLiDARTransform] = None):
        self.camera_geom = camera_geom or CameraGeometry()
        self.transform = transform or CameraToLiDARTransform()
        self.association_angular_tolerance = math.radians(5.0) # 5 degrees
        
    def get_camera_ray(self, u: float, v: float) -> Tuple[float, float, float]:
        """
        Convert pixel (u,v) to a normalized 3D ray in camera frame.
        """
        x_norm = (u - self.camera_geom.cx) / self.camera_geom.fx
        y_norm = (v - self.camera_geom.cy) / self.camera_geom.fy
        z_norm = 1.0
        
        # Normalize vector
        length = math.sqrt(x_norm**2 + y_norm**2 + z_norm**2)
        return x_norm/length, y_norm/length, z_norm/length

    def associate_lidar(self, lidar_ray: Tuple[float, float, float], scan: LiDARScan) -> List[float]:
        """
        Search LiDAR points near the expected ray and return candidate ranges.
        In 2D LiDAR, we only care about the yaw angle (atan2(y, x)).
        """
        l_x, l_y, l_z = lidar_ray
        target_yaw = math.atan2(l_y, l_x)
        
        candidates = []
        for pt in scan.points:
            angle_diff = abs(pt.angle - target_yaw)
            # handle wrap-around
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
                
            if angle_diff <= self.association_angular_tolerance:
                if scan.min_range < pt.distance < scan.max_range:
                    candidates.append(pt.distance)
                    
        return candidates

    def estimate_range(self, candidate_ranges: List[float]) -> Tuple[Optional[float], float]:
        """
        Robust range estimator (e.g. median). Returns (range, confidence).
        """
        if not candidate_ranges:
            return None, 0.0
            
        sorted_ranges = sorted(candidate_ranges)
        mid = len(sorted_ranges) // 2
        median_range = sorted_ranges[mid]
        
        # Simple confidence based on number of points clustered
        conf = min(1.0, len(candidate_ranges) / 5.0) 
        return median_range, conf

    def locate_target(self, target_id: str, u: float, v: float, spatial_state: SpatialState) -> Tuple[Optional[SpatialTarget], Optional[SpatialTarget]]:
        """
        Locate target. Returns (base_link_target, map_target).
        If SLAM is lost, map_target will be None.
        If LiDAR fails/misses, both will be None.
        """
        scan = spatial_state.latest_scan
        if not scan:
            return None, None
            
        # 1. Camera Ray
        cam_ray = self.get_camera_ray(u, v)
        
        # 2. Transform to LiDAR ray
        lidar_ray = self.transform.camera_ray_to_lidar_ray(*cam_ray)
        
        # 3. Association
        candidate_ranges = self.associate_lidar(lidar_ray, scan)
        
        # 4. Range Estimation
        target_range, conf = self.estimate_range(candidate_ranges)
        if target_range is None:
            return None, None
            
        # 5. Position in LiDAR/base_link frame
        # Assuming LiDAR frame = base_link for 2D simplicity
        bl_x = lidar_ray[0] * target_range
        bl_y = lidar_ray[1] * target_range
        bl_z = lidar_ray[2] * target_range
        
        base_link_target = SpatialTarget(
            target_id=target_id,
            frame_id="base_link",
            x=bl_x,
            y=bl_y,
            z=bl_z,
            range=target_range,
            position_confidence=conf
        )
        
        # 6. Transform to Map Frame using SLAM Pose
        if spatial_state.slam_status == "TRACKING" and spatial_state.current_pose:
            pose = spatial_state.current_pose
            
            # 2D Transform (ignoring pitch/roll for now)
            map_x = pose.x + (bl_x * math.cos(pose.yaw) - bl_y * math.sin(pose.yaw))
            map_y = pose.y + (bl_x * math.sin(pose.yaw) + bl_y * math.cos(pose.yaw))
            map_z = pose.z + bl_z
            
            map_target = SpatialTarget(
                target_id=target_id,
                frame_id="map",
                x=map_x,
                y=map_y,
                z=map_z,
                range=target_range,
                position_confidence=conf
            )
            return base_link_target, map_target
            
        return base_link_target, None
