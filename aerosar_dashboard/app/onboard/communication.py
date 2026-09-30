import logging
import threading
import time
from typing import Dict, Any, Optional

from app.onboard.service_manager import OnboardService
from app.onboard.buffer import OnboardEventBuffer
from app.onboard.config import OnboardConfig
from app.models.communication import UAVMessage, DeliveryClass
from app.onboard.transports import Transport, LoopbackTransport, WebSocketTransport

logger = logging.getLogger(__name__)

class CommunicationService(OnboardService):
    """
    Handles communication between the onboard Raspberry Pi and the ground station
    using transport abstractions (WebSocket/Loopback).
    Features offline-first behavior using the OnboardEventBuffer and reliable ACKs.
    """
    def __init__(self, config: OnboardConfig, event_buffer: OnboardEventBuffer, transport: Optional[Transport] = None):
        self.config = config
        self.buffer = event_buffer
        
        if transport:
            self.transport = transport
        elif self.config.transport_type == "loopback":
            self.transport = LoopbackTransport()
        else:
            self.transport = WebSocketTransport(self.config.ground_station_ws_url)
            
        self._running = False
        self._sync_thread = None
        self._receive_thread = None
        self._status = "INIT"
        
        self.is_connected = False
        self._last_success = 0.0
        self._sequence = 0
        
        self._unacked_messages = {} # message_id -> buffer_id

    def initialize(self) -> bool:
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._sync_thread.start()
        self._receive_thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        self.transport.disconnect()
        if self._sync_thread:
            self._sync_thread.join(timeout=2.0)
        if self._receive_thread:
            self._receive_thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        if not self._running:
            return self._status
        return "CONNECTED" if self.is_connected else "OFFLINE"

    def get_health(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected,
            "buffered_events": self.buffer.count(),
            "last_success_age": time.time() - self._last_success if self._last_success else -1,
            "sequence": self._sequence
        }

    def _get_delivery_class(self, event_type: str) -> DeliveryClass:
        reliable_events = ["INCIDENT_CREATED", "INCIDENT_UPDATED", "SYSTEM_EVENT", "REPORT_GENERATED"]
        if event_type in reliable_events:
            return DeliveryClass.RELIABLE
        return DeliveryClass.BEST_EFFORT

    def send_event(self, event_type: str, payload: Dict[str, Any], force_sync: bool = False):
        """Primary interface to send data to the ground station."""
        if not self.config.communication_enabled:
            return
            
        delivery = self._get_delivery_class(event_type)
        
        buffer_id = None
        if self.config.buffer_enabled:
            # We buffer RELIABLE always, BEST_EFFORT only if offline
            if delivery == DeliveryClass.RELIABLE or not self.is_connected:
                # Assuming enqueue returns True/False, we need the buffer ID if reliable
                # Wait, buffer currently returns bool. We should just let sync loop handle RELIABLE.
                self.buffer.enqueue(event_type, payload)
                if delivery == DeliveryClass.RELIABLE:
                    return # Sync loop will handle sending it

        # If it's BEST_EFFORT and we are online, send it directly
        if self.is_connected and delivery == DeliveryClass.BEST_EFFORT:
            self._sequence += 1
            msg = UAVMessage(
                vehicle_id=self.config.vehicle_id,
                mission_id=self.config.mission_id,
                message_type=event_type,
                sequence_number=self._sequence,
                delivery_class=delivery,
                payload=payload
            )
            if self.transport.send(msg):
                self._last_success = time.time()

    def _sync_loop(self):
        """Background thread for heartbeat, reconnection, and buffer syncing."""
        heartbeat_interval = self.config.heartbeat_interval_ms / 1000.0
        last_heartbeat = 0.0
        
        while self._running:
            if not self.config.communication_enabled:
                time.sleep(2.0)
                continue
                
            if not self.transport.is_connected():
                self.is_connected = False
                logger.debug("Attempting to connect transport...")
                if self.transport.connect():
                    self.is_connected = True
                    self._last_success = time.time()
                    # Send an initial SYNC event or HEARTBEAT
                    self._send_heartbeat()
                    last_heartbeat = time.time()
                else:
                    time.sleep(2.0)
                    continue

            # We are connected
            now = time.time()
            if now - last_heartbeat >= heartbeat_interval:
                self._send_heartbeat()
                last_heartbeat = now
                
            # Drain buffer
            pending = self.buffer.retrieve_pending(limit=20)
            if pending:
                success_ids = []
                for event in pending:
                    self._sequence += 1
                    msg = UAVMessage(
                        vehicle_id=self.config.vehicle_id,
                        mission_id=self.config.mission_id,
                        message_type=event["event_type"],
                        sequence_number=self._sequence,
                        delivery_class=DeliveryClass.RELIABLE,
                        payload=event["payload"]
                    )
                    
                    if self.transport.send(msg):
                        self._last_success = time.time()
                        self._unacked_messages[msg.message_id] = event["id"]
                    else:
                        self.is_connected = False
                        break
                        
            time.sleep(0.5)

    def _receive_loop(self):
        """Background thread to receive ACKs and incoming commands."""
        while self._running:
            if not self.transport.is_connected():
                time.sleep(1.0)
                continue
                
            msg = self.transport.receive(timeout=1.0)
            if msg:
                self._last_success = time.time()
                if msg.message_type == "ACK":
                    acked_id = msg.payload.get("message_id")
                    if acked_id in self._unacked_messages:
                        buffer_id = self._unacked_messages.pop(acked_id)
                        self.buffer.mark_sent([buffer_id])
                # In the future, process incoming commands here

    def _send_heartbeat(self):
        self._sequence += 1
        msg = UAVMessage(
            vehicle_id=self.config.vehicle_id,
            mission_id=self.config.mission_id,
            message_type="HEARTBEAT",
            sequence_number=self._sequence,
            delivery_class=DeliveryClass.BEST_EFFORT,
            payload={"status": self.get_status()}
        )
        if self.transport.send(msg):
            self._last_success = time.time()
        else:
            self.is_connected = False
