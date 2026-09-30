import logging
import threading
import time
import requests
from typing import Dict, Any, Optional

from app.onboard.service_manager import OnboardService
from app.onboard.buffer import OnboardEventBuffer
from app.onboard.config import OnboardConfig

logger = logging.getLogger(__name__)

class CommunicationService(OnboardService):
    """
    Handles communication between the onboard Raspberry Pi and the ground station.
    Features offline-first behavior using the OnboardEventBuffer.
    """
    def __init__(self, config: OnboardConfig, event_buffer: OnboardEventBuffer):
        self.config = config
        self.buffer = event_buffer
        self._running = False
        self._sync_thread = None
        self._status = "INIT"
        
        # Determine actual state dynamically
        self.is_connected = False
        self._last_success = 0.0

    def initialize(self) -> bool:
        self._status = "INITIALIZED"
        return True

    def start(self):
        self._running = True
        self._status = "RUNNING"
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()

    def stop(self):
        self._running = False
        self._status = "STOPPING"
        if self._sync_thread:
            self._sync_thread.join(timeout=2.0)
        self._status = "STOPPED"

    def get_status(self) -> str:
        if not self._running:
            return self._status
        return "CONNECTED" if self.is_connected else "OFFLINE"

    def get_health(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected,
            "buffered_events": self.buffer.count(),
            "last_success_age": time.time() - self._last_success if self._last_success else -1
        }

    def send_event(self, event_type: str, payload: Dict[str, Any], force_sync: bool = False):
        """
        Primary interface to send data to the ground station.
        If offline, it buffers. If online, it may buffer and sync immediately.
        """
        if self.config.buffer_enabled:
            # Always buffer first for reliability
            self.buffer.enqueue(event_type, payload)
        else:
            # Fire and forget if buffer disabled (not recommended)
            if self.is_connected or force_sync:
                self._post_to_ground(event_type, payload)

    def _sync_loop(self):
        """Background thread that continuously tries to flush the buffer to the ground station."""
        while self._running:
            if self.config.communication_mode == "offline":
                self.is_connected = False
                time.sleep(2.0)
                continue
                
            # Check connection with a simple health ping
            self._check_connection()
            
            if self.is_connected:
                # We are online, drain buffer
                pending = self.buffer.retrieve_pending(limit=20)
                if pending:
                    success_ids = []
                    for event in pending:
                        if self._post_to_ground(event["event_type"], event["payload"]):
                            success_ids.append(event["id"])
                        else:
                            # Failed to post, probably connection lost again
                            self.is_connected = False
                            break
                            
                    if success_ids:
                        self.buffer.mark_sent(success_ids)
                else:
                    # Nothing to send, idle
                    time.sleep(0.5)
            else:
                # Offline, wait before retrying
                time.sleep(2.0)

    def _check_connection(self):
        try:
            url = f"{self.config.ground_station_url}/api/v1/system/health"
            response = requests.get(url, timeout=1.0)
            if response.status_code == 200:
                self.is_connected = True
                self._last_success = time.time()
                return
        except requests.RequestException:
            pass
        self.is_connected = False

    def _post_to_ground(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Helper to actually send the HTTP POST."""
        try:
            # We use a generic event ingest endpoint or specific ones based on type
            # For this step, we can use a generic onboard ingest endpoint that we will create
            url = f"{self.config.ground_station_url}/api/v1/onboard/ingest"
            
            wrapper = {
                "event_type": event_type,
                "payload": payload,
                "timestamp": time.time()
            }
            
            response = requests.post(url, json=wrapper, timeout=2.0)
            if response.status_code in [200, 201, 202]:
                self._last_success = time.time()
                return True
            return False
        except requests.RequestException:
            return False
