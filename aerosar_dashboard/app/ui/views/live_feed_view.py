from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from app.services.data_service import DataService
from app.ui.widgets.live_feed_panels import (
    CameraPanel, AIPerceptionPanel, DetectionListPanel, CameraStatusBar
)

class LiveFeedView(QWidget):
    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._setup_ui()
        self._start_live_updates()
        
    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        # Left Side (Camera + Status Bar) - Takes ~70% width
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        
        self.camera_panel = CameraPanel()
        self.camera_status = CameraStatusBar()
        
        left_layout.addWidget(self.camera_panel, 1) # Camera expands
        left_layout.addWidget(self.camera_status)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        self.layout.addWidget(left_widget, 7)
        
        # Right Side (AI Panel + Detections) - Takes ~30% width
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)
        
        self.ai_panel = AIPerceptionPanel()
        self.detections_panel = DetectionListPanel()
        
        right_layout.addWidget(self.ai_panel)
        right_layout.addWidget(self.detections_panel, 1) # List expands
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        self.layout.addWidget(right_widget, 3)
        
    def _start_live_updates(self):
        # We update the Live Feed at 500ms for smoother visual bbox updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fetch_and_update_data)
        self.timer.start(500)
        self._fetch_and_update_data()
        
    def _fetch_and_update_data(self):
        cam_data = self.data_service.get_camera_data()
        ai_data = self.data_service.get_ai_data()
        detections = self.data_service.get_detections()
        
        self.camera_panel.update_data(detections)
        self.camera_status.update_data(cam_data)
        self.ai_panel.update_data(ai_data)
        self.detections_panel.update_data(detections)
