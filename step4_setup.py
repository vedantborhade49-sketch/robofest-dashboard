import os

base_dir = r"d:\robofest builds\python dashboard\aerosar_dashboard"
files = {}

files["app/models/detection.py"] = """\
from pydantic import BaseModel
from datetime import datetime

class BoundingBox(BaseModel):
    x: float # Center X, Normalized 0.0 to 1.0
    y: float # Center Y, Normalized 0.0 to 1.0
    width: float # Normalized 0.0 to 1.0
    height: float # Normalized 0.0 to 1.0

class Detection(BaseModel):
    detection_id: str
    class_name: str
    confidence: float
    bbox: BoundingBox
    timestamp: datetime
"""

files["app/models/camera.py"] = """\
from pydantic import BaseModel

class Camera(BaseModel):
    connected: bool
    fps: float
    latency: float
    frame_count: int = 0
    dropped_frames: int = 0
    resolution: str = "1280x720"
"""

files["app/models/ai.py"] = """\
from pydantic import BaseModel

class AIStatus(BaseModel):
    status: str
    model_name: str
    inference_fps: float
    detections_count: int
    device: str = "MOCK / CPU"
"""

files["app/data/provider.py"] = """\
from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Incident
from app.models.event import Event
from app.models.detection import Detection

class DataProvider(ABC):
    \"\"\"Abstract base class for all data providers.\"\"\"
    @abstractmethod
    def get_mission(self) -> Optional[Mission]: pass
    @abstractmethod
    def get_drone(self) -> Optional[Drone]: pass
    @abstractmethod
    def get_camera(self) -> Optional[Camera]: pass
    @abstractmethod
    def get_ai_status(self) -> Optional[AIStatus]: pass
    @abstractmethod
    def get_telemetry(self) -> Optional[Telemetry]: pass
    @abstractmethod
    def get_system_health(self) -> Optional[SystemHealth]: pass
    @abstractmethod
    def get_incidents(self) -> List[Incident]: pass
    @abstractmethod
    def get_events(self) -> List[Event]: pass
    @abstractmethod
    def get_detections(self) -> List[Detection]: pass
"""

files["app/data/mock_provider.py"] = """\
import random
from datetime import datetime, timedelta
from typing import List
from .provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Incident, Location
from app.models.event import Event
from app.models.detection import Detection, BoundingBox

class MockDataProvider(DataProvider):
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        # Telemetry State
        self._drone_altitude = 14.8
        self._drone_speed = 3.2
        self._drone_battery = 82.0
        
        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        
        # Camera State
        self._frame_count = 12482
        self._dropped_frames = 0
        
        # Detection State (Mock moving bounding boxes)
        self._det_x = 0.4
        self._det_y = 0.5
        
        # Static mock lists
        self._incidents = [
            Incident(
                incident_id="INC-001", type="PERSON", confidence=0.94,
                timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                status="DETECTED", location=Location(x=10.5, y=20.1, z=14.8)
            ),
            Incident(
                incident_id="INC-002", type="PERSON", confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                status="REVIEW", location=Location(x=12.2, y=19.8, z=14.5)
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected", severity="WARNING")
        ]
        
    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001",
            mission_status="ACTIVE",
            elapsed_time=elapsed,
            search_progress=42.0,
            connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        self._drone_altitude += random.uniform(-0.2, 0.2)
        self._drone_speed += random.uniform(-0.1, 0.1)
        self._drone_speed = max(0.0, self._drone_speed)
        return Drone(
            drone_id="AEROSAR-01", status="AIRBORNE", battery=self._drone_battery,
            altitude=round(self._drone_altitude, 1), speed=round(self._drone_speed, 1),
            heading=127.0, signal_strength=98.0
        )

    def get_camera(self) -> Camera:
        self._frame_count += int(random.uniform(28, 30))
        if random.random() < 0.05:
            self._dropped_frames += 1
            
        return Camera(
            connected=True,
            fps=random.uniform(27.0, 30.0),
            latency=random.uniform(35.0, 55.0),
            frame_count=self._frame_count,
            dropped_frames=self._dropped_frames,
            resolution="1280x720"
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="READY",
            model_name="YOLO-PERSON-V1",
            inference_fps=random.uniform(27.0, 29.0),
            detections_count=1,
            device="MOCK / CPU"
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=round(self._drone_altitude, 1), speed=round(self._drone_speed, 1),
            heading=127.0, battery=self._drone_battery, signal=98.0,
            position=Location(x=10.5, y=20.1, z=self._drone_altitude)
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=32.0, memory_usage=41.0, temperature=48.0,
            communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_events(self) -> List[Event]:
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        
    def get_detections(self) -> List[Detection]:
        # Move the box slowly
        self._det_x += random.uniform(-0.01, 0.01)
        self._det_y += random.uniform(-0.01, 0.01)
        self._det_x = max(0.1, min(0.9, self._det_x))
        self._det_y = max(0.1, min(0.9, self._det_y))
        
        return [
            Detection(
                detection_id="DET-1029",
                class_name="PERSON",
                confidence=random.uniform(0.85, 0.98),
                bbox=BoundingBox(x=self._det_x, y=self._det_y, width=0.15, height=0.25),
                timestamp=datetime.now()
            )
        ]
"""

files["app/services/data_service.py"] = """\
from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider

class DataService:
    def __init__(self, provider: DataProvider = None):
        self._provider = provider or MockDataProvider()
        
    def get_mission_data(self): return self._provider.get_mission()
    def get_drone_data(self): return self._provider.get_drone()
    def get_telemetry_data(self): return self._provider.get_telemetry()
    def get_camera_data(self): return self._provider.get_camera()
    def get_ai_data(self): return self._provider.get_ai_status()
    def get_system_health(self): return self._provider.get_system_health()
    def get_incidents(self): return self._provider.get_incidents()
    def get_events(self): return self._provider.get_events()
    def get_detections(self): return self._provider.get_detections()
"""

files["app/ui/widgets/live_feed_panels.py"] = """\
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QSizePolicy
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from app.ui.theme import Theme
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.detection import Detection
from typing import List
from .overview_panels import BasePanel

class CameraPanel(QFrame):
    \"\"\"
    Mock camera viewport.
    In the future, this class will receive a QPixmap/QImage from an OpenCV thread
    and draw it inside paintEvent, followed by drawing the bounding boxes over it.
    \"\"\"
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: #030507; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(640, 480)
        
        self.detections: List[Detection] = []
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_main = QLabel("CAMERA FEED\\n[ MOCK VIDEO STREAM ]")
        self.lbl_main.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 20px; font-weight: bold; border: none;")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_main)
        
        self.lbl_cam = QLabel("AEROSAR-01 / CAM-01")
        self.lbl_cam.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 12px; border: none;")
        self.lbl_cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_cam)
        
    def update_data(self, detections: List[Detection]):
        self.detections = detections
        # Trigger a repaint to draw the new bounding boxes
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.detections:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        for det in self.detections:
            # bbox is normalized 0.0-1.0, representing center_x, center_y, w, h
            bw = det.bbox.width * w
            bh = det.bbox.height * h
            bx = (det.bbox.x * w) - (bw / 2)
            by = (det.bbox.y * h) - (bh / 2)
            
            rect = QRectF(bx, by, bw, bh)
            
            # Draw bounding box
            pen = QPen(QColor(Theme.STATUS_WARNING))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
            
            # Draw label background
            lbl_text = f"{det.class_name} {det.confidence*100:.0f}%"
            painter.setBrush(QColor(Theme.STATUS_WARNING))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(bx, by - 20, 100, 20))
            
            # Draw text
            painter.setPen(QColor(Theme.BG_BASE))
            painter.drawText(QRectF(bx + 4, by - 20, 96, 20), Qt.AlignmentFlag.AlignVCenter, lbl_text)
            
        painter.end()


class AIPerceptionPanel(BasePanel):
    def __init__(self):
        super().__init__("AI PERCEPTION")
        
        grid = QGridLayout()
        grid.setSpacing(16)
        self.layout.addLayout(grid)
        
        self.model_lbl = self._create_value_label("-")
        self.status_lbl = self._create_value_label("-", Theme.STATUS_SUCCESS)
        self.fps_lbl = self._create_value_label("0 FPS")
        self.det_count_lbl = self._create_value_label("0")
        self.device_lbl = self._create_value_label("-")
        
        grid.addWidget(self._create_header_label("MODEL"), 0, 0)
        grid.addWidget(self.model_lbl, 1, 0)
        grid.addWidget(self._create_header_label("STATUS"), 2, 0)
        grid.addWidget(self.status_lbl, 3, 0)
        grid.addWidget(self._create_header_label("INFERENCE FPS"), 4, 0)
        grid.addWidget(self.fps_lbl, 5, 0)
        grid.addWidget(self._create_header_label("DETECTIONS"), 6, 0)
        grid.addWidget(self.det_count_lbl, 7, 0)
        grid.addWidget(self._create_header_label("DEVICE"), 8, 0)
        grid.addWidget(self.device_lbl, 9, 0)
        
        self.layout.addStretch()
        
    def _create_header_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
        return lbl
        
    def _create_value_label(self, text, color=Theme.TEXT_PRIMARY):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; border: none;")
        return lbl

    def update_data(self, ai: AIStatus):
        if not ai: return
        self.model_lbl.setText(ai.model_name)
        self.status_lbl.setText(ai.status)
        self.fps_lbl.setText(f"{ai.inference_fps:.1f} FPS")
        self.det_count_lbl.setText(str(ai.detections_count))
        self.device_lbl.setText(ai.device)


class DetectionListPanel(BasePanel):
    def __init__(self):
        super().__init__("RECENT DETECTIONS")
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(8)
        self.layout.addLayout(self.rows_layout)
        self.layout.addStretch()
        
        self.seen_detections = []
        
    def update_data(self, detections: List[Detection]):
        for det in detections:
            # Prevent duplicates by checking ID in a real app, here we just append continuously to simulate streaming
            self.seen_detections.insert(0, det)
            
        self.seen_detections = self.seen_detections[:8]
        
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        for det in self.seen_detections:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            
            lbl_time = QLabel(det.timestamp.strftime("%H:%M:%S"))
            lbl_time.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-family: monospace; border: none;")
            
            lbl_class = QLabel(det.class_name)
            lbl_class.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold; border: none;")
            
            lbl_conf = QLabel(f"{det.confidence*100:.0f}%")
            lbl_conf.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 12px; font-weight: bold; border: none;")
            
            row.addWidget(lbl_time)
            row.addWidget(lbl_class)
            row.addStretch()
            row.addWidget(lbl_conf)
            
            w = QWidget()
            w.setLayout(row)
            w.setStyleSheet("border: none; background: transparent;")
            self.rows_layout.addWidget(w)


class CameraStatusBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        self.setFixedHeight(48)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 16, 0)
        
        self.status_lbl = self._create_value_pair("CAMERA STATUS", "-", Theme.STATUS_SUCCESS)
        self.fps_lbl = self._create_value_pair("FPS", "-")
        self.lat_lbl = self._create_value_pair("LATENCY", "-")
        self.frames_lbl = self._create_value_pair("FRAME COUNT", "-")
        self.drop_lbl = self._create_value_pair("DROPPED", "-")
        self.res_lbl = self._create_value_pair("RESOLUTION", "-")
        
    def _create_value_pair(self, header: str, val: str, val_color=Theme.TEXT_PRIMARY):
        layout = QHBoxLayout()
        h = QLabel(f"{header}:")
        h.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
        v = QLabel(val)
        v.setStyleSheet(f"color: {val_color}; font-size: 12px; font-weight: bold; border: none;")
        layout.addWidget(h)
        layout.addWidget(v)
        
        w = QWidget()
        w.setLayout(layout)
        w.setStyleSheet("border: none; background: transparent;")
        self.layout.addWidget(w)
        self.layout.addStretch()
        return v
        
    def update_data(self, cam: Camera):
        if not cam: return
        self.status_lbl.setText("READY" if cam.connected else "OFFLINE")
        self.fps_lbl.setText(f"{cam.fps:.1f}")
        self.lat_lbl.setText(f"{cam.latency:.0f} ms")
        self.frames_lbl.setText(str(cam.frame_count))
        self.drop_lbl.setText(str(cam.dropped_frames))
        self.res_lbl.setText(cam.resolution)
"""

files["app/ui/views/live_feed_view.py"] = """\
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
"""

import os
for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Step 4 scaffolding complete.")
