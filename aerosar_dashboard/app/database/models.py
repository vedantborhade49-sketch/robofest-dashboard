from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from datetime import datetime, timezone
from app.database.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class MissionModel(Base):
    __tablename__ = "missions"
    mission_id = Column(String, primary_key=True, index=True)
    mission_name = Column(String, default="Search and Rescue")
    status = Column(String)
    start_time = Column(DateTime, default=get_utc_now)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class IncidentModel(Base):
    __tablename__ = "incidents"
    incident_id = Column(String, primary_key=True, index=True)
    mission_id = Column(String, index=True)
    type = Column(String)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=get_utc_now)
    
    # Optional bounding box
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)
    
    # Location
    location_x = Column(Float)
    location_y = Column(Float)
    location_z = Column(Float)
    
    evidence_image = Column(String, nullable=True)
    status = Column(String)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class ReportModel(Base):
    __tablename__ = "reports"
    report_id = Column(String, primary_key=True, index=True)
    incident_id = Column(String, index=True)
    mission_id = Column(String, index=True)
    status = Column(String)
    generated_at = Column(DateTime, default=get_utc_now)
    
    incident_type = Column(String)
    confidence = Column(Float)
    
    # Incident Summary flatten
    summary_incident_id = Column(String)
    summary_timestamp = Column(DateTime)
    summary_loc_x = Column(Float)
    summary_loc_y = Column(Float)
    summary_loc_z = Column(Float)
    summary_status = Column(String)
    
    ai_report = Column(String)
    evidence_image = Column(String, nullable=True)
    evidence_source = Column(String, nullable=True)
    evidence_frame: int | None = Column(Integer, nullable=True)
    human_review_status = Column(String)
    model_name = Column(String)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class RetrievedContextModel(Base):
    __tablename__ = "retrieved_context"
    context_id = Column(String, primary_key=True, index=True)
    report_id = Column(String, index=True)
    source_id = Column(String)
    source_type = Column(String)
    content = Column(String)
    relevance_score = Column(Float)
    timestamp = Column(DateTime, default=get_utc_now)

class EventModel(Base):
    __tablename__ = "events"
    event_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_utc_now)
    level = Column(String)
    source = Column(String)
    event_type = Column(String)
    message = Column(String)
    severity = Column(String)
    mission_id = Column(String, nullable=True, index=True)
    incident_id = Column(String, nullable=True, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
