from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QComboBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.event import Event
from app.ui.widgets.event_table import EventTableWidget
from app.ui.widgets.event_detail_panel import EventDetailPanel

class EventCountersBar(QFrame):
    """
    Compact status metrics bar at the top of the Event Log.
    Displays counts categorized by event level.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            EventCountersBar {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # Title & Subtitle
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("EVENT LOG / MISSION TIMELINE")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; letter-spacing: 0.8px;")
        title_box.addWidget(title)

        sub = QLabel("CHRONOLOGICAL SUBSYSTEM JOURNAL & OPERATIONAL AUDIT")
        sub.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 9px; font-weight: 600; letter-spacing: 0.5px;")
        title_box.addWidget(sub)

        layout.addLayout(title_box)
        layout.addStretch(1)

        # Counters: TOTAL | INFO | WARNING | ERROR | SUCCESS
        self.val_total = self._add_counter_item(layout, "TOTAL EVENTS", "0", Theme.TEXT_PRIMARY)
        self._add_v_separator(layout)
        self.val_info = self._add_counter_item(layout, "INFO", "0", Theme.ACCENT)
        self._add_v_separator(layout)
        self.val_warning = self._add_counter_item(layout, "WARNING", "0", Theme.STATUS_WARNING)
        self._add_v_separator(layout)
        self.val_error = self._add_counter_item(layout, "ERROR", "0", Theme.STATUS_CRITICAL)
        self._add_v_separator(layout)
        self.val_success = self._add_counter_item(layout, "SUCCESS", "0", Theme.STATUS_SUCCESS)

    def _add_counter_item(self, layout: QHBoxLayout, label: str, init_val: str, color: str) -> QLabel:
        box = QWidget()
        box_l = QVBoxLayout(box)
        box_l.setContentsMargins(0, 0, 0, 0)
        box_l.setSpacing(1)
        box_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val_lbl = QLabel(init_val)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: monospace;")

        title_lbl = QLabel(label)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 8px; font-weight: bold; letter-spacing: 0.6px;")

        box_l.addWidget(val_lbl)
        box_l.addWidget(title_lbl)
        layout.addWidget(box)
        return val_lbl

    def _add_v_separator(self, layout: QHBoxLayout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"border: none; border-left: 1px solid {Theme.BORDER};")
        sep.setFixedHeight(26)
        layout.addWidget(sep)

    def update_counts(self, events: List[Event]):
        total = len(events)
        info_c = sum(1 for e in events if e.level.upper() == "INFO")
        warn_c = sum(1 for e in events if e.level.upper() == "WARNING")
        err_c = sum(1 for e in events if e.level.upper() in ("ERROR", "CRITICAL"))
        succ_c = sum(1 for e in events if e.level.upper() == "SUCCESS")

        self.val_total.setText(str(total))
        self.val_info.setText(str(info_c))
        self.val_warning.setText(str(warn_c))
        self.val_error.setText(str(err_c))
        self.val_success.setText(str(succ_c))


class EventLogView(QWidget):
    """
    Main operator-facing Event Log view conforming to Step 9 requirements:
    1. Event Counters Bar (live counts by level)
    2. Interactive Level and Source Filters + Keyword Search
    3. Chronological Event Table
    4. Selected Event Details Panel with formatted parameters
    5. Cross-page navigation to related incidents
    """
    navigate_to_incidents = Signal(str)

    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self.all_events: List[Event] = []
        self.active_level_filter: str = "ALL"
        self.active_source_filter: str = "ALL SOURCES"
        self.active_search_query: str = ""
        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(12)

        # 1. Top Metrics Counters Bar
        self.counters_bar = EventCountersBar()
        root_layout.addWidget(self.counters_bar)

        # 2. Filters & Search Control Bar
        filter_card = QFrame()
        filter_card.setFixedHeight(48)
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        fc_layout = QHBoxLayout(filter_card)
        fc_layout.setContentsMargins(12, 6, 12, 6)
        fc_layout.setSpacing(8)

        # Level filter buttons: ALL | INFO | WARNING | ERROR | SUCCESS
        self.level_buttons = {}
        for lvl in ["ALL", "INFO", "WARNING", "ERROR", "SUCCESS"]:
            btn = QPushButton(lvl)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, l=lvl: self._on_level_filter_changed(l))
            fc_layout.addWidget(btn)
            self.level_buttons[lvl] = btn

        self.level_buttons["ALL"].setChecked(True)
        self._update_level_button_styles()

        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"border: none; border-left: 1px solid {Theme.BORDER};")
        sep.setFixedHeight(24)
        fc_layout.addWidget(sep)

        # Source filter combo
        self.source_combo = QComboBox()
        self.source_combo.setFixedHeight(28)
        self.source_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        sources = [
            "ALL SOURCES", "MISSION", "CAMERA", "AI", "INCIDENT", "TELEMETRY",
            "COMMUNICATION", "SLAM", "LIDAR", "DATABASE", "BACKEND", "RAG", "LLM", "SYSTEM", "DASHBOARD"
        ]
        self.source_combo.addItems(sources)
        self.source_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.ACCENT};
                selection-color: #0B0F14;
            }}
        """)
        self.source_combo.currentTextChanged.connect(self._on_source_filter_changed)
        fc_layout.addWidget(self.source_combo)

        # Search field
        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(28)
        self.search_input.setPlaceholderText("🔍  Search events (message, source, incident, mission)...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        fc_layout.addWidget(self.search_input, 1)

        # Clear Filters Button
        self.btn_clear = QPushButton("CLEAR FILTERS")
        self.btn_clear.setFixedHeight(28)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.btn_clear.clicked.connect(self._on_clear_filters)
        fc_layout.addWidget(self.btn_clear)

        # Refresh Button
        self.btn_refresh = QPushButton("REFRESH")
        self.btn_refresh.setFixedHeight(28)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 180, 216, 0.15);
            }}
        """)
        self.btn_refresh.clicked.connect(self._poll_data)
        fc_layout.addWidget(self.btn_refresh)

        root_layout.addWidget(filter_card)

        # 3. Main Area: Splitter containing Event Table (top) and Event Detail Panel (bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
                height: 8px;
            }
        """)

        # Event Table
        self.event_table = EventTableWidget()
        self.event_table.event_selected.connect(self._on_event_selected)
        splitter.addWidget(self.event_table)

        # Event Detail Panel
        self.event_detail = EventDetailPanel()
        self.event_detail.view_incident_requested.connect(self._on_view_incident)
        splitter.addWidget(self.event_detail)

        # Initial splitter stretch (65% table, 35% detail)
        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)

        root_layout.addWidget(splitter, 1)

    def _update_level_button_styles(self):
        for lvl, btn in self.level_buttons.items():
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.BG_PANEL};
                        color: {Theme.ACCENT};
                        border: 1px solid {Theme.ACCENT};
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 2px 10px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {Theme.TEXT_SECONDARY};
                        border: none;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: 500;
                        padding: 2px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.BG_SECONDARY};
                        color: {Theme.TEXT_PRIMARY};
                    }}
                """)

    def _init_data(self):
        self.all_events = self.data_service.get_events()
        self.counters_bar.update_counts(self.all_events)
        self._apply_filters()

        # Select first event if available
        if self.all_events:
            self.event_detail.show_event(self.all_events[0])

    def _start_live_updates(self):
        self.data_service.event_added.connect(self._on_event_added)
        self.data_service.events_updated.connect(self._on_events_updated)

    def _on_event_added(self, event):
        self.all_events = self.data_service.get_events()
        self.counters_bar.update_counts(self.all_events)
        self._apply_filters()

    def _on_events_updated(self, events):
        self.all_events = events
        self.counters_bar.update_counts(self.all_events)
        self._apply_filters()

    def _poll_data(self):
        """Manual refresh triggered by the Refresh button."""
        self._on_events_updated(self.data_service.get_events())

    def _apply_filters(self):
        filtered = []
        q = self.active_search_query.strip().lower()

        for ev in self.all_events:
            # 1. Level filter
            if self.active_level_filter != "ALL":
                if ev.level.upper() != self.active_level_filter.upper():
                    continue

            # 2. Source filter
            if self.active_source_filter != "ALL SOURCES":
                if ev.source.upper() != self.active_source_filter.upper():
                    continue

            # 3. Search query filter
            if q:
                msg_match = q in ev.message.lower()
                src_match = q in ev.source.lower()
                type_match = q in ev.event_type.lower()
                msn_match = q in (ev.mission_id or "").lower()
                inc_match = q in (ev.incident_id or "").lower()
                id_match = q in ev.event_id.lower()
                if not (msg_match or src_match or type_match or msn_match or inc_match or id_match):
                    continue

            filtered.append(ev)

        self.event_table.set_events(filtered)

    def _on_level_filter_changed(self, level: str):
        self.active_level_filter = level
        for lvl, btn in self.level_buttons.items():
            btn.setChecked(lvl == level)
        self._update_level_button_styles()
        self._apply_filters()

    def _on_source_filter_changed(self, source: str):
        self.active_source_filter = source
        self._apply_filters()

    def _on_search_text_changed(self, text: str):
        self.active_search_query = text
        self._apply_filters()

    def _on_clear_filters(self):
        self.active_level_filter = "ALL"
        for lvl, btn in self.level_buttons.items():
            btn.setChecked(lvl == "ALL")
        self._update_level_button_styles()

        self.source_combo.setCurrentIndex(0)
        self.active_source_filter = "ALL SOURCES"

        self.search_input.clear()
        self.active_search_query = ""

        self._apply_filters()

    def _on_event_selected(self, ev: Event):
        self.event_detail.show_event(ev)

    def _on_view_incident(self, incident_id: str):
        self.data_service.log_event(
            message=f"Jump to incident {incident_id} requested from Event Log",
            event_type="NAVIGATION",
            severity="INFO",
            source="DASHBOARD"
        )
        self.navigate_to_incidents.emit(incident_id)
