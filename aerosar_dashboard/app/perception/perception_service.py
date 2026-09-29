from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from app.perception.camera import VideoSource
from app.perception.detection_processor import process_raw_detections
from app.perception.detector import YOLODetector
from app.perception.frame_processor import FrameProcessor
from app.perception.types import PerceptionStatus


class PerceptionService:
    def __init__(self, source: Optional[VideoSource] = None, detector: Optional[YOLODetector] = None, confidence_threshold: float = 0.5):
        self.source = source
        self.detector = detector or YOLODetector(confidence_threshold=confidence_threshold)
        self.frame_processor = FrameProcessor()
        self.detection_processor = None
        self.status = PerceptionStatus()
        self._running = False
        self._frame_id = 0

    @property
    def running(self) -> bool:
        return self._running

    def start(self):
        self._running = True
        self.status.running = True
        self.status.model_loaded = self.detector.model_loaded
        self.status.model_name = "AEROSAR YOLO"
        self.status.input_source = getattr(self.source, "source", "unknown") if self.source else "unknown"
        self.status.error = None

    def stop(self):
        self._running = False
        self.status.running = False
        if self.source is not None:
            self.source.release()

    def process_single_frame(self, frame):
        if frame is None:
            self.status.error = "Frame unavailable"
            return [], None

        processed = self.frame_processor.preprocess(frame)
        if processed is None:
            self.status.error = "Invalid frame"
            return [], None

        start = time.perf_counter()
        raw = self.detector.predict(processed) if self.detector.model_loaded else []
        inference_time = (time.perf_counter() - start) * 1000.0
        self.status.inference_time_ms = inference_time

        self._frame_id += 1
        detections = process_raw_detections(
            raw,
            frame_id=self._frame_id,
            width=frame.shape[1],
            height=frame.shape[0],
            source=self.status.input_source,
        )
        self.status.detection_count = len(detections)
        self.status.frame_count = self._frame_id
        self.status.last_frame_timestamp = datetime.now()
        self.status.error = None if detections or not raw else "No valid detections above threshold"
        return detections, processed

    def run_once(self):
        if self.source is None:
            self.status.error = "No video source configured"
            return [], None
        frame = self.source.read()
        if frame is None:
            self.status.error = "Frame read failed"
            return [], None
        return self.process_single_frame(frame)
