from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from app.services.data_service import DataService
from app.ui.widgets.incidents_panels import (
    IncidentCountersPanel, IncidentListPanel, IncidentDetailPanel, IncidentFilterPanel
)

class IncidentsView(QWidget):
    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._setup_ui()
        self._start_updates()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        self.counters = IncidentCountersPanel()
        self.layout.addWidget(self.counters)
        
        main_h = QHBoxLayout()
        main_h.setSpacing(16)
        
        self.list_panel = IncidentListPanel()
        self.detail_panel = IncidentDetailPanel()
        
        main_h.addWidget(self.list_panel, 1) # ~40% width
        main_h.addWidget(self.detail_panel, 2) # ~60% width
        
        self.layout.addLayout(main_h, 1) # Expands
        
        self.filter_panel = IncidentFilterPanel()
        self.layout.addWidget(self.filter_panel)
        
        # Connections
        self.list_panel.incident_selected.connect(self.detail_panel.show_incident)
        self.filter_panel.filter_changed.connect(self.list_panel.apply_filter)
        
    def _start_updates(self):
        # Initial load (in a real app, this might poll slowly or subscribe to signals)
        self._fetch_and_update_data()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fetch_and_update_data)
        self.timer.start(5000) # Only refresh every 5 seconds to not interrupt user selection
        
    def _fetch_and_update_data(self):
        incidents = self.data_service.get_incidents()
        self.counters.update_counts(incidents)
        # Avoid redrawing the whole list if lengths match, to prevent selection reset (simple heuristic for mock UI)
        if len(self.list_panel.incidents) != len(incidents):
            self.list_panel.update_data(incidents)
        elif not self.list_panel.incidents:
            self.list_panel.update_data(incidents)
