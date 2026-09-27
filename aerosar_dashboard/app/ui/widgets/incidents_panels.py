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
        self.setStyleSheet(f"""
            IncidentCountersPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
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
        self.setStyleSheet(f"""
            IncidentFilterPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
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
            btn.setStyleSheet(f"""
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
            """)
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
        self.setStyleSheet(f"""
            IncidentListPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
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
            
            btn.setStyleSheet(f"""
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
            """)
            
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
        self.setStyleSheet(f"""
            IncidentDetailPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(20)
        
        self.empty_lbl = QLabel("NO INCIDENT SELECTED\nSELECT AN INCIDENT TO VIEW DETAILS")
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
            btn.setStyleSheet(f"""
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
            """)
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
        self.ev_img_lbl.setText(f"[ EVIDENCE IMAGE PLACEHOLDER ]\nIMAGE ID: EV-{inc.incident_id}\nTIMESTAMP: {inc.timestamp.strftime('%H:%M:%S')}")
