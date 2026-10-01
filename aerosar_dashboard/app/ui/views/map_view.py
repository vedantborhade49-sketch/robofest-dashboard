from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.incident import Incident
from app.models.map import MapState
from app.ui.widgets.mission_map import MissionMap
from app.ui.widgets.map_info_panel import MapInfoPanel
from app.ui.responsive import ScreenSize

class MapLegendBar(QFrame):
    """
    Compact bottom legend explaining all symbols on the 2D local SLAM map.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            MapLegendBar {{
                background-color: {Theme.SURFACE_ELEVATED};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 0, 16, 0)
        self.main_layout.setSpacing(20)

        self.title = QLabel("LEGEND:")
        self.title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.8px;")
        self.main_layout.addWidget(self.title)

        # 1. Drone
        self.main_layout.addLayout(self._create_legend_item("◆", Theme.ACCENT, "DRONE (CURRENT POSE)"))

        # 2. Incident
        self.main_layout.addLayout(self._create_legend_item("●", Theme.SUCCESS, "INCIDENT"))

        # 3. Trajectory
        self.main_layout.addLayout(self._create_legend_item("━", Theme.ACCENT, "TRAJECTORY"))

        # 4. Search Area
        self.main_layout.addLayout(self._create_legend_item("▧", Theme.TEXT_SECONDARY, "SEARCH AREA BOUNDARY"))

        # 5. Explored
        self.main_layout.addLayout(self._create_legend_item("░", Theme.ACCENT, "EXPLORED REGION"))

        self.main_layout.addStretch()

        self.frame_note = QLabel("LOCAL ROBOTICS MAP — GPS INDEPENDENT")
        self.frame_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-style: italic;")
        self.main_layout.addWidget(self.frame_note)

    def _create_legend_item(self, symbol: str, color: str, text: str) -> QHBoxLayout:
        item = QHBoxLayout()
        item.setSpacing(6)

        sym_lbl = QLabel(symbol)
        sym_lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        item.addWidget(sym_lbl)

        txt_lbl = QLabel(text)
        txt_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 10px; font-weight: 600;")
        item.addWidget(txt_lbl)

        return item

    def set_responsive_state(self, state: ScreenSize):
        if state == ScreenSize.MINIMUM:
            self.title.hide()
            self.frame_note.hide()
            self.main_layout.setSpacing(8)
        else:
            self.title.show()
            self.frame_note.show()
            self.main_layout.setSpacing(20)


class MapView(QWidget):
    """
    Mission Map Page View conforming to Step 6 requirements:
    1. Header Bar: MISSION MAP | LOCAL / GPS-DENIED
    2. Left Section (~72%): Reusable MissionMap widget (Offline 2D SLAM robotics map)
    3. Right Section (~28%): Reusable MapInfoPanel widget (Telemetry, Heading, Coverage, Incidents)
    4. Bottom: Tactical Legend Bar
    5. Live updates of subtle drone movement & flight trajectory
    6. Cross-page navigation and incident selection
    """
    navigate_to_incidents = Signal(str)  # Optional navigation back to incidents page

    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._incidents: List[Incident] = []
        self._map_state: Optional[MapState] = None
        self.current_state = None

        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        # 1. Top Header Bar
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(50)
        self.header_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE_ELEVATED};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.h_layout = QHBoxLayout(self.header_bar)
        self.h_layout.setContentsMargins(18, 0, 18, 0)

        self.title = QLabel("MISSION MAP")
        self.title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; letter-spacing: 0.8px;")
        self.h_layout.addWidget(self.title)

        self.h_layout.addStretch()

        self.cb_show_lidar = QCheckBox("Show LiDAR")
        self.cb_show_lidar.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.cb_show_lidar.setChecked(True)
        self.cb_show_lidar.toggled.connect(self._on_lidar_toggled)
        self.h_layout.addWidget(self.cb_show_lidar)

        self.cb_show_obstacles = QCheckBox("Show Obstacles")
        self.cb_show_obstacles.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.cb_show_obstacles.setChecked(True)
        self.cb_show_obstacles.toggled.connect(self._on_lidar_toggled)
        self.h_layout.addWidget(self.cb_show_obstacles)
        
        self.cb_show_trajectory = QCheckBox("Show Trajectory")
        self.cb_show_trajectory.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.cb_show_trajectory.setChecked(True)
        self.cb_show_trajectory.toggled.connect(self._on_lidar_toggled)
        self.h_layout.addWidget(self.cb_show_trajectory)

        self.cb_show_occupancy = QCheckBox("Occupancy Map")
        self.cb_show_occupancy.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.cb_show_occupancy.setChecked(True)
        self.cb_show_occupancy.toggled.connect(self._on_lidar_toggled)
        self.h_layout.addWidget(self.cb_show_occupancy)

        from PySide6.QtWidgets import QPushButton
        self.btn_reset_slam = QPushButton("Reset SLAM")
        self.btn_reset_slam.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.WARNING};
                border: 1px solid {Theme.WARNING};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 170, 0, 0.15);
            }}
        """)
        self.btn_reset_slam.clicked.connect(self._on_reset_slam_clicked)
        self.h_layout.addWidget(self.btn_reset_slam)

        self.h_layout.addSpacing(20)

        self.badge = QLabel("LOCAL / GPS-DENIED")
        self.badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT};
                background-color: rgba(0, 180, 216, 0.12);
                border: 1px solid rgba(0, 180, 216, 0.35);
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)
        self.h_layout.addWidget(self.badge)

        self.main_layout.addWidget(self.header_bar)

        # 2. Main Middle Area (Splitter)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        # Reusable 2D MissionMap (~72%)
        self.mission_map = MissionMap()
        self.splitter.addWidget(self.mission_map)

        # Reusable MapInfoPanel (~28%)
        self.info_panel = MapInfoPanel()
        self.splitter.addWidget(self.info_panel)

        self.splitter.setStretchFactor(0, 72)
        self.splitter.setStretchFactor(1, 28)

        self.main_layout.addWidget(self.splitter, 1)

        # 3. Bottom Legend Bar
        self.legend_bar = MapLegendBar()
        self.main_layout.addWidget(self.legend_bar)

        # Connect signals
        self.mission_map.incident_selected.connect(self._on_map_incident_selected)
        self.info_panel.open_incident_requested.connect(self._on_open_incident)

    def set_responsive_state(self, state: ScreenSize):
        if self.current_state == state:
            return
        self.current_state = state
        
        self.legend_bar.set_responsive_state(state)
        
        if state in (ScreenSize.COMPACT, ScreenSize.MINIMUM):
            self.splitter.setOrientation(Qt.Orientation.Vertical)
            self.cb_show_lidar.hide()
            self.cb_show_obstacles.hide()
            self.cb_show_trajectory.hide()
            self.cb_show_occupancy.hide()
            self.badge.hide()
            self.main_layout.setContentsMargins(8, 8, 8, 8)
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
            self.splitter.setSizes([int(self.width() * 0.72), int(self.width() * 0.28)])
            self.cb_show_lidar.show()
            self.cb_show_obstacles.show()
            self.cb_show_trajectory.show()
            self.cb_show_occupancy.show()
            self.badge.show()
            self.main_layout.setContentsMargins(24, 20, 24, 20)

    def _init_data(self):
        self._incidents = self.data_service.get_incidents()
        
        app_state = self.data_service._state_manager.get_state()
        self._map_state = app_state.map_state if app_state else None
        self._spatial_state = app_state.spatial if app_state else None
        
        self.mission_map.update_map(self._map_state, self._incidents, self._spatial_state)
        self.info_panel.update_data(self._map_state, self._incidents)

    def _on_lidar_toggled(self):
        self.mission_map.show_lidar = self.cb_show_lidar.isChecked()
        self.mission_map.show_obstacles = self.cb_show_obstacles.isChecked()
        self.mission_map.show_trajectory = self.cb_show_trajectory.isChecked()
        self.mission_map.show_occupancy = self.cb_show_occupancy.isChecked()
        self.mission_map.update()

    def _on_reset_slam_clicked(self):
        if hasattr(self.data_service, 'spatial_service'):
            self.data_service.spatial_service.reset_slam()

    def _start_live_updates(self):
        self.data_service.map_updated.connect(self._on_map_updated)
        self.data_service.incidents_updated.connect(self._on_incidents_updated)
        self.data_service.spatial_updated.connect(self._on_spatial_updated)

    def _on_spatial_updated(self, spatial_state):
        self._spatial_state = spatial_state
        self.mission_map.update_map(self._map_state, self._incidents, self._spatial_state)

    def _on_map_updated(self, map_state):
        self._map_state = map_state
        self.mission_map.update_map(self._map_state, self._incidents, self._spatial_state)
        self.info_panel.update_data(self._map_state, self._incidents)

    def _on_incidents_updated(self, incidents):
        self._incidents = incidents
        self.mission_map.update_map(self._map_state, self._incidents, self._spatial_state)
        self.info_panel.update_data(self._map_state, self._incidents)

    def select_incident(self, incident_id: str):
        """
        Public method called when navigating to map with a pre-selected incident
        (e.g., from Incidents Page 'VIEW ON MAP' button).
        """
        self.mission_map.select_incident(incident_id)
        match = next((i for i in self._incidents if i.incident_id == incident_id), None)
        self.info_panel.show_selected_incident(match)

        if match:
            self.data_service.log_event(
                message=f"Mission map focused on target {incident_id} [{match.location.x:.1f}, {match.location.y:.1f}, {match.location.z:.1f}]",
                event_type="NAVIGATION",
                severity="INFO"
            )

    def _on_map_incident_selected(self, incident_id: str):
        if incident_id:
            match = next((i for i in self._incidents if i.incident_id == incident_id), None)
            self.info_panel.show_selected_incident(match)
            if match:
                self.data_service.log_event(
                    message=f"Target {incident_id} selected on Mission Map ({match.type})",
                    event_type="NAVIGATION",
                    severity="INFO"
                )
        else:
            self.info_panel.show_selected_incident(None)

    def _on_open_incident(self, incident_id: str):
        self.navigate_to_incidents.emit(incident_id)
