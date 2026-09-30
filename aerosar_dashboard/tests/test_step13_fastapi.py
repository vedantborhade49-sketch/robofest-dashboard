import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.database import database
from app.api.app import app


class TestFastAPIStep13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["AEROSAR_DB_PATH"] = cls.temp_db.name

        database.engine = None
        database.SessionLocal = None
        database._db_initialized = False
        database.init_db(cls.temp_db.name)

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        try:
            if os.path.exists(cls.temp_db.name):
                os.remove(cls.temp_db.name)
        except OSError:
            pass

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_system_status(self):
        response = self.client.get("/api/v1/system/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["backend"], "online")
        self.assertEqual(payload["database"], "connected")

    def test_mission_flow(self):
        payload = {"mission_id": "SAR-API-001", "mission_name": "API Mission Test"}
        create_res = self.client.post("/api/v1/missions", json=payload)
        self.assertEqual(create_res.status_code, 200)

        list_res = self.client.get("/api/v1/missions")
        self.assertEqual(list_res.status_code, 200)
        missions = list_res.json()
        self.assertTrue(any(item["mission_id"] == "SAR-API-001" for item in missions))

    def test_incident_flow(self):
        payload = {
            "incident_id": "INC-API-001",
            "mission_id": "SAR-API-001",
            "type": "person",
            "confidence": 0.942,
            "timestamp": "2026-09-28T12:00:00Z",
            "location": {"x": 12.4, "y": -6.8, "z": 3.2},
            "status": "NEW",
        }
        create_res = self.client.post("/api/v1/incidents", json=payload)
        self.assertEqual(create_res.status_code, 200)

        list_res = self.client.get("/api/v1/incidents")
        self.assertEqual(list_res.status_code, 200)
        incidents = list_res.json()
        self.assertTrue(any(item["incident_id"] == "INC-API-001" for item in incidents))

        patch_res = self.client.patch("/api/v1/incidents/INC-API-001", json={"status": "REVIEW"})
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "REVIEW")

    def test_report_and_context_flow(self):
        report_payload = {
            "report_id": "RPT-API-001",
            "incident_id": "INC-API-001",
            "mission_id": "SAR-API-001",
            "status": "GENERATED",
            "generated_at": "2026-09-28T12:10:00Z",
            "incident_type": "person",
            "confidence": 0.942,
            "incident_summary": {
                "incident_id": "INC-API-001",
                "type": "person",
                "confidence": 0.942,
                "timestamp": "2026-09-28T12:00:00Z",
                "location": {"x": 12.4, "y": -6.8, "z": 3.2},
                "status": "NEW",
            },
            "ai_report": "Detected a person at the north-west sector.",
            "context_sources": [
                {"source_id": "SRC-1", "source_type": "LOG", "content": "Recent patrol log", "relevance_score": 0.88}
            ],
            "evidence_image": "evidence/inc-001.jpg",
            "human_review_status": "PENDING REVIEW",
            "model_name": "SIMULATED-API-LLM",
        }

        create_res = self.client.post("/api/v1/reports", json=report_payload)
        self.assertEqual(create_res.status_code, 200)

        get_res = self.client.get("/api/v1/reports")
        self.assertEqual(get_res.status_code, 200)
        reports = get_res.json()
        self.assertTrue(any(item["report_id"] == "RPT-API-001" for item in reports))

        context_res = self.client.get("/api/v1/reports/RPT-API-001/context")
        self.assertEqual(context_res.status_code, 200)
        context_items = context_res.json()
        self.assertTrue(any(item["source_id"] == "SRC-1" for item in context_items))

    def test_events_and_telemetry(self):
        event_payload = {
            "event_id": "EVT-API-001",
            "timestamp": "2026-09-28T12:15:00Z",
            "level": "WARNING",
            "source": "SYSTEM",
            "event_type": "API",
            "message": "API test event logged",
            "severity": "WARNING",
            "mission_id": "SAR-API-001",
            "details": {"origin": "fastapi-test"},
        }
        event_res = self.client.post("/api/v1/events", json=event_payload)
        self.assertEqual(event_res.status_code, 200)

        list_events = self.client.get("/api/v1/events")
        self.assertEqual(list_events.status_code, 200)
        self.assertTrue(any(item["event_id"] == "EVT-API-001" for item in list_events.json()))

        from app.models.telemetry import TelemetryState
        telem = TelemetryState()
        telem.position.z = 120.0
        
        from unittest.mock import patch
        with patch('app.core.state_manager.StateManager.get_telemetry', return_value=telem):
            telemetry_res = self.client.get("/api/v1/telemetry/position")
            self.assertEqual(telemetry_res.status_code, 200)
            self.assertIn("z", telemetry_res.json())
            self.assertEqual(telemetry_res.json()["z"], 120.0)

    def test_status_endpoints(self):
        self.assertEqual(self.client.get("/api/v1/drone/status").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/camera/status").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/ai/status").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/drone/position").status_code, 200)

    def test_missing_record_returns_404(self):
        response = self.client.get("/api/v1/incidents/NOT-REAL")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
