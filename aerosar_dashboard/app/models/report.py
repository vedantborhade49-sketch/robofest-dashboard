from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from app.models.context import RetrievedContext
from app.models.incident import Location

class IncidentSummary(BaseModel):
    """
    Structured detected incident facts.
    Originates directly from the field detection pipeline, distinct from AI interpretation.
    """
    incident_id: str
    type: str = "PERSON DETECTED"
    confidence: float
    timestamp: datetime
    location: Location
    status: str = "NEW"

class Report(BaseModel):
    """
    Represents an incident intelligence report synthesized by the RAG + LLM pipeline.
    Combines detected facts, AI synthesis, retrieved context, and human supervision status.
    """
    report_id: str
    incident_id: str
    mission_id: str = "SAR-001"
    status: str = "GENERATED"  # PENDING | GENERATED | REVIEWED | UNAVAILABLE
    generated_at: datetime
    incident_type: str = "PERSON DETECTED"
    confidence: float = 0.94
    incident_summary: IncidentSummary
    ai_report: str
    context_sources: List[RetrievedContext] = Field(default_factory=list)
    evidence_image: Optional[str] = None
    evidence_source: str = "Camera-01 (EO Payload)"
    evidence_frame: int = 18342
    human_review_status: str = "PENDING REVIEW"  # PENDING REVIEW | REVIEWED
    model_name: str = "MOCK-RAG-LLM (SIMULATED)"
