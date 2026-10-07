import socket
import time
import threading
import logging
import cv2
import numpy as np
from typing import Optional

from app.communication.frame_protocol import FramePacket

logger = logging.getLogger(__name__)

class FrameSender:
    """
    Sends frames over TCP using the AEROSAR frame protocol.
    Can be used on PC for local development or on Raspberry Pi.
    """
    def __init__(self, host: str = "0.0.0.0", port: int = 5000, camera_id: str = "camera_1", jpeg_quality: int = 80):
        self.host = host
        self.port = port
        self.camera_id = camera_id
        self.jpeg_quality = jpeg_quality
        
        self._running = False
        self._server_socket: Optional[socket.socket] = None
        self._client_socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._frame_id = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._server_loop, daemon=True, name="FrameSenderWorker")
        self._thread.start()
        logger.info(f"FrameSender started on {self.host}:{self.port}")

    def stop(self):
        self._running = False
        if self._client_socket:
            try:
                self._client_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self._client_socket.close()
        if self._server_socket:
            try:
                self._server_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self._server_socket.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("FrameSender stopped")

    def _server_loop(self):
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(1)
            self._server_socket.settimeout(1.0)
        except Exception as e:
            logger.error(f"FrameSender failed to bind to {self.host}:{self.port}: {e}")
            self._running = False
            return

        while self._running:
            try:
                client, addr = self._server_socket.accept()
                logger.info(f"Client connected from {addr}")
                self._client_socket = client
                self._client_socket.settimeout(5.0)
                
                # We just hold the connection here. 
                # Actual frames are sent when send_frame() is called.
                # If connection drops, send_frame() will error and close _client_socket.
                # So we wait until _client_socket is closed.
                while self._running and self._client_socket is not None:
                    time.sleep(0.1)
                    
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"FrameSender server loop error: {e}")
                if self._client_socket:
                    self._client_socket.close()
                    self._client_socket = None

    def send_frame(self, frame: np.ndarray) -> bool:
        if not self._running or self._client_socket is None:
            return False

        self._frame_id += 1
        height, width = frame.shape[:2]
        
        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        success, encoded = cv2.imencode('.jpg', frame, encode_param)
        if not success:
            logger.error("Failed to encode frame to JPEG")
            return False
            
        payload = encoded.tobytes()
        
        packet = FramePacket(
            frame_id=self._frame_id,
            timestamp_ms=int(time.time() * 1000),
            payload=payload
        )
        
        data = packet.serialize()
        try:
            self._client_socket.sendall(data)
            return True
        except Exception as e:
            logger.warning(f"Failed to send frame, dropping client: {e}")
            try:
                self._client_socket.close()
            except Exception:
                pass
            self._client_socket = None
            return False

# Local development test script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Try webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("No webcam available for testing")
        exit(1)
        
    sender = FrameSender(host="0.0.0.0", port=5000)
    sender.start()
    
    logger.info("Starting to capture and send frames (press Ctrl+C to stop)")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            sender.send_frame(frame)
            time.sleep(1/30.0)  # Aim for ~30 fps
    except KeyboardInterrupt:
        pass
    finally:
        sender.stop()
        cap.release()
