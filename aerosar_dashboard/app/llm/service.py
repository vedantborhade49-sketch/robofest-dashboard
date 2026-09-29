import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.incident import Incident
from app.models.report import Report, IncidentSummary
from app.rag.models import RAGResult
from app.llm.config import LLMConfig
from app.llm.provider import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.prompts import build_prompt, SYSTEM_PROMPT
from app.database.repository import Repository

logger = logging.getLogger(__name__)

class LLMService:
    """
    Independent service for generating LLM-based incident reports.
    Coordinates incident data, retrieved context, and the configured LLM provider.
    """

    def __init__(self, config: Optional[LLMConfig] = None, repository: Optional[Repository] = None):
        self.config = config or LLMConfig()
        self.repository = repository or Repository()
        
        # Instantiate provider based on config
        if self.config.provider.lower() == "mock":
            self.provider: LLMProvider = MockLLMProvider(self.config)
        else:
            # Fallback to mock if an unknown provider is specified
            logger.warning(f"Provider '{self.config.provider}' not recognized. Falling back to MockLLMProvider.")
            self.provider: LLMProvider = MockLLMProvider(self.config)

    def generate_report(self, incident: Incident, retrieved_context: RAGResult) -> Report:
        """
        Generates an incident report from the provided incident and context.
        """
        if not incident:
            raise ValueError("Incident is required to generate a report.")
            
        try:
            # 1. Build prompts
            user_prompt = build_prompt(incident, retrieved_context)
            
            # 2. Call LLM provider
            llm_response = self.provider.generate(SYSTEM_PROMPT, user_prompt)
            
            # 3. Format the structured response for the existing UI
            ai_report_text = llm_response.to_markdown()
            
            # 4. Construct Report model
            summary = IncidentSummary(
                incident_id=incident.incident_id,
                type=incident.type,
                confidence=incident.confidence,
                timestamp=incident.timestamp,
                location=incident.location,
                status=incident.status
            )
            
            report = Report(
                report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
                incident_id=incident.incident_id,
                mission_id=incident.mission_id,
                status="GENERATED",
                generated_at=datetime.now(timezone.utc),
                incident_type=incident.type,
                confidence=llm_response.confidence,
                incident_summary=summary,
                ai_report=ai_report_text,
                context_sources=retrieved_context.retrieved_context if retrieved_context else [],
                evidence_image=incident.evidence_image,
                human_review_status="PENDING REVIEW",
                model_name=self.config.model_name
            )
            
            # 5. Persist to repository
            try:
                self.repository.save_report(report)
            except Exception as e:
                logger.error(f"Failed to persist generated report for incident {incident.incident_id}: {e}")
                # We still return the report even if persistence fails, so the system doesn't crash completely.
                
            return report
            
        except Exception as e:
            logger.error(f"LLM generation failed for incident {incident.incident_id}: {e}")
            raise RuntimeError(f"Failed to generate LLM report: {str(e)}") from e
