import logging
from typing import Optional
from datetime import datetime
import uuid
import math

from app.models.spatial import SpatialState, Obstacle, LocalPosition
from app.spatial.provider import LiDARProvider
from app.spatial.adapter import LiDARAdapter

logger = logging.getLogger(__name__)

class SpatialService:
    def __init__(self, provider: LiDARProvider):
        self.provider = provider
        self.adapter = LiDARAdapter()
        self.state = SpatialState()
        self.state.local_position = LocalPosition(x=0.0, y=0.0, z=0.0)

    def start(self):
        logger.info("Starting SpatialService...")
        self.provider.start()
        self.state.sensor_status = "CONNECTED"

    def stop(self):
        logger.info("Stopping SpatialService...")
        self.provider.stop()
        self.state.sensor_status = "DISCONNECTED"

    def update(self) -> SpatialState:
        """Called periodically by the main update loop to process new LiDAR data."""
        if not self.provider.is_connected():
            self.state.sensor_status = "DISCONNECTED"
            return self.state

        raw_scan = self.provider.get_scan()
        if not raw_scan:
            return self.state

        scan = self.adapter.adapt(raw_scan)
        if not scan:
            return self.state

        # Filter valid points
        valid_points = [p for p in scan.points if scan.min_range <= p.distance <= scan.max_range]
        scan.points = valid_points

        self.state.latest_scan = scan
        self.state.timestamp = datetime.now()
        self.state.sensor_status = "CONNECTED"
        
        # Basic Obstacle Extraction (Simple naive clustering)
        # We'll just look for points that are close to each other.
        self._extract_obstacles(valid_points)
        
        return self.state

    def _extract_obstacles(self, points):
        """Very basic obstacle extraction for Phase 21."""
        if not points:
            self.state.obstacles = []
            return
            
        obstacles = []
        cluster_threshold = 0.5  # meters
        
        # We just group consecutive points that are close to each other.
        # This is a naive approach, assuming points are sorted by angle.
        current_cluster = []
        
        for p in points:
            if not current_cluster:
                current_cluster.append(p)
                continue
                
            last_p = current_cluster[-1]
            dist_to_last = math.hypot(p.x - last_p.x, p.y - last_p.y)
            
            if dist_to_last < cluster_threshold:
                current_cluster.append(p)
            else:
                if len(current_cluster) > 3: # Min points to be considered an obstacle
                    obstacles.append(self._create_obstacle(current_cluster))
                current_cluster = [p]
                
        # Check last cluster
        if len(current_cluster) > 3:
            # Handle wrap-around (end connects to beginning)
            first_p = points[0]
            last_p = current_cluster[-1]
            dist_to_first = math.hypot(first_p.x - last_p.x, first_p.y - last_p.y)
            if dist_to_first < cluster_threshold and len(obstacles) > 0:
                # Merge with first cluster (naive)
                pass # skip for simplicity
            else:
                obstacles.append(self._create_obstacle(current_cluster))
                
        self.state.obstacles = obstacles
        
    def _create_obstacle(self, cluster) -> Obstacle:
        # Center of cluster
        avg_x = sum(p.x for p in cluster) / len(cluster)
        avg_y = sum(p.y for p in cluster) / len(cluster)
        distance = math.hypot(avg_x, avg_y)
        
        # Estimate size
        max_dist = 0
        for p1 in cluster:
            for p2 in cluster:
                d = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if d > max_dist:
                    max_dist = d
                    
        return Obstacle(
            obstacle_id=f"obs_{uuid.uuid4().hex[:6]}",
            x=avg_x,
            y=avg_y,
            distance=distance,
            size_estimate=max_dist
        )
