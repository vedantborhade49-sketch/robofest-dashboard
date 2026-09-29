import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock

from app.models.incident import Incident, Location
from app.intelligence.service import IntelligenceService
from app.llm.config import LLMConfig
from app.llm.mock_provider import MockLLMProvider
from app.llm.cloud_provider import CloudLLMProvider
from app.llm.service import LLMService
from app.rag.rag_service import RAGService
from app.models.report import Report
from datetime import datetime, timezone

class TestStep20Intelligence(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = Incident(
            incident_id="INC-TEST-001",
            type="PERSON_DETECTED",
            confidence=0.91,
            timestamp=datetime.now(timezone.utc),
            location=Location(x=12.4, y=5.7, z=2.1),
            status="NEW"
        )
        # Force mock provider
        self.config = LLMConfig(provider="mock")
        
    async def test_intelligence_pipeline_mock(self):
        rag = RAGService()
        llm = LLMService(config=self.config)
        intelligence = IntelligenceService(rag_service=rag, llm_service=llm)
        
        # Test full flow: Incident -> RAG -> LLM -> Report
        # Ensure that no realtime websocket manager tries to broadcast if it's not setup correctly
        # We can patch ws_manager to just track calls
        with patch('app.intelligence.service.ws_manager.broadcast_json') as mock_broadcast:
            report = await intelligence.generate_incident_report(self.incident)
            self.assertIsInstance(report, Report)
            self.assertEqual(report.incident_id, self.incident.incident_id)
            self.assertEqual(report.status, "GENERATED")
            self.assertEqual(report.model_name, "mock-rag-llm")
            
            # Check if websocket was called
            mock_broadcast.assert_called_once()
            call_arg = mock_broadcast.call_args[0][0]
            self.assertEqual(call_arg["event_type"], "REPORT_GENERATED")
            self.assertEqual(call_arg["payload"]["report_id"], report.report_id)
            
    def test_cloud_provider_config(self):
        config = LLMConfig(provider="cloud", api_key="test-key")
        llm = LLMService(config=config)
        self.assertIsInstance(llm.provider, CloudLLMProvider)
        self.assertEqual(llm.provider.config.api_key, "test-key")
        
    @unittest.skipIf(not os.getenv("RUN_LLM_INTEGRATION_TEST"), "Skipping real LLM integration test")
    async def test_real_llm_integration(self):
        # This only runs if RUN_LLM_INTEGRATION_TEST is set
        config = LLMConfig(provider="cloud") # expects env vars to be set
        rag = RAGService()
        llm = LLMService(config=config)
        intelligence = IntelligenceService(rag_service=rag, llm_service=llm)
        
        with patch('app.intelligence.service.ws_manager.broadcast_json'):
            report = await intelligence.generate_incident_report(self.incident)
            self.assertIsInstance(report, Report)
            self.assertTrue(len(report.ai_report) > 0)
            self.assertIn("PERSON_DETECTED", report.ai_report)

if __name__ == '__main__':
    unittest.main()
