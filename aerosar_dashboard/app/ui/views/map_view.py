from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.incident import Incident
from app.models.map import MapState
from app.ui.widgets.mission_map import MissionMap
from app.ui.widgets.map_info_panel import MapInfoPanel

class MapLegendBar(QFrame):
    """
    Compact bottom legend explaining all symbols on the 2D local SLAM map.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            MapLegendBar {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        title = QLabel("LEGEND:")
        title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.8px;")
        layout.addWidget(title)

        # 1. Drone
        layout.addLayout(self._create_legend_item("◆", Theme.ACCENT, "DRONE (CURRENT POSE)"))

        # 2. Incident
        layout.addLayout(self._create_legend_item("●", Theme.STATUS_SUCCESS, "INCIDENT"))

        # 3. Trajectory
        layout.addLayout(self._create_legend_item("━", Theme.ACCENT, "TRAJECTORY"))

        # 4. Search Area
        layout.addLayout(self._create_legend_item("▧", Theme.TEXT_SECONDARY, "SEARCH AREA BOUNDARY"))

        # 5. Explored
        layout.addLayout(self._create_legend_item("░", Theme.ACCENT, "EXPLORED REGION"))

        layout.addStretch()

        frame_note = QLabel("LOCAL ROBOTICS MAP — GPS INDEPENDENT")
        frame_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-style: italic;")
        layout.addWidget(frame_note)

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

        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        # 1. Top Header Bar
        header_bar = QFrame()
        header_bar.setFixedHeight(50)
        header_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(18, 0, 18, 0)

        title = QLabel("MISSION MAP")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; letter-spacing: 0.8px;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        badge = QLabel("LOCAL / GPS-DENIED")
        badge.setStyleSheet(f"""
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
        h_layout.addWidget(badge)

        self.main_layout.addWidget(header_bar)

        # 2. Main Middle Area (Map + Info Panel)
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(16)

        # Reusable 2D MissionMap (~70%)
        self.mission_map = MissionMap()
        middle_layout.addWidget(self.mission_map, 72)

        # Reusable MapInfoPanel (~30%)
        self.info_panel = MapInfoPanel()
        middle_layout.addWidget(self.info_panel, 28)

        self.main_layout.addLayout(middle_layout, 1)

        # 3. Bottom Legend Bar
        self.legend_bar = MapLegendBar()
        self.main_layout.addWidget(self.legend_bar)

        # Connect signals
        self.mission_map.incident_selected.connect(self._on_map_incident_selected)
        self.info_panel.open_incident_requested.connect(self._on_open_incident)

    def _init_data(self):
        self._incidents = self.data_service.get_incidents()
        self._map_state = self.data_service.get_map_state()
        self.mission_map.update_map(self._map_state, self._incidents)
        self.info_panel.update_data(self._map_state, self._incidents)

    def _start_live_updates(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_data)
        self.timer.start(1000)  # 1-second update cycle for smooth mock movement

    def _poll_data(self):
        self._map_state = self.data_service.get_map_state()
        self._incidents = self.data_service.get_incidents()
        self.mission_map.update_map(self._map_state, self._incidents)
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
