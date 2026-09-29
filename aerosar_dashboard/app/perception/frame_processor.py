from __future__ import annotations

import cv2
import numpy as np


class FrameProcessor:
    def __init__(self, target_size: int = 640):
        self.target_size = target_size

    def preprocess(self, frame):
        if frame is None:
            return None
        if len(frame.shape) != 3:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def resize_if_needed(self, frame, width: int | None = None, height: int | None = None):
        if frame is None:
            return None
        if width is None and height is None:
            return frame
        h, w = frame.shape[:2]
        if width is None:
            width = int((h / height) * w)
        if height is None:
            height = int((w / width) * h)
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
