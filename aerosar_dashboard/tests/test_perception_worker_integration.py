import unittest
from datetime import datetime
import numpy as np

from app.perception.qt_worker import PerceptionWorker
from app.models.detection import Detection, BoundingBox
from app.services.data_service import DataService
from app.perception.types import PerceptionStatus


class MockPerceptionService:
    def __init__(self, detections, frame=None):
        self._detections = detections
        self._frame = frame if frame is not None else np.zeros((10, 10, 3), dtype=np.uint8)
        self.status = PerceptionStatus()

    def run_once(self):
        return self._detections, self._frame


class TestPerceptionWorkerIntegration(unittest.TestCase):
    def test_worker_creates_and_persists_incidents(self):
        # Create 3 spatially separated detections (should produce 3 incidents)
        now = datetime.now()
        dets = []
        centers = [(0.1, 0.1), (0.5, 0.5), (0.9, 0.9)]
        for i, (cx, cy) in enumerate(centers):
            bbox = BoundingBox(x=cx, y=cy, width=0.05, height=0.05)
            det = Detection(
                detection_id=f"D{i}",
                frame_id=1,
                class_id=0,
                class_name="person",
                confidence=0.95,
                bbox=bbox,
                source="test",
                image_width=1280,
                image_height=720,
                timestamp=now
            )
            dets.append(det)

        mock_service = MockPerceptionService(dets)

        # Monkeypatch DataService.add_incident to capture calls
        ds = DataService()
        captured = []

        original_add = ds.add_incident
        original_log = ds.log_event

        try:
            def fake_add(incident, auto_create_event_and_report=True):
                captured.append(incident)

            ds.add_incident = fake_add
            ds.log_event = lambda *args, **kwargs: None

            worker = PerceptionWorker(service=mock_service)
            # enable worker loop (do not call start() to avoid real service.start())
            worker._running = True
            # run a single capture/process cycle
            worker.capture_and_process()

            # Expect 3 incidents created and passed to DataService
            self.assertEqual(len(captured), 3)
        finally:
            ds.add_incident = original_add
            ds.log_event = original_log


if __name__ == "__main__":
    unittest.main()
