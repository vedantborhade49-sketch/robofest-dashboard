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
        # On Windows cv2.CAP_DSHOW might be better, but we leave default
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

class MockCameraSource(VideoSource):
    """Produces generated frames for deterministic testing without hardware."""
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self._is_open = False
        
    def open(self):
        self._is_open = True
        return True
        
    def read(self):
        if not self._is_open:
            return None
        # Return a black frame or one with some text
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.putText(frame, "MOCK CAMERA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame
        
    def is_open(self) -> bool:
        return self._is_open
        
    def release(self):
        self._is_open = False
