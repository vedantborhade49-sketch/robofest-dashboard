import logging
from typing import Optional
from app.models.incident import Incident
from app.models.report import Report
from app.rag.rag_service import RAGService
from app.llm.service import LLMService
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

logger = logging.getLogger(__name__)

class IntelligenceService:
    """
    Orchestrates the Full RAG + LLM Integration for AEROSAR.
    Coordinates between Incident data, RAG retrieval, LLM generation, and Realtime events.
    """
    def __init__(self, rag_service: Optional[RAGService] = None, llm_service: Optional[LLMService] = None):
        self.rag_service = rag_service or RAGService()
        self.llm_service = llm_service or LLMService()

    async def generate_incident_report(self, incident: Incident) -> Report:
        """
        Main orchestration flow for report generation.
        1. Retrieve context via RAG
        2. Generate report via LLM
        3. Persist (handled by LLMService currently)
        4. Broadcast WebSocket event
        """
        logger.info(f"Generating intelligence report for incident {incident.incident_id}")

        # 1. Retrieve Context using RAG
        rag_result = self.rag_service.retrieve_for_incident(incident)

        # 2. Generate Report using LLM (also persists it)
        report = self.llm_service.generate_report(incident, rag_result)

        # 3. Publish WebSocket event
        event_bus.publish(
            EventType.REPORT_GENERATED,
            payload={
                "report_id": report.report_id,
                "incident_id": incident.incident_id,
                "status": report.status
            },
            mission_id=incident.mission_id
        )

        return report
