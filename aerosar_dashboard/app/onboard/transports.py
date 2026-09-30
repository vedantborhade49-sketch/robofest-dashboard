import time
import logging
import json
import threading
import queue
from typing import Optional, Callable
import websocket

from app.models.communication import UAVMessage

logger = logging.getLogger(__name__)

class Transport:
    def connect(self) -> bool:
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def send(self, message: UAVMessage) -> bool:
        raise NotImplementedError

    def receive(self, timeout: float = 1.0) -> Optional[UAVMessage]:
        raise NotImplementedError

    def is_connected(self) -> bool:
        raise NotImplementedError


class LoopbackTransport(Transport):
    """Simulates a network connection locally without touching the network layer."""
    def __init__(self, simulate_latency: float = 0.0):
        self._connected = False
        self._latency = simulate_latency
        self._inbox = queue.Queue()
        self._outbox = queue.Queue()

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def send(self, message: UAVMessage) -> bool:
        if not self._connected:
            return False
        if self._latency > 0:
            time.sleep(self._latency)
        # In a real loopback, we might hook this directly to a mock server.
        # For tests, we just put it in the outbox.
        self._outbox.put(message)
        return True

    def receive(self, timeout: float = 1.0) -> Optional[UAVMessage]:
        if not self._connected:
            return None
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_connected(self) -> bool:
        return self._connected

    # Helpers for tests
    def pop_sent(self):
        try:
            return self._outbox.get_nowait()
        except queue.Empty:
            return None
            
    def push_received(self, msg: UAVMessage):
        self._inbox.put(msg)


class WebSocketTransport(Transport):
    """Real IP-based transport using WebSockets."""
    def __init__(self, url: str):
        self.url = url
        self.ws = None
        self._connected = False
        self._inbox = queue.Queue()
        self._thread = None
        self._running = False

    def connect(self) -> bool:
        if self._connected:
            return True
            
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            self._running = True
            self._thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self._thread.start()
            
            # Wait for open
            start = time.time()
            while not self._connected and time.time() - start < 5.0:
                time.sleep(0.1)
                
            return self._connected
        except Exception as e:
            logger.error(f"WebSocket connect error: {e}")
            return False

    def disconnect(self):
        self._running = False
        if self.ws:
            self.ws.close()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._connected = False

    def send(self, message: UAVMessage) -> bool:
        if not self._connected or not self.ws:
            return False
        try:
            # Serialize model
            payload = message.model_dump_json()
            self.ws.send(payload)
            return True
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            self._connected = False
            return False

    def receive(self, timeout: float = 1.0) -> Optional[UAVMessage]:
        if not self._connected:
            return None
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_connected(self) -> bool:
        return self._connected

    def _on_open(self, ws):
        logger.info(f"WebSocket connected to {self.url}")
        self._connected = True

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg = UAVMessage(**data)
            self._inbox.put(msg)
        except Exception as e:
            logger.error(f"WebSocket parsing error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        self._connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket closed")
        self._connected = False
