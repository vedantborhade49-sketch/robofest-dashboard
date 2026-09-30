from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt
from app.ui.theme import Theme
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.system import SystemHealth
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.incident import Incident
from app.models.event import Event
from typing import List

class BasePanel(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setStyleSheet(f"""
            BasePanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        self.layout.addWidget(self.title_label)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; max-height: 1px; border: none;")
        self.layout.addWidget(sep)

class MissionStatusPanel(BasePanel):
    def __init__(self):
        super().__init__("MISSION STATUS")
        grid = QGridLayout()
        grid.setSpacing(16)
        self.layout.addLayout(grid)
        
        self.mission_id = self._create_value_label("-")
        self.status = self._create_value_label("-", Theme.STATUS_SUCCESS)
        self.elapsed = self._create_value_label("00:00:00")
        self.progress = self._create_value_label("0%")
        
        grid.addWidget(self._create_header_label("MISSION"), 0, 0)
        grid.addWidget(self.mission_id, 1, 0)
        grid.addWidget(self._create_header_label("STATUS"), 0, 1)
        grid.addWidget(self.status, 1, 1)
        grid.addWidget(self._create_header_label("ELAPSED"), 0, 2)
        grid.addWidget(self.elapsed, 1, 2)
        grid.addWidget(self._create_header_label("SEARCH PROGRESS"), 0, 3)
        grid.addWidget(self.progress, 1, 3)
        
    def _create_header_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
        return lbl
        
    def _create_value_label(self, text, color=Theme.TEXT_PRIMARY):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; border: none;")
        return lbl

    def update_data(self, data: Mission):
        if not data: return
        self.mission_id.setText(data.mission_id)
        self.status.setText(data.mission_status)
        hours = int(data.elapsed_time // 3600)
        minutes = int((data.elapsed_time % 3600) // 60)
        seconds = int(data.elapsed_time % 60)
        self.elapsed.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.progress.setText(f"{data.search_progress}%")

class DroneStatusPanel(BasePanel):
    def __init__(self):
        super().__init__("DRONE STATUS")
        grid = QGridLayout()
        grid.setSpacing(16)
        self.layout.addLayout(grid)
        
        self.drone_id = self._create_value_label("-")
        self.mode = self._create_value_label("-", Theme.ACCENT)
        self.battery = self._create_value_label("0%")
        self.altitude = self._create_value_label("0.0 m")
        self.speed = self._create_value_label("0.0 m/s")
        self.link = self._create_value_label("-")
        
        grid.addWidget(self._create_header_label("DRONE"), 0, 0)
        grid.addWidget(self.drone_id, 1, 0)
        grid.addWidget(self._create_header_label("MODE/STATUS"), 0, 1)
        grid.addWidget(self.mode, 1, 1)
        grid.addWidget(self._create_header_label("BATTERY"), 0, 2)
        grid.addWidget(self.battery, 1, 2)
        grid.addWidget(self._create_header_label("ALTITUDE"), 0, 3)
        grid.addWidget(self.altitude, 1, 3)
        grid.addWidget(self._create_header_label("SPEED"), 0, 4)
        grid.addWidget(self.speed, 1, 4)
        grid.addWidget(self._create_header_label("LINK"), 0, 5)
        grid.addWidget(self.link, 1, 5)
        
    def _create_header_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
        return lbl
        
    def _create_value_label(self, text, color=Theme.TEXT_PRIMARY):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; border: none;")
        return lbl

    def update_data(self, data: Drone):
        if not data: return
        self.drone_id.setText(data.drone_id)
        self.mode.setText(data.status)
        self.battery.setText(f"{data.battery:.0f}%")
        self.altitude.setText(f"{data.altitude:.1f} m")
        self.speed.setText(f"{data.speed:.1f} m/s")
        
        link_str = "CONNECTED" if data.signal_strength > 0 else "LOST"
        link_col = Theme.STATUS_SUCCESS if data.signal_strength > 30 else Theme.STATUS_WARNING
        if data.signal_strength <= 0: link_col = Theme.STATUS_CRITICAL
        
        self.link.setText(link_str)
        self.link.setStyleSheet(f"color: {link_col}; font-size: 16px; font-weight: bold; border: none;")

class SystemStatusPanel(BasePanel):
    def __init__(self):
        super().__init__("SYSTEM STATUS")
        grid = QGridLayout()
        grid.setSpacing(16)
        self.layout.addLayout(grid)
        
        self.system = self._create_value_label("-", Theme.STATUS_SUCCESS)
        self.comm = self._create_value_label("-", Theme.STATUS_SUCCESS)
        self.camera = self._create_value_label("-", Theme.STATUS_SUCCESS)
        self.ai = self._create_value_label("-", Theme.STATUS_SUCCESS)
        
        grid.addWidget(self._create_header_label("SYSTEM"), 0, 0)
        grid.addWidget(self.system, 1, 0)
        grid.addWidget(self._create_header_label("COMMUNICATION"), 0, 1)
        grid.addWidget(self.comm, 1, 1)
        grid.addWidget(self._create_header_label("CAMERA"), 0, 2)
        grid.addWidget(self.camera, 1, 2)
        grid.addWidget(self._create_header_label("AI"), 0, 3)
        grid.addWidget(self.ai, 1, 3)
        
    def _create_header_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
        return lbl
        
    def _create_value_label(self, text, color=Theme.TEXT_PRIMARY):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; border: none;")
        return lbl

    def update_data(self, sys: SystemHealth, cam: Camera, ai: AIStatus):
        if sys:
            self.system.setText("ONLINE")
            self.comm.setText(sys.communication_status)
        if cam:
            self.camera.setText("READY" if cam.connected else "OFFLINE")
        if ai:
            self.ai.setText(ai.status)

class CameraPlaceholderPanel(BasePanel):
    def __init__(self):
        super().__init__("LIVE CAMERA FEED")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        feed_area = QFrame()
        feed_area.setStyleSheet(f"background-color: {Theme.BG_BASE}; border: 1px dashed {Theme.BORDER}; border-radius: 4px;")
        feed_layout = QVBoxLayout(feed_area)
        feed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl1 = QLabel("NO LIVE FEED")
        lbl1.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 18px; font-weight: bold; border: none;")
        lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl2 = QLabel("AWAITING CAMERA CONNECTION")
        lbl2.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; border: none;")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        feed_layout.addWidget(lbl1)
        feed_layout.addWidget(lbl2)
        
        self.layout.addWidget(feed_area, 1)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.cam_status = QLabel("CAMERA: READY")
        self.cam_fps = QLabel("FPS: --")
        self.cam_lat = QLabel("LATENCY: --")
        
        for lbl in (self.cam_status, self.cam_fps, self.cam_lat):
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; border: none;")
            stats_layout.addWidget(lbl)
        stats_layout.addStretch()
        
        self.layout.addLayout(stats_layout)
        
    def update_data(self, cam: Camera):
        if cam and cam.connected:
            self.cam_status.setText("CAMERA: READY")
            self.cam_status.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 11px; font-weight: bold; border: none;")
            self.cam_fps.setText(f"FPS: {cam.fps:.1f}")
            self.cam_lat.setText(f"LATENCY: {cam.latency:.0f}ms")

class MapPlaceholderPanel(BasePanel):
    def __init__(self):
        super().__init__("MISSION MAP / GPS-DENIED LOCAL MAP")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        map_area = QFrame()
        map_area.setStyleSheet(f"background-color: {Theme.BG_BASE}; border: 1px dashed {Theme.BORDER}; border-radius: 4px;")
        map_layout = QVBoxLayout(map_area)
        map_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel("[ SLAM MAP PLACEHOLDER ]")
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 16px; font-weight: bold; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.coord_lbl = QLabel("X: 0.0  Y: 0.0  Z: 0.0")
        self.coord_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 12px; font-family: monospace; border: none;")
        self.coord_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        map_layout.addWidget(lbl)
        map_layout.addWidget(self.coord_lbl)
        
        self.layout.addWidget(map_area, 1)

    def update_data(self, drone: Drone):
        if drone:
            self.coord_lbl.setText(f"X: 12.4  Y: 8.7  Z: {drone.altitude:.1f}")

class IncidentsPanel(BasePanel):
    def __init__(self):
        super().__init__("RECENT INCIDENTS")
        self.setMinimumHeight(200)
        
        hdr_layout = QHBoxLayout()
        for t in ["ID", "TYPE", "CONF", "TIME", "STATUS"]:
            lbl = QLabel(t)
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; border: none;")
            hdr_layout.addWidget(lbl)
        self.layout.addLayout(hdr_layout)
        
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(8)
        self.layout.addLayout(self.rows_layout)
        self.layout.addStretch()
        
    def update_data(self, incidents: List[Incident]):
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        for inc in incidents[:4]:
            row = QHBoxLayout()
            lbl_id = QLabel(inc.incident_id)
            lbl_type = QLabel(inc.type)
            lbl_conf = QLabel(f"{inc.confidence*100:.0f}%")
            lbl_time = QLabel(inc.timestamp.strftime("%H:%M:%S"))
            lbl_status = QLabel(inc.status)
            
            for lbl in (lbl_id, lbl_type, lbl_conf, lbl_time, lbl_status):
                lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; border: none;")
                row.addWidget(lbl)
            
            if inc.status == "DETECTED":
                lbl_status.setStyleSheet(f"color: {Theme.STATUS_WARNING}; font-size: 12px; font-weight: bold; border: none;")
            elif inc.status == "CONFIRMED":
                lbl_status.setStyleSheet(f"color: {Theme.STATUS_CRITICAL}; font-size: 12px; font-weight: bold; border: none;")
                
            row_widget = QWidget()
            row_widget.setLayout(row)
            row_widget.setStyleSheet("border: none; background: transparent;")
            self.rows_layout.addWidget(row_widget)

class SystemHealthPanel(BasePanel):
    def __init__(self):
        super().__init__("SYSTEM HEALTH")
        self.setMinimumHeight(200)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        self.layout.addLayout(grid)
        
        self.cpu_lbl = QLabel("CPU: 0%")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(6)
        
        self.mem_lbl = QLabel("MEMORY: 0%")
        self.mem_bar = QProgressBar()
        self.mem_bar.setTextVisible(False)
        self.mem_bar.setFixedHeight(6)
        
        self.temp_lbl = QLabel("TEMP: 0°C")
        
        grid.addWidget(self.cpu_lbl, 0, 0)
        grid.addWidget(self.cpu_bar, 0, 1)
        grid.addWidget(self.mem_lbl, 1, 0)
        grid.addWidget(self.mem_bar, 1, 1)
        grid.addWidget(self.temp_lbl, 2, 0, 1, 2)
        
        for lbl in (self.cpu_lbl, self.mem_lbl, self.temp_lbl):
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; border: none;")
            
        bar_style = f"""
            QProgressBar {{ border: none; background-color: {Theme.BG_BASE}; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {Theme.ACCENT}; border-radius: 3px; }}
        """
        self.cpu_bar.setStyleSheet(bar_style)
        self.mem_bar.setStyleSheet(bar_style)
        
        self.layout.addStretch()
        
    def update_data(self, health: SystemHealth):
        if not health: return
        self.cpu_lbl.setText(f"CPU: {health.cpu_usage:.0f}%")
        self.cpu_bar.setValue(int(health.cpu_usage))
        
        self.mem_lbl.setText(f"MEMORY: {health.memory_usage:.0f}%")
        self.mem_bar.setValue(int(health.memory_usage))
        
        self.temp_lbl.setText(f"TEMP: {health.temperature:.0f}°C")

class EventLogPanel(BasePanel):
    def __init__(self):
        super().__init__("EVENT LOG")
        self.setMinimumHeight(200)
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(6)
        self.layout.addLayout(self.rows_layout)
        self.layout.addStretch()
        
    def update_data(self, events: List[Event]):
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        for ev in events[:6]:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            
            lbl_time = QLabel(ev.timestamp.strftime("%H:%M:%S"))
            lbl_time.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-family: monospace; border: none;")
            lbl_time.setFixedWidth(60)
            
            lbl_msg = QLabel(ev.message)
            color = Theme.TEXT_PRIMARY
            if ev.severity == "WARNING": color = Theme.STATUS_WARNING
            if ev.severity == "CRITICAL": color = Theme.STATUS_CRITICAL
            lbl_msg.setStyleSheet(f"color: {color}; font-size: 11px; border: none;")
            
            row.addWidget(lbl_time)
            row.addWidget(lbl_msg)
            row.addStretch()
            
            w = QWidget()
            w.setLayout(row)
            w.setStyleSheet("border: none; background: transparent;")
            self.rows_layout.addWidget(w)
