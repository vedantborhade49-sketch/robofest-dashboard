import unittest
from datetime import datetime, timedelta

from app.incidents.incident_engine import IncidentEngine
from app.models.detection import Detection, BoundingBox


def make_detection(class_name="person", conf=0.9, frame_id=1, w=1280, h=720, timestamp=None, x=0.5, y=0.5):
    return Detection(
        detection_id=f"D-{frame_id}",
        frame_id=frame_id,
        class_id=0,
        class_name=class_name,
        confidence=conf,
        bbox=BoundingBox(x=x, y=y, width=0.2, height=0.3),
        source="test",
        image_width=w,
        image_height=h,
        timestamp=timestamp or datetime.utcnow(),
    )


class TestIncidentEngine(unittest.TestCase):
    def test_person_detection_creates_incident(self):
        eng = IncidentEngine()
        det = make_detection()
        incs = eng.process_detections([det])
        self.assertEqual(len(incs), 1)
        inc = incs[0]
        self.assertEqual(inc.type, "PERSON_DETECTED")
        self.assertEqual(inc.status, "NEW")
        self.assertAlmostEqual(inc.confidence, det.confidence)

    def test_low_confidence_ignored(self):
        eng = IncidentEngine()
        det = make_detection(conf=0.1)
        incs = eng.process_detections([det])
        self.assertEqual(len(incs), 0)

    def test_duplicate_suppression(self):
        eng = IncidentEngine()
        t0 = datetime.utcnow()
        det1 = make_detection(timestamp=t0)
        det2 = make_detection(timestamp=t0 + timedelta(milliseconds=100))
        incs1 = eng.process_detections([det1])
        incs2 = eng.process_detections([det2])
        self.assertEqual(len(incs1), 1)
        # second should be suppressed -> zero created
        self.assertEqual(len(incs2), 0)

    def test_multiple_detections_create_multiple_incidents(self):
        eng = IncidentEngine()
        # create detections with separated centers to avoid duplicate suppression
        dets = [
            make_detection(frame_id=1, x=0.1, y=0.1),
            make_detection(frame_id=2, x=0.5, y=0.5),
            make_detection(frame_id=3, x=0.9, y=0.9),
        ]
        incs = eng.process_detections(dets)
        self.assertEqual(len(incs), 3)


if __name__ == "__main__":
    unittest.main()
