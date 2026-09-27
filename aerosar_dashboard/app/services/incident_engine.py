from app.models.detection import Detection
from app.models.incident import Incident, Location
from datetime import datetime

class IncidentEngine:
    """
    Mock Incident Engine.
    Future flow:
    Detection -> Validation/filtering -> Context association -> Incident creation -> Evidence handling -> Structured Incident
    """
    def __init__(self):
        self.counter = 100
        
    def process_detection(self, detection: Detection, current_location: Location) -> Incident:
        self.counter += 1
        return Incident(
            incident_id=f"INC-{self.counter}",
            mission_id="SAR-001",
            type=f"{detection.class_name} DETECTED",
            confidence=detection.confidence,
            timestamp=detection.timestamp,
            status="NEW",
            location=current_location,
            evidence_image=f"mock_evidence_ev{self.counter}.jpg"
        )
