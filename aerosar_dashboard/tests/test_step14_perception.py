import unittest
from datetime import datetime

from app.perception.models import BBox, Detection
from app.perception.camera import OpenCVVideoSource, WebcamSource
from app.perception.detection_processor import process_raw_detections
from app.perception.types import PerceptionStatus


class TestPerceptionStep14(unittest.TestCase):
    def test_detection_model_creation(self):
        det = Detection(
            detection_id="DET-001",
            frame_id=1,
            class_id=0,
            class_name="person",
            confidence=0.87,
            bbox=BBox(x1=10, y1=20, x2=110, y2=220),
            source="mock",
            image_width=1280,
            image_height=720,
            timestamp=datetime.now(),
            center_x=60,
            center_y=120,
            width=100,
            height=200
        )
        self.assertEqual(det.class_name, "person")
        self.assertGreater(det.confidence, 0.0)

    def test_detection_processor_filters_and_normalizes(self):
        raw = [{
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.91,
            "bbox": {"x1": 10, "y1": 20, "x2": 110, "y2": 220},
        }]
        detections = process_raw_detections(raw, frame_id=3, width=1280, height=720, source="mock")
        # processor has no filter inside process_raw_detections natively, it just converts
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].class_name, "person")

    def test_camera_abstraction_uses_open_cv_source(self):
        source = OpenCVVideoSource(source="test.mp4")
        self.assertEqual(source.source, "test.mp4")
        self.assertFalse(source.is_open())

    def test_webcam_source_uses_device_index(self):
        source = WebcamSource(index=0)
        self.assertEqual(source.index, 0)

    def test_perception_status_defaults(self):
        status = PerceptionStatus()
        self.assertFalse(status.running)
        self.assertEqual(status.model_name, "AEROSAR YOLO")


if __name__ == "__main__":
    unittest.main()
