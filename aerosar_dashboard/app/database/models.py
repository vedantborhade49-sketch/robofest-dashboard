from sqlalchemy import String, Float, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.database.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class MissionModel(Base):
    __tablename__ = "missions"
    mission_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    mission_name: Mapped[str] = mapped_column(String, default="Search and Rescue")
    status: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class IncidentModel(Base):
    __tablename__ = "incidents"
    incident_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    mission_id: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    
    # Optional bounding box
    bbox_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Location
    location_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_z: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    spatial_status: Mapped[str] = mapped_column(String, default="UNAVAILABLE")
    position_frame: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    range: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spatial_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_sensor: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    evidence_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class EvidenceModel(Base):
    __tablename__ = "evidence"
    evidence_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    incident_id: Mapped[str] = mapped_column(String, ForeignKey("incidents.incident_id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, default="image/jpeg")
    frame_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class ReportModel(Base):
    __tablename__ = "reports"
    report_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    incident_id: Mapped[str] = mapped_column(String, index=True)
    mission_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    
    incident_type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    
    # Incident Summary flatten
    summary_incident_id: Mapped[str] = mapped_column(String)
    summary_timestamp: Mapped[datetime] = mapped_column(DateTime)
    summary_loc_x: Mapped[float] = mapped_column(Float)
    summary_loc_y: Mapped[float] = mapped_column(Float)
    summary_loc_z: Mapped[float] = mapped_column(Float)
    summary_status: Mapped[str] = mapped_column(String)
    
    ai_report: Mapped[str] = mapped_column(String)
    evidence_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_frame: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    human_review_status: Mapped[str] = mapped_column(String)
    model_name: Mapped[str] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class RetrievedContextModel(Base):
    __tablename__ = "retrieved_context"
    context_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    report_id: Mapped[str] = mapped_column(String, index=True)
    source_id: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    relevance_score: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class EventModel(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    level: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    mission_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class EntityModel(Base):
    __tablename__ = "entities"
    entity_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    first_frame_id: Mapped[int] = mapped_column(Integer, default=0)
    last_frame_id: Mapped[int] = mapped_column(Integer, default=0)
    sighting_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String)
    image_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class AnomalyEventModel(Base):
    __tablename__ = "anomaly_events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    first_frame_id: Mapped[int] = mapped_column(Integer, default=0)
    last_frame_id: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    spatial_information: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)
