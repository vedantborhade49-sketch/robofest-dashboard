from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.models.event import Event

class EventDetailPanel(QFrame):
    """
    Operator detail panel displaying complete structured metadata, full event message,
    and formatted contextual telemetry/debug parameters for the selected event.
    """
    view_incident_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_event: Optional[Event] = None
        self.setStyleSheet(f"""
            EventDetailPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # 1. Header Bar: Title, Event ID, Badges, and Action Button
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        p_lbl = QLabel("EVENT DETAILS")
        p_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        title_box.addWidget(p_lbl)

        self.val_event_id = QLabel("EVT-0000")
        self.val_event_id.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; font-family: monospace;")
        title_box.addWidget(self.val_event_id)

        header_row.addLayout(title_box)
        header_row.addStretch()

        # Level Badge
        self.val_level_badge = QLabel("INFO")
        self.val_level_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_level_badge_style("INFO")
        header_row.addWidget(self.val_level_badge)

        # Source Badge
        self.val_source_badge = QLabel("SYSTEM")
        self.val_source_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_source_badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT};
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
                font-family: monospace;
            }}
        """)
        header_row.addWidget(self.val_source_badge)

        # View Incident Action Button
        self.btn_view_incident = QPushButton("↗ VIEW INCIDENT")
        self.btn_view_incident.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_incident.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 180, 216, 0.15);
            }}
            QPushButton:disabled {{
                color: {Theme.TEXT_SECONDARY};
                border-color: {Theme.BORDER};
                background-color: transparent;
            }}
        """)
        self.btn_view_incident.clicked.connect(self._on_view_incident_clicked)
        header_row.addWidget(self.btn_view_incident)

        layout.addLayout(header_row)

        # Subtle divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        layout.addWidget(div)

        # 2. Key Metadata Grid (Timestamp, Mission, Incident, Type)
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_timestamp = self._add_field(grid, 0, 0, "TIMESTAMP", "14:32:08", Theme.TEXT_PRIMARY)
        self.val_mission = self._add_field(grid, 0, 1, "MISSION ID", "SAR-001", Theme.TEXT_PRIMARY)
        self.val_incident = self._add_field(grid, 0, 2, "INCIDENT ID", "—", Theme.ACCENT)
        self.val_type = self._add_field(grid, 0, 3, "EVENT TYPE", "SYSTEM", Theme.TEXT_SECONDARY)

        layout.addLayout(grid)

        # 3. Event Message Callout
        msg_box = QFrame()
        msg_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
            }}
        """)
        mb_layout = QVBoxLayout(msg_box)
        mb_layout.setContentsMargins(12, 8, 12, 8)
        mb_layout.setSpacing(2)

        m_title = QLabel("EVENT MESSAGE")
        m_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        mb_layout.addWidget(m_title)

        self.val_message = QLabel("No event selected.")
        self.val_message.setWordWrap(True)
        self.val_message.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
        mb_layout.addWidget(self.val_message)

        layout.addWidget(msg_box)

        # 4. Structured Details Section
        details_box = QFrame()
        details_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
            }}
        """)
        self.db_layout = QVBoxLayout(details_box)
        self.db_layout.setContentsMargins(12, 8, 12, 8)
        self.db_layout.setSpacing(6)

        d_title = QLabel("STRUCTURED PARAMETERS / TELEMETRY")
        d_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        self.db_layout.addWidget(d_title)

        self.details_content_widget = QWidget()
        self.details_content_widget.setStyleSheet("background: transparent;")
        self.details_items_layout = QGridLayout(self.details_content_widget)
        self.details_items_layout.setContentsMargins(0, 0, 0, 0)
        self.details_items_layout.setSpacing(8)

        self.db_layout.addWidget(self.details_content_widget)
        layout.addWidget(details_box)

    def _add_field(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def _apply_level_badge_style(self, level: str):
        lvl = level.upper()
        if lvl == "SUCCESS":
            color = Theme.STATUS_SUCCESS
            bg = "rgba(34, 197, 94, 0.15)"
            border = "rgba(34, 197, 94, 0.4)"
        elif lvl == "WARNING":
            color = Theme.STATUS_WARNING
            bg = "rgba(245, 158, 11, 0.15)"
            border = "rgba(245, 158, 11, 0.4)"
        elif lvl in ("ERROR", "CRITICAL"):
            color = Theme.STATUS_CRITICAL
            bg = "rgba(239, 68, 68, 0.15)"
            border = "rgba(239, 68, 68, 0.4)"
        else:  # INFO
            color = Theme.ACCENT
            bg = "rgba(0, 180, 216, 0.15)"
            border = "rgba(0, 180, 216, 0.4)"

        self.val_level_badge.setText(lvl)
        self.val_level_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
                font-family: monospace;
            }}
        """)

    @property
    def current_event(self) -> Optional[Event]:
        return self._current_event

    def show_event(self, ev: Event):
        self._current_event = ev

        self.val_event_id.setText(ev.event_id)
        self._apply_level_badge_style(ev.level)
        self.val_source_badge.setText(ev.source.upper())

        self.val_timestamp.setText(ev.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        self.val_mission.setText(ev.mission_id or "SAR-001")
        self.val_incident.setText(ev.incident_id or "—")
        self.val_type.setText(ev.event_type.upper())

        self.val_message.setText(ev.message)

        # Enable/Disable view incident button
        self.btn_view_incident.setEnabled(bool(ev.incident_id))

        # Render structured details cleanly
        # Clear existing items
        while self.details_items_layout.count() > 0:
            item = self.details_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if ev.details and isinstance(ev.details, dict) and len(ev.details) > 0:
            row, col = 0, 0
            for key, val in ev.details.items():
                k_clean = str(key).replace("_", " ").upper()
                v_clean = str(val)

                card = QFrame()
                card.setStyleSheet(f"background-color: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER}; border-radius: 3px; padding: 2px;")
                cl = QVBoxLayout(card)
                cl.setContentsMargins(6, 4, 6, 4)
                cl.setSpacing(1)

                kl = QLabel(k_clean)
                kl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 8px; font-weight: bold;")
                vl = QLabel(v_clean)
                vl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold; font-family: monospace;")

                cl.addWidget(kl)
                cl.addWidget(vl)

                self.details_items_layout.addWidget(card, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        else:
            no_det = QLabel("No additional telemetry or debug parameters recorded for this event.")
            no_det.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-style: italic;")
            self.details_items_layout.addWidget(no_det, 0, 0)

    def _on_view_incident_clicked(self):
        if self._current_event and self._current_event.incident_id:
            self.view_incident_requested.emit(self._current_event.incident_id)
