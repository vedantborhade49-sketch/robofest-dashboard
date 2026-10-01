from __future__ import annotations

import time
from typing import Any, List, Optional

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None


class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5, device: str = "cpu", image_size: int = 640, target_classes: Optional[List[str]] = None):
        import os
        if not os.path.exists(model_path) and model_path.endswith(".pt"):
            self.model_path = "yolov8n.pt"
        else:
            self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.image_size = image_size
        self.target_classes = target_classes or []
        self.model = None
        self.model_loaded = False
        self.last_error: Optional[str] = None
        self._load()

    def _load(self):
        if YOLO is None:
            self.last_error = "ultralytics is not available"
            self.model_loaded = False
            return
        try:
            self.model = YOLO(self.model_path)
            self.model_loaded = True
            self.last_error = None
        except Exception as exc:  # pragma: no cover
            self.last_error = str(exc)
            self.model_loaded = False

    def predict(self, frame):
        if self.model is None or not self.model_loaded:
            return []
        try:
            results = self.model(frame, conf=self.confidence_threshold, imgsz=self.image_size, device=self.device, verbose=False)
            detections: List[dict] = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                    cls_id = int(box.cls[0])
                    cls_name = result.names.get(cls_id, "object")
                    confidence = float(box.conf[0])
                    if self.target_classes and cls_name not in self.target_classes:
                        continue
                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": confidence,
                        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    })
            return detections
        except Exception as exc:  # pragma: no cover
            self.last_error = str(exc)
            return []
