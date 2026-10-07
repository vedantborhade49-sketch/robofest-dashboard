import cv2
import numpy as np
from app.perception.camera import VideoSource

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
