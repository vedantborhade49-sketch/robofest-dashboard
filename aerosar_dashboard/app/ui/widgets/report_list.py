from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.models.report import Report

class ReportRowWidget(QFrame):
    clicked = Signal(Report)

    def __init__(self, report: Report, is_selected: bool = False):
        super().__init__()
        self.report = report
        self.is_selected = is_selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self.update_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: Report ID, Incident ID, Status Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.id_label = QLabel(self.report.report_id)
        self.id_label.setStyleSheet("font-size: 13px; font-weight: bold; font-family: monospace;")
        top_row.addWidget(self.id_label)

        self.inc_badge = QLabel(self.report.incident_id)
        self.inc_badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-family: monospace;
            }}
        """)
        top_row.addWidget(self.inc_badge)

        top_row.addStretch()

        self.status_badge = QLabel(self.report.status)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_status_badge_style()
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # Middle row: Incident Type & Confidence
        mid_row = QHBoxLayout()
        mid_row.setSpacing(8)

        type_text = self.report.incident_type
        conf_percent = int(self.report.confidence * 100)
        self.type_conf_label = QLabel(f"{type_text}   {conf_percent}%")
        self.type_conf_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
        mid_row.addWidget(self.type_conf_label)
        mid_row.addStretch()

        layout.addLayout(mid_row)

        # Bottom row: Generated Time & Context Sources count
        bot_row = QHBoxLayout()
        bot_row.setSpacing(8)

        time_str = self.report.generated_at.strftime("%H:%M:%S")
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-family: monospace;")
        bot_row.addWidget(self.time_label)

        bot_row.addStretch()

        src_count = len(self.report.context_sources)
        src_label = f"{src_count} source{'s' if src_count != 1 else ''}"
        self.sources_pill = QLabel(src_label)
        self.sources_pill.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 10px;
                font-style: italic;
            }}
        """)
        bot_row.addWidget(self.sources_pill)

        layout.addLayout(bot_row)

    def _apply_status_badge_style(self):
        st = self.report.status.upper()
        if st == "REVIEWED":
            color = Theme.STATUS_SUCCESS
            bg = "rgba(34, 197, 94, 0.15)"
            border = "rgba(34, 197, 94, 0.4)"
        elif st == "GENERATED":
            color = Theme.ACCENT
            bg = "rgba(0, 180, 216, 0.15)"
            border = "rgba(0, 180, 216, 0.4)"
        elif st == "PENDING":
            color = Theme.STATUS_WARNING
            bg = "rgba(245, 158, 11, 0.15)"
            border = "rgba(245, 158, 11, 0.4)"
        else:  # UNAVAILABLE
            color = Theme.TEXT_SECONDARY
            bg = "rgba(140, 152, 166, 0.15)"
            border = "rgba(140, 152, 166, 0.3)"

        self.status_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 2px 7px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)

    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_style()

    def update_report(self, report: Report):
        self.report = report
        self.status_badge.setText(report.status)
        self._apply_status_badge_style()
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                ReportRowWidget {{
                    background-color: {Theme.BG_PANEL};
                    border: 1px solid {Theme.ACCENT};
                    border-left: 4px solid {Theme.ACCENT};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ReportRowWidget {{
                    background-color: {Theme.BG_SECONDARY};
                    border: 1px solid {Theme.BORDER};
                    border-left: 4px solid transparent;
                    border-radius: 6px;
                }}
                ReportRowWidget:hover {{
                    background-color: {Theme.BG_PANEL};
                    border-color: {Theme.BORDER};
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.report)
        super().mousePressEvent(event)


class ReportList(QWidget):
    report_selected = Signal(Report)

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMaximumWidth(360)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.reports: List[Report] = []
        self.current_filter: str = "ALL"
        self.selected_report: Optional[Report] = None
        self._row_widgets: List[ReportRowWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 1. Header Bar: Title and Count Badge
        header_frame = QFrame()
        header_frame.setFixedHeight(44)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(14, 0, 14, 0)

        title = QLabel("INCIDENT REPORTS")
        title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self.count_badge = QLabel("0 REPORTS")
        self.count_badge.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 10px; font-weight: bold; font-family: monospace;")
        h_layout.addWidget(self.count_badge)

        main_layout.addWidget(header_frame)

        # 2. Filter tabs: ALL | GENERATED | REVIEWED | PENDING
        filter_frame = QFrame()
        filter_frame.setFixedHeight(36)
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        f_layout = QHBoxLayout(filter_frame)
        f_layout.setContentsMargins(4, 3, 4, 3)
        f_layout.setSpacing(4)

        self.filter_buttons = {}
        for f_name in ["ALL", "GENERATED", "REVIEWED", "PENDING"]:
            btn = QPushButton(f_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked, n=f_name: self.set_filter(n))
            f_layout.addWidget(btn)
            self.filter_buttons[f_name] = btn

        self.filter_buttons["ALL"].setChecked(True)
        self._update_filter_button_styles()
        main_layout.addWidget(filter_frame)

        # 3. Scrollable List Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #0D1219;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #252D38;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3B4758;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

    def _update_filter_button_styles(self):
        for name, btn in self.filter_buttons.items():
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.BG_PANEL};
                        color: {Theme.ACCENT};
                        border: 1px solid {Theme.ACCENT};
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 2px 6px;
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
                        padding: 2px 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.BG_PANEL};
                        color: {Theme.TEXT_PRIMARY};
                    }}
                """)

    def set_filter(self, filter_name: str):
        self.current_filter = filter_name
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == filter_name)
        self._update_filter_button_styles()
        self._rebuild_list()

    def set_reports(self, reports: List[Report]):
        self.reports = reports
        self.count_badge.setText(f"{len(reports)} REPORTS")
        self._rebuild_list()

    def _rebuild_list(self):
        # Clear existing rows
        for w in self._row_widgets:
            self.list_layout.removeWidget(w)
            w.deleteLater()
        self._row_widgets.clear()

        # Filter reports
        filtered = []
        for r in self.reports:
            if self.current_filter == "ALL":
                filtered.append(r)
            elif self.current_filter == "GENERATED" and r.status.upper() == "GENERATED":
                filtered.append(r)
            elif self.current_filter == "REVIEWED" and (r.status.upper() == "REVIEWED" or r.human_review_status.upper() == "REVIEWED"):
                filtered.append(r)
            elif self.current_filter == "PENDING" and (r.status.upper() == "PENDING" or r.human_review_status.upper() == "PENDING REVIEW"):
                filtered.append(r)

        # Insert before the stretch at the end
        stretch_index = self.list_layout.count() - 1

        selected_id = self.selected_report.report_id if self.selected_report else None

        for report in filtered:
            is_sel = (selected_id == report.report_id)
            row = ReportRowWidget(report, is_selected=is_sel)
            row.clicked.connect(self._on_row_clicked)
            self.list_layout.insertWidget(stretch_index, row)
            self._row_widgets.append(row)
            stretch_index += 1

    def _on_row_clicked(self, report: Report):
        self.select_report(report)

    def select_report(self, report: Report):
        self.selected_report = report
        for row in self._row_widgets:
            row.set_selected(row.report.report_id == report.report_id)
        self.report_selected.emit(report)

    def select_report_by_id(self, report_id: str):
        for r in self.reports:
            if r.report_id == report_id:
                self.select_report(r)
                return

    def select_report_by_incident_id(self, incident_id: str):
        for r in self.reports:
            if r.incident_id == incident_id:
                self.select_report(r)
                return

    def update_report_in_place(self, report: Report):
        """Updates report in memory and in matching row widget without rebuilding list."""
        for i, r in enumerate(self.reports):
            if r.report_id == report.report_id:
                self.reports[i] = report
                break
        for row in self._row_widgets:
            if row.report.report_id == report.report_id:
                row.update_report(report)
                break
