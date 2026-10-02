import unittest
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QMouseEvent
import sys
import os

# Add parent directory (aerosar_dashboard) to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.incident import Incident, Location
from app.models.map import MapState, SearchBoundary
from app.services.data_service import DataService
from tests.mocks.mock_provider import MockDataProvider
from app.ui.widgets.mission_map import MissionMap
from app.ui.widgets.map_info_panel import MapInfoPanel
from app.ui.views.map_view import MapView
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep6MissionMap(unittest.TestCase):
    def test_map_state_model(self):
        ms = MapState(
            drone_position=Location(x=12.4, y=8.7, z=14.8),
            drone_heading=127.0,
            trajectory=[Location(x=3.5, y=4.2, z=14.2), Location(x=12.4, y=8.7, z=14.8)],
            search_boundary=SearchBoundary(min_x=0.0, max_x=30.0, min_y=0.0, max_y=25.0),
            explored_percentage=42.0,
            map_status="READY",
            coordinate_frame="LOCAL / SLAM"
        )
        self.assertEqual(ms.drone_position.x, 12.4)
        self.assertEqual(ms.drone_position.y, 8.7)
        self.assertEqual(ms.drone_heading, 127.0)
        self.assertEqual(len(ms.trajectory), 2)
        self.assertEqual(ms.coordinate_frame, "LOCAL / SLAM")
        self.assertEqual(ms.map_status, "READY")

    def test_mock_provider_map_state(self):
        provider = MockDataProvider()
        state1 = provider.get_map_state()
        self.assertEqual(state1.coordinate_frame, "LOCAL / SLAM")
        self.assertGreaterEqual(len(state1.trajectory), 5)
        self.assertEqual(state1.search_boundary.max_x, 30.0)
        self.assertEqual(state1.search_boundary.max_y, 25.0)

        # Verify subtle movement simulation
        init_x = state1.drone_position.x
        init_y = state1.drone_position.y
        state2 = provider.get_map_state()
        # Drone position moved or progressed
        self.assertTrue(abs(state2.drone_position.x - init_x) > 0.05 or abs(state2.drone_position.y - init_y) > 0.05)

    def test_mission_map_widget(self):
        map_widget = MissionMap()
        map_widget.resize(800, 600)
        
        provider = MockDataProvider()
        state = provider.get_map_state()
        incidents = provider.get_incidents()
        
        map_widget.update_map(state, incidents)
        
        # Test transforms
        pt = map_widget._to_screen(12.4, 8.7)
        self.assertIsInstance(pt, QPointF)
        self.assertGreater(pt.x(), 0)
        self.assertGreater(pt.y(), 0)

        # Test incident selection
        map_widget.select_incident("INC-001")
        self.assertEqual(map_widget.get_selected_incident_id(), "INC-001")

        map_widget.select_incident(None)
        self.assertIsNone(map_widget.get_selected_incident_id())

    def test_map_info_panel(self):
        panel = MapInfoPanel()
        provider = MockDataProvider()
        state = provider.get_map_state()
        incidents = provider.get_incidents()
        
        panel.update_data(state, incidents)
        self.assertEqual(panel.lbl_map_status.text(), "READY")
        self.assertEqual(panel.lbl_frame.text(), "LOCAL / SLAM")
        self.assertIn("m", panel.lbl_x.text())
        self.assertIn("°", panel.lbl_heading.text())
        self.assertEqual(panel.lbl_inc_total.text(), str(len(incidents)))

        # Test selected incident display
        panel.show_selected_incident(incidents[0])
        self.assertIn("INC-001", panel.lbl_sel_id.text())
        self.assertFalse(panel.btn_view_incident.isHidden())

    def test_map_view_integration(self):
        DataService._instance = None
        ds = DataService(provider=MockDataProvider())
        
        view = MapView()
        self.assertIsNotNone(view.mission_map)
        self.assertIsNotNone(view.info_panel)
        self.assertIsNotNone(view.legend_bar)

        # Test public select_incident method
        view.select_incident("INC-002")
        self.assertEqual(view.mission_map.get_selected_incident_id(), "INC-002")
        self.assertIn("INC-002", view.info_panel.lbl_sel_id.text())

    def test_cross_navigation_incidents_to_map(self):
        DataService._instance = None
        ds = DataService(provider=MockDataProvider())
        
        os.environ["DATA_MODE"] = "mock"
        win = MainWindow()
        win.show()

        # 1. Start on Incidents view (page 2)
        win.sidebar.set_active_page(2)
        win._on_page_changed(2, "Incidents")
        self.assertEqual(win.stacked_widget.currentIndex(), 2)

        # 2. Select INC-001 in Incidents View
        incidents = win.incidents_view.data_service.get_incidents()
        inc1 = next(i for i in incidents if i.incident_id == "INC-001")
        win.incidents_view.incident_list.select_incident(inc1)

        # 3. Click "VIEW ON MAP" button
        win.incidents_view.incident_detail.btn_map.click()

        # 4. Verify application navigated to Map Page (index 3) and selected INC-001
        self.assertEqual(win.stacked_widget.currentIndex(), 3)
        self.assertIn("MAP", win.header.page_title.text())
        self.assertEqual(win.map_view.mission_map.get_selected_incident_id(), "INC-001")
        self.assertIn("INC-001", win.map_view.info_panel.lbl_sel_id.text())
        
        win.close()
        app.processEvents()

if __name__ == "__main__":
    unittest.main()
