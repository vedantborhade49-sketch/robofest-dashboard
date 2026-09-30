import unittest
import time
from unittest.mock import MagicMock, patch

from app.onboard.config import OnboardConfig
from app.onboard.buffer import OnboardEventBuffer
from app.onboard.health import SystemHealthMonitor
from app.onboard.service_manager import ServiceManager
from app.onboard.communication import CommunicationService
from app.onboard.runtime import OnboardRuntime
from app.models.onboard import OnboardStatus

class TestStep25Onboard(unittest.TestCase):
    def setUp(self):
        self.config = OnboardConfig(
            runtime_mode="development",
            buffer_enabled=True,
            health_monitor_interval_ms=100
        )
        # Use an in-memory db for testing buffer
        self.buffer = OnboardEventBuffer(db_path=":memory:")

    def test_buffer_enqueue_retrieve_mark_sent(self):
        # Enqueue
        self.assertTrue(self.buffer.enqueue("TEST_EVENT", {"key": "value1"}))
        self.assertTrue(self.buffer.enqueue("TEST_EVENT", {"key": "value2"}))
        
        self.assertEqual(self.buffer.count(), 2)
        
        # Retrieve
        pending = self.buffer.retrieve_pending(limit=5)
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["payload"]["key"], "value1")
        
        # Mark sent
        self.buffer.mark_sent([pending[0]["id"]])
        self.assertEqual(self.buffer.count(), 1)
        
        # Clear
        self.buffer.clear()
        self.assertEqual(self.buffer.count(), 0)

    def test_health_monitor(self):
        monitor = SystemHealthMonitor()
        report = monitor.get_health_report()
        
        self.assertIn("cpu_percent", report)
        self.assertIn("memory_percent", report)
        self.assertIn("disk_percent", report)
        self.assertIn("temperature_c", report)

    def test_service_manager_lifecycle(self):
        manager = ServiceManager()
        
        mock_service = MagicMock()
        mock_service.initialize.return_value = True
        mock_service.get_status.return_value = "RUNNING"
        
        manager.register_service("mock", mock_service)
        
        manager.initialize_all()
        self.assertEqual(manager.statuses["mock"], "INITIALIZED")
        
        manager.start_all()
        self.assertEqual(manager.statuses["mock"], "RUNNING")
        
        statuses = manager.get_all_statuses()
        self.assertEqual(statuses["mock"], "RUNNING")
        
        manager.stop_all()
        self.assertEqual(manager.statuses["mock"], "STOPPED")

    @patch('app.onboard.communication.requests.post')
    @patch('app.onboard.communication.requests.get')
    def test_communication_offline_buffer(self, mock_get, mock_post):
        # Simulate offline
        mock_get.return_value.status_code = 500
        mock_post.return_value.status_code = 500
        
        comms = CommunicationService(self.config, self.buffer)
        comms.initialize()
        comms.start()
        
        comms.send_event("TEST", {"data": 123})
        
        time.sleep(0.1) # Let sync loop run
        
        self.assertFalse(comms.is_connected)
        self.assertEqual(self.buffer.count(), 1)
        
        comms.stop()

    def test_runtime_startup_shutdown(self):
        runtime = OnboardRuntime(self.config)
        runtime.buffer = self.buffer # Inject memory buffer
        
        runtime.start()
        status: OnboardStatus = runtime.get_status()
        self.assertEqual(status.state, "RUNNING")
        
        runtime.stop()
        status: OnboardStatus = runtime.get_status()
        self.assertEqual(status.state, "STOPPED")

if __name__ == "__main__":
    unittest.main()
