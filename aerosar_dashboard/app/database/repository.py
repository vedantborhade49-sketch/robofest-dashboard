from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_session
from app.database.models import MissionModel, IncidentModel, ReportModel, EventModel, RetrievedContextModel, EvidenceModel
from app.models.mission import Mission
from app.models.incident import Incident, Location
from app.models.report import Report, IncidentSummary
from app.models.event import Event
from app.models.context import RetrievedContext
from app.models.detection import BoundingBox
from app.models.evidence import Evidence, EvidenceType

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

    # --- MISSIONS ---
    def save_mission(self, mission: "Mission"):
        with self._get_session() as db:
            db_mission = db.query(MissionModel).filter(MissionModel.mission_id == mission.mission_id).first()
            if not db_mission:
                db_mission = MissionModel(mission_id=mission.mission_id)
                db.add(db_mission)

            db_mission.mission_name = getattr(mission, "mission_name", "Search and Rescue")
            db_mission.status = getattr(mission, "status", getattr(mission, "mission_status", "ACTIVE"))
            start_time = getattr(mission, "start_time", None)
            if start_time is not None:
                db_mission.start_time = start_time
            end_time = getattr(mission, "end_time", None)
            if end_time is not None:
                db_mission.end_time = end_time
            db.commit()

    def get_missions(self) -> List[Mission]:
        with self._get_session() as db:
            models = db.query(MissionModel).order_by(MissionModel.created_at.asc()).all()
            missions: List[Mission] = []
            for m in models:
                missions.append(Mission(
                    mission_id=m.mission_id,
                    mission_status=m.status,
                    elapsed_time=0.0,
                    search_progress=0.0,
                    connection_status="CONNECTED",
                ))
            return missions

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        with self._get_session() as db:
            m = db.query(MissionModel).filter(MissionModel.mission_id == mission_id).first()
            if not m:
                return None
            return Mission(
                mission_id=m.mission_id,
                mission_status=m.status,
                elapsed_time=0.0,
                search_progress=0.0,
                connection_status="CONNECTED",
            )

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
                
            if incident.location:
                db_incident.location_x = incident.location.x
                db_incident.location_y = incident.location.y
                db_incident.location_z = incident.location.z
            else:
                db_incident.location_x = None
                db_incident.location_y = None
                db_incident.location_z = None
                
            db_incident.spatial_status = incident.spatial_status
            db_incident.position_frame = incident.position_frame
            db_incident.range = incident.range
            db_incident.spatial_confidence = incident.spatial_confidence
            db_incident.source_sensor = incident.source_sensor
            
            db_incident.evidence_id = getattr(incident, "evidence_id", None)
            db_incident.evidence_image = incident.evidence_image
            status_val = getattr(incident.status, "value", incident.status)
            db_incident.status = str(status_val)
            db_incident.updated_at = datetime.now(timezone.utc)
            
            db.commit()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        incidents = self.get_incidents()
        for incident in incidents:
            if incident.incident_id == incident_id:
                return incident
        return None

    def get_incidents(self) -> List[Incident]:
        with self._get_session() as db:
            models = db.query(IncidentModel).all()
            incidents: List[Incident] = []
            for m in models:
                bbox = None
                if m.bbox_x is not None:
                    bbox = BoundingBox(x=m.bbox_x, y=m.bbox_y, width=m.bbox_width, height=m.bbox_height)
                    
                location = None
                if m.location_x is not None and m.location_y is not None and m.location_z is not None:
                    location = Location(x=m.location_x, y=m.location_y, z=m.location_z)
                    
                inc = Incident(
                    incident_id=m.incident_id,
                    mission_id=m.mission_id,
                    type=m.type,
                    confidence=m.confidence,
                    timestamp=m.timestamp,
                    bbox=bbox,
                    location=location,
                    spatial_status=m.spatial_status,
                    position_frame=m.position_frame,
                    range=m.range,
                    spatial_confidence=m.spatial_confidence,
                    source_sensor=m.source_sensor,
                    evidence_id=getattr(m, "evidence_id", None),
                    evidence_image=m.evidence_image,
                    status=m.status
                )
                incidents.append(inc)
            return incidents

    # --- EVIDENCE ---
    def save_evidence(self, evidence: Evidence):
        with self._get_session() as db:
            db_evidence = db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence.evidence_id).first()
            if not db_evidence:
                db_evidence = EvidenceModel(evidence_id=evidence.evidence_id)
                db.add(db_evidence)

            db_evidence.incident_id = evidence.incident_id
            db_evidence.timestamp = evidence.timestamp
            db_evidence.type = evidence.type.value
            db_evidence.file_path = evidence.file_path
            db_evidence.mime_type = evidence.mime_type
            db_evidence.frame_id = evidence.frame_id
            db_evidence.source = evidence.source
            db_evidence.description = evidence.description
            db.commit()

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        with self._get_session() as db:
            model = db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence_id).first()
            if not model:
                return None
            return Evidence(
                evidence_id=model.evidence_id,
                incident_id=model.incident_id,
                timestamp=model.timestamp,
                type=EvidenceType(model.type) if model.type in {member.value for member in EvidenceType} else EvidenceType.ANNOTATED_FRAME,
                file_path=model.file_path,
                mime_type=model.mime_type,
                frame_id=model.frame_id,
                source=model.source or "unknown",
                description=model.description,
            )

    def get_incident_evidence(self, incident_id: str) -> List[Evidence]:
        with self._get_session() as db:
            models = db.query(EvidenceModel).filter(EvidenceModel.incident_id == incident_id).order_by(EvidenceModel.timestamp.asc()).all()
            evidence: List[Evidence] = []
            for model in models:
                evidence.append(Evidence(
                    evidence_id=model.evidence_id,
                    incident_id=model.incident_id,
                    timestamp=model.timestamp,
                    type=EvidenceType(model.type) if model.type in {member.value for member in EvidenceType} else EvidenceType.ANNOTATED_FRAME,
                    file_path=model.file_path,
                    mime_type=model.mime_type,
                    frame_id=model.frame_id,
                    source=model.source or "unknown",
                    description=model.description,
                ))
            return evidence

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
            
            if report.incident_summary.location:
                db_report.summary_loc_x = report.incident_summary.location.x
                db_report.summary_loc_y = report.incident_summary.location.y
                db_report.summary_loc_z = report.incident_summary.location.z
            else:
                db_report.summary_loc_x = 0.0
                db_report.summary_loc_y = 0.0
                db_report.summary_loc_z = 0.0
                
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
            reports: List[Report] = []
            for m in models:
                ctx_models = db.query(RetrievedContextModel).filter(RetrievedContextModel.report_id == m.report_id).all()
                contexts: List[RetrievedContext] = []
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

    def get_report(self, report_id: str) -> Optional[Report]:
        reports = self.get_reports()
        for report in reports:
            if report.report_id == report_id:
                return report
        return None

    def save_context(self, report_id: str, context: RetrievedContext):
        with self._get_session() as db:
            db_ctx = db.query(RetrievedContextModel).filter(
                RetrievedContextModel.report_id == report_id,
                RetrievedContextModel.source_id == context.source_id,
            ).first()
            if not db_ctx:
                db_ctx = RetrievedContextModel(context_id=f"CTX-{report_id}-{context.source_id}")
                db.add(db_ctx)
            db_ctx.report_id = report_id
            db_ctx.source_id = context.source_id
            db_ctx.source_type = context.source_type
            db_ctx.content = context.content
            db_ctx.relevance_score = context.relevance_score
            db.commit()

    def get_context_for_report(self, report_id: str) -> List[RetrievedContext]:
        with self._get_session() as db:
            rows = db.query(RetrievedContextModel).filter(RetrievedContextModel.report_id == report_id).all()
            return [
                RetrievedContext(
                    source_id=r.source_id,
                    source_type=r.source_type,
                    content=r.content,
                    relevance_score=r.relevance_score,
                )
                for r in rows
            ]

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
            events: List[Event] = []
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
