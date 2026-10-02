import unittest
from datetime import datetime
from PySide6.QtWidgets import QApplication
import sys
import os

# Add parent directory (aerosar_dashboard) to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.telemetry import (
    Telemetry, TelemetryState, FlightTelemetry, PositionTelemetry,
    PowerTelemetry, CommunicationTelemetry, SensorStatus,
    FlightControllerStatus, CompanionComputerStatus, TelemetryHistoryPoint
)
from app.services.data_service import DataService
from tests.mocks.mock_provider import MockDataProvider
from app.ui.widgets.telemetry_panels import (
    FlightTelemetryPanel, PositionPanel, PowerPanel,
    CommunicationPanel, SensorStatusPanel, FlightControllerPanel,
    CompanionComputerPanel
)
from app.ui.widgets.telemetry_graph import TelemetryGraphSection
from app.ui.views.telemetry_view import TelemetryView
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep7Telemetry(unittest.TestCase):
    def test_telemetry_models(self):
        f = FlightTelemetry(altitude=14.8, speed=3.2, vertical_speed=0.4, heading=127.0, roll=0.8, pitch=-1.2, yaw=127.0)
        self.assertEqual(f.altitude, 14.8)
        self.assertEqual(f.speed, 3.2)
        self.assertEqual(f.heading, 127.0)

        p = PositionTelemetry(x=12.4, y=8.7, z=14.8, frame="LOCAL / SLAM", heading=127.0)
        self.assertEqual(p.x, 12.4)
        self.assertEqual(p.frame, "LOCAL / SLAM")

        pow_m = PowerTelemetry(battery_percent=82.0, voltage=15.7, current=8.4, power_watts=132.0, status="GOOD")
        self.assertEqual(pow_m.battery_percent, 82.0)
        self.assertEqual(pow_m.status, "GOOD")

        comm = CommunicationTelemetry(link_status="CONNECTED", signal_percent=87.0, latency_ms=38.0, packet_loss_percent=0.2)
        self.assertEqual(comm.signal_percent, 87.0)
        self.assertEqual(comm.link_status, "CONNECTED")

        sens = SensorStatus(imu="READY", barometer="READY", camera="READY", lidar="STANDBY", gps="NOT REQUIRED", slam="STANDBY")
        self.assertEqual(sens.gps, "NOT REQUIRED")

        fc = FlightControllerStatus(status="CONNECTED", autopilot="ARDUPILOT", mode="GUIDED", armed=False, link="CONNECTED")
        self.assertEqual(fc.autopilot, "ARDUPILOT")
        self.assertFalse(fc.armed)

        cc = CompanionComputerStatus(device="RASPBERRY PI 5", status="ONLINE", cpu_percent=34.0, ram_percent=42.0, temperature_c=51.0)
        self.assertEqual(cc.device, "RASPBERRY PI 5")

        state = TelemetryState(
            flight=f, position=p, power=pow_m, communication=comm,
            sensors=sens, flight_controller=fc, companion_computer=cc
        )
        self.assertEqual(state.flight.altitude, 14.8)

    def test_mock_provider_telemetry_state(self):
        provider = MockDataProvider()
        state = provider.get_telemetry_state()

        self.assertIsInstance(state, TelemetryState)
        self.assertAlmostEqual(state.flight.altitude, 14.8, delta=2.0)
        self.assertAlmostEqual(state.power.battery_percent, 82.0, delta=2.0)
        self.assertEqual(state.position.frame, "LOCAL / SLAM")
        self.assertEqual(state.flight_controller.autopilot, "ARDUPILOT")
        self.assertEqual(state.companion_computer.device, "RASPBERRY PI 5")
        self.assertGreaterEqual(len(state.history), 10)

        # Legacy model backwards compatibility
        legacy = provider.get_telemetry()
        self.assertIsInstance(legacy, Telemetry)
        self.assertAlmostEqual(legacy.altitude, 14.8, delta=2.0)

    def test_telemetry_panels(self):
        state = MockDataProvider().get_telemetry_state()

        # Flight panel
        fp = FlightTelemetryPanel()
        fp.update_data(state.flight)
        self.assertIn("m", fp.val_alt.text())
        self.assertIn("m/s", fp.val_spd.text())

        # Position panel
        pp = PositionPanel()
        pp.update_data(state.position)
        self.assertIn("m", pp.val_x.text())

        # Power panel
        pwp = PowerPanel()
        pwp.update_data(state.power)
        self.assertIn("%", pwp.val_battery.text())
        self.assertEqual(pwp.val_status.text(), "GOOD")

        # Comm panel
        cp = CommunicationPanel()
        cp.update_data(state.communication)
        self.assertEqual(cp.val_link.text(), "CONNECTED")

        # Sensor panel
        sp = SensorStatusPanel()
        sp.update_data(state.sensors)
        self.assertIn("READY", sp.p_imu.text())
        self.assertIn("NOT REQUIRED", sp.p_gps.text())

        # FC panel
        fcp = FlightControllerPanel()
        fcp.update_data(state.flight_controller)
        self.assertEqual(fcp.val_auto.text(), "ARDUPILOT")
        self.assertEqual(fcp.val_armed.text(), "NO")

        # Companion computer panel
        ccp = CompanionComputerPanel()
        ccp.update_data(state.companion_computer)
        self.assertEqual(ccp.val_dev.text(), "RASPBERRY PI 5")

    def test_telemetry_graph_section(self):
        gs = TelemetryGraphSection()
        provider = MockDataProvider()
        state = provider.get_telemetry_state()
        gs.update_history(state.history)

        self.assertIn("m", gs.alt_graph.val_lbl.text())
        self.assertIn("m/s", gs.spd_graph.val_lbl.text())
        self.assertIn("%", gs.bat_graph.val_lbl.text())

    def test_telemetry_view(self):
        view = TelemetryView()
        self.assertIsNotNone(view.header_bar)
        self.assertIsNotNone(view.flight_panel)
        self.assertIsNotNone(view.position_panel)
        self.assertIsNotNone(view.power_panel)
        self.assertIsNotNone(view.comm_panel)
        self.assertIsNotNone(view.sensor_panel)
        self.assertIsNotNone(view.fc_panel)
        self.assertIsNotNone(view.computer_panel)
        self.assertIsNotNone(view.graph_section)

    def test_navigation_and_regression(self):
        os.environ["DATA_MODE"] = "mock"
        win = MainWindow()
        win.show()

        # Test navigating to Telemetry page (index 4)
        win.sidebar.set_active_page(4)
        win._on_page_changed(4, "Telemetry")
        self.assertEqual(win.stacked_widget.currentIndex(), 4)
        self.assertIn("TELEMETRY", win.header.page_title.text())

        # Test navigating through all pages
        pages = ["Overview", "Live Feed", "Incidents", "Map", "Telemetry"]
        for idx, name in enumerate(pages):
            win.sidebar.set_active_page(idx)
            win._on_page_changed(idx, name)
            self.assertEqual(win.stacked_widget.currentIndex(), idx)

        win.close()
        app.processEvents()

if __name__ == "__main__":
    unittest.main()
