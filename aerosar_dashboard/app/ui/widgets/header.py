from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
from app.ui.theme import Theme

class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)
        
        self.setStyleSheet(f"""
            Header {{
                background-color: {Theme.BG_BASE};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        
        self._setup_ui()
        self._start_clock()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)
        
        # Left: Breadcrumb / Page Title
        self.page_title = QLabel("AEROSAR / OVERVIEW")
        self.page_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(self.page_title)
        
        layout.addStretch(1)
        
        # Center/Left: Mission
        mission_label = QLabel("Mission: SAR-001")
        mission_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; font-weight: 500;")
        layout.addWidget(mission_label)
        
        layout.addStretch(1)
        
        # Right: Drone Status
        drone_status = QLabel("DRONE: READY")
        drone_status.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold; background-color: {Theme.BG_PANEL}; padding: 4px 8px; border-radius: 4px; border: 1px solid {Theme.BORDER};")
        layout.addWidget(drone_status)
        
        # Right: Connection Status
        connection_status = QLabel("● CONNECTED")
        connection_status.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 12px; font-weight: bold;")
        layout.addWidget(connection_status)
        
        # Vertical Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet(f"border-left: 1px solid {Theme.BORDER};")
        layout.addWidget(separator)
        
        # Right: Time
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px; font-family: monospace;")
        layout.addWidget(self.time_label)
        
    def set_page_title(self, title: str):
        self.page_title.setText(f"AEROSAR / {title.upper()}")
        
    def _start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        
    def _update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_label.setText(current_time)
