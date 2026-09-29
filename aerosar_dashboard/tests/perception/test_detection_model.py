import unittest
from datetime import datetime
from app.perception.models import Detection, BBox

class TestDetectionModel(unittest.TestCase):
    def test_bbox_and_detection_creation(self):
        bb = BBox(x1=10, y1=20, x2=110, y2=220)
        det = Detection(
            detection_id='D-1',
            timestamp=datetime.utcnow(),
            frame_id=1,
            class_id=0,
            class_name='person',
            confidence=0.87,
            bbox=bb,
            source='test',
            image_width=1280,
            image_height=720
        )
        self.assertEqual(det.bbox.x1, 10)
        self.assertEqual(det.class_name, 'person')
