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
        
        self.setWindowTitle("STALLION AEROSAR — Ground Station")
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
