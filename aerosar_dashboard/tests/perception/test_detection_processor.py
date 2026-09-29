import unittest
from app.perception.detection_processor import process_raw_detections

class TestDetectionProcessor(unittest.TestCase):
    def test_process_single_detection(self):
        raw = [{
            'class_id': 0,
            'class_name': 'person',
            'confidence': 0.9,
            'bbox': {'x1': 10, 'y1': 20, 'x2': 110, 'y2': 220}
        }]
        dets = process_raw_detections(raw, frame_id=1, width=1280, height=720, source='camera')
        self.assertEqual(len(dets), 1)
        d = dets[0]
        self.assertEqual(d.class_name, 'person')
        self.assertAlmostEqual(d.center_x, 60.0)
