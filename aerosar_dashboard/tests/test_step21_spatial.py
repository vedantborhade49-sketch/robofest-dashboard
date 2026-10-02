
import math
from app.models.spatial import LiDARPoint, LiDARScan, Obstacle
from app.spatial.adapter import LiDARAdapter
from app.spatial.service import SpatialService
from app.models.settings import DashboardSettings
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

def test_lidar_adapter_normalizes_data():
    adapter = LiDARAdapter()
    
    raw = {
        "id": "test_1",
        "timestamp": "2026-09-30T10:00:00",
        "measurements": [
            {"angle": 0.0, "distance": 1.0, "intensity": 100},
            {"angle": 1.57079632679, "distance": 2.0, "intensity": 200}
        ]
    }
    
    scan = adapter.adapt(raw)
    assert len(scan.points) == 2
    assert math.isclose(scan.points[0].x, 1.0, abs_tol=1e-5)
    assert math.isclose(scan.points[0].y, 0.0, abs_tol=1e-5)
    
    assert math.isclose(scan.points[1].x, 0.0, abs_tol=1e-5)
    assert math.isclose(scan.points[1].y, 2.0, abs_tol=1e-5)

def test_spatial_service_extracts_clustering_correctly():
    from tests.mocks.mock_lidar_provider import MockLiDARProvider
    service = SpatialService(provider=MockLiDARProvider())
    
    # Inject a scan with two clusters of points
    points = [
        # Cluster 1 around (2.0, 0.0) - needs 4 points minimum
        LiDARPoint(x=2.0, y=0.0, z=0.0, distance=2.0, angle=0.0, intensity=1.0),
        LiDARPoint(x=2.1, y=0.0, z=0.0, distance=2.1, angle=0.0, intensity=1.0),
        LiDARPoint(x=2.0, y=0.1, z=0.0, distance=2.0, angle=0.0, intensity=1.0),
        LiDARPoint(x=2.1, y=0.1, z=0.0, distance=2.1, angle=0.0, intensity=1.0),
        
        # gap
        LiDARPoint(x=10.0, y=10.0, z=0.0, distance=14.0, angle=0.5, intensity=1.0),
        
        # Cluster 2 around (0.0, 3.0) - needs 4 points minimum
        LiDARPoint(x=0.0, y=3.0, z=0.0, distance=3.0, angle=1.57, intensity=1.0),
        LiDARPoint(x=0.0, y=3.1, z=0.0, distance=3.1, angle=1.57, intensity=1.0),
        LiDARPoint(x=0.1, y=3.0, z=0.0, distance=3.0, angle=1.57, intensity=1.0),
        LiDARPoint(x=0.1, y=3.1, z=0.0, distance=3.1, angle=1.57, intensity=1.0),
        
        # another gap
        LiDARPoint(x=10.0, y=10.0, z=0.0, distance=14.0, angle=0.5, intensity=1.0),
    ]
    scan = LiDARScan(scan_id="test_1", points=points, source="TEST")
    
    # Notice that the new method takes points, not a scan
    service._extract_obstacles(points)
    obstacles = service.state.obstacles
    
    # Should detect 2 obstacles
    assert len(obstacles) == 2
    
    # Verify the extracted obstacles roughly match the clusters
    dists = [obs.distance for obs in obstacles]
    dists.sort()
    
    assert math.isclose(dists[0], 2.0, abs_tol=0.2)
    assert math.isclose(dists[1], 3.0, abs_tol=0.2)

import pytest


