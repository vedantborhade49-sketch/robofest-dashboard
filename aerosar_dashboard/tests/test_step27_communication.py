import unittest
import time
from unittest.mock import MagicMock

from app.onboard.config import OnboardConfig
from app.onboard.buffer import OnboardEventBuffer
from app.onboard.communication import CommunicationService
from app.onboard.transports import LoopbackTransport
from app.models.communication import UAVMessage, DeliveryClass

class TestStep27Communication(unittest.TestCase):
    def setUp(self):
        self.config = OnboardConfig(
            communication_enabled=True,
            transport_type="loopback",
            vehicle_id="TEST-01",
            heartbeat_interval_ms=100,
            buffer_enabled=True
        )
        self.buffer = OnboardEventBuffer(db_path=":memory:")
        self.transport = LoopbackTransport()
        self.comms = CommunicationService(self.config, self.buffer, transport=self.transport)
        
    def test_message_envelope(self):
        msg = UAVMessage(
            message_type="TEST",
            sequence_number=1,
            payload={"data": 123}
        )
        self.assertEqual(msg.vehicle_id, "AEROSAR-01") # default
        self.assertEqual(msg.schema_version, "1.0")
        self.assertEqual(msg.delivery_class, DeliveryClass.BEST_EFFORT)
        
    def test_reliable_vs_best_effort(self):
        self.assertEqual(self.comms._get_delivery_class("INCIDENT_CREATED"), DeliveryClass.RELIABLE)
        self.assertEqual(self.comms._get_delivery_class("TELEMETRY_UPDATE"), DeliveryClass.BEST_EFFORT)

    def test_loopback_transport(self):
        self.transport.connect()
        self.assertTrue(self.transport.is_connected())
        
        msg = UAVMessage(message_type="PING", sequence_number=1, payload={})
        self.transport.send(msg)
        
        popped = self.transport.pop_sent()
        self.assertIsNotNone(popped)
        self.assertEqual(popped.message_type, "PING")

    def test_offline_buffering(self):
        # Mock connect before starting
        self.transport.connect = MagicMock(return_value=False)
        self.comms.start()
        
        time.sleep(0.2) # Sync loop runs
        
        self.assertFalse(self.comms.is_connected)
        
        # Send reliable event
        self.comms.send_event("INCIDENT_CREATED", {"id": 1})
        # Send best effort event
        self.comms.send_event("TELEMETRY_UPDATE", {"id": 2})
        
        # Both should be buffered because we are offline
        self.assertEqual(self.buffer.count(), 2)
        
        self.comms.stop()

    def test_sync_reconnect(self):
        self.comms.start()
        time.sleep(0.2) # Let sync loop connect
        self.assertTrue(self.comms.is_connected)
        
        # We manually insert something in buffer
        self.buffer.enqueue("INCIDENT_CREATED", {"id": 99})
        
        time.sleep(0.6) # Let sync loop drain it
        
        # It should send the reliable message and heartbeat
        sent_messages = []
        while True:
            m = self.transport.pop_sent()
            if not m:
                break
            sent_messages.append(m)
            
        # Should have Heartbeats and the INCIDENT_CREATED
        types = [m.message_type for m in sent_messages]
        self.assertIn("HEARTBEAT", types)
        self.assertIn("INCIDENT_CREATED", types)
        
        incident_msg = next(m for m in sent_messages if m.message_type == "INCIDENT_CREATED")
        
        # Now simulate ground station ACK
        ack_msg = UAVMessage(
            message_type="ACK",
            sequence_number=0,
            payload={"message_id": incident_msg.message_id}
        )
        self.transport.push_received(ack_msg)
        
        time.sleep(0.2) # Let receive loop process ACK
        
        # Buffer should be cleared
        self.assertEqual(self.buffer.count(), 0)
        
        self.comms.stop()

if __name__ == "__main__":
    unittest.main()
