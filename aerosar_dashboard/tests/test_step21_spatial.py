
import math
from app.models.spatial import LiDARPoint, LiDARScan, Obstacle
from app.spatial.adapter import LiDARAdapter
from app.spatial.service import SpatialService
from app.models.settings import Settings
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

def test_lidar_adapter_normalizes_data():
    adapter = LiDARAdapter()
    
    # 1. Cartesian data
    raw_cart = {
        "format": "cartesian",
        "points": [
            [1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0]
        ]
    }
    
    scan = adapter.adapt_scan(raw_cart, source="MOCK_TEST")
    assert len(scan.points) == 2
    assert scan.points[0].x == 1.0
    assert scan.points[0].y == 0.0
    assert scan.points[1].x == 0.0
    assert scan.points[1].y == 2.0
    
    # 2. Polar data (angle in degrees, distance in meters)
    raw_polar = {
        "format": "polar",
        "points": [
            {"angle": 0.0, "distance": 1.0}, # forward
            {"angle": 90.0, "distance": 2.0} # left
        ]
    }
    
    scan2 = adapter.adapt_scan(raw_polar, source="MOCK_TEST")
    assert len(scan2.points) == 2
    # 0 degrees is +x
    assert math.isclose(scan2.points[0].x, 1.0, abs_tol=1e-5)
    assert math.isclose(scan2.points[0].y, 0.0, abs_tol=1e-5)
    
    # 90 degrees is +y
    assert math.isclose(scan2.points[1].x, 0.0, abs_tol=1e-5)
    assert math.isclose(scan2.points[1].y, 2.0, abs_tol=1e-5)

def test_spatial_service_extracts_clustering_correctly():
    service = SpatialService(config=Settings().lidar)
    
    # Inject a scan with two clusters of points
    points = [
        # Cluster 1 around (2.0, 0.0)
        LiDARPoint(x=2.0, y=0.0, z=0.0, intensity=1.0),
        LiDARPoint(x=2.1, y=0.0, z=0.0, intensity=1.0),
        LiDARPoint(x=2.0, y=0.1, z=0.0, intensity=1.0),
        # Cluster 2 around (0.0, 3.0)
        LiDARPoint(x=0.0, y=3.0, z=0.0, intensity=1.0),
        LiDARPoint(x=0.0, y=3.1, z=0.0, intensity=1.0),
    ]
    scan = LiDARScan(points=points, source="TEST")
    
    obstacles = service._extract_obstacles(scan)
    
    # Should detect 2 obstacles
    assert len(obstacles) == 2
    
    # Verify the extracted obstacles roughly match the clusters
    dists = [obs.distance for obs in obstacles]
    dists.sort()
    
    assert math.isclose(dists[0], 2.0, abs_tol=0.2)
    assert math.isclose(dists[1], 3.0, abs_tol=0.2)

async def test_spatial_update_event_generation():
    # Clear the event bus
    events = []
    def event_callback(event_type, timestamp, mission_id, payload):
        events.append({"type": event_type, "payload": payload})
        
    event_bus.subscribe(EventType.SPATIAL_UPDATE, event_callback)
    
    # Generate the event
    spatial_payload = {
        "sensor_status": "CONNECTED",
        "obstacles_count": 2,
        "nearest_obstacle": 1.5
    }
    
    event_bus.publish(
        EventType.SPATIAL_UPDATE,
        payload=spatial_payload,
        mission_id="TEST_MISSION"
    )
    
    # Small delay for asyncio callback to execute
    import asyncio
    await asyncio.sleep(0.1)
    
    # Assert
    assert len(events) >= 1
    event = next((e for e in events if e["type"] == EventType.SPATIAL_UPDATE), None)
    assert event is not None
    assert event["payload"]["sensor_status"] == "CONNECTED"
    assert event["payload"]["obstacles_count"] == 2

if __name__ == "__main__":
    test_lidar_adapter_normalizes_data()
    test_spatial_service_extracts_clustering_correctly()
    import asyncio
    asyncio.run(test_spatial_update_event_generation())
    print("All tests passed!")
