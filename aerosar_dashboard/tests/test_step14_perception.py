import unittest
from datetime import datetime

from app.models.detection import BoundingBox, Detection
from app.perception.camera import OpenCVVideoSource, WebcamSource
from app.perception.detection_processor import DetectionProcessor
from app.perception.types import PerceptionStatus


class TestPerceptionStep14(unittest.TestCase):
    def test_detection_model_creation(self):
        det = Detection(
            detection_id="DET-001",
            frame_id=1,
            class_id=0,
            class_name="person",
            confidence=0.87,
            bbox=BoundingBox(x1=10, y1=20, x2=110, y2=220),
            source="mock",
            image_width=1280,
            image_height=720,
            timestamp=datetime.now(),
        )
        self.assertEqual(det.class_name, "person")
        self.assertGreater(det.confidence, 0.0)

    def test_bbox_validation(self):
        det = BoundingBox(x1=5, y1=6, x2=15, y2=20)
        self.assertEqual(det.width, 10)
        self.assertEqual(det.height, 14)

    def test_detection_processor_filters_and_normalizes(self):
        processor = DetectionProcessor(confidence_threshold=0.5)
        raw = [{
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.91,
            "bbox": {"x1": 10, "y1": 20, "x2": 110, "y2": 220},
        }]
        detections = processor.process(raw, frame_id=3, source="mock", image_width=1280, image_height=720)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].class_name, "person")

    def test_low_confidence_is_filtered(self):
        processor = DetectionProcessor(confidence_threshold=0.8)
        raw = [{
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.2,
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        }]
        detections = processor.process(raw, frame_id=4, source="mock", image_width=640, image_height=480)
        self.assertEqual(len(detections), 0)

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
