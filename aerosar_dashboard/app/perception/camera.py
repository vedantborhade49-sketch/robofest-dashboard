from __future__ import annotations

import cv2
import numpy as np
from typing import Optional


class VideoSource:
    def open(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def is_open(self) -> bool:
        raise NotImplementedError

    def release(self):
        raise NotImplementedError


class OpenCVVideoSource(VideoSource):
    def __init__(self, source: str = "0"):
        self.source = source
        self._cap = None

    def open(self):
        self._cap = cv2.VideoCapture(self.source)
        return self._cap is not None and self._cap.isOpened()

    def read(self):
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        return frame

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class WebcamSource(OpenCVVideoSource):
    def __init__(self, index: int = 0):
        super().__init__(index if isinstance(index, str) else str(index))
        # Sometimes Windows requires int for DirectShow, Linux string for device path
        self.index = index
        
    def open(self):
        # On Windows cv2.CAP_DSHOW is much more reliable
        import sys
        if sys.platform.startswith('win'):
            self._cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(self.index)
        return self._cap is not None and self._cap.isOpened()

class VideoFileSource(OpenCVVideoSource):
    def __init__(self, filepath: str, loop: bool = True):
        super().__init__(filepath)
        self.loop = loop
        
    def read(self):
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            if self.loop:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
                if not ok or frame is None:
                    return None
            else:
                return None
        return frame

class PiCameraSource(OpenCVVideoSource):
    """
    Raspberry Pi 5 specific camera source.
    Often uses libcamera via GStreamer or V4L2.
    For simplicity in this architecture, we attempt a V4L2 connection 
    with a preferred Pi resolution, falling back to standard index 0.
    """
    def __init__(self, index: int = 0, width: int = 1280, height: int = 720):
        super().__init__(str(index))
        self.index = index
        self.width = width
        self.height = height

    def open(self):
        # Try V4L2 specifically for Pi
        self._cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
        if self._cap is not None and self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            return True
        return False


class MockVideoSource(VideoSource):
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self._is_open = False
        import time
        self._start_time = time.time()

    def open(self):
        self._is_open = True
        return True

    def read(self):
        import time
        if not self._is_open:
            return None
        
        # Generate a simple synthetic frame with moving pattern
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add a moving gradient based on time
        t = time.time() - self._start_time
        offset = int((t * 50) % self.width)
        
        frame[:, offset:offset+100, 1] = 200  # Green vertical bar
        
        cv2.putText(frame, f"AEROSAR MOCK CAMERA: {t:.1f}s", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Simulate ~30 FPS
        time.sleep(1/30.0)
        return frame

    def is_open(self) -> bool:
        return self._is_open

    def release(self):
        self._is_open = False


class TCPVideoProvider(VideoSource):
    """
    Connects to a remote camera stream via the binary AEROSAR Frame Protocol.
    """
    def __init__(self, host: str, port: int, reconnect_delay: float = 2.0, frame_timeout: float = 2.0):
        from app.communication.frame_receiver import FrameReceiver
        self.host = host
        self.port = port
        self.source = f"tcp://{host}:{port}"
        self.receiver = FrameReceiver(host, port, reconnect_delay, frame_timeout)
        
    def open(self):
        self.receiver.start()
        return True
        
    def read(self):
        import time
        # Provide blocking behavior (up to a timeout) similar to OpenCV
        timeout = 1.0
        start = time.time()
        while time.time() - start < timeout:
            frame = self.receiver.get_latest_frame()
            if frame is not None:
                # We consume the latest frame
                with self.receiver._lock:
                    self.receiver._latest_network_frame = None
                return frame
            time.sleep(0.01)
        return None

    def is_open(self) -> bool:
        from app.communication.frame_receiver import ConnectionState
        return self.receiver._running and self.receiver.state in (ConnectionState.CONNECTED, ConnectionState.RECEIVING)
        
    def release(self):
        self.receiver.stop()

