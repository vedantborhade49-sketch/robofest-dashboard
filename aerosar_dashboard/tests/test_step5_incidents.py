import unittest
from datetime import datetime
from PySide6.QtWidgets import QApplication
import sys
import os
import math

# Add parent directory (aerosar_dashboard) to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.detection import Detection, BoundingBox
from app.models.incident import Incident, Location
from app.services.incident_engine import IncidentEngine
from app.services.data_service import DataService
from tests.mocks.mock_provider import MockDataProvider
from app.ui.widgets.incident_list import IncidentList
from app.ui.widgets.incident_detail import IncidentDetail
from app.ui.views.incidents_view import IncidentsView
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep5Incidents(unittest.TestCase):
    def test_incident_model(self):
        loc = Location(x=12.4, y=8.7, z=14.8)
        bbox = BoundingBox(x=0.5, y=0.5, width=0.2, height=0.3)
        inc = Incident(
            incident_id="INC-001",
            mission_id="SAR-001",
            type="PERSON DETECTED",
            confidence=0.94,
            timestamp=datetime.now(),
            bbox=bbox,
            location=loc,
            evidence_image="EV-INC-001.jpg",
            status="CONFIRMED"
        )
        self.assertEqual(inc.incident_id, "INC-001")
        self.assertEqual(inc.location.x, 12.4)
        self.assertEqual(inc.location.y, 8.7)
        self.assertEqual(inc.location.z, 14.8)
        self.assertTrue(math.isclose(inc.bbox.width, 0.2, abs_tol=1e-5))
        self.assertEqual(inc.status, "CONFIRMED")

    def test_incident_engine_separation(self):
        engine = IncidentEngine(initial_counter=10)
        det = Detection(
            detection_id="DET-01",
            class_name="person",
            confidence=0.95,
            bbox=BoundingBox(x=0.5, y=0.5, width=0.2, height=0.3),
            timestamp=datetime.now()
        )
        loc = Location(x=15.0, y=20.0, z=12.0)
        incident = engine.process_detection(det, loc, mission_id="SAR-001", status="NEW")
        
        self.assertIsNotNone(incident)
        self.assertEqual(incident.incident_id, "INC-011")
        self.assertEqual(incident.mission_id, "SAR-001")
        self.assertIn("PERSON", incident.type)
        self.assertEqual(incident.confidence, 0.95)
        self.assertEqual(incident.location.x, 15.0)
        self.assertEqual(incident.status, "NEW")
        self.assertEqual(incident.evidence_image, "EV-INC-011.jpg")

    def test_mock_data_provider_incidents(self):
        provider = MockDataProvider()
        incidents = provider.get_incidents()
        self.assertGreaterEqual(len(incidents), 3)

        ids = [i.incident_id for i in incidents]
        self.assertIn("INC-001", ids)
        self.assertIn("INC-002", ids)
        self.assertIn("INC-003", ids)

        inc1 = next(i for i in incidents if i.incident_id == "INC-001")
        self.assertEqual(inc1.status, "CONFIRMED")
        self.assertEqual(inc1.confidence, 0.94)
        self.assertEqual(inc1.location.x, 12.4)
        self.assertEqual(inc1.location.y, 8.7)
        self.assertEqual(inc1.location.z, 14.8)

        inc2 = next(i for i in incidents if i.incident_id == "INC-002")
        self.assertEqual(inc2.status, "REVIEW")
        self.assertEqual(inc2.confidence, 0.87)

        inc3 = next(i for i in incidents if i.incident_id == "INC-003")
        self.assertEqual(inc3.status, "NEW")
        self.assertEqual(inc3.confidence, 0.91)

    def test_data_service_events(self):
        ds = DataService()
        initial_event_count = len(ds.get_events())
        ds.log_event("Testing incident event generation", "INCIDENT", "INFO")
        new_event_count = len(ds.get_events())
        self.assertEqual(new_event_count, initial_event_count + 1)

    def test_incident_list_and_detail_widgets(self):
        provider = MockDataProvider()
        incidents = provider.get_incidents()

        ilist = IncidentList()
        ilist.set_incidents(incidents)
        self.assertEqual(len(ilist._row_widgets), len(incidents))

        # Test filtering
        ilist.set_filter("CONFIRMED")
        self.assertEqual(len(ilist._row_widgets), 1)
        self.assertEqual(ilist._row_widgets[0].incident.incident_id, "INC-001")

        ilist.set_filter("ALL")
        self.assertEqual(len(ilist._row_widgets), len(incidents))

        # Test detail population
        idetail = IncidentDetail()
        inc1 = incidents[0]
        inc1.spatial_status = "CONFIRMED"
        idetail.show_incident(inc1)
        self.assertEqual(idetail.id_lbl.text(), inc1.incident_id)
        self.assertIn("12.4", idetail.lbl_x.text())
        self.assertIn("CONFIRMED", idetail.status_badge.text())

    def test_incidents_view_counters_and_actions(self):
        # We need to refresh or clear to ensure predictable tests
        DataService._instance = None
        ds = DataService(provider=MockDataProvider())
        
        view = IncidentsView()
        current_incidents = view.data_service.get_incidents()
        
        self.assertEqual(view.counters_bar.val_total.text(), str(len(current_incidents)))
        self.assertEqual(view.counters_bar.val_confirmed.text(), str(sum(1 for i in current_incidents if i.status == "CONFIRMED")))
        self.assertEqual(view.counters_bar.val_new.text(), str(sum(1 for i in current_incidents if i.status == "NEW")))
        self.assertEqual(view.counters_bar.val_review.text(), str(sum(1 for i in current_incidents if i.status == "REVIEW")))
        self.assertEqual(view.counters_bar.val_resolved.text(), str(sum(1 for i in current_incidents if i.status == "RESOLVED")))

        # Test selection & actions
        incidents = view.data_service.get_incidents()
        inc2 = [i for i in incidents if i.incident_id == "INC-002"][0]
        view.incident_list.select_incident(inc2)
        self.assertEqual(view.incident_detail.id_lbl.text(), "INC-002")

        view.incident_detail.btn_map.click()
        self.assertFalse(view.incident_detail.action_banner.isHidden())

        view.incident_detail.btn_report.click()
        self.assertFalse(view.incident_detail.action_banner.isHidden())

if __name__ == "__main__":
    unittest.main()
