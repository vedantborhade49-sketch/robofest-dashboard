from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from app.ui.theme import Theme
from app.models.report import Report
from app.models.context import RetrievedContext

class ReportEvidenceWidget(QFrame):
    """
    Simulated tactical payload evidence display for the selected report.
    Paints a mission viewfinder with grid, corner brackets, target bounding box, and telemetry overlay.
    """
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.report: Optional[Report] = None

    def set_report(self, report: Report):
        self.report = report
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Dark tactical background
        painter.fillRect(0, 0, w, h, QColor("#090D13"))

        # Subtle grid lines
        grid_pen = QPen(QColor(30, 42, 58, 65))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        grid_step = 28
        for x in range(0, w, grid_step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_step):
            painter.drawLine(0, y, w, y)

        if not self.report:
            # Empty state
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "NO EVIDENCE SELECTED")
            return

        # Viewfinder corners
        corner_pen = QPen(QColor(Theme.TEXT_SECONDARY), 1.2)
        painter.setPen(corner_pen)
        c_len = 16
        # Top-left
        painter.drawLine(12, 12, 12 + c_len, 12)
        painter.drawLine(12, 12, 12, 12 + c_len)
        # Top-right
        painter.drawLine(w - 12, 12, w - 12 - c_len, 12)
        painter.drawLine(w - 12, 12, w - 12, 12 + c_len)
        # Bottom-left
        painter.drawLine(12, h - 12, 12 + c_len, h - 12)
        painter.drawLine(12, h - 12, 12, h - 12 - c_len)
        # Bottom-right
        painter.drawLine(w - 12, h - 12, w - 12 - c_len, h - 12)
        painter.drawLine(w - 12, h - 12, w - 12, h - 12 - c_len)

        # Center reticle
        cx, cy = w // 2, h // 2
        ret_pen = QPen(QColor(Theme.BORDER), 1)
        painter.setPen(ret_pen)
        painter.drawLine(cx - 8, cy, cx + 8, cy)
        painter.drawLine(cx, cy - 8, cx, cy + 8)

        # Simulated Target Bounding Box
        if self.report.evidence_image:
            bx, by = 0.50, 0.48
            bw, bh = 0.22, 0.38
            box_w = max(70.0, bw * w)
            box_h = max(80.0, bh * h)
            box_x = (bx * w) - (box_w / 2.0)
            box_y = (by * h) - (box_h / 2.0)

            # Box fill & outline
            box_fill = QColor(0, 180, 216, 25)
            accent_col = QColor(Theme.ACCENT)
            if self.report.status == "REVIEWED":
                box_fill = QColor(34, 197, 94, 25)
                accent_col = QColor(Theme.STATUS_SUCCESS)

            painter.fillRect(QRectF(box_x, box_y, box_w, box_h), box_fill)
            painter.setPen(QPen(accent_col, 1.5))
            painter.drawRect(QRectF(box_x, box_y, box_w, box_h))

            # Target label banner above bbox
            painter.fillRect(QRectF(box_x, max(14.0, box_y - 18.0), 120.0, 16.0), QColor("#11161D"))
            painter.setPen(QPen(accent_col, 1))
            painter.drawRect(QRectF(box_x, max(14.0, box_y - 18.0), 120.0, 16.0))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(
                QRectF(box_x + 4.0, max(14.0, box_y - 18.0), 116.0, 16.0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"TARGET: {self.report.incident_type[:10]} {int(self.report.confidence * 100)}%"
            )
        else:
            # Unavailable or dismissed evidence
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "NO EVIDENCE PAYLOAD RECORDED")

        # Top overlay info: Source & Frame
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        painter.drawText(20, 24, f"SOURCE: {self.report.evidence_source}")
        painter.drawText(w - 180, 24, f"FRAME: #{self.report.evidence_frame}")

        # Bottom overlay info: Coordinates & File
        loc = self.report.incident_summary.location
        painter.drawText(20, h - 20, f"LOCAL COORDS: X={loc.x:.1f}m  Y={loc.y:.1f}m  Z={loc.z:.1f}m")
        if self.report.evidence_image:
            painter.drawText(w - 180, h - 20, f"FILE: {self.report.evidence_image}")


class RetrievedContextCard(QFrame):
    """Card displaying a single retrieved context item from the simulated RAG engine."""
    def __init__(self, ctx: RetrievedContext):
        super().__init__()
        self.setStyleSheet(f"""
            RetrievedContextCard {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 5px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header row: Source ID, Type tag, Relevance Score
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        src_id = QLabel(ctx.source_id)
        src_id.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: bold; font-family: monospace;")
        top_row.addWidget(src_id)

        type_lbl = QLabel(ctx.source_type)
        type_lbl.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)
        top_row.addWidget(type_lbl)

        top_row.addStretch()

        score_pct = int(ctx.relevance_score * 100)
        rel_badge = QLabel(f"Relevance: {ctx.relevance_score:.2f} ({score_pct}%)")
        rel_badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.STATUS_SUCCESS if ctx.relevance_score >= 0.85 else Theme.ACCENT};
                background-color: rgba(0, 180, 216, 0.1);
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: bold;
                font-family: monospace;
            }}
        """)
        top_row.addWidget(rel_badge)

        layout.addLayout(top_row)

        # Content text
        content_lbl = QLabel(ctx.content)
        content_lbl.setWordWrap(True)
        content_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; line-height: 1.4;")
        layout.addWidget(content_lbl)


class ReportDetail(QWidget):
    view_incident_requested = Signal(str)      # Emits incident_id to navigate to Incidents view
    review_report_requested = Signal(str)      # Emits report_id to mark as reviewed

    def __init__(self):
        super().__init__()
        self.report: Optional[Report] = None
        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area for the entire detail view
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
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
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3B4758;
            }
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 8, 16)
        self.content_layout.setSpacing(14)

        # Empty state placeholder
        self.placeholder_widget = QWidget()
        ph_layout = QVBoxLayout(self.placeholder_widget)
        ph_layout.setContentsMargins(20, 60, 20, 60)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_lbl = QLabel("NO REPORT SELECTED")
        ph_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 16px; font-weight: bold; letter-spacing: 1px;")
        ph_sub = QLabel("Select an incident intelligence report from the list to view synthesis details.")
        ph_sub.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; margin-top: 4px;")
        ph_layout.addWidget(ph_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(ph_sub, alignment=Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder_widget)

        # Detail Container (hidden when no report)
        self.detail_container = QWidget()
        self.detail_container.setStyleSheet("background-color: transparent;")
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(14)

        # 1. Header & Actions Bar
        self._setup_header_section()

        # 2. Section 3 — Incident Summary (Detected Facts)
        self._setup_incident_summary_section()

        # 3. Section 4 — AI-Generated Report Area
        self._setup_ai_report_section()

        # 4. Section 6 — Evidence Section
        self._setup_evidence_section()

        # 5. Section 5 — Retrieved Context Section
        self._setup_retrieved_context_section()

        # 6. Section 7 — Report Metadata Section
        self._setup_metadata_section()

        # 7. Section 8 — Human Review Section
        self._setup_human_review_section()

        self.detail_container.setVisible(False)
        self.content_layout.addWidget(self.detail_container)

        scroll.setWidget(self.content_widget)
        root_layout.addWidget(scroll)

    def _setup_header_section(self):
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(18, 14, 18, 14)
        h_layout.setSpacing(14)

        # Title & Incident ID
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.val_report_id = QLabel("REPORT RPT-001")
        self.val_report_id.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold; font-family: monospace; letter-spacing: 0.5px;")
        title_box.addWidget(self.val_report_id)

        sub_line = QHBoxLayout()
        sub_line.setSpacing(10)
        self.val_sub_tags = QLabel("INCIDENT: INC-001  |  MISSION: SAR-001")
        self.val_sub_tags.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-family: monospace;")
        sub_line.addWidget(self.val_sub_tags)
        title_box.addLayout(sub_line)

        h_layout.addLayout(title_box)
        h_layout.addStretch()

        # Status badge
        self.val_status_badge = QLabel("GENERATED")
        self.val_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_header_status_badge("GENERATED")
        h_layout.addWidget(self.val_status_badge)

        # Navigate to Incident button
        self.btn_view_incident = QPushButton("↗ VIEW INCIDENT")
        self.btn_view_incident.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_incident.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 180, 216, 0.15);
            }}
        """)
        self.btn_view_incident.clicked.connect(self._on_view_incident_clicked)
        h_layout.addWidget(self.btn_view_incident)

        self.detail_layout.addWidget(header_card)

    def _setup_incident_summary_section(self):
        card = self._create_section_card("INCIDENT SUMMARY", "Underlying raw telemetry & detection facts recorded by the drone payload.")
        layout = card.layout()

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setHorizontalSpacing(16)

        self.val_inc_type = self._add_field(grid, 0, 0, "INCIDENT TYPE", "PERSON DETECTED", Theme.TEXT_PRIMARY)
        self.val_inc_conf = self._add_field(grid, 0, 1, "DETECTION CONFIDENCE", "94.2%", Theme.ACCENT)
        self.val_inc_time = self._add_field(grid, 0, 2, "TIMESTAMP", "14:32:08", Theme.TEXT_PRIMARY)
        self.val_inc_status = self._add_field(grid, 0, 3, "INCIDENT STATUS", "CONFIRMED", Theme.STATUS_SUCCESS)

        self.val_inc_x = self._add_field(grid, 1, 0, "LOCATION X", "12.4 m", Theme.TEXT_PRIMARY)
        self.val_inc_y = self._add_field(grid, 1, 1, "LOCATION Y", "-6.8 m", Theme.TEXT_PRIMARY)
        self.val_inc_z = self._add_field(grid, 1, 2, "LOCATION Z (ALT)", "3.2 m", Theme.TEXT_PRIMARY)
        self.val_inc_frame = self._add_field(grid, 1, 3, "COORDINATE FRAME", "LOCAL / SLAM", Theme.TEXT_SECONDARY)

        layout.addLayout(grid)
        self.detail_layout.addWidget(card)

    def _setup_ai_report_section(self):
        card = self._create_section_card(
            "AI-GENERATED INCIDENT REPORT",
            "Synthesized situational narrative generated from detection facts and retrieved mission context."
        )
        layout = card.layout()

        # Simulated AI Notice Badge
        notice_box = QFrame()
        notice_box.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(245, 158, 11, 0.08);
                border: 1px solid rgba(245, 158, 11, 0.35);
                border-radius: 4px;
            }}
        """)
        nb_layout = QHBoxLayout(notice_box)
        nb_layout.setContentsMargins(10, 6, 10, 6)
        nb_layout.setSpacing(8)

        warn_icon = QLabel("⚠ SIMULATED MOCK AI REPORT")
        warn_icon.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        nb_layout.addWidget(warn_icon)

        warn_desc = QLabel("Ground station architecture placeholder — no real LLM inference backend connected.")
        warn_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-style: italic;")
        nb_layout.addWidget(warn_desc)
        nb_layout.addStretch()

        layout.addWidget(notice_box)

        # AI Report Text Box
        text_box = QFrame()
        text_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 5px;
            }}
        """)
        tb_layout = QVBoxLayout(text_box)
        tb_layout.setContentsMargins(14, 12, 14, 12)

        self.val_ai_text = QLabel()
        self.val_ai_text.setWordWrap(True)
        self.val_ai_text.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
                line-height: 1.5;
                font-family: {Theme.FONT_FAMILY};
            }}
        """)
        tb_layout.addWidget(self.val_ai_text)

        layout.addWidget(text_box)
        self.detail_layout.addWidget(card)

    def _setup_evidence_section(self):
        card = self._create_section_card(
            "EVIDENCE",
            "Visual payload snapshot captured at the moment of detection."
        )
        layout = card.layout()

        self.evidence_widget = ReportEvidenceWidget()
        layout.addWidget(self.evidence_widget)

        self.detail_layout.addWidget(card)

    def _setup_retrieved_context_section(self):
        card = self._create_section_card(
            "RETRIEVED CONTEXT",
            "Simulated RAG pipeline outputs retrieved to inform report synthesis."
        )
        self.context_card_layout = card.layout()

        self.context_container = QWidget()
        self.context_container.setStyleSheet("background-color: transparent;")
        self.context_items_layout = QVBoxLayout(self.context_container)
        self.context_items_layout.setContentsMargins(0, 0, 0, 0)
        self.context_items_layout.setSpacing(8)

        self.context_card_layout.addWidget(self.context_container)
        self.detail_layout.addWidget(card)

    def _setup_metadata_section(self):
        card = self._create_section_card(
            "REPORT METADATA",
            "System generation provenance and pipeline parameters."
        )
        layout = card.layout()

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setHorizontalSpacing(16)

        self.val_meta_rpt = self._add_field(grid, 0, 0, "REPORT ID", "RPT-001", Theme.TEXT_PRIMARY)
        self.val_meta_inc = self._add_field(grid, 0, 1, "INCIDENT ID", "INC-001", Theme.TEXT_PRIMARY)
        self.val_meta_msn = self._add_field(grid, 0, 2, "MISSION ID", "SAR-001", Theme.TEXT_PRIMARY)
        self.val_meta_time = self._add_field(grid, 0, 3, "GENERATED AT", "14:32:08", Theme.TEXT_PRIMARY)

        self.val_meta_model = self._add_field(grid, 1, 0, "MODEL", "MOCK-RAG-LLM (SIMULATED)", Theme.ACCENT)
        self.val_meta_sources = self._add_field(grid, 1, 1, "CONTEXT SOURCES", "3 Sources", Theme.TEXT_PRIMARY)
        self.val_meta_status = self._add_field(grid, 1, 2, "REPORT STATUS", "GENERATED", Theme.ACCENT)
        self.val_meta_review = self._add_field(grid, 1, 3, "HUMAN REVIEW", "PENDING REVIEW", Theme.STATUS_WARNING)

        layout.addLayout(grid)
        self.detail_layout.addWidget(card)

    def _setup_human_review_section(self):
        card = self._create_section_card(
            "HUMAN REVIEW",
            "Operator supervision requirement: All autonomous intelligence reports require human sign-off."
        )
        layout = card.layout()

        row = QHBoxLayout()
        row.setSpacing(14)

        # Status indicator
        status_box = QVBoxLayout()
        status_box.setSpacing(2)

        st_title = QLabel("CURRENT REVIEW STATUS")
        st_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        status_box.addWidget(st_title)

        self.val_review_status_lbl = QLabel("PENDING REVIEW")
        self.val_review_status_lbl.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 13px; font-weight: bold; font-family: monospace;")
        status_box.addWidget(self.val_review_status_lbl)

        row.addLayout(status_box)
        row.addStretch()

        # Action Button: Mark as Reviewed
        self.btn_mark_reviewed = QPushButton("MARK AS REVIEWED")
        self.btn_mark_reviewed.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mark_reviewed.setFixedHeight(34)
        self.btn_mark_reviewed.clicked.connect(self._on_mark_reviewed_clicked)
        row.addWidget(self.btn_mark_reviewed)

        layout.addLayout(row)

        # Operational disclaimer note
        note = QLabel("Note: Marking as reviewed modifies local ground station state and logs operator audit trail. It does not issue autonomous flight or arming commands.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-style: italic; margin-top: 4px;")
        layout.addWidget(note)

        self.detail_layout.addWidget(card)

    def _create_section_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header with title and subtitle
        header_box = QVBoxLayout()
        header_box.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        header_box.addWidget(t_lbl)

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-style: italic;")
        header_box.addWidget(s_lbl)

        layout.addLayout(header_box)

        # Subtle divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        layout.addWidget(div)

        return card

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

    def _apply_header_status_badge(self, status: str):
        st = status.upper()
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

        self.val_status_badge.setText(st)
        self.val_status_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)

    def _update_review_button_style(self, is_reviewed: bool):
        if is_reviewed:
            self.val_review_status_lbl.setText("REVIEWED")
            self.val_review_status_lbl.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 13px; font-weight: bold; font-family: monospace;")
            self.btn_mark_reviewed.setText("REVIEWED ✓")
            self.btn_mark_reviewed.setEnabled(False)
            self.btn_mark_reviewed.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(34, 197, 94, 0.12);
                    color: {Theme.STATUS_SUCCESS};
                    border: 1px solid {Theme.STATUS_SUCCESS};
                    border-radius: 4px;
                    padding: 6px 16px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            self.val_review_status_lbl.setText("PENDING REVIEW")
            self.val_review_status_lbl.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 13px; font-weight: bold; font-family: monospace;")
            self.btn_mark_reviewed.setText("MARK AS REVIEWED")
            self.btn_mark_reviewed.setEnabled(True)
            self.btn_mark_reviewed.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    color: #0B0F14;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                    font-size: 11px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_HOVER};
                }}
            """)

    def show_report(self, report: Report):
        self.report = report
        self.placeholder_widget.setVisible(False)
        self.detail_container.setVisible(True)

        # 1. Header
        self.val_report_id.setText(f"REPORT {report.report_id}")
        self.val_sub_tags.setText(f"INCIDENT: {report.incident_id}  |  MISSION: {report.mission_id}")
        self._apply_header_status_badge(report.status)

        # 2. Incident Summary
        inc = report.incident_summary
        self.val_inc_type.setText(inc.type)
        self.val_inc_conf.setText(f"{inc.confidence * 100:.1f}%")
        self.val_inc_time.setText(inc.timestamp.strftime("%H:%M:%S"))
        self.val_inc_status.setText(inc.status)
        self.val_inc_x.setText(f"{inc.location.x:.1f} m")
        self.val_inc_y.setText(f"{inc.location.y:.1f} m")
        self.val_inc_z.setText(f"{inc.location.z:.1f} m")
        self.val_inc_frame.setText("LOCAL / SLAM")

        # 3. AI Report
        self.val_ai_text.setText(report.ai_report)

        # 4. Evidence
        self.evidence_widget.set_report(report)

        # 5. Retrieved Context
        # Clear existing context cards
        while self.context_items_layout.count() > 0:
            item = self.context_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if report.context_sources:
            for ctx in report.context_sources:
                card = RetrievedContextCard(ctx)
                self.context_items_layout.addWidget(card)
        else:
            empty_ctx = QLabel("No retrieved contextual sources for this report.")
            empty_ctx.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-style: italic; padding: 6px 0;")
            self.context_items_layout.addWidget(empty_ctx)

        # 6. Metadata
        self.val_meta_rpt.setText(report.report_id)
        self.val_meta_inc.setText(report.incident_id)
        self.val_meta_msn.setText(report.mission_id)
        self.val_meta_time.setText(report.generated_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.val_meta_model.setText(report.model_name)
        self.val_meta_sources.setText(f"{len(report.context_sources)} Sources")
        self.val_meta_status.setText(report.status)
        self.val_meta_review.setText(report.human_review_status)

        # 7. Human Review
        is_rev = (report.human_review_status.upper() == "REVIEWED" or report.status.upper() == "REVIEWED")
        self._update_review_button_style(is_rev)

    def _on_view_incident_clicked(self):
        if self.report:
            self.view_incident_requested.emit(self.report.incident_id)

    def _on_mark_reviewed_clicked(self):
        if self.report:
            self.review_report_requested.emit(self.report.report_id)
