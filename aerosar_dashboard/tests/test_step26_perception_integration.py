import unittest
import time
from unittest.mock import MagicMock, patch

from app.onboard.config import OnboardConfig
from app.onboard.adapters import PerceptionAdapterService
from app.onboard.communication import CommunicationService
from app.onboard.buffer import OnboardEventBuffer
from app.services.incident_engine import IncidentEngine
from app.perception.camera import MockCameraSource

class TestStep26PerceptionIntegration(unittest.TestCase):
    def setUp(self):
        self.config = OnboardConfig(
            runtime_mode="development",
            camera_provider="mock",
            camera_fps=30,
            perception_interval_ms=100  # 10 fps
        )
        self.buffer = OnboardEventBuffer(db_path=":memory:")
        self.comms = CommunicationService(self.config, self.buffer)
        self.comms.initialize()
        
        self.incident_engine = IncidentEngine()
        
    def test_camera_provider_initialization(self):
        adapter = PerceptionAdapterService(self.config, self.comms, self.incident_engine)
        self.assertTrue(adapter.initialize())
        self.assertIsInstance(adapter.source, MockCameraSource)
        self.assertEqual(adapter.get_status(), "INITIALIZED")

    def test_perception_throttling_and_fps(self):
        adapter = PerceptionAdapterService(self.config, self.comms, self.incident_engine)
        adapter.initialize()
        
        # Start the adapter which starts the camera and inference loops
        adapter.start()
        self.assertEqual(adapter.get_status(), "RUNNING")
        
        # Let it run for just over 1 second to calculate FPS
        time.sleep(1.2)
        
        health = adapter.get_health()
        
        # Ensure FPS is being calculated
        self.assertIn("camera_fps", health)
        self.assertIn("inference_fps", health)
        
        # The mock camera pulls around 30 FPS due to config.camera_fps
        # The inference pulls around 10 FPS due to perception_interval_ms=100
        self.assertGreater(health["camera_fps"], 0)
        self.assertGreater(health["inference_fps"], 0)
        
        # Camera FPS should be higher than inference FPS (throttling works)
        self.assertGreater(health["camera_fps"], health["inference_fps"])
        
        adapter.stop()
        self.assertEqual(adapter.get_status(), "STOPPED")

    @patch('app.perception.perception_service.PerceptionService.process_single_frame')
    def test_incident_generation_and_sync(self, mock_process):
        # Mock the perception service to return a dummy detection
        from app.models.detection import Detection, BoundingBox
        from datetime import datetime
        
        dummy_det = Detection(
            detection_id="DET-001",
            class_name="person",
            confidence=0.9,
            bbox=BoundingBox(x1=10, y1=10, x2=100, y2=100),
            timestamp=datetime.utcnow()
        )
        mock_process.return_value = ([dummy_det], None)
        
        adapter = PerceptionAdapterService(self.config, self.comms, self.incident_engine)
        adapter.initialize()
        adapter.start()
        
        # Let inference loop run at least once
        time.sleep(0.3)
        
        # Buffer should contain an INCIDENT_CREATED event
        self.assertGreater(self.buffer.count(), 0)
        
        pending = self.buffer.retrieve_pending(limit=10)
        self.assertTrue(any(e["event_type"] == "INCIDENT_CREATED" for e in pending))
        
        adapter.stop()

if __name__ == "__main__":
    unittest.main()
