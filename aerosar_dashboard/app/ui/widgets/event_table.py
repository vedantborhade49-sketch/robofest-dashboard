from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from app.ui.theme import Theme
from app.models.event import Event

class EventTableWidget(QTableWidget):
    """
    Compact mission-control chronological event activity table.
    Columns: TIME | LEVEL | SOURCE | EVENT | MISSION | INCIDENT
    """
    event_selected = Signal(Event)

    def __init__(self):
        super().__init__()
        self.events: List[Event] = []
        self._displayed_events: List[Event] = []
        self._selected_event_id: Optional[str] = None
        self._setup_table()

    def _setup_table(self):
        # Configure columns
        headers = ["TIME", "LEVEL", "SOURCE", "EVENT", "MISSION", "INCIDENT"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Selection and interaction rules
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        # Column widths & sizing
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.setColumnWidth(0, 88)   # TIME
        self.setColumnWidth(1, 92)   # LEVEL
        self.setColumnWidth(2, 120)  # SOURCE
        self.setColumnWidth(4, 88)   # MISSION
        self.setColumnWidth(5, 88)   # INCIDENT

        # Table stylesheet
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                color: {Theme.TEXT_PRIMARY};
                font-family: {Theme.FONT_FAMILY};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid #1A212B;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(0, 180, 216, 0.16);
                border-left: 3px solid {Theme.ACCENT};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.04);
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_SECONDARY};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {Theme.BORDER};
                border-right: 1px solid #1A212B;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.6px;
            }}
            QScrollBar:vertical {{
                background: #0D1219;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #252D38;
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #3B4758;
            }}
        """)

        self.itemSelectionChanged.connect(self._on_selection_changed)

    def set_events(self, events: List[Event]):
        self.events = events
        self._displayed_events = list(events)
        self._render_rows()

    def _render_rows(self):
        self.blockSignals(True)
        prev_id = self._selected_event_id

        self.setRowCount(len(self._displayed_events))
        row_to_select = -1

        for row_idx, ev in enumerate(self._displayed_events):
            self.setRowHeight(row_idx, 32)

            # 1. TIME
            time_str = ev.timestamp.strftime("%H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setFont(QFont("Segoe UI", 9))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            time_item.setForeground(QColor(Theme.TEXT_SECONDARY))
            self.setItem(row_idx, 0, time_item)

            # 2. LEVEL Badge Widget
            level_widget = self._create_level_badge(ev.level)
            self.setCellWidget(row_idx, 1, level_widget)

            # 3. SOURCE
            source_item = QTableWidgetItem(ev.source.upper())
            source_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            source_item.setForeground(QColor(Theme.ACCENT))
            self.setItem(row_idx, 2, source_item)

            # 4. EVENT / MESSAGE
            msg_item = QTableWidgetItem(ev.message)
            msg_item.setFont(QFont("Segoe UI", 9))
            msg_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            msg_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.setItem(row_idx, 3, msg_item)

            # 5. MISSION
            msn_str = ev.mission_id or "—"
            msn_item = QTableWidgetItem(msn_str)
            msn_item.setFont(QFont("Segoe UI", 9))
            msn_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
            msn_item.setForeground(QColor(Theme.TEXT_SECONDARY))
            self.setItem(row_idx, 4, msn_item)

            # 6. INCIDENT
            inc_str = ev.incident_id or "—"
            inc_item = QTableWidgetItem(inc_str)
            inc_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            inc_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
            if ev.incident_id:
                inc_item.setForeground(QColor(Theme.ACCENT))
            else:
                inc_item.setForeground(QColor(Theme.TEXT_SECONDARY))
            self.setItem(row_idx, 5, inc_item)

            if ev.event_id == prev_id:
                row_to_select = row_idx

        self.blockSignals(False)

        # Preserve selection or select top row
        if row_to_select != -1:
            self.selectRow(row_to_select)
        elif self.rowCount() > 0:
            self.selectRow(0)

    def _create_level_badge(self, level: str) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        l = QHBoxLayout(container)
        l.setContentsMargins(6, 4, 6, 4)
        l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(level.upper())
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

        lbl.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 1px 7px;
                font-size: 9px;
                font-weight: bold;
                font-family: monospace;
            }}
        """)
        l.addWidget(lbl)
        return container

    def _on_selection_changed(self):
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            idx = selected_rows[0].row()
            if 0 <= idx < len(self._displayed_events):
                ev = self._displayed_events[idx]
                self._selected_event_id = ev.event_id
                self.event_selected.emit(ev)

    def select_event_by_id(self, event_id: str):
        for row_idx, ev in enumerate(self._displayed_events):
            if ev.event_id == event_id:
                self.selectRow(row_idx)
                return

    def get_selected_event(self) -> Optional[Event]:
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            idx = selected_rows[0].row()
            if 0 <= idx < len(self._displayed_events):
                return self._displayed_events[idx]
        return None
