from datetime import datetime
import pytest
import numpy as np

from app.perception.models import CVResult, DetectionResult, BBox
from app.perception.types import NetworkFrame
from app.perception.processor import CVProcessor
from app.perception.insight_adapter import InsightAdapter
from app.perception.yolo_processor import YOLOProcessor


class DeterministicCVProcessor(CVProcessor):
    def __init__(self, fail: bool = False, detections: list = None):
        self.fail = fail
        self.detections = detections or []
        
    def process(self, frame: NetworkFrame) -> CVResult:
        result = CVResult(
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            model_name="TestCV",
            model_version="1.0"
        )
        
        if self.fail:
            result.error = "Simulated CV failure"
            return result
            
        result.detections = self.detections
        return result


def create_dummy_frame(frame_id=1):
    return NetworkFrame(
        frame_id=frame_id,
        timestamp=datetime.now(),
        image=np.zeros((480, 640, 3), dtype=np.uint8),
        camera_id="cam_test",
        metadata={}
    )


def test_empty_cv_result():
    # Test 1 — Empty CV result
    processor = DeterministicCVProcessor(detections=[])
    frame = create_dummy_frame()
    
    cv_result = processor.process(frame)
    assert not cv_result.error
    assert len(cv_result.detections) == 0
    
    # Adapter
    detections = InsightAdapter.to_detections(cv_result, frame)
    assert len(detections) == 0


def test_single_detection():
    # Test 2 — Single detection
    processor = DeterministicCVProcessor(detections=[
        DetectionResult(
            class_name="person",
            confidence=0.95,
            bbox=BBox(x1=10, y1=10, x2=50, y2=100)
        )
    ])
    frame = create_dummy_frame()
    
    cv_result = processor.process(frame)
    assert len(cv_result.detections) == 1
    
    det = cv_result.detections[0]
    assert det.class_name == "person"
    assert det.confidence == 0.95
    assert det.bbox.x1 == 10
    
    detections = InsightAdapter.to_detections(cv_result, frame)
    assert len(detections) == 1
    assert detections[0].class_name == "person"
    assert detections[0].confidence == 0.95


def test_multiple_detections():
    # Test 3 — Multiple detections
    processor = DeterministicCVProcessor(detections=[
        DetectionResult(class_name="person", confidence=0.9, bbox=BBox(x1=0, y1=0, x2=10, y2=10)),
        DetectionResult(class_name="car", confidence=0.8, bbox=BBox(x1=20, y1=20, x2=30, y2=30))
    ])
    frame = create_dummy_frame()
    
    cv_result = processor.process(frame)
    assert len(cv_result.detections) == 2
    
    detections = InsightAdapter.to_detections(cv_result, frame)
    assert len(detections) == 2


def test_adapter_and_provenance():
    # Test 4 & 5 — Adapter and Provenance
    processor = DeterministicCVProcessor(detections=[
        DetectionResult(class_name="drone", confidence=0.99, bbox=BBox(x1=5, y1=5, x2=15, y2=15))
    ])
    frame = create_dummy_frame(frame_id=42)
    
    cv_result = processor.process(frame)
    detections = InsightAdapter.to_detections(cv_result, frame)
    
    assert len(detections) == 1
    det = detections[0]
    
    # Provenance verification
    assert det.frame_id == 42
    assert det.timestamp == frame.timestamp
    assert det.source == "TestCV"
    
    # Check width/height computed correctly
    assert det.width == 10
    assert det.height == 10
    assert det.center_x == 10.0
    assert det.center_y == 10.0


def test_cv_exception_handled():
    # Test 6 — CV exception isolation
    processor = DeterministicCVProcessor(fail=True)
    frame = create_dummy_frame()
    
    cv_result = processor.process(frame)
    
    # TCP receiver would stay alive, result returns error rather than raising
    assert cv_result.error == "Simulated CV failure"
    assert len(cv_result.detections) == 0
    
    detections = InsightAdapter.to_detections(cv_result, frame)
    assert len(detections) == 0


def test_existing_yolo_compatibility():
    # Test 7 — Existing YOLO compatibility
    # Ensure the wrapper can be instantiated and conceptually processes frames
    # (Without relying on a fully trained YOLO model working in CI, we just verify the boundary)
    yolo_processor = YOLOProcessor(model_path="yolov8n.pt")
    assert isinstance(yolo_processor, CVProcessor)
    
    # For a missing/invalid frame, it should fail gracefully
    frame = create_dummy_frame()
    frame.image = None
    cv_result = yolo_processor.process(frame)
    assert cv_result.error is not None
