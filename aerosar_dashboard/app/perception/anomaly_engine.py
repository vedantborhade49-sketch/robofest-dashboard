from typing import Optional, List
from app.models.detection import Detection
from app.models.entity import Entity
from app.models.spatial import SpatialAssociation

class AnomalyEngine:
    """
    Evaluates real evidence (Detection, Entity, etc.) and determines the Anomaly type.
    Does NOT persist data.
    """
    
    def evaluate(self, 
                 detection: Detection, 
                 entity: Entity, 
                 spatial_association: Optional[SpatialAssociation] = None,
                 temporal_context: Optional[dict] = None) -> List[str]:
        """
        Evaluates the current state and returns a list of active anomaly types.
        If unsupported or lacking evidence, does NOT return the anomaly.
        """
        anomalies = []
        cls = detection.class_name.upper()

        # 1. PERSON_DETECTED
        if cls in ("PERSON", "HUMAN"):
            anomalies.append("PERSON_DETECTED")
            
        # 2. VEHICLE_DETECTED
        elif cls in ("VEHICLE", "CAR", "TRUCK"):
            anomalies.append("VEHICLE_DETECTED")

        # 3. UNKNOWN_HAZARD
        else:
            # We can map other YOLO classes to generic hazards if useful
            # But let's only generate events if they are explicitly interesting
            # Currently leaving it out unless specifically needed, or map it.
            pass
            
        # Note on unavailable anomalies:
        # PERSON_IMMOBILE -> Requires position history, elapsed time, movement threshold (NOT AVAILABLE)
        # POSSIBLE_FALL -> Requires pose/trajectory (NOT AVAILABLE)
        # PERSON_ENTERED_RESTRICTED_ZONE -> Requires configured zones (NOT AVAILABLE)
        # MULTIPLE_PERSONS -> Handled at a global frame level, not per detection, but could be added 
        #                     if temporal_context contains other active entities in frame.

        return anomalies
