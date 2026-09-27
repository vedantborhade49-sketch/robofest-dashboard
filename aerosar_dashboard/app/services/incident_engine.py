"""
STALLION AEROSAR - Incident Engine
Architectural role: Converts raw AI detections (YOLO/perception) into structured,
actionable incidents with spatial context, mission reference, and evidence tracking.

Future Flow:
Camera -> OpenCV -> YOLO -> Detection -> Incident Engine -> Structured Incident -> DB -> FastAPI -> Ground Station
"""

from typing import Optional
from datetime import datetime
from app.models.detection import Detection
from app.models.incident import Incident, Location

class IncidentEngine:
    """
    Incident Engine handles the architectural boundary between perception and mission operations.
    
    Responsibilities:
    1. Detection validation & filtering (confidence thresholds, noise reduction)
    2. Spatial & context association (robotics SLAM/LiDAR pose -> 3D target coordinates)
    3. Incident creation with unique tracking IDs
    4. Evidence frame cataloging & reference assignment
    5. Initial triage status assignment (NEW / REVIEW / CONFIRMED)
    """
    def __init__(self, initial_counter: int = 100):
        self._counter = initial_counter

    def validate_detection(self, detection: Detection, min_confidence: float = 0.50) -> bool:
        """Filter out low confidence or invalid detections."""
        return detection.confidence >= min_confidence

    def process_detection(
        self,
        detection: Detection,
        current_location: Location,
        mission_id: str = "SAR-001",
        status: str = "NEW"
    ) -> Optional[Incident]:
        """
        Transforms an AI Detection into a structured Incident.
        """
        if not self.validate_detection(detection):
            return None

        self._counter += 1
        incident_id = f"INC-{self._counter:03d}"
        
        # Format incident type cleanly (e.g., PERSON DETECTED or PERSON)
        class_name = detection.class_name.upper()
        incident_type = f"{class_name} DETECTED" if not class_name.endswith("DETECTED") else class_name
        
        return Incident(
            incident_id=incident_id,
            mission_id=mission_id,
            type=incident_type,
            confidence=round(detection.confidence, 2),
            timestamp=detection.timestamp,
            bbox=detection.bbox,
            location=current_location,
            evidence_image=f"EV-{incident_id}.jpg",
            status=status
        )
