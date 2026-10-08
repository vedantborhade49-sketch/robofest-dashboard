import uuid
from typing import List
from app.perception.types import NetworkFrame
from app.perception.models import CVResult, Detection

class InsightAdapter:
    """
    Adapter that bridges the generic CV output (CVResult) and the 
    AEROSAR actionable insight pipeline (Detection/IncidentEngine).
    """

    @staticmethod
    def to_detections(cv_result: CVResult, frame: NetworkFrame) -> List[Detection]:
        """
        Converts a generic CVResult into a list of AEROSAR Detection models.
        Preserves frame_id and timestamp for evidence traceability.
        """
        if not cv_result or cv_result.error or not cv_result.detections:
            return []
            
        img_h, img_w = 0, 0
        if frame and frame.image is not None and hasattr(frame.image, "shape"):
            if len(frame.image.shape) >= 2:
                img_h, img_w = frame.image.shape[:2]

        detections = []
        for det in cv_result.detections:
            width_bb = det.bbox.x2 - det.bbox.x1
            height_bb = det.bbox.y2 - det.bbox.y1
            center_x = det.bbox.x1 + width_bb / 2.0
            center_y = det.bbox.y1 + height_bb / 2.0

            d = Detection(
                detection_id=str(uuid.uuid4()),
                timestamp=cv_result.timestamp,
                frame_id=cv_result.frame_id,
                class_id=det.class_id if det.class_id is not None else -1,
                class_name=det.class_name,
                confidence=det.confidence,
                bbox=det.bbox,
                source=cv_result.model_name or "CVProcessor",
                image_width=img_w,
                image_height=img_h,
                center_x=center_x,
                center_y=center_y,
                width=width_bb,
                height=height_bb,
                camera_id=frame.camera_id if frame and hasattr(frame, "camera_id") else "webcam_0",
            )
            detections.append(d)

        return detections
