from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme
from app.ui.responsive import ScreenSize

class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_text: str, page_index: int):
        super().__init__()
        self.page_index = page_index
        self.full_text = text
        self.icon_text = icon_text
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(text)
        
        self.set_compact(False)
        
    def set_compact(self, compact: bool):
        if compact:
            self.setText(self.icon_text)
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: center;
                    padding: 12px 0px;
                    font-size: 18px;
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: none;
                    border-left: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: {Theme.SURFACE_ELEVATED};
                    color: {Theme.TEXT_PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: {Theme.SURFACE_ELEVATED};
                    color: {Theme.ACCENT};
                    border-left: 3px solid {Theme.ACCENT};
                }}
            """)
        else:
            self.setText(f"{self.icon_text}   {self.full_text}")
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 0px 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: none;
                    border-left: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: {Theme.SURFACE_ELEVATED};
                    color: {Theme.TEXT_PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: {Theme.SURFACE_ELEVATED};
                    color: {Theme.ACCENT};
                    border-left: 3px solid {Theme.ACCENT};
                }}
            """)

class Sidebar(QWidget):
    page_selected = Signal(int, str) # Emits (page_index, page_name)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        
        # Enforce styling for the sidebar container
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Theme.SURFACE};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)
        
        self.buttons = []
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Branding Header
        self.branding_container = QWidget()
        branding_layout = QVBoxLayout(self.branding_container)
        branding_layout.setContentsMargins(20, 24, 20, 24)
        branding_layout.setSpacing(4)
        
        self.title = QLabel("AEROSAR")
        self.title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 20px; font-weight: bold; letter-spacing: 2px;")
        
        self.subtitle = QLabel("GROUND STATION")
        self.subtitle.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        
        branding_layout.addWidget(self.title)
        branding_layout.addWidget(self.subtitle)
        
        layout.addWidget(self.branding_container)
        
        # Navigation Items
        nav_items = [
            ("Overview", "◉"),
            ("Live Feed", "◫"),
            ("Incidents", "⚠"),
            ("Map", "🗺"),
            ("Telemetry", "≋"),
            ("Reports", "▤"),
            ("Event Log", "≡"),
            ("Settings", "⚙")
        ]
        
        for idx, (name, icon) in enumerate(nav_items):
            btn = SidebarButton(name, icon, idx)
            btn.clicked.connect(lambda checked, i=idx, n=name: self._on_button_clicked(i, n))
            self.buttons.append(btn)
            layout.addWidget(btn)
            
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer - System Status
        self.footer_container = QWidget()
        self.footer_container.setStyleSheet(f"border-top: 1px solid {Theme.BORDER}; background-color: transparent;")
        footer_layout = QVBoxLayout(self.footer_container)
        footer_layout.setContentsMargins(20, 20, 20, 20)
        
        self.system_label = QLabel("SYSTEM")
        self.system_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        
        self.status_indicator = QLabel("● ONLINE")
        self.status_indicator.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 13px; font-weight: 600; border: none;")
        
        footer_layout.addWidget(self.system_label)
        footer_layout.addWidget(self.status_indicator)
        
        layout.addWidget(self.footer_container)
        
    def _on_button_clicked(self, page_index: int, page_name: str):
        self.set_active_page(page_index)
        self.page_selected.emit(page_index, page_name)
        
    def set_active_page(self, index: int):
        for btn in self.buttons:
            if btn.page_index == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

    def set_responsive_state(self, state: ScreenSize):
        if state in (ScreenSize.COMPACT, ScreenSize.MINIMUM):
            self.setFixedWidth(64)
            self.title.setText("A")
            self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.subtitle.hide()
            self.branding_container.layout().setContentsMargins(0, 24, 0, 24)
            
            for btn in self.buttons:
                btn.set_compact(True)
                
            self.system_label.hide()
            self.status_indicator.setText("●")
            self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.footer_container.layout().setContentsMargins(0, 20, 0, 20)
        else:
            self.setFixedWidth(240)
            self.title.setText("AEROSAR")
            self.title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.subtitle.show()
            self.branding_container.layout().setContentsMargins(20, 24, 20, 24)
            
            for btn in self.buttons:
                btn.set_compact(False)
                
            self.system_label.show()
            self.status_indicator.setText("● ONLINE")
            self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.footer_container.layout().setContentsMargins(20, 20, 20, 20)
