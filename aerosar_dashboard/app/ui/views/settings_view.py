import sys
import platform
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QScrollArea, QGridLayout, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from app.ui.theme import Theme
from app.models.settings import DashboardSettings
from app.services.settings_service import SettingsService
from app.services.data_service import DataService

class SettingsCategoryCard(QFrame):
    """Card container for a specific category of dashboard settings."""
    def __init__(self, title: str, subtitle: Optional[str] = None):
        super().__init__()
        self.setStyleSheet(f"""
            SettingsCategoryCard {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(12)

        # Header
        hdr_layout = QVBoxLayout()
        hdr_layout.setSpacing(2)

        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        hdr_layout.addWidget(t_lbl)

        if subtitle:
            s_lbl = QLabel(subtitle)
            s_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
            hdr_layout.addWidget(s_lbl)

        self.layout.addLayout(hdr_layout)

        # Subtle divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        self.layout.addWidget(div)

        # Form content layout
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.form_layout.setHorizontalSpacing(24)
        self.form_layout.setVerticalSpacing(10)
        self.layout.addLayout(self.form_layout)

    def add_row(self, label_text: str, widget: QWidget, tooltip: Optional[str] = None):
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
        if tooltip:
            lbl.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        self.form_layout.addRow(lbl, widget)


class SettingsView(QWidget):
    """
    Main operator-facing Settings and System Configuration view.
    Provides structured controls for ground station software configuration,
    display preferences, perception thresholds, camera resolution, mock communication,
    and read-only system telemetry info.
    """
    def __init__(self):
        super().__init__()
        self.settings_service = SettingsService()
        self.data_service = DataService()
        self._setup_ui()
        self._load_settings_into_form(self.settings_service.get_settings())

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(12)

        # 1. Top Header Bar: Title, Subtitle, and Global Action Buttons
        top_bar = QHBoxLayout()
        top_bar.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("SYSTEM CONFIGURATION")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 20px; font-weight: bold; letter-spacing: 1.5px;")
        title_box.addWidget(title)

        subtitle = QLabel("Non-flight-critical ground station software parameters, UI preferences, and perception thresholds.")
        subtitle.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        title_box.addWidget(subtitle)

        top_bar.addLayout(title_box)
        top_bar.addStretch()

        # Action Buttons
        self.btn_reset = QPushButton("↺ RESET DEFAULTS")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        top_bar.addWidget(self.btn_reset)

        self.btn_apply = QPushButton("✔ APPLY SETTINGS")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #0B0F14;
                border: 1px solid {Theme.ACCENT};
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        top_bar.addWidget(self.btn_apply)

        root_layout.addLayout(top_bar)

        # 2. Notification / Validation Banner (hidden initially)
        self.banner = QFrame()
        self.banner.setVisible(False)
        self.banner_layout = QHBoxLayout(self.banner)
        self.banner_layout.setContentsMargins(14, 8, 14, 8)

        self.banner_label = QLabel("")
        self.banner_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.banner_layout.addWidget(self.banner_label)

        self.banner_timer = QTimer(self)
        self.banner_timer.setSingleShot(True)
        self.banner_timer.timeout.connect(lambda: self.banner.setVisible(False))

        root_layout.addWidget(self.banner)

        # 3. Main Scroll Area for configuration categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {Theme.BG_BASE};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER};
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.TEXT_SECONDARY};
            }}
        """)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 4, 10, 20)
        c_layout.setSpacing(16)

        # Two-column grid layout for cards
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Card 1: GENERAL
        card_general = self._build_general_card()
        grid.addWidget(card_general, 0, 0)

        # Card 2: DISPLAY
        card_display = self._build_display_card()
        grid.addWidget(card_display, 0, 1)

        # Card 3: AI / PERCEPTION
        card_ai = self._build_ai_card()
        grid.addWidget(card_ai, 1, 0)

        # Card 4: CAMERA
        card_camera = self._build_camera_card()
        grid.addWidget(card_camera, 1, 1)

        # Card 5: MISSION MAP
        card_map = self._build_map_card()
        grid.addWidget(card_map, 2, 0)

        # Card 6: BACKEND / DATA CONNECTION
        card_backend = self._build_backend_card()
        grid.addWidget(card_backend, 2, 1)

        # Card 7: COMMUNICATION
        card_comm = self._build_comm_card()
        grid.addWidget(card_comm, 3, 0)

        # Card 8: LOGGING
        card_logging = self._build_logging_card()
        grid.addWidget(card_logging, 3, 1)

        c_layout.addLayout(grid)

        # Card 9: SYSTEM INFORMATION (Full Width)
        card_sysinfo = self._build_sysinfo_card()
        c_layout.addWidget(card_sysinfo)

        scroll.setWidget(container)
        root_layout.addWidget(scroll, 1)

    # -------------------------------------------------------------
    # CARD BUILDERS
    # -------------------------------------------------------------
    def _build_general_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("General", "Ground station identification and display rhythm.")

        self.input_gs_name = QLineEdit()
        self._style_input(self.input_gs_name)
        card.add_row("Ground Station Name", self.input_gs_name, "Operator title for this ground control terminal")

        self.input_mission_id = QLineEdit()
        self._style_input(self.input_mission_id)
        card.add_row("Mission ID", self.input_mission_id, "Active search and rescue operation identifier")

        self.combo_refresh = QComboBox()
        self.combo_refresh.addItems(["200 ms (Fast)", "500 ms (Standard)", "1000 ms (Conserve)", "2000 ms (Low Bandwidth)"])
        self._style_combo(self.combo_refresh)
        card.add_row("Refresh Interval", self.combo_refresh, "Data refresh rate for telemetry and UI status")

        self.combo_time_format = QComboBox()
        self.combo_time_format.addItems(["24-hour (UTC)", "24-hour (Local)", "12-hour (Local AM/PM)"])
        self._style_combo(self.combo_time_format)
        card.add_row("Time Display Format", self.combo_time_format, "Timestamp formatting across all dashboard panels")

        return card

    def _build_display_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Display", "Visual indicators, overlays, and UI element toggles.")

        self.chk_dark_theme = QCheckBox("Enabled (Fixed Tactical Dark)")
        self.chk_dark_theme.setChecked(True)
        self.chk_dark_theme.setEnabled(False)
        self._style_chk(self.chk_dark_theme)
        card.add_row("Theme Mode", self.chk_dark_theme, "Mission-control dark theme is locked for tactical visibility")

        self.chk_boxes = QCheckBox("Show AI Bounding Boxes")
        self._style_chk(self.chk_boxes)
        card.add_row("Detection Overlays", self.chk_boxes, "Render live perception boxes on optical video stream")

        self.chk_trajectory = QCheckBox("Show Drone Flight Trail")
        self._style_chk(self.chk_trajectory)
        card.add_row("Trajectory History", self.chk_trajectory, "Display historical breadcrumb trail on Mission Map")

        self.chk_grid = QCheckBox("Show Coordinates Grid")
        self._style_chk(self.chk_grid)
        card.add_row("Tactical Grid", self.chk_grid, "Display metric coordinate grid on map and viewfinders")

        self.chk_compact_telemetry = QCheckBox("Compact Telemetry View")
        self._style_chk(self.chk_compact_telemetry)
        card.add_row("Telemetry Density", self.chk_compact_telemetry, "Reduce padding on sensor telemetry panels")

        self.chk_notifications = QCheckBox("Show System Notifications")
        self._style_chk(self.chk_notifications)
        card.add_row("Operator Alerts", self.chk_notifications, "Display toast banners when mission incidents are created")

        return card

    def _build_ai_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("AI / Perception", "Simulated edge detection model and inference thresholds.")

        self.combo_model = QComboBox()
        self.combo_model.addItems(["person_detector", "sar_yolov8_nano", "thermal_human_v1", "debris_detector"])
        self._style_combo(self.combo_model)
        card.add_row("Perception Model", self.combo_model, "Primary object detection model for autonomous search")

        self.spin_confidence = QDoubleSpinBox()
        self.spin_confidence.setRange(0.00, 1.00)
        self.spin_confidence.setSingleStep(0.05)
        self.spin_confidence.setDecimals(2)
        self._style_spin(self.spin_confidence)
        card.add_row("Confidence Threshold", self.spin_confidence, "Minimum probability required to flag an incident (0.0 - 1.0)")

        self.spin_max_detections = QSpinBox()
        self.spin_max_detections.setRange(1, 100)
        self._style_spin(self.spin_max_detections)
        card.add_row("Maximum Detections", self.spin_max_detections, "Max targets tracked simultaneously per frame")

        self.chk_detection_labels = QCheckBox("Show Class & Confidence Tag")
        self._style_chk(self.chk_detection_labels)
        card.add_row("Detection Labels", self.chk_detection_labels, "Render text annotations above bounding boxes")

        return card

    def _build_camera_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Camera Configuration", "Video payload feeds, resolution, and viewport settings.")

        self.combo_cam_source = QComboBox()
        self.combo_cam_source.addItems(["Mock Camera", "EO/IR Gimbal CAM-01", "Thermal IR FLIR-02", "Synthetic Test Pattern"])
        self._style_combo(self.combo_cam_source)
        card.add_row("Camera Source", self.combo_cam_source, "Primary payload optical sensor")

        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(["1280 × 720", "1920 × 1080", "640 × 480"])
        self._style_combo(self.combo_resolution)
        card.add_row("Resolution", self.combo_resolution, "Target stream resolution for video display")

        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 FPS", "60 FPS", "15 FPS"])
        self._style_combo(self.combo_fps)
        card.add_row("Frame Rate", self.combo_fps, "Capture frame rate")

        self.chk_mirror = QCheckBox("Mirror Preview")
        self._style_chk(self.chk_mirror)
        card.add_row("Orientation", self.chk_mirror, "Flip horizontal axis for front-facing camera")

        self.chk_cam_overlay = QCheckBox("Render Reticle & HUD")
        self._style_chk(self.chk_cam_overlay)
        card.add_row("HUD Overlay", self.chk_cam_overlay, "Display crosshair reticle and coordinate markings")

        return card

    def _build_map_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Mission Map", "2D search grid, boundary geometry, and vehicle indicators.")

        self.chk_map_grid = QCheckBox("Show Metric Grid")
        self._style_chk(self.chk_map_grid)
        card.add_row("Grid Overlay", self.chk_map_grid, "Display 5m grid intervals on map canvas")

        self.chk_map_drone = QCheckBox("Show Drone & Heading Arrow")
        self._style_chk(self.chk_map_drone)
        card.add_row("Vehicle Marker", self.chk_map_drone, "Render aircraft location with directional vector")

        self.chk_map_traj = QCheckBox("Show Flight Trajectory Trail")
        self._style_chk(self.chk_map_traj)
        card.add_row("Trajectory Trail", self.chk_map_traj, "Draw continuous path of visited coordinates")

        self.chk_map_inc = QCheckBox("Show Incidents on Map")
        self._style_chk(self.chk_map_inc)
        card.add_row("Incident Flags", self.chk_map_inc, "Render color-coded hazard markers at detection sites")

        self.chk_map_boundary = QCheckBox("Show Search Boundary")
        self._style_chk(self.chk_map_boundary)
        card.add_row("Search Boundary", self.chk_map_boundary, "Highlight perimeter box of assigned operational area")

        self.chk_map_explored = QCheckBox("Show Explored Coverage Area")
        self._style_chk(self.chk_map_explored)
        card.add_row("Area Coverage", self.chk_map_explored, "Shade sectors swept by drone sensors")

        return card

    def _build_backend_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Backend / Data Link", "Future FastAPI integration and runtime connectivity.")

        self.combo_backend_mode = QComboBox()
        self.combo_backend_mode.addItems(["MOCK", "LOCAL_DEV", "REMOTE_SERVER"])
        self._style_combo(self.combo_backend_mode)
        card.add_row("Data Mode", self.combo_backend_mode, "Operational data source architecture")

        self.input_backend_url = QLineEdit()
        self._style_input(self.input_backend_url)
        card.add_row("Backend URL", self.input_backend_url, "REST / WebSocket endpoint for future server connection")

        # Connection status badge
        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px;")
        val = QLabel("DISCONNECTED / SIMULATED")
        val.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; font-family: monospace;")
        status_box.addWidget(dot)
        status_box.addWidget(val)
        status_box.addStretch()

        stat_widget = QWidget()
        stat_widget.setLayout(status_box)
        card.add_row("Link Status", stat_widget, "Current live socket status to backend service")

        self.chk_reconnect = QCheckBox("Auto Reconnect")
        self._style_chk(self.chk_reconnect)
        card.add_row("Link Management", self.chk_reconnect, "Automatically retry backend connection upon dropout")

        return card

    def _build_comm_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Communication", "Simulated telemetry downlink and transport parameters.")

        self.combo_comm_mode = QComboBox()
        self.combo_comm_mode.addItems(["SIMULATED", "DIRECT_UDP", "SERIAL_RADIO"])
        self._style_combo(self.combo_comm_mode)
        card.add_row("Communication Mode", self.combo_comm_mode, "Downlink protocol simulation or interface")

        self.combo_transport = QComboBox()
        self.combo_transport.addItems(["LOCAL", "UDP 14550", "COM3 57600"])
        self._style_combo(self.combo_transport)
        card.add_row("Transport Bus", self.combo_transport, "Hardware port or socket configuration")

        self.spin_comm_interval = QSpinBox()
        self.spin_comm_interval.setRange(50, 5000)
        self.spin_comm_interval.setSingleStep(50)
        self.spin_comm_interval.setSuffix(" ms")
        self._style_spin(self.spin_comm_interval)
        card.add_row("Packet Interval", self.spin_comm_interval, "Transmission frequency of simulated telemetry")

        self.spin_comm_timeout = QSpinBox()
        self.spin_comm_timeout.setRange(500, 30000)
        self.spin_comm_timeout.setSingleStep(500)
        self.spin_comm_timeout.setSuffix(" ms")
        self._style_spin(self.spin_comm_timeout)
        card.add_row("Timeout Threshold", self.spin_comm_timeout, "Heartbeat duration before link warning triggers")

        return card

    def _build_logging_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("Event Logging", "Ground station event logging and retention policies.")

        self.chk_event_logging = QCheckBox("Enable Event Logging")
        self._style_chk(self.chk_event_logging)
        card.add_row("Activity Logger", self.chk_event_logging, "Record chronological mission events to timeline")

        self.combo_log_level = QComboBox()
        self.combo_log_level.addItems(["INFO", "WARNING", "ERROR", "DEBUG"])
        self._style_combo(self.combo_log_level)
        card.add_row("Minimum Log Level", self.combo_log_level, "Filter threshold for capturing subsystem logs")

        self.spin_max_events = QSpinBox()
        self.spin_max_events.setRange(100, 10000)
        self.spin_max_events.setSingleStep(250)
        self._style_spin(self.spin_max_events)
        card.add_row("Max Event Retention", self.spin_max_events, "Maximum entries retained in memory timeline")

        self.chk_console = QCheckBox("Mirror to Console")
        self._style_chk(self.chk_console)
        card.add_row("Terminal Output", self.chk_console, "Echo event logs to operator stdout terminal")

        return card

    def _build_sysinfo_card(self) -> SettingsCategoryCard:
        card = SettingsCategoryCard("System Information", "Read-only application runtime and diagnostics metadata.")

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        py_ver = f"{platform.python_version()} ({platform.architecture()[0]})"

        info_items = [
            ("APPLICATION", "STALLION AEROSAR Ground Station"),
            ("VERSION", "0.1.0"),
            ("ENVIRONMENT", "Development"),
            ("DATA PROVIDER", "MockDataProvider"),
            ("GUI FRAMEWORK", "PySide6 (Qt 6.x)"),
            ("PYTHON RUNTIME", py_ver),
            ("PERCEPTION STATUS", "SIMULATED (No real YOLO)"),
            ("BACKEND STATUS", "NOT CONNECTED (Mock Mode)"),
            ("FLIGHT SAFETY", "NON-CRITICAL / READ-ONLY"),
            ("PLATFORM OS", f"{platform.system()} {platform.release()}")
        ]

        for idx, (label, val) in enumerate(info_items):
            row = idx // 2
            col = (idx % 2) * 2

            lbl_title = QLabel(label)
            lbl_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")

            lbl_val = QLabel(val)
            lbl_val.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold; font-family: monospace;")

            grid.addWidget(lbl_title, row, col)
            grid.addWidget(lbl_val, row, col + 1)

        card.layout.addLayout(grid)
        return card

    # -------------------------------------------------------------
    # STYLING HELPERS
    # -------------------------------------------------------------
    def _style_input(self, input_widget: QLineEdit):
        input_widget.setFixedHeight(28)
        input_widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                font-family: monospace;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)

    def _style_combo(self, combo: QComboBox):
        combo.setFixedHeight(28)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 500;
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

    def _style_spin(self, spin):
        spin.setFixedHeight(28)
        spin.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                font-family: monospace;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)

    def _style_chk(self, chk: QCheckBox):
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        chk.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {Theme.BORDER};
                background: {Theme.BG_SECONDARY};
            }}
            QCheckBox::indicator:checked {{
                background: {Theme.ACCENT};
                border-color: {Theme.ACCENT};
            }}
            QCheckBox::indicator:disabled {{
                background: {Theme.BORDER};
            }}
        """)

    # -------------------------------------------------------------
    # FORM BINDINGS & ACTIONS
    # -------------------------------------------------------------
    def _load_settings_into_form(self, s: DashboardSettings):
        """Populates all UI input widgets from a DashboardSettings instance."""
        # General
        self.input_gs_name.setText(s.ground_station_name)
        self.input_mission_id.setText(s.mission_id)
        # Match refresh combo
        ref_text = f"{s.refresh_interval_ms} ms"
        for i in range(self.combo_refresh.count()):
            if ref_text in self.combo_refresh.itemText(i):
                self.combo_refresh.setCurrentIndex(i)
                break
        # Match time format
        for i in range(self.combo_time_format.count()):
            if s.time_format in self.combo_time_format.itemText(i):
                self.combo_time_format.setCurrentIndex(i)
                break

        # Display
        self.chk_boxes.setChecked(s.show_detection_boxes)
        self.chk_trajectory.setChecked(s.show_trajectory)
        self.chk_grid.setChecked(s.show_grid)
        self.chk_compact_telemetry.setChecked(s.compact_telemetry)
        self.chk_notifications.setChecked(s.show_system_notifications)

        # AI
        idx = self.combo_model.findText(s.detection_model)
        if idx >= 0:
            self.combo_model.setCurrentIndex(idx)
        self.spin_confidence.setValue(s.confidence_threshold)
        self.spin_max_detections.setValue(s.max_detections)
        self.chk_detection_labels.setChecked(s.show_detection_labels)

        # Camera
        idx = self.combo_cam_source.findText(s.camera_source)
        if idx >= 0:
            self.combo_cam_source.setCurrentIndex(idx)
        idx = self.combo_resolution.findText(s.camera_resolution)
        if idx >= 0:
            self.combo_resolution.setCurrentIndex(idx)
        fps_text = f"{s.camera_fps} FPS"
        for i in range(self.combo_fps.count()):
            if fps_text in self.combo_fps.itemText(i):
                self.combo_fps.setCurrentIndex(i)
                break
        self.chk_mirror.setChecked(s.mirror_preview)
        self.chk_cam_overlay.setChecked(s.detection_overlay)

        # Map
        self.chk_map_grid.setChecked(s.map_show_grid)
        self.chk_map_drone.setChecked(s.map_show_drone)
        self.chk_map_traj.setChecked(s.map_show_trajectory)
        self.chk_map_inc.setChecked(s.map_show_incidents)
        self.chk_map_boundary.setChecked(s.map_show_search_boundary)
        self.chk_map_explored.setChecked(s.map_show_explored_area)

        # Backend
        idx = self.combo_backend_mode.findText(s.backend_mode)
        if idx >= 0:
            self.combo_backend_mode.setCurrentIndex(idx)
        self.input_backend_url.setText(s.backend_url)
        self.chk_reconnect.setChecked(s.auto_reconnect)

        # Communication
        idx = self.combo_comm_mode.findText(s.communication_mode)
        if idx >= 0:
            self.combo_comm_mode.setCurrentIndex(idx)
        idx = self.combo_transport.findText(s.transport)
        if idx >= 0:
            self.combo_transport.setCurrentIndex(idx)
        self.spin_comm_interval.setValue(s.update_interval_ms)
        self.spin_comm_timeout.setValue(s.connection_timeout_ms)

        # Logging
        self.chk_event_logging.setChecked(s.event_logging_enabled)
        idx = self.combo_log_level.findText(s.log_level)
        if idx >= 0:
            self.combo_log_level.setCurrentIndex(idx)
        self.spin_max_events.setValue(s.max_stored_events)
        self.chk_console.setChecked(s.console_logging)

    def _collect_settings_from_form(self) -> DashboardSettings:
        """Parses current widget values into a DashboardSettings instance."""
        # Parse refresh interval
        ref_str = self.combo_refresh.currentText().split()[0]
        try:
            ref_ms = int(ref_str)
        except ValueError:
            ref_ms = 500

        # Parse FPS
        fps_str = self.combo_fps.currentText().split()[0]
        try:
            fps_val = int(fps_str)
        except ValueError:
            fps_val = 30

        # Time format key
        t_fmt = "24-hour" if "24-hour" in self.combo_time_format.currentText() else "12-hour"

        return DashboardSettings(
            ground_station_name=self.input_gs_name.text().strip() or "AEROSAR Ground Station",
            mission_id=self.input_mission_id.text().strip() or "SAR-001",
            refresh_interval_ms=ref_ms,
            time_format=t_fmt,

            dark_theme=True,
            show_detection_boxes=self.chk_boxes.isChecked(),
            show_trajectory=self.chk_trajectory.isChecked(),
            show_grid=self.chk_grid.isChecked(),
            compact_telemetry=self.chk_compact_telemetry.isChecked(),
            show_system_notifications=self.chk_notifications.isChecked(),

            detection_model=self.combo_model.currentText(),
            confidence_threshold=round(self.spin_confidence.value(), 2),
            max_detections=self.spin_max_detections.value(),
            show_detection_labels=self.chk_detection_labels.isChecked(),

            camera_source=self.combo_cam_source.currentText(),
            camera_resolution=self.combo_resolution.currentText(),
            camera_fps=fps_val,
            mirror_preview=self.chk_mirror.isChecked(),
            detection_overlay=self.chk_cam_overlay.isChecked(),

            map_show_grid=self.chk_map_grid.isChecked(),
            map_show_drone=self.chk_map_drone.isChecked(),
            map_show_trajectory=self.chk_map_traj.isChecked(),
            map_show_incidents=self.chk_map_inc.isChecked(),
            map_show_search_boundary=self.chk_map_boundary.isChecked(),
            map_show_explored_area=self.chk_map_explored.isChecked(),

            backend_mode=self.combo_backend_mode.currentText(),
            backend_url=self.input_backend_url.text().strip(),
            auto_reconnect=self.chk_reconnect.isChecked(),

            communication_mode=self.combo_comm_mode.currentText(),
            transport=self.combo_transport.currentText(),
            update_interval_ms=self.spin_comm_interval.value(),
            connection_timeout_ms=self.spin_comm_timeout.value(),

            event_logging_enabled=self.chk_event_logging.isChecked(),
            log_level=self.combo_log_level.currentText(),
            max_stored_events=self.spin_max_events.value(),
            console_logging=self.chk_console.isChecked()
        )

    def _on_apply_clicked(self):
        """Validates form, commits settings to service, logs success event, and displays feedback."""
        try:
            settings = self._collect_settings_from_form()
            success, msg = self.settings_service.update_settings(settings)
            if success:
                self._show_banner(msg, is_error=False)
                # Log event in Event Log timeline
                self.data_service.log_event(
                    message="Dashboard settings updated by operator",
                    severity="SUCCESS",
                    source="SYSTEM",
                    level="SUCCESS",
                    details={
                        "refresh_ms": settings.refresh_interval_ms,
                        "model": settings.detection_model,
                        "confidence": settings.confidence_threshold,
                        "camera": settings.camera_source
                    }
                )
            else:
                self._show_banner(msg, is_error=True)
        except Exception as e:
            self._show_banner(f"Validation Error: {str(e)}", is_error=True)

    def _on_reset_clicked(self):
        """Restores all inputs to system defaults and updates the service."""
        defaults = self.settings_service.reset_to_defaults()
        self._load_settings_into_form(defaults)
        self._show_banner("Dashboard configuration restored to system defaults.", is_error=False)

    def _show_banner(self, message: str, is_error: bool = False):
        if is_error:
            self.banner.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(239, 68, 68, 0.15);
                    border: 1px solid {Theme.STATUS_CRITICAL};
                    border-radius: 4px;
                }}
            """)
            self.banner_label.setStyleSheet(f"color: {Theme.STATUS_CRITICAL}; font-size: 12px; font-weight: bold;")
            self.banner_label.setText(f"⚠  {message}")
        else:
            self.banner.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(34, 197, 94, 0.15);
                    border: 1px solid {Theme.STATUS_SUCCESS};
                    border-radius: 4px;
                }}
            """)
            self.banner_label.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 12px; font-weight: bold;")
            self.banner_label.setText(f"✔  {message}")

        self.banner.setVisible(True)
        self.banner_timer.start(5000) # Hide after 5 seconds
