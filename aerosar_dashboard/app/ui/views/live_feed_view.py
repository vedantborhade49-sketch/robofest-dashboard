from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, QTimer, QThread
from app.services.data_service import DataService
from app.ui.widgets.live_feed_panels import (
    CameraPanel, AIPerceptionPanel, DetectionListPanel, CameraStatusBar
)
from app.perception.qt_worker import PerceptionWorker
from app.perception.camera import WebcamSource
from app.ui.responsive import ScreenSize


class LiveFeedView(QWidget):
    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self.current_state = None
        self._setup_ui()
        self._start_live_updates()
        self._start_perception_worker()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        # Left Side (Camera + Status Bar)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(12)

        self.camera_panel = CameraPanel()
        self.camera_status = CameraStatusBar()

        self.left_layout.addWidget(self.camera_panel, 1)
        self.left_layout.addWidget(self.camera_status)

        # Right Side (AI Panel + Detections)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(16)

        self.ai_panel = AIPerceptionPanel()
        self.detections_panel = DetectionListPanel()

        self.right_layout.addWidget(self.ai_panel)
        self.right_layout.addWidget(self.detections_panel, 1)

        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        
        # Default proportions
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 3)

        self.main_layout.addWidget(self.splitter)

    def set_responsive_state(self, state: ScreenSize):
        if self.current_state == state:
            return
        self.current_state = state
        
        if state in (ScreenSize.COMPACT, ScreenSize.MINIMUM):
            self.splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
            self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])

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
        # configure default camera source and YOLO model from settings
        from app.services.settings_service import SettingsService
        from app.perception.detector import YOLODetector
        settings = SettingsService().get_settings()
        
        cam_index = getattr(settings, "perception_camera_index", 0)
        host = getattr(settings, "camera_network_host", "127.0.0.1")
        port = getattr(settings, "camera_network_port", 5000)
        if type(self.data_service._provider).__name__ == "MockDataProvider":
            # For tests to avoid cv2.VideoCapture failures
            from tests.mocks.mock_camera import MockCameraSource
            source = MockCameraSource()
        else:
            from app.perception.camera import TCPVideoProvider, WebcamSource
            if getattr(settings, "camera_source", "") == "Network Camera":
                reconnect_delay = getattr(settings, "camera_reconnect_delay", 2.0)
                frame_timeout = getattr(settings, "camera_frame_timeout", 2.0)
                source = TCPVideoProvider(host=host, port=port, reconnect_delay=reconnect_delay, frame_timeout=frame_timeout)
            else:
                source = WebcamSource(int(cam_index))
        
        model_name = getattr(settings, "detection_model", "person_detector")
        model_path = f"{model_name}.pt" if model_name != "person_detector" else "yolov8n.pt"
        conf_thresh = getattr(settings, "confidence_threshold", 0.5)
        
        detector = YOLODetector(model_path=model_path, confidence_threshold=conf_thresh, target_classes=["person"])
        
        from app.perception.perception_service import PerceptionService
        service = PerceptionService(source=source, detector=detector, confidence_threshold=conf_thresh)
        self._perception_worker = PerceptionWorker(service=service)
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

