from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QSizePolicy
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QImage, QPixmap
import cv2
import numpy as np
from app.ui.theme import Theme
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.detection import Detection
from typing import List
from .overview_panels import BasePanel

class CameraPanel(QFrame):
    """
    Camera viewport.
    In the future, this class will receive a QPixmap/QImage from an OpenCV thread
    and draw it inside paintEvent, followed by drawing the bounding boxes over it.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: #030507; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        
        self.detections: List[Detection] = []
        self._pixmap: QPixmap | None = None
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_main = QLabel("CAMERA FEED\n[ WAITING FOR STREAM ]")
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

    def update_frame(self, frame):
        try:
            if frame is None:
                return
            
            # frame is already RGB from FrameProcessor, we just need to create QImage
            # ensure contiguous array
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
                
            if frame.ndim == 3 and frame.shape[2] == 3:
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
            else:
                # grayscale or unexpected format
                h, w = frame.shape[:2]
                bytes_per_line = w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8).copy()

            self._pixmap = QPixmap.fromImage(qimg)
            # hide placeholder labels when showing real frames
            self.lbl_main.hide()
            self.lbl_cam.hide()
            self.update()
        except Exception:
            return
        
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # draw camera frame if available
        if self._pixmap is not None:
            painter.drawPixmap(0, 0, w, h, self._pixmap)

        if not self.detections:
            painter.end()
            return

        for det in self.detections:
            bbox = det.bbox
            if getattr(bbox, "x1", None) is not None and getattr(bbox, "x2", None) is not None and det.image_width and det.image_height:
                bx = (bbox.x1 / det.image_width) * w
                by = (bbox.y1 / det.image_height) * h
                bw = ((bbox.x2 - bbox.x1) / det.image_width) * w
                bh = ((bbox.y2 - bbox.y1) / det.image_height) * h
            else:
                bw = bbox.width * w
                bh = bbox.height * h
                bx = (bbox.x * w) - (bw / 2)
                by = (bbox.y * h) - (bh / 2)
            
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
        self.recv_fps_lbl = self._create_value_label("0 FPS")
        self.drops_lbl = self._create_value_label("0")
        self.conn_state_lbl = self._create_value_label("DISCONNECTED", Theme.STATUS_WARNING)
        self.det_count_lbl = self._create_value_label("0")
        self.device_lbl = self._create_value_label("-")
        
        grid.addWidget(self._create_header_label("MODEL"), 0, 0)
        grid.addWidget(self.model_lbl, 1, 0)
        grid.addWidget(self._create_header_label("STATUS"), 2, 0)
        grid.addWidget(self.status_lbl, 3, 0)
        
        grid.addWidget(self._create_header_label("CONN STATE"), 0, 1)
        grid.addWidget(self.conn_state_lbl, 1, 1)
        grid.addWidget(self._create_header_label("RECV FPS"), 2, 1)
        grid.addWidget(self.recv_fps_lbl, 3, 1)
        
        grid.addWidget(self._create_header_label("INFERENCE FPS"), 4, 0)
        grid.addWidget(self.fps_lbl, 5, 0)
        grid.addWidget(self._create_header_label("DETECTIONS"), 6, 0)
        grid.addWidget(self.det_count_lbl, 7, 0)
        
        grid.addWidget(self._create_header_label("DROPS"), 4, 1)
        grid.addWidget(self.drops_lbl, 5, 1)
        grid.addWidget(self._create_header_label("DEVICE"), 6, 1)
        grid.addWidget(self.device_lbl, 7, 1)
        
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
        if not ai:
            return
        # support both AIStatus and PerceptionStatus shapes
        model_name = getattr(ai, "model_name", "-")
        running = getattr(ai, "running", None)
        model_loaded = getattr(ai, "model_loaded", None)
        # status string: prefer explicit 'status' if present, else derive
        status_text = getattr(ai, "status", None)
        if status_text is None:
            if running is True:
                status_text = "RUNNING"
            elif model_loaded:
                status_text = "LOADED"
            else:
                status_text = "STOPPED"

        # fps: prefer 'inference_fps' or 'fps', else compute from inference_time_ms
        fps = getattr(ai, "inference_fps", None)
        if fps is None:
            fps = getattr(ai, "fps", None)
        if fps is None:
            inf_ms = getattr(ai, "inference_time_ms", 0.0)
            fps = (1000.0 / inf_ms) if inf_ms and inf_ms > 0 else 0.0

        det_count = getattr(ai, "detections_count", None)
        if det_count is None:
            det_count = getattr(ai, "detection_count", 0)

        device = getattr(ai, "device", "-")
        recv_fps = getattr(ai, "received_fps", 0.0)
        drops = getattr(ai, "dropped_frames", 0)
        conn_state = getattr(ai, "connection_state", "UNKNOWN")

        self.model_lbl.setText(model_name)
        self.status_lbl.setText(status_text)
        try:
            self.fps_lbl.setText(f"{float(fps):.1f} FPS")
        except Exception:
            self.fps_lbl.setText("0.0 FPS")
            
        try:
            self.recv_fps_lbl.setText(f"{float(recv_fps):.1f} FPS")
        except Exception:
            self.recv_fps_lbl.setText("0.0 FPS")
            
        self.drops_lbl.setText(str(drops))
        self.conn_state_lbl.setText(conn_state)
        
        if conn_state == "CONNECTED":
            self.conn_state_lbl.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 14px; font-weight: bold; border: none;")
        elif conn_state == "DISCONNECTED" or conn_state == "ERROR":
            self.conn_state_lbl.setStyleSheet(f"color: {Theme.STATUS_ERROR}; font-size: 14px; font-weight: bold; border: none;")
        else:
            self.conn_state_lbl.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 14px; font-weight: bold; border: none;")

        self.det_count_lbl.setText(str(det_count))
        self.device_lbl.setText(device)


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
