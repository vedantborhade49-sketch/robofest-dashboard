import time
from typing import List
from app.perception.processor import CVProcessor
from app.perception.types import NetworkFrame
from app.perception.models import CVResult, DetectionResult, BBox
from app.perception.detector import YOLODetector
from app.perception.frame_processor import FrameProcessor

class YOLOProcessor(CVProcessor):
    """
    Implements CVProcessor using the existing YOLODetector.
    Provides backward compatibility while conforming to the new CV contract.
    """
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        self.detector = YOLODetector(
            model_path=model_path, 
            confidence_threshold=confidence_threshold
        )
        self.frame_processor = FrameProcessor()
        self.model_name = "AEROSAR YOLO"
        self.model_version = "8n"
        
    def process(self, frame: NetworkFrame) -> CVResult:
        result = CVResult(
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            model_name=self.model_name,
            model_version=self.model_version
        )
        
        if not self.detector.model_loaded:
            result.error = "Model not loaded"
            return result
            
        try:
            processed = self.frame_processor.preprocess(frame.image)
            if processed is None:
                result.error = "Frame preprocessing failed"
                return result
                
            start = time.perf_counter()
            raw_detections = self.detector.predict(processed)
            result.processing_time = (time.perf_counter() - start) * 1000.0
            
            for raw in raw_detections:
                bbox_dict = raw.get("bbox", {})
                bbox = BBox(
                    x1=int(bbox_dict.get("x1", 0)),
                    y1=int(bbox_dict.get("y1", 0)),
                    x2=int(bbox_dict.get("x2", 0)),
                    y2=int(bbox_dict.get("y2", 0))
                )
                
                det = DetectionResult(
                    class_name=raw.get("class_name", "object"),
                    confidence=float(raw.get("confidence", 0.0)),
                    bbox=bbox,
                    class_id=int(raw.get("class_id", -1))
                )
                result.detections.append(det)
                
        except Exception as e:
            result.error = str(e)
            
        return result
