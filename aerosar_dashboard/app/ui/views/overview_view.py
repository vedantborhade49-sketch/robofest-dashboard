from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from app.ui.theme import Theme
from app.services.data_service import DataService

from app.ui.widgets.overview_panels import (
    MissionStatusPanel, DroneStatusPanel, SystemStatusPanel,
    CameraPlaceholderPanel, MapPlaceholderPanel,
    IncidentsPanel, SystemHealthPanel, EventLogPanel
)

class OverviewView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize the DataService
        self.data_service = DataService()
        
        self._setup_ui()
        self._start_live_updates()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        # 1. Top Status Row
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        self.mission_panel = MissionStatusPanel()
        self.drone_panel = DroneStatusPanel()
        self.system_panel = SystemStatusPanel()
        
        top_row.addWidget(self.mission_panel, 1)
        top_row.addWidget(self.drone_panel, 1)
        top_row.addWidget(self.system_panel, 1)
        
        self.layout.addLayout(top_row)
        
        # 2. Middle Row (Camera & Map)
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)
        
        self.camera_panel = CameraPlaceholderPanel()
        self.map_panel = MapPlaceholderPanel()
        
        mid_row.addWidget(self.camera_panel, 1)
        mid_row.addWidget(self.map_panel, 1)
        
        self.layout.addLayout(mid_row, 1)
        
        # 3. Bottom Row (Incidents, Health, Events)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        
        self.incidents_panel = IncidentsPanel()
        self.health_panel = SystemHealthPanel()
        self.events_panel = EventLogPanel()
        
        bottom_row.addWidget(self.incidents_panel, 1)
        bottom_row.addWidget(self.health_panel, 1)
        bottom_row.addWidget(self.events_panel, 1)
        
        self.layout.addLayout(bottom_row)
        
    def _start_live_updates(self):
        # Initial population from central state
        self._fetch_and_update_data()

        # Connect to centralized reactive data signals
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
