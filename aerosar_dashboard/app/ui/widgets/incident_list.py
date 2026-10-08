from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.models.incident import Incident

class IncidentRowWidget(QFrame):
    clicked = Signal(Incident)

    def __init__(self, incident: Incident, is_selected: bool = False):
        super().__init__()
        self.incident = incident
        self.is_selected = is_selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self.update_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: Incident ID & Status badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.id_label = QLabel(self.incident.incident_id)
        self.id_label.setStyleSheet("font-size: 13px; font-weight: bold; font-family: monospace;")
        top_row.addWidget(self.id_label)
        top_row.addStretch()

        self.status_badge = QLabel(self.incident.status)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_status_badge_style()
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # Bottom row: Type + Confidence & Timestamp
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        # Short type (e.g. PERSON if PERSON DETECTED)
        short_type = self.incident.type
        conf_percent = int(self.incident.confidence * 100) if self.incident.confidence else 0
        self.type_conf_label = QLabel(f"{short_type}   {conf_percent}%")
        self.type_conf_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        bottom_row.addWidget(self.type_conf_label)
        bottom_row.addStretch()

        time_str = self.incident.timestamp.strftime("%H:%M:%S")
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-family: monospace;")
        bottom_row.addWidget(self.time_label)

        layout.addLayout(bottom_row)

        # Extra row for Evidence and Entity ID
        extra_row = QHBoxLayout()
        extra_row.setSpacing(8)
        
        # Entity ID (not directly on incident, but if we had it. Let's just put evidence for now or default entity)
        # The user requested "Entity ID if available". We can check if metadata has it.
        entity_id = getattr(self.incident, "entity_id", None)
        if entity_id:
            ent_lbl = QLabel(entity_id)
            ent_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
            extra_row.addWidget(ent_lbl)

        evidence_status = "AVAILABLE" if getattr(self.incident, "evidence_image", None) else "NONE"
        ev_label = QLabel(f"Evidence: {evidence_status}")
        ev_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        extra_row.addWidget(ev_label)
        extra_row.addStretch()

        layout.addLayout(extra_row)

    def _apply_status_badge_style(self):
        st = self.incident.status.upper()
        if st == "CONFIRMED":
            color = Theme.STATUS_SUCCESS
            bg = "rgba(34, 197, 94, 0.15)"
            border = "rgba(34, 197, 94, 0.4)"
        elif st == "REVIEW":
            color = Theme.STATUS_WARNING
            bg = "rgba(245, 158, 11, 0.15)"
            border = "rgba(245, 158, 11, 0.4)"
        elif st == "NEW":
            color = Theme.ACCENT
            bg = "rgba(0, 180, 216, 0.15)"
            border = "rgba(0, 180, 216, 0.4)"
        else:  # RESOLVED
            color = Theme.TEXT_SECONDARY
            bg = "rgba(140, 152, 166, 0.15)"
            border = "rgba(140, 152, 166, 0.3)"

        self.status_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)

    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                IncidentRowWidget {{
                    background-color: #17212E;
                    border: 1px solid {Theme.ACCENT};
                    border-left: 4px solid {Theme.ACCENT};
                    border-radius: 5px;
                }}
            """)
            self.id_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 13px; font-weight: bold; font-family: monospace;")
        else:
            self.setStyleSheet(f"""
                IncidentRowWidget {{
                    background-color: {Theme.BG_SECONDARY};
                    border: 1px solid {Theme.BORDER};
                    border-left: 4px solid #1E2736;
                    border-radius: 5px;
                }}
                IncidentRowWidget:hover {{
                    background-color: #161D27;
                    border: 1px solid #364354;
                    border-left: 4px solid #364354;
                }}
            """)
            self.id_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; font-family: monospace;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.incident)
        super().mousePressEvent(event)


class IncidentList(QFrame):
    """
    Reusable IncidentList widget displaying list of mission incidents with filtering
    and visual selection indication.
    """
    incident_selected = Signal(Incident)

    def __init__(self):
        super().__init__()
        self._incidents: List[Incident] = []
        self._current_filter: str = "ALL"
        self._selected_incident_id: Optional[str] = None
        self._row_widgets: List[IncidentRowWidget] = []

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            IncidentList {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panel Header
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet(f"border-bottom: 1px solid {Theme.BORDER}; background-color: rgba(21, 27, 35, 0.8);")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("INCIDENT LIST")
        title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self.count_badge = QLabel("0 ITEMS")
        self.count_badge.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: 600; font-family: monospace;")
        h_layout.addWidget(self.count_badge)

        main_layout.addWidget(header)

        # Scrollable area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #0D1219;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #252D38;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3B4758;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.items_layout = QVBoxLayout(self.container)
        self.items_layout.setContentsMargins(12, 12, 12, 12)
        self.items_layout.setSpacing(8)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

    def set_incidents(self, incidents: List[Incident]):
        """Updates the incidents list while preserving active selection."""
        self._incidents = incidents
        self._refresh_list()

    def set_filter(self, filter_name: str):
        """Sets the active filter (ALL, NEW, REVIEW, CONFIRMED, RESOLVED)."""
        self._current_filter = filter_name.upper()
        self._refresh_list()

    def get_selected_incident(self) -> Optional[Incident]:
        if not self._selected_incident_id:
            return None
        for inc in self._incidents:
            if inc.incident_id == self._selected_incident_id:
                return inc
        return None

    def select_incident(self, incident: Incident):
        """Programmatically select an incident."""
        self._selected_incident_id = incident.incident_id
        for row in self._row_widgets:
            is_match = row.incident.incident_id == self._selected_incident_id
            row.set_selected(is_match)
        self.incident_selected.emit(incident)

    def _on_row_clicked(self, incident: Incident):
        self._selected_incident_id = incident.incident_id
        for row in self._row_widgets:
            row.set_selected(row.incident.incident_id == incident.incident_id)
        self.incident_selected.emit(incident)

    def _refresh_list(self):
        # Clear existing row widgets
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._row_widgets.clear()

        # Filter incidents
        filtered = [
            inc for inc in self._incidents
            if self._current_filter == "ALL" or inc.status.upper() == self._current_filter
        ]

        self.count_badge.setText(f"{len(filtered)} ITEMS")

        if not filtered:
            empty_lbl = QLabel(f"NO {self._current_filter} INCIDENTS" if self._current_filter != "ALL" else "NO INCIDENTS DETECTED")
            empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold; padding: 24px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.addWidget(empty_lbl)
            return

        for inc in filtered:
            is_selected = (inc.incident_id == self._selected_incident_id)
            row = IncidentRowWidget(inc, is_selected=is_selected)
            row.clicked.connect(self._on_row_clicked)
            self._row_widgets.append(row)
            self.items_layout.addWidget(row)
