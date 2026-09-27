from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QProgressBar, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.models.incident import Incident
from app.models.map import MapState

class MapInfoPanel(QFrame):
    """
    Right-side operational telemetry and mission status panel for the Mission Map.
    Displays drone 3D position (X, Y, Z meters), orientation heading, search progress,
    active incidents, and detailed inspector for the currently selected incident marker.
    """
    open_incident_requested = Signal(str)  # Emits incident_id

    def __init__(self):
        super().__init__()
        self.setFixedWidth(290)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            MapInfoPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self._selected_incident: Optional[Incident] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # 1. Panel Header
        header = QLabel("MAP INFORMATION")
        header.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        layout.addWidget(header)
        layout.addWidget(self._create_divider())

        # 2. Map Status Card
        status_box = self._create_section_box("MAP STATUS")
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(10, 8, 10, 8)
        sb_layout.setSpacing(4)

        row1 = QHBoxLayout()
        r1_t = QLabel("LOCAL MAP")
        r1_t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        self.lbl_map_status = QLabel("READY")
        self.lbl_map_status.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 11px; font-weight: bold;")
        row1.addWidget(r1_t)
        row1.addStretch()
        row1.addWidget(self.lbl_map_status)
        sb_layout.addLayout(row1)

        row2 = QHBoxLayout()
        r2_t = QLabel("FRAME")
        r2_t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        self.lbl_frame = QLabel("LOCAL / SLAM")
        self.lbl_frame.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: bold; font-family: monospace;")
        row2.addWidget(r2_t)
        row2.addStretch()
        row2.addWidget(self.lbl_frame)
        sb_layout.addLayout(row2)

        layout.addWidget(status_box)

        # 3. Drone Position (X, Y, Z in meters)
        pos_box = self._create_section_box("DRONE POSITION")
        pb_layout = QGridLayout(pos_box)
        pb_layout.setContentsMargins(10, 8, 10, 8)
        pb_layout.setHorizontalSpacing(12)
        pb_layout.setVerticalSpacing(4)

        self.lbl_x = QLabel("12.4 m")
        self.lbl_y = QLabel("8.7 m")
        self.lbl_z = QLabel("14.8 m")
        for lbl in (self.lbl_x, self.lbl_y, self.lbl_z):
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; font-family: monospace;")

        self._add_grid_row(pb_layout, 0, "X", self.lbl_x)
        self._add_grid_row(pb_layout, 1, "Y", self.lbl_y)
        self._add_grid_row(pb_layout, 2, "Z (ALT)", self.lbl_z)
        layout.addWidget(pos_box)

        # 4. Orientation / Heading
        heading_box = self._create_section_box("ORIENTATION")
        hb_layout = QHBoxLayout(heading_box)
        hb_layout.setContentsMargins(10, 8, 10, 8)
        hb_t = QLabel("HEADING")
        hb_t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        self.lbl_heading = QLabel("127°")
        self.lbl_heading.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 16px; font-weight: bold; font-family: monospace;")
        hb_layout.addWidget(hb_t)
        hb_layout.addStretch()
        hb_layout.addWidget(self.lbl_heading)
        layout.addWidget(heading_box)

        # 5. Mission Search Progress & Explored Area
        mission_box = self._create_section_box("MISSION COVERAGE")
        mb_layout = QVBoxLayout(mission_box)
        mb_layout.setContentsMargins(10, 8, 10, 8)
        mb_layout.setSpacing(6)

        m_row = QHBoxLayout()
        m_lbl = QLabel("SEARCH PROGRESS")
        m_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        self.lbl_progress = QLabel("42%")
        self.lbl_progress.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 12px; font-weight: bold;")
        m_row.addWidget(m_lbl)
        m_row.addStretch()
        m_row.addWidget(self.lbl_progress)
        mb_layout.addLayout(m_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(42)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_BASE};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT};
                border-radius: 2px;
            }}
        """)
        mb_layout.addWidget(self.progress_bar)

        exp_row = QHBoxLayout()
        exp_lbl = QLabel("EXPLORED AREA")
        exp_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        self.lbl_explored = QLabel("42%")
        self.lbl_explored.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        exp_row.addWidget(exp_lbl)
        exp_row.addStretch()
        exp_row.addWidget(self.lbl_explored)
        mb_layout.addLayout(exp_row)

        layout.addWidget(mission_box)

        # 6. Incidents Overview
        inc_box = self._create_section_box("INCIDENTS")
        ib_layout = QHBoxLayout(inc_box)
        ib_layout.setContentsMargins(10, 8, 10, 8)

        total_w = QWidget()
        tl = QVBoxLayout(total_w)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(2)
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_inc_total = QLabel("3")
        self.lbl_inc_total.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold; font-family: monospace;")
        self.lbl_inc_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl_tag = QLabel("TOTAL")
        tl_tag.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold;")
        tl_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.addWidget(self.lbl_inc_total)
        tl.addWidget(tl_tag)
        ib_layout.addWidget(total_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {Theme.BORDER};")
        ib_layout.addWidget(sep)

        act_w = QWidget()
        al = QVBoxLayout(act_w)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(2)
        al.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_inc_active = QLabel("3")
        self.lbl_inc_active.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 18px; font-weight: bold; font-family: monospace;")
        self.lbl_inc_active.setAlignment(Qt.AlignmentFlag.AlignCenter)
        al_tag = QLabel("ACTIVE")
        al_tag.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold;")
        al_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        al.addWidget(self.lbl_inc_active)
        al.addWidget(al_tag)
        ib_layout.addWidget(act_w)

        layout.addWidget(inc_box)

        # 7. Selected Incident Details Box (Contextual Inspector)
        self.sel_inc_box = self._create_section_box("SELECTED INCIDENT")
        self.sel_inc_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.ACCENT};
                border-radius: 4px;
            }}
        """)
        sib_layout = QVBoxLayout(self.sel_inc_box)
        sib_layout.setContentsMargins(10, 8, 10, 8)
        sib_layout.setSpacing(4)

        self.lbl_sel_id = QLabel("NONE")
        self.lbl_sel_id.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 13px; font-weight: bold; font-family: monospace;")
        sib_layout.addWidget(self.lbl_sel_id)

        self.lbl_sel_details = QLabel("Click an incident on map to inspect")
        self.lbl_sel_details.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        self.lbl_sel_details.setWordWrap(True)
        sib_layout.addWidget(self.lbl_sel_details)

        self.btn_view_incident = QPushButton("VIEW DETAILS")
        self.btn_view_incident.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_incident.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 180, 216, 0.15);
            }}
        """)
        self.btn_view_incident.clicked.connect(self._on_view_incident_clicked)
        self.btn_view_incident.hide()
        sib_layout.addWidget(self.btn_view_incident)

        layout.addWidget(self.sel_inc_box)
        layout.addStretch()

    def _create_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        return div

    def _create_section_box(self, title: str) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        return box

    def _add_grid_row(self, grid: QGridLayout, row: int, name: str, val_lbl: QLabel):
        t = QLabel(name)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        grid.addWidget(t, row, 0)
        grid.addWidget(val_lbl, row, 1)

    def update_data(self, map_state: Optional[MapState], incidents: List[Incident]):
        if map_state:
            dp = map_state.drone_position
            self.lbl_x.setText(f"{dp.x:.1f} m")
            self.lbl_y.setText(f"{dp.y:.1f} m")
            self.lbl_z.setText(f"{dp.z:.1f} m")
            self.lbl_heading.setText(f"{int(map_state.drone_heading)}°")
            self.lbl_map_status.setText(map_state.map_status)
            self.lbl_frame.setText(map_state.coordinate_frame)

            prog = int(map_state.explored_percentage)
            self.lbl_progress.setText(f"{prog}%")
            self.progress_bar.setValue(prog)
            self.lbl_explored.setText(f"{prog}%")

        total_cnt = len(incidents)
        active_cnt = sum(1 for i in incidents if i.status.upper() != "RESOLVED")
        self.lbl_inc_total.setText(str(total_cnt))
        self.lbl_inc_active.setText(str(active_cnt))

        # Update selected incident details if one is selected
        if self._selected_incident:
            # Refresh from current incidents list in case confidence/status changed
            match = next((i for i in incidents if i.incident_id == self._selected_incident.incident_id), None)
            if match:
                self.show_selected_incident(match)

    def show_selected_incident(self, incident: Optional[Incident]):
        self._selected_incident = incident
        if incident:
            self.lbl_sel_id.setText(f"{incident.incident_id}  ({incident.status})")
            short_type = incident.type.replace(" DETECTED", "")
            self.lbl_sel_details.setText(
                f"TYPE: {short_type} ({int(incident.confidence * 100)}%)\n"
                f"LOC: X {incident.location.x:.1f}m, Y {incident.location.y:.1f}m, Z {incident.location.z:.1f}m"
            )
            self.btn_view_incident.show()
        else:
            self.lbl_sel_id.setText("NONE")
            self.lbl_sel_details.setText("Click an incident on map to inspect")
            self.btn_view_incident.hide()

    def _on_view_incident_clicked(self):
        if self._selected_incident:
            self.open_incident_requested.emit(self._selected_incident.incident_id)
