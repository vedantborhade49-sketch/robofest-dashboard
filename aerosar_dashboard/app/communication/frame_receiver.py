import socket
import struct
import threading
import time
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
import cv2
import numpy as np

from app.communication.frame_protocol import FramePacket, HEADER_SIZE
from app.perception.types import NetworkFrame

logger = logging.getLogger(__name__)

class ConnectionState:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECEIVING = "RECEIVING"
    ERROR = "ERROR"

class FrameReceiver:
    def __init__(self, host: str, port: int, reconnect_delay: float = 2.0, frame_timeout: float = 2.0):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.frame_timeout = frame_timeout
        
        self.state = ConnectionState.DISCONNECTED
        self._running = False
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self._latest_network_frame: Optional[NetworkFrame] = None
        
        # Metrics
        self.received_frames = 0
        self.dropped_frames = 0
        self.decode_failures = 0
        self.last_frame_time = 0.0
        self.received_fps = 0.0
        
        self._fps_counter = 0
        self._fps_timer = time.time()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True, name="FrameReceiverWorker")
        self._thread.start()
        logger.info(f"FrameReceiver started for {self.host}:{self.port}")

    def stop(self):
        if not self._running:
            return
        self._running = False
        
        if self._thread and self._thread.is_alive():
            # The receive loop has a 1.0s timeout, so it will break naturally.
            self._thread.join(timeout=2.0)
            
        self.state = ConnectionState.DISCONNECTED
        logger.info("FrameReceiver stopped")

    def get_latest_frame(self) -> Optional[NetworkFrame]:
        # Timeout handling
        if self.state == ConnectionState.RECEIVING and (time.time() - self.last_frame_time > self.frame_timeout):
            logger.warning("Frame timeout. Transitioning to CONNECTED (no valid stream).")
            self.state = ConnectionState.CONNECTED

        with self._lock:
            return self._latest_network_frame

    def _receive_loop(self):
        while self._running:
            self._connect()
            if not self._running:
                break
                
            buffer = bytearray()
            while self._running and self.state in (ConnectionState.CONNECTED, ConnectionState.RECEIVING):
                try:
                    chunk = self._socket.recv(8192)
                    if not chunk:
                        logger.warning("Connection lost (empty read)")
                        break
                    buffer.extend(chunk)
                    
                    self._process_buffer(buffer)
                except (socket.timeout, BlockingIOError):
                    # Check for timeout manually as well
                    if self.state == ConnectionState.RECEIVING and (time.time() - self.last_frame_time > self.frame_timeout):
                        self.state = ConnectionState.CONNECTED
                    continue
                except Exception as e:
                    logger.error(f"Error receiving data: {e}")
                    break
                    
            if self._socket:
                try:
                    self._socket.close()
                except Exception as e:
                    logger.debug(f"Error during socket cleanup: {e}")
                self._socket = None
                
            self.state = ConnectionState.DISCONNECTED
            if self._running:
                time.sleep(self.reconnect_delay)

    def _connect(self):
        self.state = ConnectionState.CONNECTING
        logger.info(f"Attempting connection to {self.host}:{self.port}...")
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(1.0) # Small timeout to avoid blocking forever on recv
            self._socket.connect((self.host, self.port))
            # Increase buffer sizes for high throughput
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)
            self.state = ConnectionState.CONNECTED
            logger.info("Connected to camera stream")
        except Exception as e:
            logger.debug(f"Connection failed: {e}")
            self.state = ConnectionState.ERROR
            if self._socket:
                self._socket.close()
                self._socket = None

    def _process_buffer(self, buffer: bytearray):
        while len(buffer) >= HEADER_SIZE:
            header_bytes = bytes(buffer[:HEADER_SIZE])
            try:
                meta = FramePacket.deserialize_header(header_bytes)
            except ValueError as e:
                logger.warning(f"Protocol error: {e}")
                del buffer[:1] # Try to slide window if desynced
                continue
                
            if meta is None:
                # Should not happen as we checked length
                return

            payload_size = meta["payload_size"]
            if payload_size > 10 * 1024 * 1024 or payload_size <= 0:  # 10MB sanity limit
                logger.warning(f"Payload size {payload_size} invalid, dropping 1 byte sync")
                del buffer[:1]
                continue
                
            total_size = HEADER_SIZE + payload_size
            if len(buffer) < total_size:
                # Need more data
                return
                
            payload = bytes(buffer[HEADER_SIZE:total_size])
            del buffer[:total_size]
            
            self._handle_frame(meta, payload)

    def _handle_frame(self, meta: dict, payload: bytes):
        now = time.time()
        self.received_frames += 1
        self._fps_counter += 1
        
        if now - self._fps_timer >= 1.0:
            self.received_fps = self._fps_counter / (now - self._fps_timer)
            self._fps_counter = 0
            self._fps_timer = now

        # Decode image
        np_arr = np.frombuffer(payload, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None or frame.size == 0 or frame.ndim != 3:
            self.decode_failures += 1
            logger.debug("Failed to decode JPEG frame")
            return
            
        self.state = ConnectionState.RECEIVING

        # Build NetworkFrame
        dt_timestamp = datetime.fromtimestamp(meta["timestamp_ms"] / 1000.0, tz=timezone.utc)
        network_frame = NetworkFrame(
            frame_id=meta["frame_id"],
            timestamp=dt_timestamp,
            image=frame,
            metadata=meta
        )

        with self._lock:
            if self._latest_network_frame is not None:
                self.dropped_frames += 1
            self._latest_network_frame = network_frame
            self.last_frame_time = now
