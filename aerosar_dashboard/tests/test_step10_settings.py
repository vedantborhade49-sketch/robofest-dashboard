import unittest
import sys
import os
from PySide6.QtWidgets import QApplication

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.settings import DashboardSettings
from app.services.settings_service import SettingsService
from app.services.data_service import DataService
from app.ui.views.settings_view import SettingsView
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep10Settings(unittest.TestCase):
    def setUp(self):
        self.service = SettingsService()
        self.service.reset_to_defaults()
        self.data_service = DataService()

    def test_settings_model_defaults_and_validation(self):
        s = DashboardSettings()
        self.assertEqual(s.ground_station_name, "AEROSAR Ground Station")
        self.assertEqual(s.mission_id, "SAR-001")
        self.assertEqual(s.refresh_interval_ms, 500)
        self.assertEqual(s.confidence_threshold, 0.50)
        self.assertEqual(s.max_detections, 20)
        self.assertEqual(s.camera_resolution, "1280 × 720")
        self.assertTrue(s.dark_theme)
        self.assertTrue(s.show_detection_boxes)
        self.assertTrue(s.event_logging_enabled)

        # Validation: Confidence threshold out of bounds
        with self.assertRaises(Exception):
            DashboardSettings(confidence_threshold=1.5)
        with self.assertRaises(Exception):
            DashboardSettings(confidence_threshold=-0.1)

        # Validation: Refresh interval <= 0
        with self.assertRaises(Exception):
            DashboardSettings(refresh_interval_ms=0)

        # Validation: Max detections <= 0
        with self.assertRaises(Exception):
            DashboardSettings(max_detections=-5)

        # Validation: Empty backend URL
        with self.assertRaises(Exception):
            DashboardSettings(backend_url="   ")

    def test_settings_service_operations(self):
        settings = self.service.get_settings()
        self.assertEqual(settings.mission_id, "SAR-001")

        # Update settings
        updated = settings.model_copy()
        updated.mission_id = "SAR-DELTA-02"
        updated.confidence_threshold = 0.65

        signal_received = []
        self.service.settings_updated.connect(lambda s: signal_received.append(s))

        success, msg = self.service.update_settings(updated)
        self.assertTrue(success)
        self.assertEqual(self.service.get_settings().mission_id, "SAR-DELTA-02")
        self.assertEqual(self.service.get_settings().confidence_threshold, 0.65)
        self.assertEqual(len(signal_received), 1)

        # Reset settings
        res = self.service.reset_to_defaults()
        self.assertEqual(res.mission_id, "SAR-001")
        self.assertEqual(self.service.get_settings().mission_id, "SAR-001")
        self.assertEqual(len(signal_received), 2)

    def test_settings_view_widgets_and_layout(self):
        view = SettingsView()
        self.assertIsNotNone(view.input_gs_name)
        self.assertIsNotNone(view.input_mission_id)
        self.assertIsNotNone(view.spin_confidence)
        self.assertIsNotNone(view.combo_model)
        self.assertIsNotNone(view.combo_cam_source)
        self.assertIsNotNone(view.chk_map_grid)
        self.assertIsNotNone(view.btn_apply)
        self.assertIsNotNone(view.btn_reset)

        # Verify initial values loaded into form
        self.assertEqual(view.input_mission_id.text(), "SAR-001")
        self.assertEqual(view.spin_confidence.value(), 0.50)
        self.assertEqual(view.spin_max_detections.value(), 20)
        self.assertEqual(view.combo_model.currentText(), "person_detector")

    def test_settings_view_apply_and_reset(self):
        view = SettingsView()
        initial_events_count = len(self.data_service.get_events())

        # Modify values in UI
        view.input_mission_id.setText("SAR-BRAVO-09")
        view.spin_confidence.setValue(0.70)
        view.spin_max_detections.setValue(35)
        view.chk_boxes.setChecked(False)

        # Click Apply
        view.btn_apply.click()

        # Check service state
        current = self.service.get_settings()
        self.assertEqual(current.mission_id, "SAR-BRAVO-09")
        self.assertEqual(current.confidence_threshold, 0.70)
        self.assertEqual(current.max_detections, 35)
        self.assertFalse(current.show_detection_boxes)

        # Check banner feedback
        self.assertFalse(view.banner.isHidden())
        self.assertIn("✔", view.banner_label.text())

        # Check event logging occurred
        events = self.data_service.get_events()
        self.assertGreater(len(events), initial_events_count)
        last_evt = events[0] # Sorted newest first
        self.assertEqual(last_evt.source, "SYSTEM")
        self.assertEqual(last_evt.level, "SUCCESS")
        self.assertIn("Dashboard settings updated", last_evt.message)

        # Click Reset
        view.btn_reset.click()
        reset_current = self.service.get_settings()
        self.assertEqual(reset_current.mission_id, "SAR-001")
        self.assertEqual(reset_current.confidence_threshold, 0.50)
        self.assertEqual(view.input_mission_id.text(), "SAR-001")
        self.assertEqual(view.spin_confidence.value(), 0.50)
        self.assertFalse(view.banner.isHidden())

    def test_settings_view_validation_error_handling(self):
        view = SettingsView()

        # Input an invalid empty backend URL
        view.input_backend_url.setText("")

        # Click Apply
        view.btn_apply.click()

        # Verify error banner is shown
        self.assertFalse(view.banner.isHidden())
        self.assertIn("⚠", view.banner_label.text())
        self.assertIn("Backend URL cannot be empty", view.banner_label.text())

    def test_navigation_and_regression(self):
        os.environ["DATA_MODE"] = "mock"
        win = MainWindow()
        win.show()

        # Navigate to Settings (page 7)
        win.sidebar.set_active_page(7)
        win._on_page_changed(7, "Settings")
        self.assertEqual(win.stacked_widget.currentIndex(), 7)
        self.assertIn("SETTINGS", win.header.page_title.text())
        self.assertIsInstance(win.stacked_widget.currentWidget(), SettingsView)

        # Verify all views exist and are registered
        self.assertEqual(len(win.views), 8)
        self.assertEqual(win.views[0], win.overview_view)
        self.assertEqual(win.views[1], win.live_feed_view)
        self.assertEqual(win.views[2], win.incidents_view)
        self.assertEqual(win.views[3], win.map_view)
        self.assertEqual(win.views[4], win.telemetry_view)
        self.assertEqual(win.views[5], win.reports_view)
        self.assertEqual(win.views[6], win.event_log_view)
        self.assertEqual(win.views[7], win.settings_view)
        # Close the main window to ensure any background threads/timers are shutdown
        win.close()

if __name__ == "__main__":
    unittest.main()
