from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from app.ui.theme import Theme
from app.models.incident import Incident

class EvidenceFrameWidget(QFrame):
    """
    Renders an operational evidence snapshot from drone optical/thermal payload,
    complete with AI detection bounding box, targeting reticle, and telemetry annotations.
    """
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.incident: Optional[Incident] = None

    def set_incident(self, incident: Incident):
        self.incident = incident
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Dark tactical background with subtle gradient
        painter.fillRect(0, 0, w, h, QColor("#090D13"))

        # 2. Subtle grid lines
        grid_pen = QPen(QColor(30, 42, 58, 60))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        grid_step = 32
        for x in range(0, w, grid_step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_step):
            painter.drawLine(0, y, w, y)

        if not self.incident:
            return

        # 2.5 Draw real evidence image if available
        if self.incident.evidence_image:
            from PySide6.QtGui import QPixmap
            import os
            if os.path.exists(self.incident.evidence_image):
                pixmap = QPixmap(self.incident.evidence_image)
                if not pixmap.isNull():
                    # Scale to fill the widget (or keep aspect ratio)
                    # The bounding box logic assumes normalized coords, so filling the widget aligns with the math.
                    pixmap = pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    painter.drawPixmap(0, 0, pixmap)
                    
                    # Dim it slightly so UI elements are readable
                    painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 80))

        # 3. Viewfinder corners
        corner_pen = QPen(QColor(Theme.TEXT_SECONDARY), 1)
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

        # 4. Target Bounding Box
        bx = self.incident.bbox.x if self.incident.bbox else 0.45
        by = self.incident.bbox.y if self.incident.bbox else 0.45
        bw = self.incident.bbox.width if self.incident.bbox else 0.18
        bh = self.incident.bbox.height if self.incident.bbox else 0.32

        # Convert normalized coords to widget pixels
        # Box centered at (bx, by)
        box_w = max(70.0, bw * w)
        box_h = max(80.0, bh * h)
        box_x = (bx * w) - (box_w / 2.0)
        box_y = (by * h) - (box_h / 2.0)

        # Clamp inside boundaries
        box_x = max(24.0, min(w - box_w - 24.0, box_x))
        box_y = max(34.0, min(h - box_h - 34.0, box_y))

        # Status accent color
        if self.incident.status == "CONFIRMED":
            accent_qcol = QColor(Theme.STATUS_SUCCESS)
            box_fill = QColor(34, 197, 94, 25)
        elif self.incident.status == "REVIEW":
            accent_qcol = QColor(Theme.STATUS_WARNING)
            box_fill = QColor(245, 158, 11, 25)
        else:
            accent_qcol = QColor(Theme.ACCENT)
            box_fill = QColor(0, 180, 216, 25)

        # Fill & outline bbox
        painter.fillRect(QRectF(box_x, box_y, box_w, box_h), box_fill)
        box_pen = QPen(accent_qcol, 1.5)
        painter.setPen(box_pen)
        painter.drawRect(QRectF(box_x, box_y, box_w, box_h))

        # Draw corner brackets on bbox
        b_bracket = 8
        painter.drawLine(int(box_x), int(box_y), int(box_x + b_bracket), int(box_y))
        painter.drawLine(int(box_x), int(box_y), int(box_x), int(box_y + b_bracket))
        painter.drawLine(int(box_x + box_w), int(box_y), int(box_x + box_w - b_bracket), int(box_y))
        painter.drawLine(int(box_x + box_w), int(box_y), int(box_x + box_w), int(box_y + b_bracket))
        painter.drawLine(int(box_x), int(box_y + box_h), int(box_x + b_bracket), int(box_y + box_h))
        painter.drawLine(int(box_x), int(box_y + box_h), int(box_x), int(box_y + box_h - b_bracket))
        painter.drawLine(int(box_x + box_w), int(box_y + box_h), int(box_x + box_w - b_bracket), int(box_y + box_h))
        painter.drawLine(int(box_x + box_w), int(box_y + box_h), int(box_x + box_w), int(box_y + box_h - b_bracket))

        # Tag above bbox
        tag_text = f"TARGET: PERSON [{int(self.incident.confidence * 100)}%]"
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.fillRect(QRectF(box_x, box_y - 18, 140, 16), QColor(15, 22, 32, 220))
        painter.setPen(accent_qcol)
        painter.drawText(QRectF(box_x + 4, box_y - 18, 136, 16), Qt.AlignmentFlag.AlignVCenter, tag_text)

        # Center reticle
        reticle_pen = QPen(QColor(Theme.TEXT_SECONDARY), 1)
        painter.setPen(reticle_pen)
        cx = w / 2.0
        cy = h / 2.0
        r_size = 8
        painter.drawLine(int(cx - r_size), int(cy), int(cx + r_size), int(cy))
        painter.drawLine(int(cx), int(cy - r_size), int(cx), int(cy + r_size))

        # Telemetry HUD overlays
        hud_font = QFont("Consolas, Courier New, monospace", 8)
        painter.setFont(hud_font)
        painter.setPen(QColor(Theme.TEXT_SECONDARY))

        # Top HUD info
        cam_info = "PAYLOAD: EO/IR GIMBAL CAM-01   RES: 1280x720   FPS: 30"
        painter.drawText(QRectF(16, 14, w - 32, 14), Qt.AlignmentFlag.AlignLeft, cam_info)

        # Bottom HUD info
        img_id = self.incident.evidence_image or f"EV-{self.incident.incident_id}.jpg"
        time_str = self.incident.timestamp.strftime("%H:%M:%S.%f")[:12]
        hud_bottom_left = f"FRAME: {img_id}   TIME: {time_str}"
        painter.drawText(QRectF(16, h - 26, w - 32, 14), Qt.AlignmentFlag.AlignLeft, hud_bottom_left)

        if self.incident.location:
            hud_bottom_right = f"LOCAL SLAM: X={self.incident.location.x:.1f}m Y={self.incident.location.y:.1f}m Z={self.incident.location.z:.1f}m"
        else:
            hud_bottom_right = "LOCAL SLAM: UNAVAILABLE"
        painter.drawText(QRectF(16, h - 26, w - 32, 14), Qt.AlignmentFlag.AlignRight, hud_bottom_right)


class IncidentDetail(QFrame):
    """
    Detailed operational inspector panel for the currently selected incident.
    Displays incident metadata, robotics local/SLAM coordinates, evidence frame,
    and action triggers (View on Map, Generate Report).
    """
    view_on_map_requested = Signal(Incident)
    generate_report_requested = Signal(Incident)

    def __init__(self):
        super().__init__()
        self._current_incident: Optional[Incident] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            IncidentDetail {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        # 1. Empty state view
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        empty_icon = QLabel("☩")
        empty_icon.setStyleSheet(f"color: {Theme.BORDER}; font-size: 36px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("NO INCIDENT SELECTED")
        empty_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold; letter-spacing: 0.8px;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_subtitle = QLabel("SELECT AN INCIDENT TO VIEW DETAILS")
        empty_subtitle.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        empty_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_subtitle)

        self.main_layout.addWidget(self.empty_widget, 1)

        # 2. Content view (hidden until incident selected)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)

        # Top Bar: Category "INCIDENT" + ID
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        inc_cat_lbl = QLabel("INCIDENT")
        inc_cat_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        header_row.addWidget(inc_cat_lbl)

        self.id_lbl = QLabel("")
        self.id_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 18px; font-weight: bold; font-family: monospace;")
        header_row.addWidget(self.id_lbl)

        header_row.addStretch()

        self.status_badge = QLabel("")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.status_badge)

        self.content_layout.addLayout(header_row)

        # Divider
        self.content_layout.addWidget(self._create_divider())

        # Metadata Grid (TYPE, CONFIDENCE, TIMESTAMP, STATUS, MISSION)
        grid_frame = QFrame()
        grid_frame.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 4px;")
        grid = QGridLayout(grid_frame)
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        # Labels
        self.val_type = QLabel("")
        self.val_conf = QLabel("")
        self.val_time = QLabel("")
        self.val_status = QLabel("")
        self.val_mission = QLabel("")

        self._add_attribute_row(grid, 0, 0, "TYPE", self.val_type)
        self._add_attribute_row(grid, 0, 1, "CONFIDENCE", self.val_conf)
        self._add_attribute_row(grid, 1, 0, "TIMESTAMP", self.val_time)
        self._add_attribute_row(grid, 1, 1, "STATUS", self.val_status)
        self._add_attribute_row(grid, 2, 0, "MISSION", self.val_mission)

        self.content_layout.addWidget(grid_frame)

        # Location Section
        loc_box = QFrame()
        loc_box.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 2px;")
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.setContentsMargins(12, 10, 12, 10)
        loc_layout.setSpacing(6)

        loc_top = QHBoxLayout()
        loc_title = QLabel("LOCATION")
        loc_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        loc_top.addWidget(loc_title)
        loc_top.addStretch()

        self.frame_tag = QLabel("COORDINATE FRAME: --")
        self.frame_tag.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: 600; font-family: monospace;")
        loc_top.addWidget(self.frame_tag)
        loc_layout.addLayout(loc_top)

        # Coordinates line
        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(16)

        self.lbl_x = QLabel("X: --")
        self.lbl_y = QLabel("Y: --")
        self.lbl_z = QLabel("Z: --")
        self.lbl_range = QLabel("R: --")
        for lbl in (self.lbl_x, self.lbl_y, self.lbl_z, self.lbl_range):
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; font-family: monospace;")
            coords_layout.addWidget(lbl)
        coords_layout.addStretch()

        self.loc_note = QLabel("Derived from LiDAR + SLAM sensor fusion")
        self.loc_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-style: italic;")
        coords_layout.addWidget(self.loc_note)

        loc_layout.addLayout(coords_layout)
        self.content_layout.addWidget(loc_box)

        # Evidence Section
        ev_title_bar = QHBoxLayout()
        ev_title = QLabel("EVIDENCE")
        ev_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        ev_title_bar.addWidget(ev_title)

        ev_sub = QLabel("CAPTURED FRAME")
        ev_sub.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 11px; font-weight: 600;")
        ev_title_bar.addWidget(ev_sub)
        ev_title_bar.addStretch()

        self.lbl_ev_id = QLabel("IMAGE ID: --")
        self.lbl_ev_id.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-family: monospace;")
        ev_title_bar.addWidget(self.lbl_ev_id)

        self.lbl_ev_time = QLabel("TIME: --")
        self.lbl_ev_time.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-family: monospace;")
        ev_title_bar.addWidget(self.lbl_ev_time)

        self.content_layout.addLayout(ev_title_bar)

        # Tactical evidence viewport
        self.evidence_viewport = EvidenceFrameWidget()
        self.content_layout.addWidget(self.evidence_viewport, 1)

        # Feedback Notification Banner (for View on Map / Generate Report)
        self.action_banner = QFrame()
        self.action_banner.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 180, 216, 0.1);
                border: 1px solid rgba(0, 180, 216, 0.3);
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
        banner_layout = QHBoxLayout(self.action_banner)
        banner_layout.setContentsMargins(8, 6, 8, 6)
        self.banner_text = QLabel("")
        self.banner_text.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-family: monospace;")
        banner_layout.addWidget(self.banner_text)
        self.action_banner.hide()
        self.content_layout.addWidget(self.action_banner)

        # Action Buttons: VIEW ON MAP & GENERATE REPORT
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_map = QPushButton("VIEW ON MAP")
        self.btn_map.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_map.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 9px 18px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: #1A2434;
                border: 1px solid {Theme.ACCENT};
                color: {Theme.ACCENT};
            }}
        """)
        self.btn_map.clicked.connect(self._on_view_on_map_clicked)
        actions_layout.addWidget(self.btn_map)

        self.btn_report = QPushButton("GENERATE REPORT")
        self.btn_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_report.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 9px 18px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: #1A2434;
                border: 1px solid {Theme.STATUS_WARNING};
                color: {Theme.STATUS_WARNING};
            }}
        """)
        self.btn_report.clicked.connect(self._on_generate_report_clicked)
        actions_layout.addWidget(self.btn_report)

        actions_layout.addStretch()
        self.content_layout.addLayout(actions_layout)

        self.main_layout.addWidget(self.content_widget, 1)
        self.content_widget.hide()

    def _create_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        return div

    def _add_attribute_row(self, grid: QGridLayout, row: int, col: int, title: str, val_lbl: QLabel):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        val_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")

        vbox.addWidget(t_lbl)
        vbox.addWidget(val_lbl)
        grid.addWidget(container, row, col)

    def show_incident(self, incident: Optional[Incident]):
        """Populates the detail panel with incident information or shows empty state."""
        self._current_incident = incident
        self.action_banner.hide()

        if incident is None:
            self.content_widget.hide()
            self.empty_widget.show()
            return

        self.empty_widget.hide()
        self.content_widget.show()

        # Header ID
        self.id_lbl.setText(incident.incident_id)

        # Status badge
        st = incident.status.upper()
        if st == "CONFIRMED":
            st_color = Theme.STATUS_SUCCESS
            st_bg = "rgba(34, 197, 94, 0.15)"
            st_border = "rgba(34, 197, 94, 0.4)"
        elif st == "REVIEW":
            st_color = Theme.STATUS_WARNING
            st_bg = "rgba(245, 158, 11, 0.15)"
            st_border = "rgba(245, 158, 11, 0.4)"
        elif st == "NEW":
            st_color = Theme.ACCENT
            st_bg = "rgba(0, 180, 216, 0.15)"
            st_border = "rgba(0, 180, 216, 0.4)"
        else:
            st_color = Theme.TEXT_SECONDARY
            st_bg = "rgba(140, 152, 166, 0.15)"
            st_border = "rgba(140, 152, 166, 0.3)"

        self.status_badge.setText(f"● {st}")
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                color: {st_color};
                background-color: {st_bg};
                border: 1px solid {st_border};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)

        # Metadata Grid values
        self.val_type.setText(incident.type)
        self.val_conf.setText(f"{int(incident.confidence * 100)}%")
        self.val_time.setText(incident.timestamp.strftime("%H:%M:%S"))
        self.val_status.setText(incident.status)
        self.val_status.setStyleSheet(f"color: {st_color}; font-size: 12px; font-weight: bold;")
        self.val_mission.setText(incident.mission_id)

        # Location
        if incident.spatial_status == "UNAVAILABLE" or incident.location is None:
            self.lbl_x.setText("X: --")
            self.lbl_y.setText("Y: --")
            self.lbl_z.setText("Z: --")
            self.lbl_range.setText("R: --")
            self.frame_tag.setText("COORDINATE FRAME: UNAVAILABLE")
            self.loc_note.setText("Spatial localization failed or unavailable.")
        else:
            self.lbl_x.setText(f"X: {incident.location.x:.1f} m")
            self.lbl_y.setText(f"Y: {incident.location.y:.1f} m")
            self.lbl_z.setText(f"Z: {incident.location.z:.1f} m")
            rng = f"{incident.range:.1f}" if incident.range is not None else "--"
            self.lbl_range.setText(f"R: {rng} m")
            frame = (incident.position_frame or "UNKNOWN").upper()
            conf = f"{int(incident.spatial_confidence * 100)}%" if incident.spatial_confidence is not None else "N/A"
            self.frame_tag.setText(f"FRAME: {frame} | STATUS: {incident.spatial_status}")
            self.loc_note.setText(f"Confidence: {conf} | Source: {incident.source_sensor or 'LiDAR'}")

        # Evidence labels & viewport
        ev_id = incident.evidence_image or f"EV-{incident.incident_id}.jpg"
        self.lbl_ev_id.setText(f"IMAGE ID: {ev_id.replace('.jpg','')}")
        self.lbl_ev_time.setText(f"TIMESTAMP: {incident.timestamp.strftime('%H:%M:%S')}")
        self.evidence_viewport.set_incident(incident)

    def _on_view_on_map_clicked(self):
        if not self._current_incident:
            return
        inc = self._current_incident
        if inc.location:
            loc_str = f"(X: {inc.location.x:.1f}m, Y: {inc.location.y:.1f}m, Z: {inc.location.z:.1f}m) LOCAL / SLAM"
        else:
            loc_str = "(LOCATION UNAVAILABLE)"
        self.banner_text.setText(
            f"📍 [MAP QUEUED] Target {inc.incident_id} at {loc_str} queued for Mission Map view."
        )
        self.action_banner.show()
        self.view_on_map_requested.emit(inc)

    def _on_generate_report_clicked(self):
        if not self._current_incident:
            return
        inc = self._current_incident
        self.banner_text.setText(
            f"⚡ REPORT GENERATION | Context for {inc.incident_id} queued for RAG pipeline."
        )
        self.action_banner.show()
        self.generate_report_requested.emit(inc)
