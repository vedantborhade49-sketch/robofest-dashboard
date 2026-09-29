from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QThread
from app.services.data_service import DataService
from app.ui.widgets.live_feed_panels import (
    CameraPanel, AIPerceptionPanel, DetectionListPanel, CameraStatusBar
)
from app.perception.qt_worker import PerceptionWorker
from app.perception.camera import OpenCVVideoSource


class LiveFeedView(QWidget):
    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self._setup_ui()
        self._start_live_updates()
        self._start_perception_worker()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Left Side (Camera + Status Bar) - Takes ~70% width
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        self.camera_panel = CameraPanel()
        self.camera_status = CameraStatusBar()

        left_layout.addWidget(self.camera_panel, 1)  # Camera expands
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
        right_layout.addWidget(self.detections_panel, 1)  # List expands

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        self.layout.addWidget(right_widget, 3)

    def _start_live_updates(self):
        # Initial display from central state
        self._fetch_and_update_data()

        # Connect to centralized signals driven by the CentralUpdateLoop
        self.data_service.detections_updated.connect(self._on_detections_updated)
        self.data_service.camera_updated.connect(self.camera_status.update_data)
        self.data_service.ai_updated.connect(self.ai_panel.update_data)

    def _start_perception_worker(self):
        # Create perception worker + thread
        self._perception_thread = QThread(self)
        # configure default camera source
        from app.services.settings_service import SettingsService
        settings = SettingsService().get_settings()
        cam_index = getattr(settings, "perception_camera_index", 0)
        source = OpenCVVideoSource(cam_index)
        self._perception_worker = PerceptionWorker()
        self._perception_worker.service.source = source
        self._perception_worker.moveToThread(self._perception_thread)

        # connect lifecycle
        self._perception_thread.started.connect(self._perception_worker.start)
        self._perception_worker.stopped.connect(self._perception_thread.quit)

        # connect signals
        self._perception_worker.detections_ready.connect(self._on_detections_updated)
        self._perception_worker.frame_ready.connect(self.camera_panel.update_frame)
        self._perception_worker.status_updated.connect(self.ai_panel.update_data)

        # start thread and timer to poll
        self._perception_thread.start()
        # Attach worker to DataService so detections/status propagate
        try:
            DataService().attach_perception_worker(self._perception_worker)
        except Exception:
            pass
        self._perception_timer = QTimer(self)
        self._perception_timer.timeout.connect(self._perception_worker.capture_and_process)
        self._perception_timer.start(50)  # ~20 FPS

    def shutdown_perception(self, wait_ms: int = 2000):
        # Stop timer
        try:
            if getattr(self, "_perception_timer", None) is not None:
                self._perception_timer.stop()
        except Exception:
            pass

        # Ask worker to stop and quit thread
        try:
            if getattr(self, "_perception_worker", None) is not None:
                self._perception_worker.stop()
        except Exception:
            pass

        try:
            if getattr(self, "_perception_thread", None) is not None:
                self._perception_thread.quit()
                self._perception_thread.wait(wait_ms)
        except Exception:
            pass

    def _on_detections_updated(self, detections):
        self.camera_panel.update_data(detections)
        self.detections_panel.update_data(detections)

    def _fetch_and_update_data(self):
        cam_data = self.data_service.get_camera_data()
        ai_data = self.data_service.get_ai_data()
        detections = self.data_service.get_detections()

        if detections is not None:
            self._on_detections_updated(detections)
        if cam_data is not None:
            self.camera_status.update_data(cam_data)
        if ai_data is not None:
            self.ai_panel.update_data(ai_data)

