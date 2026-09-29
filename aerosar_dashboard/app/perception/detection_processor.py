from datetime import datetime
from typing import List

import uuid

from app.perception.models import Detection, BBox


def process_raw_detections(raw, frame_id: int, width: int, height: int, source: str = "camera") -> List[Detection]:
    detections = []
    for r in raw:
        try:
            cls_id = int(r.get("class_id", -1))
            cls_name = r.get("class_name", "object")
            conf = float(r.get("confidence", 0.0))
            bb = r.get("bbox", {})
            x1 = int(bb.get("x1", 0))
            y1 = int(bb.get("y1", 0))
            x2 = int(bb.get("x2", 0))
            y2 = int(bb.get("y2", 0))

            width_bb = x2 - x1
            height_bb = y2 - y1
            center_x = x1 + width_bb / 2.0
            center_y = y1 + height_bb / 2.0

            det = Detection(
                detection_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                frame_id=frame_id,
                class_id=cls_id,
                class_name=cls_name,
                confidence=conf,
                bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
                source=source,
                image_width=width,
                image_height=height,
                center_x=center_x,
                center_y=center_y,
                width=width_bb,
                height=height_bb,
            )
            detections.append(det)
        except Exception:
            continue
    return detections
