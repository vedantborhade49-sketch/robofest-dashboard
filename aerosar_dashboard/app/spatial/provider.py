from typing import Optional, List
import math
import random
import uuid
from datetime import datetime
from app.models.spatial import LiDARScan, LiDARPoint

class LiDARProvider:
    def start(self) -> bool:
        """Starts the LiDAR sensor."""
        raise NotImplementedError

    def stop(self):
        """Stops the LiDAR sensor."""
        raise NotImplementedError

    def get_scan(self) -> Optional[Any]:
        """Returns the latest raw scan from the sensor."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Returns True if the sensor is connected."""
        raise NotImplementedError


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

    def start(self) -> bool:
        self._connected = True
        self._start_time = datetime.now()
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
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        dynamic_obs_x = 5.0 + math.sin(elapsed * 0.5) * 2.0
        dynamic_obs_y = 2.0 + math.cos(elapsed * 0.3) * 1.5
        
        for i in range(self.num_points):
            angle = i * angle_increment
            
            # Simulate walls (box from x=-10..10, y=-10..10)
            # Ray intersection with x=10, x=-10, y=10, y=-10
            d_x1 = 10.0 / math.cos(angle) if abs(math.cos(angle)) > 1e-6 else float('inf')
            d_x2 = -10.0 / math.cos(angle) if abs(math.cos(angle)) > 1e-6 else float('inf')
            d_y1 = 10.0 / math.sin(angle) if abs(math.sin(angle)) > 1e-6 else float('inf')
            d_y2 = -10.0 / math.sin(angle) if abs(math.sin(angle)) > 1e-6 else float('inf')
            
            d_walls = min([d for d in [d_x1, d_x2, d_y1, d_y2] if d > 0])
            
            # Check dynamic obstacle (circle of radius 1m)
            # distance to obstacle center
            dx = dynamic_obs_x
            dy = dynamic_obs_y
            dist_to_obs = math.hypot(dx, dy)
            angle_to_obs = math.atan2(dy, dx)
            if angle_to_obs < 0:
                angle_to_obs += 2 * math.pi
                
            angle_diff = abs(angle - angle_to_obs)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
                
            d_obs = float('inf')
            # If ray hits the circle (approx angle diff)
            if angle_diff < math.atan2(1.0, dist_to_obs):
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
