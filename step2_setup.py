import os

base_dir = r"d:\robofest builds\python dashboard\aerosar_dashboard"

theme_content = """\
class Theme:
    # Colors
    BG_BASE = "#0B0F14"
    BG_SECONDARY = "#11161D"
    BG_PANEL = "#151B23"
    BORDER = "#252D38"
    
    TEXT_PRIMARY = "#E8EDF2"
    TEXT_SECONDARY = "#8C98A6"
    
    ACCENT = "#00B4D8" # Aerospace cyan/blue
    ACCENT_HOVER = "#0096B4"
    ACCENT_SELECTED = "#007790"
    
    STATUS_SUCCESS = "#22C55E"
    STATUS_WARNING = "#F59E0B"
    STATUS_CRITICAL = "#EF4444"
    
    # Typography
    FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif"
    
    @classmethod
    def get_global_stylesheet(cls) -> str:
        return f\"\"\"
        QMainWindow, QDialog, QWidget {{
            background-color: {cls.BG_BASE};
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        
        QLabel {{
            background-color: transparent;
        }}
        \"\"\"
"""

sidebar_content = """\
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme

class SidebarButton(QPushButton):
    def __init__(self, text: str, page_index: int):
        super().__init__(text)
        self.page_index = page_index
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style definition
        self.setStyleSheet(f\"\"\"
            QPushButton {{
                text-align: left;
                padding: 12px 16px;
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-left: 3px solid transparent;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.ACCENT};
                border-left: 3px solid {Theme.ACCENT};
            }}
        \"\"\")

class Sidebar(QWidget):
    page_selected = Signal(int, str) # Emits (page_index, page_name)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        
        # Enforce styling for the sidebar container
        self.setStyleSheet(f\"\"\"
            Sidebar {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        \"\"\")
        
        self.buttons = []
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Branding Header
        branding_container = QWidget()
        branding_layout = QVBoxLayout(branding_container)
        branding_layout.setContentsMargins(20, 24, 20, 24)
        branding_layout.setSpacing(4)
        
        title = QLabel("AEROSAR")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 20px; font-weight: bold; letter-spacing: 2px;")
        
        subtitle = QLabel("GROUND STATION")
        subtitle.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        
        branding_layout.addWidget(title)
        branding_layout.addWidget(subtitle)
        
        layout.addWidget(branding_container)
        
        # Navigation Items
        nav_items = [
            "Overview",
            "Live Feed",
            "Incidents",
            "Map",
            "Telemetry",
            "Reports",
            "Event Log",
            "Settings"
        ]
        
        for idx, name in enumerate(nav_items):
            btn = SidebarButton(name, idx)
            btn.clicked.connect(lambda checked, i=idx, n=name: self._on_button_clicked(i, n))
            self.buttons.append(btn)
            layout.addWidget(btn)
            
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer - System Status
        footer_container = QWidget()
        footer_container.setStyleSheet(f"border-top: 1px solid {Theme.BORDER}; background-color: transparent;")
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(20, 20, 20, 20)
        
        system_label = QLabel("SYSTEM")
        system_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        
        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)
        
        status_indicator = QLabel("● ONLINE")
        status_indicator.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 13px; font-weight: 600; border: none;")
        
        footer_layout.addWidget(system_label)
        footer_layout.addWidget(status_indicator)
        
        layout.addWidget(footer_container)
        
    def _on_button_clicked(self, page_index: int, page_name: str):
        self.set_active_page(page_index)
        self.page_selected.emit(page_index, page_name)
        
    def set_active_page(self, index: int):
        for btn in self.buttons:
            if btn.page_index == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
"""

header_content = """\
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
from app.ui.theme import Theme

class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)
        
        self.setStyleSheet(f\"\"\"
            Header {{
                background-color: {Theme.BG_BASE};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        \"\"\")
        
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
"""

main_window_content = """\
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from app.core.constants import WINDOW_WIDTH, WINDOW_HEIGHT
from app.ui.theme import Theme

from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.header import Header

# Import views
from app.ui.views.overview_view import OverviewView
from app.ui.views.live_feed_view import LiveFeedView
from app.ui.views.incidents_view import IncidentsView
from app.ui.views.map_view import MapView
from app.ui.views.telemetry_view import TelemetryView
from app.ui.views.reports_view import ReportsView
from app.ui.views.event_log_view import EventLogView
from app.ui.views.settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("STALLION AEROSAR \u2014 Ground Station")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Apply global stylesheet
        self.setStyleSheet(Theme.get_global_stylesheet())
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout (Horizontal: Sidebar + Right Content Area)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)
        
        # 2. Right Content Area (Vertical: Header + StackedWidget)
        self.right_area = QWidget()
        self.right_layout = QVBoxLayout(self.right_area)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        # Header
        self.header = Header()
        self.right_layout.addWidget(self.header)
        
        # Stacked Widget (Page content)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: {Theme.BG_BASE}; border: none;")
        
        self._setup_views()
        self.right_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.right_area)
        
        # Connect signals
        self.sidebar.page_selected.connect(self._on_page_changed)
        
        # Set initial page
        self.sidebar.set_active_page(0)
        self._on_page_changed(0, "Overview")
        
    def _setup_views(self):
        # Instantiate views and add to stacked widget
        # Must match the order in Sidebar
        self.views = [
            OverviewView(),
            LiveFeedView(),
            IncidentsView(),
            MapView(),
            TelemetryView(),
            ReportsView(),
            EventLogView(),
            SettingsView()
        ]
        
        for view in self.views:
            self.stacked_widget.addWidget(view)
            
    def _on_page_changed(self, index: int, page_name: str):
        # Update stacked widget
        self.stacked_widget.setCurrentIndex(index)
        
        # Update header
        self.header.set_page_title(page_name)
"""

views_to_create = {
    "overview_view.py": ("Overview", "Mission overview and system status."),
    "live_feed_view.py": ("Live Feed", "Live camera and AI perception."),
    "incidents_view.py": ("Incidents", "Detected incidents and evidence."),
    "map_view.py": ("Map", "Mission map and spatial information."),
    "telemetry_view.py": ("Telemetry", "Drone and system telemetry."),
    "reports_view.py": ("Reports", "RAG and AI-generated incident reports."),
    "event_log_view.py": ("Event Log", "Mission and system events."),
    "settings_view.py": ("Settings", "Ground station configuration.")
}

view_template = """\
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.ui.theme import Theme

class {class_name}(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("{title}")
        title.setStyleSheet(f"color: {{Theme.TEXT_PRIMARY}}; font-size: 24px; font-weight: bold; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("{desc}")
        desc.setStyleSheet(f"color: {{Theme.TEXT_SECONDARY}}; font-size: 14px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(desc)
"""

import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Write theme.py
write_file(os.path.join(base_dir, "app/ui/theme.py"), theme_content)

# Write sidebar.py
write_file(os.path.join(base_dir, "app/ui/widgets/sidebar.py"), sidebar_content)

# Write header.py
write_file(os.path.join(base_dir, "app/ui/widgets/header.py"), header_content)

# Write main_window.py
write_file(os.path.join(base_dir, "app/ui/main_window.py"), main_window_content)

# Write views
for filename, (title, desc) in views_to_create.items():
    class_name = "".join([word.capitalize() for word in title.split()]) + "View"
    content = view_template.format(class_name=class_name, title=title.upper(), desc=desc)
    write_file(os.path.join(base_dir, "app/ui/views", filename), content)

print("Step 2 scaffolding complete.")
