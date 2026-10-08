from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class BoundingBox(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None

    @model_validator(mode="after")
    def normalize_bbox(self):
        if self.x1 is not None and self.y1 is not None and self.x2 is not None and self.y2 is not None:
            width = max(0.0, float(self.x2 - self.x1))
            height = max(0.0, float(self.y2 - self.y1))
            self.width = width
            self.height = height
            self.x = (float(self.x1) + float(self.x2)) / 2.0
            self.y = (float(self.y1) + float(self.y2)) / 2.0
            return self

        if self.x is not None and self.y is not None and self.width is not None and self.height is not None:
            self.x1 = float(self.x) - float(self.width) / 2.0
            self.y1 = float(self.y) - float(self.height) / 2.0
            self.x2 = float(self.x) + float(self.width) / 2.0
            self.y2 = float(self.y) + float(self.height) / 2.0
            return self

        if self.x1 is not None and self.y1 is not None:
            if self.width is not None:
                self.x2 = float(self.x1) + float(self.width)
            if self.height is not None:
                self.y2 = float(self.y1) + float(self.height)

        if self.x2 is not None and self.y2 is not None and self.width is None and self.height is None:
            if self.x1 is not None:
                self.width = max(0.0, float(self.x2) - float(self.x1))
            if self.y1 is not None:
                self.height = max(0.0, float(self.y2) - float(self.y1))

        return self


class Detection(BaseModel):
    detection_id: str
    frame_id: int = 0
    class_id: int = -1
    class_name: str
    confidence: float
    bbox: BoundingBox
    source: str = "YOLO"
    camera_id: str = "webcam_0"
    image_width: int = 0
    image_height: int = 0
    timestamp: datetime
