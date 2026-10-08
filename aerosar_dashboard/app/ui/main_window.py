from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from app.core.constants import WINDOW_WIDTH, WINDOW_HEIGHT
from app.ui.theme import Theme

from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.header import Header
from app.ui.responsive import ScreenSize, get_screen_size

# Import views
from app.ui.views.overview_view import OverviewView
from app.ui.views.live_feed_view import LiveFeedView
from app.ui.views.incidents_view import IncidentsView
from app.ui.views.reports_view import ReportsView
from app.ui.views.event_log_view import EventLogView
from app.ui.views.settings_view import SettingsView
from app.models.incident import Incident

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("STALLION AEROSAR — Ground Station")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.current_screen_size = None
        
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
        
        import os
        from app.services.data_service import DataService
        
        from app.data.api_provider import APIDataProvider
        provider = APIDataProvider()
            
        self.data_service = DataService(provider)
        self.data_service.realtime_status_updated.connect(self.header.set_realtime_status)
        
        # Cross-view navigation connections
        self.reports_view.navigate_to_incidents.connect(self._on_navigate_to_incidents)
        self.incidents_view.navigate_to_reports.connect(self._on_navigate_to_reports)
        self.event_log_view.navigate_to_incidents.connect(self._on_navigate_to_incidents)

        # Start backend threads
        self._start_background_workers()

        # Set initial page
        self.sidebar.set_active_page(0)
        self._on_page_changed(0, "Overview")

    def _start_background_workers(self):
        from app.core.state_manager import StateManager
        settings = StateManager.instance().get_settings()
        
        if settings.mavlink_enabled:
            from app.telemetry.worker import TelemetryWorker
            self.telemetry_worker = TelemetryWorker(settings)
            self.telemetry_worker.start()
        else:
            self.telemetry_worker = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_size = get_screen_size(self.width())
        if new_size != self.current_screen_size:
            self.current_screen_size = new_size
            self._apply_responsive_state(new_size)

    def _apply_responsive_state(self, state: ScreenSize):
        self.sidebar.set_responsive_state(state)
        self.header.set_responsive_state(state)
        for view in self.views:
            if hasattr(view, "set_responsive_state"):
                view.set_responsive_state(state)

    def closeEvent(self, event):
        # Ensure workers are cleaned up on exit
        if hasattr(self, "telemetry_worker") and self.telemetry_worker:
            self.telemetry_worker.stop()
        try:
            if getattr(self, "live_feed_view", None) is not None:
                self.live_feed_view.shutdown_perception()
        except Exception:
            pass
        super().closeEvent(event)
        
    def _setup_views(self):
        # Instantiate views and keep references
        self.overview_view = OverviewView()
        self.live_feed_view = LiveFeedView()
        self.incidents_view = IncidentsView()
        self.reports_view = ReportsView()
        self.event_log_view = EventLogView()
        self.settings_view = SettingsView()

        # Must match the order in Sidebar
        self.views = [
            self.overview_view,
            self.live_feed_view,
            self.incidents_view,
            self.reports_view,
            self.event_log_view,
            self.settings_view
        ]
        
        for view in self.views:
            view.setMinimumSize(0, 0)
            self.stacked_widget.addWidget(view)
            
        # Connect perception worker to overview panels
        if hasattr(self.live_feed_view, "_perception_worker"):
            try:
                self.live_feed_view._perception_worker.frame_ready.connect(self.overview_view.camera_panel.update_frame)
                self.live_feed_view._perception_worker.detections_ready.connect(self.overview_view.camera_panel.update_detections)
            except Exception as e:
                pass
            
    def _on_page_changed(self, index: int, page_name: str):
        # Update stacked widget
        self.stacked_widget.setCurrentIndex(index)
        
        # Update header
        self.header.set_page_title(page_name)

    def _on_navigate_to_incidents(self, incident_id: str):
        """Cross-page action: Opens selected incident in Incidents View."""
        self.sidebar.set_active_page(2)
        self._on_page_changed(2, "Incidents")
        self.incidents_view.select_incident_by_id(incident_id)

    def _on_navigate_to_reports(self, incident_id: str):
        """Cross-page action: Opens selected incident's report in Reports View."""
        self.sidebar.set_active_page(3)
        self._on_page_changed(3, "Reports")
        self.reports_view.select_report_by_incident_id(incident_id)

