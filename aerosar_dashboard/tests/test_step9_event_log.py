import unittest
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
import sys
import os

# Add parent directory (aerosar_dashboard) to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.event import Event
from tests.mocks.mock_provider import MockDataProvider
from app.services.data_service import DataService
from app.ui.widgets.event_table import EventTableWidget
from app.ui.widgets.event_detail_panel import EventDetailPanel
from app.ui.views.event_log_view import EventLogView, EventCountersBar
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep9EventLog(unittest.TestCase):
    def test_event_model(self):
        # 1. Full parameter initialization
        ev1 = Event(
            event_id="EVT-1001",
            timestamp=datetime.now(),
            level="WARNING",
            source="AI",
            event_type="DETECTION",
            message="Candidate person detected under foliage shadow",
            mission_id="SAR-001",
            incident_id="INC-002",
            details={"confidence": 0.874, "camera": "Camera-01", "frame": 19120}
        )
        self.assertEqual(ev1.event_id, "EVT-1001")
        self.assertEqual(ev1.level, "WARNING")
        self.assertEqual(ev1.severity, "WARNING")
        self.assertEqual(ev1.source, "AI")
        self.assertEqual(ev1.incident_id, "INC-002")
        self.assertEqual(ev1.details["confidence"], 0.874)

        # 2. Backwards-compatible initialization (severity -> level)
        ev2 = Event(
            timestamp=datetime.now(),
            event_type="SYSTEM",
            message="Mission SAR-001 started",
            severity="INFO"
        )
        self.assertTrue(ev2.event_id.startswith("EVT-"))
        self.assertEqual(ev2.level, "INFO")
        self.assertEqual(ev2.severity, "INFO")
        self.assertEqual(ev2.source, "SYSTEM")

    def test_data_provider_and_service(self):
        provider = MockDataProvider()
        service = DataService(provider)

        events = service.get_events()
        self.assertGreaterEqual(len(events), 20)

        # Test lookup by ID
        first_ev = events[0]
        match = service.get_event(first_ev.event_id)
        self.assertIsNotNone(match)
        self.assertEqual(match.event_id, first_ev.event_id)

        # Test structured event logging
        service.log_event(
            message="Test mission checkpoint reached",
            event_type="MISSION",
            source="MISSION",
            level="SUCCESS",
            mission_id="SAR-001",
            details={"checkpoint": "CP-1", "altitude": 14.8}
        )
        updated_events = service.get_events()
        latest = updated_events[0]
        self.assertEqual(latest.message, "Test mission checkpoint reached")
        self.assertEqual(latest.level, "SUCCESS")
        self.assertEqual(latest.source, "MISSION")
        self.assertEqual(latest.details["checkpoint"], "CP-1")

    def test_event_table_widget(self):
        provider = MockDataProvider()
        events = provider.get_events()

        table = EventTableWidget()
        table.set_events(events)

        self.assertEqual(table.rowCount(), len(events))
        self.assertEqual(table.columnCount(), 6)

        # Verify selection emission
        selected = []
        table.event_selected.connect(lambda e: selected.append(e))
        table.selectRow(1)
        self.assertGreaterEqual(len(selected), 1)

        # Verify programmatic selection
        target_id = events[2].event_id
        table.select_event_by_id(target_id)
        self.assertEqual(table.get_selected_event().event_id, target_id)

    def test_event_detail_panel(self):
        panel = EventDetailPanel()
        ev = Event(
            event_id="EVT-0010",
            timestamp=datetime.now(),
            level="INFO",
            source="AI",
            event_type="AI",
            message="Person detected with confidence 94.2%",
            mission_id="SAR-001",
            incident_id="INC-001",
            details={"confidence": 0.942, "camera": "Camera-01", "frame": 18342}
        )
        panel.show_event(ev)

        self.assertEqual(panel.val_event_id.text(), "EVT-0010")
        self.assertEqual(panel.val_level_badge.text(), "INFO")
        self.assertEqual(panel.val_source_badge.text(), "AI")
        self.assertEqual(panel.val_incident.text(), "INC-001")
        self.assertEqual(panel.val_message.text(), "Person detected with confidence 94.2%")
        self.assertTrue(panel.btn_view_incident.isEnabled())

        # Test incident navigation signal
        nav_targets = []
        panel.view_incident_requested.connect(lambda inc_id: nav_targets.append(inc_id))
        panel.btn_view_incident.click()
        self.assertEqual(len(nav_targets), 1)
        self.assertEqual(nav_targets[0], "INC-001")

        # Test event without incident
        ev_no_inc = Event(message="System heartbeat", source="SYSTEM", level="INFO")
        panel.show_event(ev_no_inc)
        self.assertFalse(panel.btn_view_incident.isEnabled())

    def test_event_log_view_filters_and_search(self):
        view = EventLogView()

        # 1. Counters verification
        self.assertGreater(int(view.counters_bar.val_total.text()), 0)

        # 2. Level filter testing
        view._on_level_filter_changed("WARNING")
        self.assertEqual(view.active_level_filter, "WARNING")
        for row in range(view.event_table.rowCount()):
            ev = view.event_table._displayed_events[row]
            self.assertEqual(ev.level.upper(), "WARNING")

        view._on_level_filter_changed("ALL")
        self.assertEqual(view.event_table.rowCount(), len(view.all_events))

        # 3. Source filter testing
        view._on_source_filter_changed("CAMERA")
        self.assertEqual(view.active_source_filter, "CAMERA")
        for row in range(view.event_table.rowCount()):
            ev = view.event_table._displayed_events[row]
            self.assertEqual(ev.source.upper(), "CAMERA")

        # 4. Keyword search testing
        view._on_clear_filters()
        view._on_search_text_changed("INC-001")
        self.assertGreater(view.event_table.rowCount(), 0)
        for row in range(view.event_table.rowCount()):
            ev = view.event_table._displayed_events[row]
            self.assertTrue("inc-001" in ev.message.lower() or "inc-001" in (ev.incident_id or "").lower())

        # 5. Clear filters testing
        view._on_clear_filters()
        self.assertEqual(view.active_level_filter, "ALL")
        self.assertEqual(view.active_source_filter, "ALL SOURCES")
        self.assertEqual(view.active_search_query, "")
        self.assertEqual(view.event_table.rowCount(), len(view.all_events))

    def test_navigation_and_regression(self):
        os.environ["DATA_MODE"] = "mock"
        win = MainWindow()
        win.show()

        # 1. Test navigating to Event Log page (index 6)
        win.sidebar.set_active_page(6)
        win._on_page_changed(6, "Event Log")
        self.assertEqual(win.stacked_widget.currentIndex(), 6)
        self.assertIn("EVENT LOG", win.header.page_title.text())

        # 2. Test cross-page jump from Event Log to Incidents
        win.event_log_view.navigate_to_incidents.emit("INC-001")
        self.assertEqual(win.stacked_widget.currentIndex(), 2)
        self.assertIn("INCIDENTS", win.header.page_title.text())

        # 3. Verify all 8 pages still navigate cleanly
        pages = ["Overview", "Live Feed", "Incidents", "Map", "Telemetry", "Reports", "Event Log", "Settings"]
        for idx, name in enumerate(pages):
            win.sidebar.set_active_page(idx)
            win._on_page_changed(idx, name)
            self.assertEqual(win.stacked_widget.currentIndex(), idx)

        win.close()
        app.processEvents()

if __name__ == "__main__":
    unittest.main()
