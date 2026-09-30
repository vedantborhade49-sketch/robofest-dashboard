import math
from datetime import datetime
from app.models.spatial import CameraGeometry, LiDARScan, LiDARPoint, SpatialState, Pose
from app.models.detection import Detection, BoundingBox
from app.spatial.locator import SpatialLocator, CameraToLiDARTransform
from app.incidents.incident_engine import IncidentEngine
import pytest

def test_camera_ray():
    geom = CameraGeometry(image_width=1280, image_height=720, fx=640.0, fy=640.0, cx=640.0, cy=360.0)
    locator = SpatialLocator(camera_geom=geom)
    
    # Center pixel
    rx, ry, rz = locator.get_camera_ray(640, 360)
    assert math.isclose(rx, 0.0, abs_tol=1e-5)
    assert math.isclose(ry, 0.0, abs_tol=1e-5)
    assert math.isclose(rz, 1.0, abs_tol=1e-5)

def test_transform_camera_to_lidar():
    transform = CameraToLiDARTransform()
    # Camera ray forward (Z axis in camera) -> should map to X in LiDAR
    lx, ly, lz = transform.camera_ray_to_lidar_ray(0.0, 0.0, 1.0)
    assert lx == 1.0
    assert ly == 0.0
    assert lz == 0.0

def test_lidar_association_and_range():
    locator = SpatialLocator()
    # Let target be exactly forward in LiDAR (x=1, y=0)
    ray = (1.0, 0.0, 0.0)
    
    points = [
        LiDARPoint(angle=0.01, distance=4.0, x=4.0, y=0.0),
        LiDARPoint(angle=-0.01, distance=4.2, x=4.2, y=0.0),
        LiDARPoint(angle=0.0, distance=4.1, x=4.1, y=0.0),
        LiDARPoint(angle=1.57, distance=2.0, x=0.0, y=2.0), # unrelated
    ]
    scan = LiDARScan(scan_id="scan-1", points=points, min_range=0.1, max_range=20.0)
    
    candidates = locator.associate_lidar(ray, scan)
    assert len(candidates) == 3
    
    rng, conf = locator.estimate_range(candidates)
    assert rng == 4.1
    assert conf == 3.0 / 5.0 # length=3, min(1.0, len/5)

def test_locate_target_with_map_transform():
    locator = SpatialLocator()
    
    points = [LiDARPoint(angle=0.0, distance=5.0, x=5.0, y=0.0)]
    scan = LiDARScan(scan_id="scan-2", points=points, min_range=0.1, max_range=20.0)
    
    pose = Pose(x=10.0, y=5.0, z=0.0, yaw=math.pi/2) # Facing left/north
    state = SpatialState(latest_scan=scan, current_pose=pose, slam_status="TRACKING")
    
    # Target center pixel
    base_t, map_t = locator.locate_target("tgt-1", 640.0, 360.0, state)
    
    assert base_t is not None
    assert math.isclose(base_t.x, 5.0, abs_tol=1e-5)
    
    assert map_t is not None
    # Drone at (10, 5), facing +Y (yaw = 90 deg). 
    # Base target is at (5, 0) relative to drone. So 5m ahead of drone.
    # Map target should be (10, 10).
    assert math.isclose(map_t.x, 10.0, abs_tol=1e-5)
    assert math.isclose(map_t.y, 10.0, abs_tol=1e-5)

def test_locate_target_slam_lost():
    locator = SpatialLocator()
    
    points = [LiDARPoint(angle=0.0, distance=5.0, x=5.0, y=0.0)]
    scan = LiDARScan(scan_id="scan-3", points=points)
    
    pose = Pose(x=10.0, y=5.0, z=0.0, yaw=0.0)
    state = SpatialState(latest_scan=scan, current_pose=pose, slam_status="LOST")
    
    base_t, map_t = locator.locate_target("tgt-1", 640.0, 360.0, state)
    
    assert base_t is not None
    assert map_t is None

def test_incident_engine_with_spatial_state():
    engine = IncidentEngine()
    
    det = Detection(
        detection_id="d1",
        timestamp=datetime.now(),
        frame_id=1,
        class_id=0,
        class_name="person",
        confidence=0.91,
        bbox=BoundingBox(x1=630, y1=300, x2=650, y2=420),
        source="camera",
        image_width=1280,
        image_height=720,
        center_x=640,
        center_y=360,
        width=20,
        height=120
    )
    
    points = [LiDARPoint(angle=0.0, distance=4.2, x=4.2, y=0.0)]
    scan = LiDARScan(scan_id="scan-4", points=points)
    pose = Pose(x=4.31 - 4.2, y=2.08, z=0.0, yaw=0.0) # simplify map matching
    state = SpatialState(latest_scan=scan, current_pose=pose, slam_status="TRACKING")
    
    incident = engine.process_detection(det, state)
    
    assert incident is not None
    assert incident.type == "PERSON_DETECTED"
    assert incident.spatial_status == "ESTIMATED"
    assert incident.range == 4.2
    assert math.isclose(incident.location.x, 4.31, abs_tol=0.1)
    
def test_incident_engine_without_spatial():
    engine = IncidentEngine()
    det = Detection(
        detection_id="d2", timestamp=datetime.now(), frame_id=2, class_id=0,
        class_name="person", confidence=0.91, bbox=BoundingBox(x1=630, y1=300, x2=650, y2=420),
        source="camera", image_width=1280, image_height=720, center_x=640, center_y=360,
        width=20, height=120
    )
    # SLAM LOST + LiDAR unavailable
    state = SpatialState(latest_scan=None, slam_status="LOST")
    
    incident = engine.process_detection(det, state)
    
    assert incident is not None
    assert incident.type == "PERSON_DETECTED"
    assert incident.spatial_status == "UNAVAILABLE"
    assert incident.location is None
    assert incident.range is None
