from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, Tuple, List

from app.perception.camera import VideoSource
from app.perception.processor import CVProcessor
from app.perception.yolo_processor import YOLOProcessor
from app.perception.insight_adapter import InsightAdapter
from app.perception.types import PerceptionStatus, NetworkFrame
from app.perception.models import Detection


class PerceptionService:
    def __init__(self, source: Optional[VideoSource] = None, processor: Optional[CVProcessor] = None, confidence_threshold: float = 0.5, detector=None):
        self.source = source
        if processor:
            self.processor = processor
        elif detector:
            # Backward compatibility wrapper for old YOLODetector injections
            self.processor = YOLOProcessor(confidence_threshold=confidence_threshold)
            self.processor.detector = detector
        else:
            self.processor = YOLOProcessor(confidence_threshold=confidence_threshold)
        
        self.status = PerceptionStatus()
        self._running = False
        self._frame_id = 0

    def process_single_frame(self, frame):
        # Legacy method kept for backward compatibility and mocking in tests.
        pass

    @property

    def running(self) -> bool:
        return self._running

    def start(self):
        self._running = True
        self.status.running = True
        self.status.model_loaded = getattr(self.processor, "detector", None) is not None and getattr(self.processor.detector, "model_loaded", True)
        self.status.model_name = getattr(self.processor, "model_name", "CVProcessor")
        self.status.input_source = getattr(self.source, "source", "unknown") if self.source else "unknown"
        if self.source:
            if not self.source.is_open():
                success = self.source.open()
                if not success:
                    self.status.error = "Failed to open video source"
        self.status.error = self.status.error or None

    def stop(self):
        self._running = False
        self.status.running = False
        if self.source is not None:
            self.source.release()

    def run_once(self) -> Tuple[List[Detection], Optional[object]]:
        if self.source is None:
            self.status.error = "No video source configured"
            return [], None
            
        # Update network metrics if using TCPVideoProvider
        if hasattr(self.source, 'receiver'):
            self.status.received_fps = getattr(self.source.receiver, 'received_fps', 0.0)
            self.status.dropped_frames = getattr(self.source.receiver, 'dropped_frames', 0)
            self.status.connection_state = getattr(self.source.receiver, 'state', "DISCONNECTED")
            
        frame_data = self.source.read()
        if frame_data is None:
            self.status.error = "Frame read failed"
            if hasattr(self.source, 'receiver'):
                self.status.camera_connected = (self.status.connection_state == "RECEIVING")
            return [], None
            
        self.status.camera_connected = True
        
        # Ensure we have a NetworkFrame
        if not isinstance(frame_data, NetworkFrame):
            # Fallback for standard VideoSource (like webcam) yielding raw frames
            self._frame_id += 1
            network_frame = NetworkFrame(
                frame_id=self._frame_id,
                timestamp=datetime.now(),
                image=frame_data,
                camera_id=self.status.input_source,
            )
        else:
            network_frame = frame_data
            self._frame_id = network_frame.frame_id
            
        # CV Processing Boundary
        try:
            cv_result = self.processor.process(network_frame)
            
            self.status.frame_count += 1
            self.status.last_frame_timestamp = network_frame.timestamp
            
            if cv_result.error:
                self.status.error = cv_result.error
                return [], network_frame.image
                
            self.status.inference_time_ms = cv_result.processing_time or 0.0
            
            # Insight Adapter Boundary
            detections = InsightAdapter.to_detections(cv_result, network_frame)
            
            self.status.detection_count = len(detections)
            self.status.error = None
            
            return detections, network_frame.image
            
        except Exception as e:
            self.status.error = f"CV Processing failed: {str(e)}"
            return [], network_frame.image


