import os

base_dir = r"d:\robofest builds\python dashboard\aerosar_dashboard"

files = {}

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

class MockDataProvider(DataProvider):
    \"\"\"Provides mock data for UI development and testing with simulated live updates.\"\"\"
    
    def __init__(self):
        self._start_time = datetime.now() - timedelta(minutes=18, seconds=42)
        
        # State variables for simulation
        self._drone_altitude = 14.8
        self._drone_speed = 3.2
        self._drone_battery = 82.0
        
        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        
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
            ),
            Incident(
                incident_id="INC-003", type="PERSON", confidence=0.91,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                status="CONFIRMED", location=Location(x=15.1, y=22.4, z=14.2)
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission started", severity="INFO"),
            Event(timestamp=self._start_time + timedelta(seconds=6), event_type="NETWORK", message="Camera connection established", severity="INFO"),
            Event(timestamp=self._start_time + timedelta(seconds=20), event_type="AI", message="AI inference started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=10), event_type="MISSION", message="Incident INC-001 created", severity="WARNING"),
            Event(timestamp=datetime.now() - timedelta(minutes=0, seconds=38), event_type="SYSTEM", message="Evidence image stored", severity="INFO")
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
            drone_id="AEROSAR-01",
            status="AIRBORNE",
            battery=self._drone_battery,
            altitude=round(self._drone_altitude, 1),
            speed=round(self._drone_speed, 1),
            heading=127.0,
            signal_strength=98.0
        )

    def get_camera(self) -> Camera:
        return Camera(
            connected=True,
            fps=random.uniform(28.0, 30.0),
            latency=random.uniform(110.0, 130.0)
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="READY",
            model_name="aerosar-yolo-v8-opt",
            inference_fps=15.0,
            detections_count=len(self._incidents)
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=round(self._drone_altitude, 1),
            speed=round(self._drone_speed, 1),
            heading=127.0,
            battery=self._drone_battery,
            signal=98.0,
            position=Location(x=10.5, y=20.1, z=self._drone_altitude)
        )
        
    def get_system_health(self) -> SystemHealth:
        self._sys_cpu += random.uniform(-2.0, 2.0)
        self._sys_cpu = max(10.0, min(100.0, self._sys_cpu))
        self._sys_mem += random.uniform(-0.5, 0.5)
        self._sys_mem = max(20.0, min(100.0, self._sys_mem))
        
        return SystemHealth(
            cpu_usage=round(self._sys_cpu, 1),
            memory_usage=round(self._sys_mem, 1),
            temperature=48.0,
            communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_events(self) -> List[Event]:
        # Return events sorted by timestamp descending
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
"""

files["app/services/data_service.py"] = """\
from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider

class DataService:
    \"\"\"
    Service layer that acts as an intermediary between the UI and the data provider.
    \"\"\"
    
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
"""

files["app/ui/widgets/overview_panels.py"] = """\
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
        self.setStyleSheet(f\"\"\"
            BasePanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        \"\"\")
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
        self.status = self._create_value_label("-", Theme.ACCENT)
        self.battery = self._create_value_label("0%")
        self.altitude = self._create_value_label("0.0 m")
        self.speed = self._create_value_label("0.0 m/s")
        self.heading = self._create_value_label("0\u00b0")
        
        grid.addWidget(self._create_header_label("DRONE"), 0, 0)
        grid.addWidget(self.drone_id, 1, 0)
        grid.addWidget(self._create_header_label("STATUS"), 0, 1)
        grid.addWidget(self.status, 1, 1)
        grid.addWidget(self._create_header_label("BATTERY"), 0, 2)
        grid.addWidget(self.battery, 1, 2)
        grid.addWidget(self._create_header_label("ALTITUDE"), 0, 3)
        grid.addWidget(self.altitude, 1, 3)
        grid.addWidget(self._create_header_label("SPEED"), 0, 4)
        grid.addWidget(self.speed, 1, 4)
        grid.addWidget(self._create_header_label("HEADING"), 0, 5)
        grid.addWidget(self.heading, 1, 5)
        
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
        self.status.setText(data.status)
        self.battery.setText(f"{data.battery:.0f}%")
        self.altitude.setText(f"{data.altitude:.1f} m")
        self.speed.setText(f"{data.speed:.1f} m/s")
        self.heading.setText(f"{data.heading:.0f}\u00b0")

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
        
        self.temp_lbl = QLabel("TEMP: 0\u00b0C")
        
        grid.addWidget(self.cpu_lbl, 0, 0)
        grid.addWidget(self.cpu_bar, 0, 1)
        grid.addWidget(self.mem_lbl, 1, 0)
        grid.addWidget(self.mem_bar, 1, 1)
        grid.addWidget(self.temp_lbl, 2, 0, 1, 2)
        
        for lbl in (self.cpu_lbl, self.mem_lbl, self.temp_lbl):
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; border: none;")
            
        bar_style = f\"\"\"
            QProgressBar {{ border: none; background-color: {Theme.BG_BASE}; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {Theme.ACCENT}; border-radius: 3px; }}
        \"\"\"
        self.cpu_bar.setStyleSheet(bar_style)
        self.mem_bar.setStyleSheet(bar_style)
        
        self.layout.addStretch()
        
    def update_data(self, health: SystemHealth):
        if not health: return
        self.cpu_lbl.setText(f"CPU: {health.cpu_usage:.0f}%")
        self.cpu_bar.setValue(int(health.cpu_usage))
        
        self.mem_lbl.setText(f"MEMORY: {health.memory_usage:.0f}%")
        self.mem_bar.setValue(int(health.memory_usage))
        
        self.temp_lbl.setText(f"TEMP: {health.temperature:.0f}\u00b0C")

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
"""

files["app/ui/views/overview_view.py"] = """\
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
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fetch_and_update_data)
        self.timer.start(1000)
        self._fetch_and_update_data()
        
    def _fetch_and_update_data(self):
        mission_data = self.data_service.get_mission_data()
        drone_data = self.data_service.get_drone_data()
        sys_health = self.data_service.get_system_health()
        cam_data = self.data_service.get_camera_data()
        ai_data = self.data_service.get_ai_data()
        incidents = self.data_service.get_incidents()
        events = self.data_service.get_events()
        
        self.mission_panel.update_data(mission_data)
        self.drone_panel.update_data(drone_data)
        self.system_panel.update_data(sys_health, cam_data, ai_data)
        self.camera_panel.update_data(cam_data)
        self.map_panel.update_data(drone_data)
        self.incidents_panel.update_data(incidents)
        self.health_panel.update_data(sys_health)
        self.events_panel.update_data(events)
"""

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Step 3 scaffolding complete.")
