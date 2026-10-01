from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
from app.ui.theme import Theme
from app.ui.responsive import ScreenSize

class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)
        
        self.setStyleSheet(f"""
            Header {{
                background-color: {Theme.BACKGROUND};
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
        self.mission_label = QLabel("Mission: SAR-001")
        self.mission_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.mission_label)
        
        layout.addStretch(1)
        
        # Right: Drone Status
        self.drone_status = QLabel("DRONE: READY")
        self.drone_status.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold; background-color: {Theme.SURFACE_ELEVATED}; padding: 4px 8px; border-radius: 4px; border: 1px solid {Theme.BORDER};")
        layout.addWidget(self.drone_status)
        
        # Right: Connection Status
        self.connection_status = QLabel("REAL-TIME: CONNECTING...")
        self.connection_status.setStyleSheet(f"color: {Theme.WARNING}; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.connection_status)
        
        # Vertical Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setStyleSheet(f"border-left: 1px solid {Theme.BORDER};")
        layout.addWidget(self.separator)
        
        # Right: Time
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px; font-family: monospace;")
        layout.addWidget(self.time_label)
        
    def set_page_title(self, title: str):
        self.page_title.setText(f"AEROSAR / {title.upper()}")
        
    def set_realtime_status(self, status: str):
        self.current_status = status
        self._update_status_display()
        
    def _update_status_display(self):
        status = getattr(self, "current_status", "CONNECTING")
        if status == "CONNECTED":
            self.connection_status.setText("REAL-TIME: CONNECTED" if not getattr(self, "_compact", False) else "CONNECTED")
            self.connection_status.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 12px; font-weight: bold;")
        elif status == "DISCONNECTED":
            self.connection_status.setText("REAL-TIME: DISCONNECTED" if not getattr(self, "_compact", False) else "DISCONNECTED")
            self.connection_status.setStyleSheet(f"color: {Theme.DANGER}; font-size: 12px; font-weight: bold;")
        elif status == "MOCK":
            self.connection_status.setText("REAL-TIME: MOCK MODE" if not getattr(self, "_compact", False) else "SIMULATION")
            self.connection_status.setStyleSheet(f"color: {Theme.INFO}; font-size: 12px; font-weight: bold;")
        
    def _start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        
    def _update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_label.setText(current_time)

    def set_responsive_state(self, state: ScreenSize):
        if state == ScreenSize.MINIMUM:
            self._compact = True
            self.mission_label.hide()
            self.drone_status.hide()
            self.separator.hide()
            self.time_label.hide()
        elif state == ScreenSize.COMPACT:
            self._compact = True
            self.mission_label.hide()
            self.drone_status.show()
            self.separator.show()
            self.time_label.show()
        else:
            self._compact = False
            self.mission_label.show()
            self.drone_status.show()
            self.separator.show()
            self.time_label.show()
        self._update_status_display()
