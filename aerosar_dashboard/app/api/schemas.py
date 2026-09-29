from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.context import RetrievedContext
from app.models.event import Event
from app.models.evidence import Evidence, EvidenceType
from app.models.incident import Incident, IncidentStatus, Location
from app.models.report import IncidentSummary, Report


class HealthResponse(BaseModel):
    status: str
    service: str


class MissionCreateRequest(BaseModel):
    mission_id: str
    mission_name: str = "Search and Rescue"


class MissionResponse(BaseModel):
    mission_id: str
    mission_name: str
    mission_status: str = "ACTIVE"
    elapsed_time: float = 0.0
    search_progress: float = 0.0
    connection_status: str = "CONNECTED"
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @classmethod
    def model_validate(cls, data: Any):
        if isinstance(data, dict) and "mission_name" not in data and "mission_status" in data:
            data = dict(data)
            data["mission_name"] = "Search and Rescue"
        return super().model_validate(data)


class LocationRequest(BaseModel):
    x: float
    y: float
    z: float


class IncidentCreateRequest(BaseModel):
    incident_id: str
    mission_id: str = "SAR-001"
    type: str
    confidence: float
    timestamp: datetime
    bbox: Optional[Dict[str, float]] = None
    location: LocationRequest
    evidence_image: Optional[str] = None
    status: str = "NEW"

    def to_incident(self) -> Incident:
        bbox = None
        if self.bbox:
            from app.models.detection import BoundingBox
            bbox = BoundingBox(**self.bbox)
        return Incident(
            incident_id=self.incident_id,
            mission_id=self.mission_id,
            type=self.type,
            confidence=self.confidence,
            timestamp=self.timestamp,
            bbox=bbox,
            location=Location(**self.location.model_dump()),
            evidence_image=self.evidence_image,
            status=self.status,
        )


class IncidentPatchRequest(BaseModel):
    mission_id: Optional[str] = None
    type: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: Optional[datetime] = None
    bbox: Optional[Dict[str, float]] = None
    location: Optional[LocationRequest] = None
    evidence_image: Optional[str] = None
    status: Optional[str] = None


class IncidentStatusUpdateRequest(BaseModel):
    status: str

    @model_validator(mode="after")
    def validate_status(self):
        new_status = str(self.status).upper()
        if not IncidentStatus.validate_transition(IncidentStatus.NEW, new_status):
            # validation is handled in service logic and API route; allow the enum to accept known values only
            pass
        return self


class IncidentResponse(BaseModel):
    incident_id: str
    mission_id: str
    type: str
    confidence: float
    timestamp: datetime
    bbox: Optional[Dict[str, float]] = None
    location: LocationRequest
    evidence_image: Optional[str] = None
    status: str = "NEW"

    @classmethod
    def model_validate(cls, data: Any):
        if isinstance(data, dict):
            if "location" in data and isinstance(data["location"], dict):
                loc = data["location"]
                data = dict(data)
                data["location"] = LocationRequest(**loc)
            if "bbox" in data and data["bbox"] is not None and isinstance(data["bbox"], dict):
                data = dict(data)
                data["bbox"] = dict(data["bbox"])
        return super().model_validate(data)


class EvidenceResponse(BaseModel):
    evidence_id: str
    incident_id: str
    timestamp: datetime
    type: str
    file_path: str
    mime_type: str = "image/jpeg"
    frame_id: Optional[int] = None
    source: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_model(cls, evidence: Evidence) -> "EvidenceResponse":
        return cls(
            evidence_id=evidence.evidence_id,
            incident_id=evidence.incident_id,
            timestamp=evidence.timestamp,
            type=evidence.type.value if isinstance(evidence.type, EvidenceType) else str(evidence.type),
            file_path=evidence.file_path,
            mime_type=evidence.mime_type,
            frame_id=evidence.frame_id,
            source=evidence.source,
            description=evidence.description,
        )


class IncidentSummaryRequest(BaseModel):
    incident_id: str
    type: str = "PERSON DETECTED"
    confidence: float
    timestamp: datetime
    location: LocationRequest
    status: str = "NEW"

    def to_summary(self) -> IncidentSummary:
        return IncidentSummary(
            incident_id=self.incident_id,
            type=self.type,
            confidence=self.confidence,
            timestamp=self.timestamp,
            location=Location(**self.location.model_dump()),
            status=self.status,
        )


class RetrievedContextRequest(BaseModel):
    source_id: str
    source_type: str
    content: str
    relevance_score: float

    def to_context(self) -> RetrievedContext:
        return RetrievedContext(
            source_id=self.source_id,
            source_type=self.source_type,
            content=self.content,
            relevance_score=self.relevance_score,
        )


class RetrievedContextResponse(BaseModel):
    source_id: str
    source_type: str
    content: str
    relevance_score: float

    def to_context(self) -> RetrievedContext:
        return RetrievedContext(
            source_id=self.source_id,
            source_type=self.source_type,
            content=self.content,
            relevance_score=self.relevance_score,
        )


class ReportCreateRequest(BaseModel):
    report_id: str
    incident_id: str
    mission_id: str = "SAR-001"
    status: str = "GENERATED"
    generated_at: datetime
    incident_type: str = "PERSON DETECTED"
    confidence: float = 0.94
    incident_summary: IncidentSummaryRequest
    ai_report: str
    context_sources: List[RetrievedContextRequest] = Field(default_factory=list)
    evidence_image: Optional[str] = None
    evidence_source: str = "Camera-01 (EO Payload)"
    evidence_frame: int = 18342
    human_review_status: str = "PENDING REVIEW"
    model_name: str = "SIMULATED-API-LLM"

    def to_report(self) -> Report:
        report = Report(
            report_id=self.report_id,
            incident_id=self.incident_id,
            mission_id=self.mission_id,
            status=self.status,
            generated_at=self.generated_at,
            incident_type=self.incident_type,
            confidence=self.confidence,
            incident_summary=self.incident_summary.to_summary(),
            ai_report=self.ai_report,
            context_sources=[item.to_context() for item in self.context_sources],
            evidence_image=self.evidence_image,
            evidence_source=self.evidence_source,
            evidence_frame=self.evidence_frame,
            human_review_status=self.human_review_status,
            model_name=self.model_name,
        )
        return report


class ReportResponse(BaseModel):
    report_id: str
    incident_id: str
    mission_id: str
    status: str
    generated_at: datetime
    incident_type: str
    confidence: float
    incident_summary: IncidentSummaryRequest
    ai_report: str
    context_sources: List[RetrievedContextResponse] = Field(default_factory=list)
    evidence_image: Optional[str] = None
    evidence_source: str = "Camera-01 (EO Payload)"
    evidence_frame: int = 18342
    human_review_status: str = "PENDING REVIEW"
    model_name: str = "SIMULATED-API-LLM"

    @classmethod
    def model_validate(cls, data: Any):
        if isinstance(data, dict) and "incident_summary" in data and isinstance(data["incident_summary"], dict):
            summary = data["incident_summary"]
            data = dict(data)
            data["incident_summary"] = IncidentSummaryRequest(**summary)
        if isinstance(data, dict) and "context_sources" in data and isinstance(data["context_sources"], list):
            data = dict(data)
            data["context_sources"] = [RetrievedContextResponse(**item) if isinstance(item, dict) else item for item in data["context_sources"]]
        return super().model_validate(data)


class EventCreateRequest(BaseModel):
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    level: str = "INFO"
    source: str = "SYSTEM"
    event_type: str = "SYSTEM"
    message: str
    severity: Optional[str] = None
    mission_id: Optional[str] = "SAR-001"
    incident_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_event(self) -> Event:
        event_id = self.event_id or f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        recorded = Event(
            event_id=event_id,
            timestamp=self.timestamp or datetime.now(),
            level=self.level,
            source=self.source,
            event_type=self.event_type,
            message=self.message,
            severity=self.severity or self.level,
            mission_id=self.mission_id,
            incident_id=self.incident_id,
            details=self.details,
        )
        return recorded


class EventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    level: str
    source: str
    event_type: str
    message: str
    severity: str
    mission_id: Optional[str] = "SAR-001"
    incident_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
