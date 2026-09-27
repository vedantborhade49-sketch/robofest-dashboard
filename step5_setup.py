import os

base_dir = r"d:\robofest builds\python dashboard\aerosar_dashboard"
files = {}

files["app/models/incident.py"] = """\
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Location(BaseModel):
    x: float
    y: float
    z: float

class Incident(BaseModel):
    incident_id: str
    mission_id: str = "SAR-001"
    type: str
    confidence: float
    timestamp: datetime
    status: str
    location: Location
    evidence_image: Optional[str] = None
"""

files["app/services/incident_engine.py"] = """\
from app.models.detection import Detection
from app.models.incident import Incident, Location
from datetime import datetime

class IncidentEngine:
    \"\"\"
    Mock Incident Engine.
    Future flow:
    Detection -> Validation/filtering -> Context association -> Incident creation -> Evidence handling -> Structured Incident
    \"\"\"
    def __init__(self):
        self.counter = 100
        
    def process_detection(self, detection: Detection, current_location: Location) -> Incident:
        self.counter += 1
        return Incident(
            incident_id=f"INC-{self.counter}",
            mission_id="SAR-001",
            type=f"{detection.class_name} DETECTED",
            confidence=detection.confidence,
            timestamp=detection.timestamp,
            status="NEW",
            location=current_location,
            evidence_image=f"mock_evidence_ev{self.counter}.jpg"
        )
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
        
        self._drone_altitude = 14.8
        self._drone_speed = 3.2
        self._drone_battery = 82.0
        self._sys_cpu = 32.0
        self._sys_mem = 41.0
        self._frame_count = 12482
        self._dropped_frames = 0
        self._det_x = 0.4
        self._det_y = 0.5
        
        self._incidents = [
            Incident(
                incident_id="INC-001", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.94,
                timestamp=datetime.now() - timedelta(minutes=2, seconds=10),
                status="CONFIRMED", location=Location(x=12.4, y=8.7, z=14.8),
                evidence_image="mock_evidence_001.jpg"
            ),
            Incident(
                incident_id="INC-002", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=51),
                status="REVIEW", location=Location(x=18.2, y=11.3, z=13.2),
                evidence_image="mock_evidence_002.jpg"
            ),
            Incident(
                incident_id="INC-003", mission_id="SAR-001", type="PERSON DETECTED", confidence=0.91,
                timestamp=datetime.now() - timedelta(minutes=0, seconds=33),
                status="NEW", location=Location(x=7.8, y=16.5, z=12.7),
                evidence_image="mock_evidence_003.jpg"
            )
        ]
        
        self._events = [
            Event(timestamp=self._start_time, event_type="SYSTEM", message="Mission started", severity="INFO"),
            Event(timestamp=datetime.now() - timedelta(minutes=2, seconds=11), event_type="AI", message="Person detected", severity="WARNING")
        ]
        
    def get_mission(self) -> Mission:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return Mission(
            mission_id="SAR-001", mission_status="ACTIVE", elapsed_time=elapsed,
            search_progress=42.0, connection_status="CONNECTED"
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
            connected=True, fps=random.uniform(27.0, 30.0), latency=random.uniform(35.0, 55.0),
            frame_count=self._frame_count, dropped_frames=self._dropped_frames, resolution="1280x720"
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="READY", model_name="YOLO-PERSON-V1", inference_fps=random.uniform(27.0, 29.0),
            detections_count=len(self._incidents), device="MOCK / CPU"
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=round(self._drone_altitude, 1), speed=round(self._drone_speed, 1),
            heading=127.0, battery=self._drone_battery, signal=98.0,
            position=Location(x=10.5, y=20.1, z=self._drone_altitude)
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=32.0, memory_usage=41.0, temperature=48.0, communication_status="CONNECTED"
        )
        
    def get_incidents(self) -> List[Incident]:
        return self._incidents
        
    def get_events(self) -> List[Event]:
        return sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        
    def get_detections(self) -> List[Detection]:
        self._det_x += random.uniform(-0.01, 0.01)
        self._det_y += random.uniform(-0.01, 0.01)
        self._det_x = max(0.1, min(0.9, self._det_x))
        self._det_y = max(0.1, min(0.9, self._det_y))
        
        return [
            Detection(
                detection_id="DET-1029", class_name="PERSON", confidence=random.uniform(0.85, 0.98),
                bbox=BoundingBox(x=self._det_x, y=self._det_y, width=0.15, height=0.25), timestamp=datetime.now()
            )
        ]
"""

files["app/ui/widgets/incidents_panels.py"] = """\
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.models.incident import Incident
from typing import List

class IncidentCountersPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80)
        self.setStyleSheet(f\"\"\"
            IncidentCountersPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        \"\"\")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 16, 24, 16)
        
        self.total_lbl = self._add_counter("TOTAL", "0")
        self._add_separator()
        self.new_lbl = self._add_counter("NEW", "0", Theme.ACCENT)
        self._add_separator()
        self.review_lbl = self._add_counter("REVIEW", "0", Theme.STATUS_WARNING)
        self._add_separator()
        self.conf_lbl = self._add_counter("CONFIRMED", "0", Theme.STATUS_SUCCESS)
        self._add_separator()
        self.res_lbl = self._add_counter("RESOLVED", "0", Theme.TEXT_SECONDARY)
        
    def _add_counter(self, title, value, color=Theme.TEXT_PRIMARY):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(t)
        l.addWidget(v)
        self.layout.addWidget(w, 1)
        return v
        
    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {Theme.BORDER};")
        self.layout.addWidget(sep)
        
    def update_counts(self, incidents: List[Incident]):
        self.total_lbl.setText(str(len(incidents)))
        new_c = sum(1 for i in incidents if i.status == "NEW")
        rev_c = sum(1 for i in incidents if i.status == "REVIEW")
        conf_c = sum(1 for i in incidents if i.status == "CONFIRMED")
        res_c = sum(1 for i in incidents if i.status == "RESOLVED")
        self.new_lbl.setText(str(new_c))
        self.review_lbl.setText(str(rev_c))
        self.conf_lbl.setText(str(conf_c))
        self.res_lbl.setText(str(res_c))


class IncidentFilterPanel(QFrame):
    filter_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)
        self.setStyleSheet(f\"\"\"
            IncidentFilterPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        \"\"\")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 16, 0)
        
        lbl = QLabel("FILTER:")
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        self.layout.addWidget(lbl)
        
        self.buttons = []
        for f in ["ALL", "NEW", "REVIEW", "CONFIRMED", "RESOLVED"]:
            btn = QPushButton(f)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: none;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 12px;
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    background-color: {Theme.BG_SECONDARY};
                    color: {Theme.TEXT_PRIMARY};
                }}
            \"\"\")
            btn.clicked.connect(lambda checked, text=f: self._on_filter_click(text))
            self.buttons.append(btn)
            self.layout.addWidget(btn)
            
        self.layout.addStretch()
        self.buttons[0].setChecked(True)
        
    def _on_filter_click(self, filter_name):
        for b in self.buttons:
            if b.text() != filter_name:
                b.setChecked(False)
            else:
                b.setChecked(True)
        self.filter_changed.emit(filter_name)


class IncidentListPanel(QFrame):
    incident_selected = Signal(Incident)
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f\"\"\"
            IncidentListPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        \"\"\")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("INCIDENT LIST")
        title_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; padding: 16px; border-bottom: 1px solid {Theme.BORDER};")
        self.layout.addWidget(title_lbl)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll)
        
        self.incidents = []
        self.current_filter = "ALL"
        
    def update_data(self, incidents: List[Incident]):
        self.incidents = incidents
        self._refresh_list()
        
    def apply_filter(self, filter_name: str):
        self.current_filter = filter_name
        self._refresh_list()
        
    def _refresh_list(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        for inc in self.incidents:
            if self.current_filter != "ALL" and inc.status != self.current_filter:
                continue
                
            btn = QPushButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Status colors
            status_color = Theme.TEXT_SECONDARY
            if inc.status == "NEW": status_color = Theme.ACCENT
            elif inc.status == "REVIEW": status_color = Theme.STATUS_WARNING
            elif inc.status == "CONFIRMED": status_color = Theme.STATUS_SUCCESS
            
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    background-color: {Theme.BG_BASE};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 4px;
                    text-align: left;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BG_SECONDARY};
                }}
                QPushButton:focus {{
                    outline: none;
                    border: 1px solid {Theme.ACCENT};
                }}
            \"\"\")
            
            blayout = QVBoxLayout(btn)
            blayout.setContentsMargins(0,0,0,0)
            
            r1 = QHBoxLayout()
            id_lbl = QLabel(inc.incident_id)
            id_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; border: none;")
            
            st_lbl = QLabel(inc.status)
            st_lbl.setStyleSheet(f"color: {status_color}; font-size: 10px; font-weight: bold; border: none;")
            r1.addWidget(id_lbl)
            r1.addStretch()
            r1.addWidget(st_lbl)
            
            r2 = QHBoxLayout()
            type_lbl = QLabel(f"{inc.type}   {inc.confidence*100:.0f}%")
            type_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; border: none;")
            
            time_lbl = QLabel(inc.timestamp.strftime("%H:%M:%S"))
            time_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; border: none;")
            r2.addWidget(type_lbl)
            r2.addStretch()
            r2.addWidget(time_lbl)
            
            blayout.addLayout(r1)
            blayout.addLayout(r2)
            
            btn.clicked.connect(lambda checked, i=inc: self.incident_selected.emit(i))
            self.content_layout.addWidget(btn)


class IncidentDetailPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f\"\"\"
            IncidentDetailPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        \"\"\")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(20)
        
        self.empty_lbl = QLabel("NO INCIDENT SELECTED\\nSELECT AN INCIDENT TO VIEW DETAILS")
        self.empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px; font-weight: bold;")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.empty_lbl)
        
        self.content_widget = QWidget()
        cl = QVBoxLayout(self.content_widget)
        cl.setContentsMargins(0,0,0,0)
        cl.setSpacing(16)
        
        # Header
        self.id_lbl = QLabel("")
        self.id_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        cl.addWidget(self.id_lbl)
        
        # Details grid
        grid = QGridLayout()
        grid.setSpacing(12)
        
        self.type_lbl = QLabel("")
        self.conf_lbl = QLabel("")
        self.time_lbl = QLabel("")
        self.status_lbl = QLabel("")
        self.mission_lbl = QLabel("")
        
        def add_row(r, title, val_lbl):
            hl = QLabel(title)
            hl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
            val_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: bold;")
            grid.addWidget(hl, r, 0)
            grid.addWidget(val_lbl, r, 1)
            
        add_row(0, "TYPE", self.type_lbl)
        add_row(1, "CONFIDENCE", self.conf_lbl)
        add_row(2, "TIMESTAMP", self.time_lbl)
        add_row(3, "STATUS", self.status_lbl)
        add_row(4, "MISSION", self.mission_lbl)
        cl.addLayout(grid)
        
        # Location
        loc_header = QLabel("LOCATION (COORDINATE FRAME: LOCAL / SLAM)")
        loc_header.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; margin-top: 12px;")
        cl.addWidget(loc_header)
        
        self.loc_lbl = QLabel("")
        self.loc_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 13px; font-family: monospace;")
        cl.addWidget(self.loc_lbl)
        
        # Evidence
        ev_header = QLabel("EVIDENCE (CAPTURED FRAME)")
        ev_header.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; margin-top: 12px;")
        cl.addWidget(ev_header)
        
        self.ev_frame = QFrame()
        self.ev_frame.setStyleSheet(f"background-color: {Theme.BG_BASE}; border: 1px dashed {Theme.BORDER}; border-radius: 4px;")
        self.ev_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ev_frame.setMinimumHeight(200)
        
        el = QVBoxLayout(self.ev_frame)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ev_img_lbl = QLabel("[ EVIDENCE IMAGE PLACEHOLDER ]")
        self.ev_img_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px; font-weight: bold; border: none;")
        self.ev_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(self.ev_img_lbl)
        cl.addWidget(self.ev_frame, 1)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_map = QPushButton("VIEW ON MAP")
        btn_report = QPushButton("GENERATE REPORT")
        
        for btn in (btn_map, btn_report):
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    background-color: {Theme.BG_SECONDARY};
                    color: {Theme.TEXT_PRIMARY};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BORDER};
                }}
            \"\"\")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
        btn_layout.addWidget(btn_map)
        btn_layout.addWidget(btn_report)
        cl.addLayout(btn_layout)
        
        self.layout.addWidget(self.content_widget, 1)
        self.content_widget.hide()
        
    def show_incident(self, inc: Incident):
        self.empty_lbl.hide()
        self.content_widget.show()
        
        self.id_lbl.setText(inc.incident_id)
        self.type_lbl.setText(inc.type)
        self.conf_lbl.setText(f"{inc.confidence*100:.0f}%")
        self.time_lbl.setText(inc.timestamp.strftime("%H:%M:%S"))
        
        status_color = Theme.TEXT_PRIMARY
        if inc.status == "NEW": status_color = Theme.ACCENT
        elif inc.status == "REVIEW": status_color = Theme.STATUS_WARNING
        elif inc.status == "CONFIRMED": status_color = Theme.STATUS_SUCCESS
        self.status_lbl.setText(f"● {inc.status}")
        self.status_lbl.setStyleSheet(f"color: {status_color}; font-size: 13px; font-weight: bold;")
        
        self.mission_lbl.setText(inc.mission_id)
        
        self.loc_lbl.setText(f"X: {inc.location.x:.1f} m   Y: {inc.location.y:.1f} m   Z: {inc.location.z:.1f} m")
        self.ev_img_lbl.setText(f"[ EVIDENCE IMAGE PLACEHOLDER ]\\nIMAGE ID: EV-{inc.incident_id}\\nTIMESTAMP: {inc.timestamp.strftime('%H:%M:%S')}")
"""

files["app/ui/views/incidents_view.py"] = """\
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
"""

import os
for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Step 5 scaffolding complete.")
