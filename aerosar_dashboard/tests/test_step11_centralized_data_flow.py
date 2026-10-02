import unittest
import sys
import os
from datetime import datetime
from PySide6.QtWidgets import QApplication

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.app_state import AppState
from app.models.incident import Incident, Location
from app.models.telemetry import TelemetryState
from app.core.state_manager import StateManager
from app.core.update_loop import CentralUpdateLoop
from app.services.data_service import DataService
from tests.mocks.mock_provider import MockDataProvider
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep11CentralizedDataFlow(unittest.TestCase):
    def setUp(self):
        self.provider = MockDataProvider()
        self.state_mgr = StateManager.instance()
        self.state_mgr.initialize_from_provider(self.provider)
        self.data_service = DataService(self.provider)

    def test_app_state_initialization(self):
        state = self.state_mgr.get_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, AppState)
        self.assertEqual(state.mission.mission_id, "SAR-001")
        self.assertIsNotNone(state.drone)
        self.assertIsNotNone(state.camera)
        self.assertIsNotNone(state.ai)
        self.assertIsNotNone(state.telemetry)
        self.assertIsNotNone(state.system)
        self.assertIsNotNone(state.map_state)
        self.assertGreater(len(state.incidents), 0)
        self.assertGreater(len(state.events), 0)
        self.assertGreater(len(state.reports), 0)
        self.assertFalse(state.is_stale)
        self.assertIsInstance(state.last_updated, datetime)

    def test_state_manager_getters_and_ssot(self):
        # All getters retrieve slices from the central AppState
        self.assertEqual(self.state_mgr.get_mission().mission_id, "SAR-001")
        self.assertEqual(self.data_service.get_mission_data().mission_id, "SAR-001")

        incidents = self.data_service.get_incidents()
        self.assertEqual(incidents, self.state_mgr.get_incidents())

        telem = self.data_service.get_telemetry_state()
        self.assertEqual(telem.flight.altitude, self.state_mgr.get_telemetry().flight.altitude)

    def test_incident_cascade_coherence(self):
        # Adding an incident must atomically link an Event and a Report
        inc_id = "INC-TEST-88"
        new_inc = Incident(
            incident_id=inc_id,
            type="SURVIVOR",
            location=Location(x=15.0, y=20.0, z=14.5),
            confidence=0.94,
            status="CONFIRMED",
            evidence_image="test_thermal.jpg",
            timestamp=datetime.now()
        )

        inc_signals = []
        evt_signals = []
        rpt_signals = []

        self.data_service.incident_added.connect(lambda inc: inc_signals.append(inc))
        self.data_service.event_added.connect(lambda ev: evt_signals.append(ev))
        self.data_service.report_added.connect(lambda rpt: rpt_signals.append(rpt))

        # Add incident through DataService
        self.data_service.add_incident(new_inc)

        # 1. Incident is present in incidents list
        self.assertIn(new_inc, self.data_service.get_incidents())
        self.assertEqual(len(inc_signals), 1)

        # 2. Associated Event was generated and linked to incident_id
        linked_events = [e for e in self.data_service.get_events() if e.incident_id == inc_id]
        self.assertGreater(len(linked_events), 0)
        self.assertEqual(linked_events[0].source, "AI")
        self.assertEqual(linked_events[0].level, "WARNING")
        self.assertEqual(len(evt_signals), 1)

        # 3. Associated Report was generated and linked to incident_id
        linked_report = self.data_service.get_report_by_incident_id(inc_id)
        self.assertIsNotNone(linked_report)
        self.assertEqual(linked_report.incident_id, inc_id)
        self.assertEqual(linked_report.incident_summary.type, "SURVIVOR")
        self.assertEqual(linked_report.incident_type, "SURVIVOR")
        self.assertEqual(len(rpt_signals), 1)

    def test_telemetry_signal_propagation(self):
        telemetry_events = []
        self.data_service.telemetry_updated.connect(lambda t: telemetry_events.append(t))

        # Trigger tick
        self.data_service.update_loop.trigger_immediate_tick()
        self.assertGreater(len(telemetry_events), 0)
        self.assertIsInstance(telemetry_events[-1], TelemetryState)

    def test_smooth_simulation_loop(self):
        initial_pos = self.state_mgr.get_drone()
        initial_batt = initial_pos.battery

        # Run several ticks of central update loop
        for _ in range(5):
            self.data_service.update_loop.trigger_immediate_tick()

        updated_pos = self.state_mgr.get_drone()
        # Battery should decrease smoothly, not wildly jump
        self.assertLessEqual(updated_pos.battery, initial_batt)
        self.assertGreater(updated_pos.battery, initial_batt - 1.0)

    def test_stale_data_detection(self):
        self.assertFalse(self.state_mgr.get_state().is_stale)
        self.state_mgr.set_stale(True)
        self.assertTrue(self.state_mgr.get_state().is_stale)
        self.state_mgr.set_stale(False)
        self.assertFalse(self.state_mgr.get_state().is_stale)

    def test_full_dashboard_navigation_and_views_integrity(self):
        os.environ["DATA_MODE"] = "mock"
        win = MainWindow()
        win.show()

        # All 8 navigation tabs function and are registered
        self.assertEqual(len(win.views), 8)
        for page_idx in range(8):
            win.sidebar.set_active_page(page_idx)
            win._on_page_changed(page_idx, f"Page-{page_idx}")
            self.assertEqual(win.stacked_widget.currentIndex(), page_idx)

        # Trigger tick while window is open — no crashes
        self.data_service.update_loop.trigger_immediate_tick()
        # Cleanup: close UI and stop central update loop to avoid background threads
        try:
            win.close()
        except Exception:
            pass
        try:
            self.data_service.update_loop.stop()
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
