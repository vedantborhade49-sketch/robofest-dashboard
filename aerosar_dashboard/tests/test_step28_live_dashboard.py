import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch

from app.services.data_service import DataService
from app.data.api_provider import APIDataProvider
from app.core.state_manager import StateManager
from app.models.telemetry import TelemetryState
from app.models.incident import Incident
from app.models.map import MapState

class TestStep28LiveDashboard(unittest.TestCase):
    def setUp(self):
        self.provider = APIDataProvider()
        # Prevent actually calling out to the internet
        self.provider.client = MagicMock()
        
        self.data_service = DataService()
        self.data_service.set_provider(self.provider)
        
        # Initialize state cleanly
        self.data_service.state_manager.initialize_from_provider(self.provider)
        
        # Mock realtime client connection
        self.data_service._realtime_client.connect_to_server = MagicMock()
        
    def tearDown(self):
        pass

    def test_api_provider_initialization(self):
        self.assertIsInstance(self.data_service._provider, APIDataProvider)
        
    def test_realtime_telemetry_routing(self):
        event_payload = {
            "flight": {
                "latitude": 34.0,
                "longitude": -118.0,
                "altitude": 100.5,
                "heading": 45.0,
                "speed": 10.0,
                "battery": 95.0,
                "signal": 100.0,
                "position": {"latitude": 34.0, "longitude": -118.0, "x": 0.0, "y": 0.0, "z": 100.5}
            }
        }
        
        event = {
            "event_type": "TELEMETRY_UPDATE",
            "payload": event_payload
        }
        
        self.data_service._on_realtime_event(event)
        
        telem = self.data_service.get_telemetry_data()
        self.assertIsNotNone(telem)
        self.assertEqual(telem.altitude, 100.5)
        
    def test_realtime_incident_routing(self):
        event_payload = {
            "incident": {
                "incident_id": "TEST-INC-1",
                "type": "person",
                "confidence": 0.99,
                "status": "NEW",
                "timestamp": "2026-10-01T00:00:00"
            }
        }
        
        event = {
            "event_type": "INCIDENT_CREATED",
            "payload": event_payload
        }
        
        self.data_service._on_realtime_event(event)
        
        incidents = self.data_service.get_incidents()
        self.assertTrue(any(i.incident_id == "TEST-INC-1" for i in incidents))
        
    def test_realtime_spatial_routing(self):
        event_payload = {
            "drone_position": {"latitude": 0.0, "longitude": 0.0, "x": 10.0, "y": 20.0, "z": 5.0}
        }
        
        event = {
            "event_type": "SPATIAL_UPDATE",
            "payload": event_payload
        }
        
        self.data_service._on_realtime_event(event)
        
        map_state = self.data_service.get_map_state()
        self.assertIsNotNone(map_state.drone_position)
        self.assertEqual(map_state.drone_position.x, 10.0)

if __name__ == "__main__":
    unittest.main()
