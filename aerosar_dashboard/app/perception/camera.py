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
        super().__init__(str(index))
        self.index = index
