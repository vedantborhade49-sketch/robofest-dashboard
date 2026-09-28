from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_session
from app.database.models import MissionModel, IncidentModel, ReportModel, EventModel, RetrievedContextModel
from app.models.mission import Mission
from app.models.incident import Incident, Location
from app.models.report import Report, IncidentSummary
from app.models.event import Event
from app.models.context import RetrievedContext
from app.models.detection import BoundingBox

class Repository:
    """
    Central database repository separating persistence logic from business logic.
    Handles Pydantic <-> SQLAlchemy conversions.
    """
    
    def __init__(self):
        # We handle sessions internally for ease of use in UI context
        pass

    def _get_session(self) -> Session:
        return next(get_session())

    # --- INCIDENTS ---
    def save_incident(self, incident: Incident):
        with self._get_session() as db:
            db_incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident.incident_id).first()
            if not db_incident:
                db_incident = IncidentModel(incident_id=incident.incident_id)
                db.add(db_incident)
            
            db_incident.mission_id = incident.mission_id
            db_incident.type = incident.type
            db_incident.confidence = incident.confidence
            db_incident.timestamp = incident.timestamp
            
            if incident.bbox:
                db_incident.bbox_x = incident.bbox.x
                db_incident.bbox_y = incident.bbox.y
                db_incident.bbox_width = incident.bbox.width
                db_incident.bbox_height = incident.bbox.height
                
            db_incident.location_x = incident.location.x
            db_incident.location_y = incident.location.y
            db_incident.location_z = incident.location.z
            db_incident.evidence_image = incident.evidence_image
            db_incident.status = incident.status
            db_incident.updated_at = datetime.now(timezone.utc)
            
            db.commit()

    def get_incidents(self) -> List[Incident]:
        with self._get_session() as db:
            models = db.query(IncidentModel).all()
            incidents = []
            for m in models:
                bbox = None
                if m.bbox_x is not None:
                    bbox = BoundingBox(x=m.bbox_x, y=m.bbox_y, width=m.bbox_width, height=m.bbox_height)
                inc = Incident(
                    incident_id=m.incident_id,
                    mission_id=m.mission_id,
                    type=m.type,
                    confidence=m.confidence,
                    timestamp=m.timestamp,
                    bbox=bbox,
                    location=Location(x=m.location_x, y=m.location_y, z=m.location_z),
                    evidence_image=m.evidence_image,
                    status=m.status
                )
                incidents.append(inc)
            return incidents

    # --- REPORTS ---
    def save_report(self, report: Report):
        with self._get_session() as db:
            db_report = db.query(ReportModel).filter(ReportModel.report_id == report.report_id).first()
            if not db_report:
                db_report = ReportModel(report_id=report.report_id)
                db.add(db_report)
                
            db_report.incident_id = report.incident_id
            db_report.mission_id = report.mission_id
            db_report.status = report.status
            db_report.generated_at = report.generated_at
            db_report.incident_type = report.incident_type
            db_report.confidence = report.confidence
            
            db_report.summary_incident_id = report.incident_summary.incident_id
            db_report.summary_timestamp = report.incident_summary.timestamp
            db_report.summary_loc_x = report.incident_summary.location.x
            db_report.summary_loc_y = report.incident_summary.location.y
            db_report.summary_loc_z = report.incident_summary.location.z
            db_report.summary_status = report.incident_summary.status
            
            db_report.ai_report = report.ai_report
            db_report.evidence_image = report.evidence_image
            db_report.evidence_source = report.evidence_source
            db_report.evidence_frame = report.evidence_frame
            db_report.human_review_status = report.human_review_status
            db_report.model_name = report.model_name
            db_report.updated_at = datetime.now(timezone.utc)
            
            # Save context sources
            for ctx in report.context_sources:
                db_ctx = db.query(RetrievedContextModel).filter(
                    RetrievedContextModel.report_id == report.report_id,
                    RetrievedContextModel.source_id == ctx.source_id
                ).first()
                if not db_ctx:
                    import uuid
                    db_ctx = RetrievedContextModel(context_id=str(uuid.uuid4()))
                    db.add(db_ctx)
                db_ctx.report_id = report.report_id
                db_ctx.source_id = ctx.source_id
                db_ctx.source_type = ctx.source_type
                db_ctx.content = ctx.content
                db_ctx.relevance_score = ctx.relevance_score
                # timestamp omitted, let DB use default
                
            db.commit()

    def get_reports(self) -> List[Report]:
        with self._get_session() as db:
            models = db.query(ReportModel).all()
            reports = []
            for m in models:
                ctx_models = db.query(RetrievedContextModel).filter(RetrievedContextModel.report_id == m.report_id).all()
                contexts = []
                for c in ctx_models:
                    contexts.append(RetrievedContext(
                        source_id=c.source_id,
                        source_type=c.source_type,
                        content=c.content,
                        relevance_score=c.relevance_score
                    ))
                
                summary = IncidentSummary(
                    incident_id=m.summary_incident_id,
                    type=m.incident_type,
                    confidence=m.confidence,
                    timestamp=m.summary_timestamp,
                    location=Location(x=m.summary_loc_x, y=m.summary_loc_y, z=m.summary_loc_z),
                    status=m.summary_status
                )
                
                rep = Report(
                    report_id=m.report_id,
                    incident_id=m.incident_id,
                    mission_id=m.mission_id,
                    status=m.status,
                    generated_at=m.generated_at,
                    incident_type=m.incident_type,
                    confidence=m.confidence,
                    incident_summary=summary,
                    ai_report=m.ai_report,
                    context_sources=contexts,
                    evidence_image=m.evidence_image,
                    evidence_source=m.evidence_source or "Camera-01 (EO Payload)",
                    evidence_frame=m.evidence_frame or 18342,
                    human_review_status=m.human_review_status,
                    model_name=m.model_name
                )
                reports.append(rep)
            return reports

    # --- EVENTS ---
    def save_event(self, event: Event):
        with self._get_session() as db:
            db_event = db.query(EventModel).filter(EventModel.event_id == event.event_id).first()
            if not db_event:
                db_event = EventModel(event_id=event.event_id)
                db.add(db_event)
            db_event.timestamp = event.timestamp
            db_event.level = event.level
            db_event.source = event.source
            db_event.event_type = event.event_type
            db_event.message = event.message
            db_event.severity = event.severity
            db_event.mission_id = event.mission_id
            db_event.incident_id = event.incident_id
            db_event.details = event.details
            db.commit()

    def get_events(self) -> List[Event]:
        with self._get_session() as db:
            models = db.query(EventModel).order_by(EventModel.timestamp.asc()).all()
            events = []
            for m in models:
                events.append(Event(
                    event_id=m.event_id,
                    timestamp=m.timestamp,
                    level=m.level,
                    source=m.source,
                    event_type=m.event_type,
                    message=m.message,
                    severity=m.severity,
                    mission_id=m.mission_id,
                    incident_id=m.incident_id,
                    details=m.details
                ))
            return events
