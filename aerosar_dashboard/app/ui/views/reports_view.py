from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.report import Report
from app.ui.widgets.report_list import ReportList
from app.ui.widgets.report_detail import ReportDetail

class ReportCountersBar(QFrame):
    """
    Status metrics bar at the top of the Reports page.
    Displays summary counts across all intelligence reports.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            ReportCountersBar {{
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

        title = QLabel("REPORTS / MISSION INTELLIGENCE")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; letter-spacing: 0.8px;")
        title_box.addWidget(title)

        sub = QLabel("RAG RETRIEVAL & AI INCIDENT SYNTHESIS (SIMULATED)")
        sub.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 9px; font-weight: 600; letter-spacing: 0.5px;")
        title_box.addWidget(sub)

        layout.addLayout(title_box)
        layout.addStretch(1)

        # Counters: TOTAL | GENERATED | REVIEWED | PENDING | UNAVAILABLE
        self.val_total = self._add_counter_item(layout, "TOTAL", "0", Theme.TEXT_PRIMARY)
        self._add_v_separator(layout)
        self.val_generated = self._add_counter_item(layout, "GENERATED", "0", Theme.ACCENT)
        self._add_v_separator(layout)
        self.val_reviewed = self._add_counter_item(layout, "REVIEWED", "0", Theme.STATUS_SUCCESS)
        self._add_v_separator(layout)
        self.val_pending = self._add_counter_item(layout, "PENDING", "0", Theme.STATUS_WARNING)
        self._add_v_separator(layout)
        self.val_unavail = self._add_counter_item(layout, "UNAVAILABLE", "0", Theme.TEXT_SECONDARY)

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

    def update_counts(self, reports: List[Report]):
        total = len(reports)
        gen = sum(1 for r in reports if r.status.upper() == "GENERATED")
        rev = sum(1 for r in reports if r.status.upper() == "REVIEWED" or r.human_review_status.upper() == "REVIEWED")
        pen = sum(1 for r in reports if r.status.upper() == "PENDING" and r.human_review_status.upper() != "REVIEWED")
        unav = sum(1 for r in reports if r.status.upper() == "UNAVAILABLE")

        self.val_total.setText(str(total))
        self.val_generated.setText(str(gen))
        self.val_reviewed.setText(str(rev))
        self.val_pending.setText(str(pen))
        self.val_unavail.setText(str(unav))


class ReportsView(QWidget):
    """
    Main operator-facing Reports & RAG Interface view conforming to Step 8 requirements:
    1. Report List (left)
    2. Selected Report Detail (right)
    3. Incident Summary (detected facts)
    4. Simulated AI-Generated Incident Report
    5. Retrieved Context (RAG sources with relevance scores)
    6. Evidence snapshot
    7. Report Metadata
    8. Human Review supervision workflow
    """
    navigate_to_incidents = Signal(str)  # Emits incident_id to switch to Incidents view

    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        # 1. Top Summary Bar
        self.counters_bar = ReportCountersBar()
        self.main_layout.addWidget(self.counters_bar)

        # 2. Main Area: Left List + Right Detail
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(16)

        self.report_list = ReportList()
        middle_layout.addWidget(self.report_list, 32)

        self.report_detail = ReportDetail()
        middle_layout.addWidget(self.report_detail, 68)

        self.main_layout.addLayout(middle_layout, 1)

        # Signal connections
        self.report_list.report_selected.connect(self._on_report_selected)
        self.report_detail.view_incident_requested.connect(self._on_view_incident)
        self.report_detail.review_report_requested.connect(self._on_review_report)

    def _init_data(self):
        reports = self.data_service.get_reports()
        self.counters_bar.update_counts(reports)
        self.report_list.set_reports(reports)

        # Pre-select first report (RPT-001) for immediate inspection
        if reports:
            self.report_list.select_report(reports[0])

    def _start_live_updates(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_data)
        self.timer.start(4000)  # Gentle 4-second cycle

    def _poll_data(self):
        reports = self.data_service.get_reports()
        self.counters_bar.update_counts(reports)

    def _on_report_selected(self, report: Report):
        self.report_detail.show_report(report)
        self.data_service.log_event(
            message=f"Report {report.report_id} selected for inspection ({report.incident_id})",
            event_type="REPORT",
            severity="INFO"
        )

    def _on_view_incident(self, incident_id: str):
        self.data_service.log_event(
            message=f"Cross-page jump to incident {incident_id} requested from Report view",
            event_type="NAVIGATION",
            severity="INFO"
        )
        self.navigate_to_incidents.emit(incident_id)

    def _on_review_report(self, report_id: str):
        success = self.data_service.review_report(report_id)
        if success:
            updated = self.data_service.get_report(report_id)
            if updated:
                self.report_detail.show_report(updated)
                self.report_list.update_report_in_place(updated)
                self.counters_bar.update_counts(self.data_service.get_reports())

    def select_report_by_id(self, report_id: str):
        """Allows programmatic selection from other navigation triggers."""
        self.report_list.select_report_by_id(report_id)

    def select_report_by_incident_id(self, incident_id: str):
        """Allows programmatic selection when jumping from an incident."""
        self.report_list.select_report_by_incident_id(incident_id)
