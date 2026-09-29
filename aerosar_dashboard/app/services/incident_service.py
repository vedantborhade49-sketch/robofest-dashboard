from __future__ import annotations

from typing import List, Optional

from app.database.repository import Repository
from app.models.evidence import Evidence, EvidenceType
from app.models.incident import Incident, IncidentStatus
from app.services.evidence_service import EvidenceService
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

class IncidentService:
    def __init__(self, repository: Optional[Repository] = None, evidence_service: Optional[EvidenceService] = None):
        self.repository = repository or Repository()
        self.evidence_service = evidence_service or EvidenceService()

    def create_incident(self, incident: Incident) -> Incident:
        self.repository.save_incident(incident)
        event_bus.publish(
            EventType.INCIDENT_CREATED,
            payload={"incident": incident.model_dump()},
            mission_id=incident.mission_id
        )
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.repository.get_incident(incident_id)

    def list_incidents(self) -> List[Incident]:
        return self.repository.get_incidents()

    def update_status(self, incident_id: str, status: str) -> Incident:
        incident = self.get_incident(incident_id)
        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")
        if not IncidentStatus.validate_transition(incident.status, status):
            raise ValueError(f"Invalid status transition from {incident.status} to {status}")
        old_status = incident.status
        incident.status = status
        self.repository.save_incident(incident)
        
        event_bus.publish(
            EventType.INCIDENT_STATUS_CHANGED,
            payload={
                "incident_id": incident.incident_id,
                "old_status": old_status,
                "new_status": status,
            },
            mission_id=incident.mission_id
        )
        
        return incident

    def attach_evidence(self, incident_id: str, evidence: Evidence) -> Incident:
        incident = self.get_incident(incident_id)
        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")
        if self.evidence_service.is_invalid_path(evidence.file_path):
            raise ValueError("Evidence path is outside the controlled evidence directory.")
        incident.evidence_id = evidence.evidence_id
        incident.evidence_image = evidence.file_path
        self.repository.save_incident(incident)
        self.repository.save_evidence(evidence)
        
        event_bus.publish(
            EventType.EVIDENCE_CREATED,
            payload={
                "incident_id": incident_id,
                "evidence_id": evidence.evidence_id,
                "evidence_type": evidence.type,
            },
            mission_id=incident.mission_id
        )
        
        return incident

    def get_evidence(self, incident_id: str) -> List[Evidence]:
        return self.repository.get_incident_evidence(incident_id)

    def resolve_incident(self, incident_id: str) -> Incident:
        return self.update_status(incident_id, IncidentStatus.RESOLVED.value)
