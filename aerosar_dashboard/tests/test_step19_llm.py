import unittest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.incident import Incident, Location
from app.models.context import RetrievedContext
from app.rag.models import RAGResult, RetrievalMetadata
from app.llm.config import LLMConfig
from app.llm.models import LLMResponse
from app.llm.prompts import build_prompt, SYSTEM_PROMPT
from tests.mocks.mock_llm_provider import MockLLMProvider
from app.llm.service import LLMService
from app.database.repository import Repository

class MockFailingProvider(MockLLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise ValueError("Simulated API Timeout")

class TestStep19LLM(unittest.TestCase):

    def setUp(self):
        self.incident = Incident(
            incident_id="INC-111",
            type="PERSON_DETECTED",
            confidence=0.91,
            timestamp=datetime.now(timezone.utc),
            location=Location(x=10.0, y=20.0, z=30.0),
            spatial_status="ESTIMATED",
            status="NEW"
        )
        
        self.incident_no_loc = Incident(
            incident_id="INC-222",
            type="PERSON_DETECTED",
            confidence=0.88,
            timestamp=datetime.now(timezone.utc),
            location=None,
            status="NEW"
        )

        self.retrieved_ctx = RAGResult(
            query="person detection",
            incident_id="INC-111",
            retrieved_context=[
                RetrievedContext(
                    source_id="DOC-1",
                    source_type="KB",
                    content="If a person is detected, operator should verify visually.",
                    relevance_score=0.95
                )
            ],
            retrieval_metadata=RetrievalMetadata(top_k=1, retriever="Mock", timestamp="2026-09-29T00:00:00")
        )
        
        self.empty_ctx = RAGResult(
            query="person detection",
            incident_id="INC-111",
            retrieved_context=[],
            retrieval_metadata=RetrievalMetadata(top_k=0, retriever="Mock", timestamp="2026-09-29T00:00:00")
        )

    def test_prompt_generation(self):
        prompt = build_prompt(self.incident, self.retrieved_ctx)
        self.assertIn("PERSON_DETECTED", prompt)
        self.assertIn("91.0%", prompt)
        self.assertIn("X: 10.0", prompt)
        self.assertIn("operator should verify visually", prompt)

    def test_prompt_missing_coordinates(self):
        prompt = build_prompt(self.incident_no_loc, self.empty_ctx)
        self.assertIn("Location: Unavailable", prompt)
        self.assertIn("No additional context retrieved", prompt)

    def test_mock_provider(self):
        provider = MockLLMProvider(LLMConfig())
        prompt = build_prompt(self.incident, self.retrieved_ctx)
        response = provider.generate(SYSTEM_PROMPT, prompt)
        
        self.assertIsInstance(response, LLMResponse)
        self.assertIn("PERSON_DETECTED", response.summary)
        self.assertEqual(response.confidence, 0.91)
        self.assertTrue(len(response.observations) > 0)

    def test_structured_output_validation(self):
        # Valid LLMResponse
        resp = LLMResponse(summary="Test", observations=[], contextual_information=[], recommended_operator_actions=[], severity="LOW", confidence=0.5)
        self.assertEqual(resp.summary, "Test")

        # Invalid should raise ValidationError
        with self.assertRaises(ValidationError):
            LLMResponse(summary=None)  # type: ignore

    def test_hallucination_prevention_behavior(self):
        # Mock provider must not invent coords if none are provided
        provider = MockLLMProvider(LLMConfig())
        prompt = build_prompt(self.incident_no_loc, self.empty_ctx)
        response = provider.generate(SYSTEM_PROMPT, prompt)
        
        # We ensure it notes exact spatial coordinates are unavailable
        self.assertIn("Exact spatial coordinates unavailable", " ".join(response.observations))
        self.assertNotIn("injured", response.summary.lower())

    def test_llm_service_end_to_end(self):
        # Mock repository to prevent actual DB writes during unit test
        class DummyRepo(Repository):
            def save_report(self, report):
                self.saved_report = report
                
        repo = DummyRepo()
        service = LLMService(config=LLMConfig(api_key="test"), repository=repo)
        service.provider = MockLLMProvider(LLMConfig())
        
        report = service.generate_report(self.incident, self.retrieved_ctx)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.incident_id, "INC-111")
        self.assertEqual(report.status, "GENERATED")
        self.assertIn("PERSON_DETECTED", report.ai_report)
        
        self.assertEqual(repo.saved_report, report)

    def test_provider_failure(self):
        service = LLMService(config=LLMConfig(api_key="test"), repository=None)
        service.provider = MockFailingProvider(LLMConfig())
        
        with self.assertRaises(RuntimeError) as context:
            service.generate_report(self.incident, self.retrieved_ctx)
        
        self.assertIn("Simulated API Timeout", str(context.exception))

if __name__ == '__main__':
    unittest.main()
