from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.ui.responsive import ScreenSize

from app.ui.widgets.overview_panels import (
    MissionStatusPanel, DroneStatusPanel, SystemStatusPanel,
    CameraPlaceholderPanel, MapPlaceholderPanel,
    IncidentsPanel, SystemHealthPanel, EventLogPanel
)

class OverviewView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.data_service = DataService()
        self.current_state = None
        self._setup_ui()
        self._start_live_updates()
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(Theme.LG, Theme.LG, Theme.LG, Theme.LG)
        self.content_layout.setSpacing(Theme.MD)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        
        # Instantiate Panels
        self.mission_panel = MissionStatusPanel()
        self.drone_panel = DroneStatusPanel()
        self.system_panel = SystemStatusPanel()
        self.camera_panel = CameraPlaceholderPanel()
        self.map_panel = MapPlaceholderPanel()
        self.incidents_panel = IncidentsPanel()
        self.health_panel = SystemHealthPanel()
        self.events_panel = EventLogPanel()
        
        self.panels = [
            self.mission_panel, self.drone_panel, self.system_panel,
            self.camera_panel, self.map_panel,
            self.incidents_panel, self.health_panel, self.events_panel
        ]
        
        # Grid layout for dynamic reflow
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(Theme.MD)
        self.content_layout.addLayout(self.grid_layout)
        self.content_layout.addStretch(1)
        
        # Default layout (LARGE)
        self._apply_large_layout()
        
    def _clear_grid(self):
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
                
    def _apply_large_layout(self):
        self._clear_grid()
        self.grid_layout.addWidget(self.mission_panel, 0, 0)
        self.grid_layout.addWidget(self.drone_panel, 0, 1)
        self.grid_layout.addWidget(self.system_panel, 0, 2)
        
        self.grid_layout.addWidget(self.camera_panel, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.map_panel, 1, 2)
        
        self.grid_layout.addWidget(self.incidents_panel, 2, 0)
        self.grid_layout.addWidget(self.health_panel, 2, 1)
        self.grid_layout.addWidget(self.events_panel, 2, 2)
        
    def _apply_compact_layout(self):
        self._clear_grid()
        self.grid_layout.addWidget(self.mission_panel, 0, 0)
        self.grid_layout.addWidget(self.drone_panel, 0, 1)
        
        self.grid_layout.addWidget(self.system_panel, 1, 0, 1, 2)
        
        self.grid_layout.addWidget(self.camera_panel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.map_panel, 3, 0, 1, 2)
        
        self.grid_layout.addWidget(self.incidents_panel, 4, 0, 1, 2)
        self.grid_layout.addWidget(self.health_panel, 5, 0, 1, 2)
        self.grid_layout.addWidget(self.events_panel, 6, 0, 1, 2)

    def _apply_minimum_layout(self):
        self._clear_grid()
        row = 0
        for panel in self.panels:
            self.grid_layout.addWidget(panel, row, 0)
            row += 1

    def set_responsive_state(self, state: ScreenSize):
        if self.current_state == state:
            return
        self.current_state = state
        
        for panel in self.panels:
            if hasattr(panel, "set_responsive_state"):
                panel.set_responsive_state(state)
                
        if state == ScreenSize.MINIMUM:
            self._apply_minimum_layout()
        elif state == ScreenSize.COMPACT:
            self._apply_compact_layout()
        else:
            self._apply_large_layout()
            
        # Re-add widgets to the visual hierarchy
        for panel in self.panels:
            panel.show()

    def _start_live_updates(self):
        self._fetch_and_update_data()
        self.data_service.mission_updated.connect(self.mission_panel.update_data)
        self.data_service.drone_updated.connect(self._on_drone_updated)
        self.data_service.system_updated.connect(self._on_system_updated)
        self.data_service.camera_updated.connect(self.camera_panel.update_data)
        self.data_service.incidents_updated.connect(self.incidents_panel.update_data)
        self.data_service.events_updated.connect(self.events_panel.update_data)

    def _on_drone_updated(self, drone_data):
        self.drone_panel.update_data(drone_data)
        self.map_panel.update_data(drone_data)

    def _on_system_updated(self, sys_health):
        cam_data = self.data_service.get_camera_data()
        ai_data = self.data_service.get_ai_data()
        self.system_panel.update_data(sys_health, cam_data, ai_data)
        self.health_panel.update_data(sys_health)

    def _fetch_and_update_data(self):
        mission_data = self.data_service.get_mission_data()
        drone_data = self.data_service.get_drone_data()
        sys_health = self.data_service.get_system_health()
        cam_data = self.data_service.get_camera_data()
        ai_data = self.data_service.get_ai_data()
        incidents = self.data_service.get_incidents()
        events = self.data_service.get_events()

        if mission_data: self.mission_panel.update_data(mission_data)
        if drone_data: self._on_drone_updated(drone_data)
        if sys_health: self._on_system_updated(sys_health)
        if cam_data: self.camera_panel.update_data(cam_data)
        if incidents is not None: self.incidents_panel.update_data(incidents)
        if events is not None: self.events_panel.update_data(events)
