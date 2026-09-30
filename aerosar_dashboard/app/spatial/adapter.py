from datetime import datetime
import math
from typing import Any, Optional
from app.models.spatial import LiDARScan, LiDARPoint

class LiDARAdapter:
    """
    Adapter to convert raw hardware/provider data into the standard LiDARScan model.
    """
    def adapt(self, raw_data: Optional[Any]) -> Optional[LiDARScan]:
        if not raw_data:
            return None
            
        # Expecting raw_data as a dictionary from MockLiDARProvider
        # (A real hardware driver would have its own specific raw structure here)
        try:
            points = []
            for m in raw_data.get("measurements", []):
                angle = m["angle"]
                dist = m["distance"]
                
                # Pre-calculate x, y for the standard model based on coordinate convention:
                # x = forward = distance * cos(angle)
                # y = left = distance * sin(angle)
                x = dist * math.cos(angle)
                y = dist * math.sin(angle)
                
                points.append(LiDARPoint(
                    angle=angle,
                    distance=dist,
                    x=x,
                    y=y,
                    intensity=m.get("intensity")
                ))
                
            return LiDARScan(
                scan_id=raw_data.get("id", "unknown"),
                timestamp=datetime.fromisoformat(raw_data["timestamp"]),
                points=points,
                min_range=raw_data.get("min_range", 0.0),
                max_range=raw_data.get("max_range", 12.0),
                angle_increment=raw_data.get("angle_increment", 0.01),
                sensor_frame="base_link"
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to adapt LiDAR scan: {e}")
            return None
