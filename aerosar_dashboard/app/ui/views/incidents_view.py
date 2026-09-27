from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.incident import Incident
from app.ui.widgets.incident_list import IncidentList
from app.ui.widgets.incident_detail import IncidentDetail

class IncidentCountersBar(QFrame):
    """
    Compact summary counters bar at the top of the Incidents page.
    Dynamically derived from incident data.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(74)
        self.setStyleSheet(f"""
            IncidentCountersBar {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 10, 24, 10)
        self.layout.setSpacing(16)

        # Title & Active summary on left
        title_box = QWidget()
        tb_layout = QVBoxLayout(title_box)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(2)

        page_title = QLabel("INCIDENTS")
        page_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; letter-spacing: 0.8px;")
        tb_layout.addWidget(page_title)

        self.active_sub_lbl = QLabel("0 ACTIVE")
        self.active_sub_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: bold; font-family: monospace;")
        tb_layout.addWidget(self.active_sub_lbl)

        self.layout.addWidget(title_box)
        self.layout.addStretch(1)

        # Counters: TOTAL | NEW | REVIEW | CONFIRMED | RESOLVED
        self.val_total = self._add_counter_item("TOTAL", "0", Theme.TEXT_PRIMARY)
        self._add_v_separator()
        self.val_new = self._add_counter_item("NEW", "0", Theme.ACCENT)
        self._add_v_separator()
        self.val_review = self._add_counter_item("REVIEW", "0", Theme.STATUS_WARNING)
        self._add_v_separator()
        self.val_confirmed = self._add_counter_item("CONFIRMED", "0", Theme.STATUS_SUCCESS)
        self._add_v_separator()
        self.val_resolved = self._add_counter_item("RESOLVED", "0", Theme.TEXT_SECONDARY)

    def _add_counter_item(self, label: str, init_val: str, color: str) -> QLabel:
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(12, 0, 12, 0)
        bl.setSpacing(2)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val_lbl = QLabel(init_val)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; font-family: monospace;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        txt_lbl = QLabel(label)
        txt_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        txt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bl.addWidget(val_lbl)
        bl.addWidget(txt_lbl)
        self.layout.addWidget(box)
        return val_lbl

    def _add_v_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {Theme.BORDER};")
        self.layout.addWidget(sep)

    def update_counts(self, incidents: List[Incident]):
        total = len(incidents)
        new_cnt = sum(1 for i in incidents if i.status.upper() == "NEW")
        review_cnt = sum(1 for i in incidents if i.status.upper() == "REVIEW")
        conf_cnt = sum(1 for i in incidents if i.status.upper() == "CONFIRMED")
        res_cnt = sum(1 for i in incidents if i.status.upper() == "RESOLVED")
        active_cnt = total - res_cnt

        self.val_total.setText(str(total))
        self.val_new.setText(str(new_cnt))
        self.val_review.setText(str(review_cnt))
        self.val_confirmed.setText(str(conf_cnt))
        self.val_resolved.setText(str(res_cnt))
        self.active_sub_lbl.setText(f"{active_cnt} ACTIVE")


class IncidentFilterBar(QFrame):
    """
    Bottom filter toolbar: ALL | NEW | REVIEW | CONFIRMED | RESOLVED
    """
    def __init__(self, on_filter_changed):
        super().__init__()
        self.on_filter_changed = on_filter_changed
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            IncidentFilterBar {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        lbl = QLabel("FILTER:")
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        layout.addWidget(lbl)

        self.filter_buttons = {}
        filters = ["ALL", "NEW", "REVIEW", "CONFIRMED", "RESOLVED"]

        for f in filters:
            btn = QPushButton(f)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, name=f: self._on_btn_clicked(name))
            layout.addWidget(btn)
            self.filter_buttons[f] = btn

        layout.addStretch()
        self._set_active_filter("ALL")

    def _set_active_filter(self, active_name: str):
        for name, btn in self.filter_buttons.items():
            is_active = (name == active_name)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.BG_SECONDARY};
                        color: {Theme.ACCENT};
                        border: 1px solid {Theme.ACCENT};
                        border-radius: 4px;
                        padding: 5px 14px;
                        font-size: 11px;
                        font-weight: bold;
                        letter-spacing: 0.5px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {Theme.TEXT_SECONDARY};
                        border: 1px solid transparent;
                        border-radius: 4px;
                        padding: 5px 14px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }}
                    QPushButton:hover {{
                        color: {Theme.TEXT_PRIMARY};
                        background-color: rgba(255, 255, 255, 0.04);
                    }}
                """)

    def _on_btn_clicked(self, name: str):
        self._set_active_filter(name)
        self.on_filter_changed(name)


class IncidentsView(QWidget):
    """
    Main Incidents View implementation conforming to Step 5 requirements:
    1. Incident Counters Bar (Dynamic counts derived from data)
    2. Main Layout (Incident List ~38%, Incident Detail ~62%)
    3. Filter Bar (ALL, NEW, REVIEW, CONFIRMED, RESOLVED)
    4. Operational event generation and live polling
    """
    navigate_to_map = Signal(Incident)

    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._last_selected_id: Optional[str] = None
        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        # 1. Top Counters Bar
        self.counters_bar = IncidentCountersBar()
        self.main_layout.addWidget(self.counters_bar)

        # 2. Main Middle Area (List + Detail)
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(16)

        # Left: Reusable IncidentList widget
        self.incident_list = IncidentList()
        middle_layout.addWidget(self.incident_list, 38)

        # Right: Reusable IncidentDetail widget
        self.incident_detail = IncidentDetail()
        middle_layout.addWidget(self.incident_detail, 62)

        self.main_layout.addLayout(middle_layout, 1)

        # 3. Bottom Filter Toolbar
        self.filter_bar = IncidentFilterBar(self._on_filter_changed)
        self.main_layout.addWidget(self.filter_bar)

        # Signal connections
        self.incident_list.incident_selected.connect(self._on_incident_selected)
        self.incident_detail.view_on_map_requested.connect(self._on_view_on_map)
        self.incident_detail.generate_report_requested.connect(self._on_generate_report)

    def _init_data(self):
        incidents = self.data_service.get_incidents()
        self.counters_bar.update_counts(incidents)
        self.incident_list.set_incidents(incidents)

        # Pre-select first incident (INC-001) for immediate operator inspection
        if incidents:
            first_inc = incidents[0]
            self.incident_list.select_incident(first_inc)

    def _start_live_updates(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_data)
        self.timer.start(4000)  # Gentle 4-second cycle

    def _poll_data(self):
        incidents = self.data_service.get_incidents()
        self.counters_bar.update_counts(incidents)
        # Update list preserving current selection
        self.incident_list.set_incidents(incidents)

    def _on_filter_changed(self, filter_name: str):
        self.incident_list.set_filter(filter_name)

    def _on_incident_selected(self, incident: Incident):
        self._last_selected_id = incident.incident_id
        self.incident_detail.show_incident(incident)
        # Log event into event system
        self.data_service.log_event(
            message=f"Incident {incident.incident_id} selected by operator ({incident.type})",
            event_type="INCIDENT",
            severity="INFO"
        )

    def _on_view_on_map(self, incident: Incident):
        self.data_service.log_event(
            message=f"Incident {incident.incident_id} map location requested [{incident.location.x:.1f}, {incident.location.y:.1f}, {incident.location.z:.1f}]",
            event_type="NAVIGATION",
            severity="INFO"
        )
        self.navigate_to_map.emit(incident)

    def _on_generate_report(self, incident: Incident):
        self.data_service.log_event(
            message=f"Report generation requested for incident {incident.incident_id} (AI module pending)",
            event_type="SYSTEM",
            severity="WARNING"
        )

    def select_incident_by_id(self, incident_id: str):
        """Allows programmatic selection from map or other navigation triggers."""
        match = self.data_service.get_incident(incident_id)
        if match:
            self.incident_list.select_incident(match)
