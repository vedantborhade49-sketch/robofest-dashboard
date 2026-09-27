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
    """
    Mock camera viewport.
    In the future, this class will receive a QPixmap/QImage from an OpenCV thread
    and draw it inside paintEvent, followed by drawing the bounding boxes over it.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: #030507; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(640, 480)
        
        self.detections: List[Detection] = []
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_main = QLabel("CAMERA FEED\n[ MOCK VIDEO STREAM ]")
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
