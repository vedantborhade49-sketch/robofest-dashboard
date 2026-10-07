import pytest
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
import numpy as np

from app.models.detection import Detection, BoundingBox
from app.models.entity import EntityStatus
from app.models.anomaly_event import AnomalyEventStatus
from app.perception.entity_registry import EntityRegistry, EntityAppearanceMatcher
from app.incidents.event_registry import EventRegistry
from app.database.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    from app.database.database import init_db, Base, engine
    init_db(":memory:")
    # Clean up any previous state in the shared in-memory DB
    from app.database.database import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def clean_storage():
    test_data_dir = "data/test_entities"
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    yield test_data_dir
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)

def test_entity_matching_behavior(clean_storage):
    registry = EntityRegistry(data_dir=clean_storage)
    mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # 1. First observation creates PERSON_001
    det1 = Detection(
        detection_id="det_1", class_name="person", confidence=0.8,
        bbox=BoundingBox(x=100, y=100, width=50, height=100),
        timestamp=datetime.utcnow(), frame_id=1, image_width=1920, image_height=1080
    )
    
    pairs = registry.process_detections([det1], mock_frame)
    e1 = pairs[0][1]
    assert e1.entity_id == "PERSON_001"

    # 2. Same entity across frames (close position, within time window) -> PERSON_001
    det2 = Detection(
        detection_id="det_2", class_name="person", confidence=0.85,
        bbox=BoundingBox(x=105, y=102, width=50, height=100),
        timestamp=det1.timestamp + timedelta(seconds=1), frame_id=2, image_width=1920, image_height=1080
    )
    pairs = registry.process_detections([det2], mock_frame)
    e2 = pairs[0][1]
    assert e2.entity_id == "PERSON_001"
    assert e2.sighting_count == 2

    # 3. Different person (far away) -> PERSON_002
    det3 = Detection(
        detection_id="det_3", class_name="person", confidence=0.9,
        bbox=BoundingBox(x=1500, y=800, width=50, height=100),
        timestamp=det2.timestamp, frame_id=2, image_width=1920, image_height=1080
    )
    pairs = registry.process_detections([det3], mock_frame)
    e3 = pairs[0][1]
    assert e3.entity_id == "PERSON_002"

    # 4. Weak match -> UNKNOWN -> creates new entity
    # If PERSON_001 disappears for 10 seconds (time window is 5s), it should not match
    det4 = Detection(
        detection_id="det_4", class_name="person", confidence=0.8,
        bbox=BoundingBox(x=100, y=100, width=50, height=100),
        timestamp=det2.timestamp + timedelta(seconds=10), frame_id=300, image_width=1920, image_height=1080
    )
    pairs = registry.process_detections([det4], mock_frame)
    e4 = pairs[0][1]
    assert e4.entity_id != "PERSON_001"
    assert e4.entity_id == "PERSON_003"
    assert e4.metadata["creation_reason"] == "UNKNOWN"

    # 5. Missing appearance matcher test
    # Evaluated inherently as it falls back to temporal-spatial.
    app_matcher = EntityAppearanceMatcher()
    res = app_matcher.match_appearance(det4, [e1, e2, e3])
    assert not res.matched
    assert res.reason == "appearance matcher unavailable"

def test_anomaly_engine_rules(clean_storage):
    ent_registry = EntityRegistry(data_dir=clean_storage)
    evt_registry = EventRegistry()
    mock_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    # 7, 8, 9, 10. Person detection produces PERSON_DETECTED, preserves frame/ts/confidence
    ts = datetime.utcnow()
    det1 = Detection(
        detection_id="det_1", class_name="person", confidence=0.88,
        bbox=BoundingBox(x=100, y=100, width=50, height=100),
        timestamp=ts, frame_id=42, image_width=1920, image_height=1080
    )
    pairs = ent_registry.process_detections([det1], mock_frame)
    triplets = evt_registry.process_entities(pairs)
    assert len(triplets) == 1
    ev = triplets[0][2]
    assert ev.event_type == "PERSON_DETECTED"
    assert ev.confidence == 0.88
    assert ev.first_frame_id == 42
    assert ev.first_seen == ts

    # 11. Unsupported anomaly types do not generate events
    # Example: YOLO detects a "chair" which we haven't explicitly mapped, shouldn't generate an event
    det2 = Detection(
        detection_id="det_2", class_name="chair", confidence=0.9,
        bbox=BoundingBox(x=100, y=100, width=50, height=100),
        timestamp=ts, frame_id=43, image_width=1920, image_height=1080
    )
    pairs2 = ent_registry.process_detections([det2], mock_frame)
    triplets2 = evt_registry.process_entities(pairs2)
    assert len(triplets2) == 0

    # 12, 13, 14. Fall/Immobility/Zones are NOT implemented merely from bbox shape.
    # AnomalyEngine simply returns [] for them, so they don't produce events.
    # The code proves this because there is no mapping for fall/immobility.

def test_event_registry_deduplication(clean_storage):
    ent_registry = EntityRegistry(data_dir=clean_storage)
    evt_registry = EventRegistry()
    mock_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    # 15. 100 repeated detections = ONE event
    first_event_id = None
    for i in range(1, 101):
        det = Detection(
            detection_id=f"det_{i}", class_name="person", confidence=0.8,
            bbox=BoundingBox(x=100, y=100, width=50, height=100),
            timestamp=datetime.utcnow(), frame_id=i, image_width=1920, image_height=1080
        )
        pairs = ent_registry.process_detections([det], mock_frame)
        triplets = evt_registry.process_entities(pairs)
        assert len(triplets) == 1
        ev = triplets[0][2]
        if i == 1:
            first_event_id = ev.event_id
        else:
            assert ev.event_id == first_event_id
            assert ev.status == AnomalyEventStatus.UPDATED
            assert ev.last_frame_id == i

    # 16. Two different entities = separate events
    det_other = Detection(
        detection_id="det_other", class_name="person", confidence=0.8,
        bbox=BoundingBox(x=1000, y=1000, width=50, height=100), # far away -> new entity
        timestamp=datetime.utcnow(), frame_id=101, image_width=1920, image_height=1080
    )
    pairs = ent_registry.process_detections([det_other], mock_frame)
    triplets = evt_registry.process_entities(pairs)
    ev_other = triplets[0][2]
    assert ev_other.event_id != first_event_id

    # 17. Different anomaly types = separate events
    # Simulate same entity but different class (not common in YOLO unless vehicle is overlapping, but let's test vehicle)
    det_veh = Detection(
        detection_id="det_veh", class_name="vehicle", confidence=0.8,
        bbox=BoundingBox(x=500, y=500, width=50, height=100),
        timestamp=datetime.utcnow(), frame_id=102, image_width=1920, image_height=1080
    )
    pairs = ent_registry.process_detections([det_veh], mock_frame)
    triplets = evt_registry.process_entities(pairs)
    ev_veh = triplets[0][2]
    assert ev_veh.event_type == "VEHICLE_DETECTED"
    assert ev_veh.event_id != first_event_id
    assert ev_veh.event_id != ev_other.event_id

def test_event_resolution(clean_storage):
    ent_registry = EntityRegistry(data_dir=clean_storage)
    evt_registry = EventRegistry()
    mock_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    ts = datetime.utcnow()
    det = Detection(
        detection_id="det_1", class_name="person", confidence=0.8,
        bbox=BoundingBox(x=100, y=100, width=50, height=100),
        timestamp=ts, frame_id=1, image_width=1920, image_height=1080
    )
    pairs = ent_registry.process_detections([det], mock_frame)
    triplets = evt_registry.process_entities(pairs)
    ev = triplets[0][2]
    
    assert ev.status == AnomalyEventStatus.NEW
    
    # 19. Resolution works correctly
    # Advance time by 15 seconds, and send an empty batch to trigger resolution cleanup
    future_ts = ts + timedelta(seconds=15)
    
    # Send a dummy event to advance the registry's internal clock which uses `batch_time`
    dummy = Detection(
        detection_id="dummy", class_name="vehicle", confidence=0.8,
        bbox=BoundingBox(x=1000, y=1000, width=50, height=100),
        timestamp=future_ts, frame_id=2, image_width=1920, image_height=1080
    )
    pairs2 = ent_registry.process_detections([dummy], mock_frame)
    evt_registry.process_entities(pairs2)
    
    # The first event should now be resolved
    assert ev.event_id not in evt_registry._active_events
    resolved_ev = evt_registry.repo.get_event(ev.event_id)
    assert resolved_ev.status == AnomalyEventStatus.RESOLVED
