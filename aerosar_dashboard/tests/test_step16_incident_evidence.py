import os
import tempfile
import unittest
from datetime import datetime, timezone

from app.models.incident import Incident, IncidentStatus, Location
from app.models.evidence import Evidence, EvidenceType
from app.services.evidence_service import EvidenceService


class TestStep16IncidentEvidence(unittest.TestCase):
    def test_incident_status_transitions_are_validated(self):
        self.assertTrue(IncidentStatus.validate_transition(IncidentStatus.NEW, IncidentStatus.REVIEW))
        self.assertTrue(IncidentStatus.validate_transition(IncidentStatus.REVIEW, IncidentStatus.CONFIRMED))
        self.assertTrue(IncidentStatus.validate_transition(IncidentStatus.REVIEW, IncidentStatus.DISMISSED))
        self.assertTrue(IncidentStatus.validate_transition(IncidentStatus.CONFIRMED, IncidentStatus.RESOLVED))
        self.assertFalse(IncidentStatus.validate_transition(IncidentStatus.NEW, IncidentStatus.RESOLVED))
        self.assertFalse(IncidentStatus.validate_transition(IncidentStatus.RESOLVED, IncidentStatus.REVIEW))

    def test_evidence_service_generates_safe_paths_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = EvidenceService(base_dir=tmpdir)
            incident = Incident(
                incident_id="INC-016",
                mission_id="SAR-001",
                type="PERSON DETECTED",
                confidence=0.87,
                timestamp=datetime.now(timezone.utc),
                location=Location(x=12.0, y=6.0, z=2.5),
                status=IncidentStatus.NEW,
            )

            evidence_path = service.generate_evidence_path(incident.incident_id)
            self.assertTrue(os.path.isabs(evidence_path))
            self.assertIn("INC-016", evidence_path)
            self.assertTrue(evidence_path.startswith(tmpdir))

            metadata = service.create_evidence_metadata(
                incident=incident,
                evidence_type=EvidenceType.ANNOTATED_FRAME,
                file_path=evidence_path,
                source="camera-01",
                description="Annotated detection frame",
            )

            self.assertEqual(metadata.incident_id, "INC-016")
            self.assertEqual(metadata.type, EvidenceType.ANNOTATED_FRAME)
            self.assertTrue(metadata.file_path.startswith(tmpdir))
            self.assertTrue(service.is_invalid_path("../../../etc/passwd"))
            self.assertTrue(service.is_invalid_path("../bad/path"))

    def test_evidence_metadata_and_status_service_work_together(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = EvidenceService(base_dir=tmpdir)
            incident = Incident(
                incident_id="INC-017",
                mission_id="SAR-001",
                type="PERSON DETECTED",
                confidence=0.91,
                timestamp=datetime.now(timezone.utc),
                location=Location(x=3.0, y=1.5, z=1.0),
                status=IncidentStatus.NEW,
            )

            evidence = service.create_evidence_record(
                incident=incident,
                evidence_type=EvidenceType.ANNOTATED_FRAME,
                source="camera-01",
                description="Operator review frame",
            )

            self.assertEqual(evidence.incident_id, "INC-017")
            self.assertEqual(evidence.type, EvidenceType.ANNOTATED_FRAME)
            self.assertTrue(os.path.exists(evidence.file_path))


if __name__ == "__main__":
    unittest.main()
