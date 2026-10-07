from typing import Optional, List, Any
import math
import random
import uuid
from datetime import datetime
from app.spatial.provider import LiDARProvider

class MockLiDARProvider(LiDARProvider):
    def __init__(self, min_range=0.1, max_range=20.0, rate=10, seed=42):
        self._connected = False
        self.min_range = min_range
        self.max_range = max_range
        self.rate = rate
        self._seed = seed
        random.seed(self._seed)
        
        # Define some static environment (walls)
        self.num_points = 360 # 1 degree resolution
        
        # A simple box room with a few obstacles
        self._start_time = None
        self._last_time = None
        
        # Ground truth drone state
        self.gt_x = 0.0
        self.gt_y = 0.0
        self.gt_yaw = 0.0

    def start(self) -> bool:
        self._connected = True
        self._start_time = datetime.now()
        self._last_time = self._start_time
        return True

    def stop(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_scan(self) -> Optional[dict]:
        """
        Returns raw dict mimicking a driver format, so LiDARAdapter can convert it.
        """
        if not self._connected:
            return None
            
        points = []
        angle_increment = (2 * math.pi) / self.num_points
        
        # Time-based dynamic obstacle movement
        now = datetime.now()
        elapsed = (now - self._start_time).total_seconds() if self._start_time else 0
        dt = (now - self._last_time).total_seconds() if self._last_time else 0.1
        self._last_time = now
        
        dynamic_obs_x = 5.0 + math.sin(elapsed * 0.5) * 2.0
        dynamic_obs_y = 2.0 + math.cos(elapsed * 0.3) * 1.5
        
        # Update drone ground truth pose
        v = 0.5
        w = 0.1
        self.gt_yaw += w * dt
        self.gt_x += v * math.cos(self.gt_yaw) * dt
        self.gt_y += v * math.sin(self.gt_yaw) * dt
        
        for i in range(self.num_points):
            angle = i * angle_increment
            global_angle = self.gt_yaw + angle
            
            cos_a = math.cos(global_angle)
            sin_a = math.sin(global_angle)
            
            # Simulate walls (box from x=-15..15, y=-15..15)
            # Ray intersection with x=15, x=-15, y=15, y=-15 from (gt_x, gt_y)
            d_x1 = (15.0 - self.gt_x) / cos_a if abs(cos_a) > 1e-6 else float('inf')
            d_x2 = (-15.0 - self.gt_x) / cos_a if abs(cos_a) > 1e-6 else float('inf')
            d_y1 = (15.0 - self.gt_y) / sin_a if abs(sin_a) > 1e-6 else float('inf')
            d_y2 = (-15.0 - self.gt_y) / sin_a if abs(sin_a) > 1e-6 else float('inf')
            
            d_walls = min([d for d in [d_x1, d_x2, d_y1, d_y2] if d > 0], default=float('inf'))
            
            # Check dynamic obstacle (circle of radius 1m)
            # relative distance from drone to obstacle
            dx = dynamic_obs_x - self.gt_x
            dy = dynamic_obs_y - self.gt_y
            dist_to_obs = math.hypot(dx, dy)
            angle_to_obs = math.atan2(dy, dx) - self.gt_yaw
            
            if angle_to_obs < 0:
                angle_to_obs += 2 * math.pi
                
            angle_diff = abs(angle - angle_to_obs)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
                
            d_obs = float('inf')
            # If ray hits the circle (approx angle diff)
            if dist_to_obs > 1.0 and angle_diff < math.atan2(1.0, dist_to_obs):
                d_obs = dist_to_obs - math.cos(angle_diff) * 1.0
            
            # Select closest hit, add noise
            dist = min(d_walls, d_obs)
            dist += random.gauss(0, 0.05) # 5cm noise
            
            # Add some random dropouts or outliers
            if random.random() < 0.02:
                dist = self.max_range + 1.0 # Invalid
                
            points.append({
                "angle": angle,
                "distance": dist,
                "intensity": random.uniform(50, 255) if dist <= self.max_range else 0
            })
            
        return {
            "id": f"scan_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "min_range": self.min_range,
            "max_range": self.max_range,
            "angle_increment": angle_increment,
            "measurements": points
        }
