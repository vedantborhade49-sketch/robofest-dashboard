from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import Theme

class SidebarButton(QPushButton):
    def __init__(self, text: str, page_index: int):
        super().__init__(text)
        self.page_index = page_index
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style definition
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 12px 16px;
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-left: 3px solid transparent;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Theme.BG_PANEL};
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
                background-color: {Theme.BG_SECONDARY};
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
        branding_container = QWidget()
        branding_layout = QVBoxLayout(branding_container)
        branding_layout.setContentsMargins(20, 24, 20, 24)
        branding_layout.setSpacing(4)
        
        title = QLabel("AEROSAR")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 20px; font-weight: bold; letter-spacing: 2px;")
        
        subtitle = QLabel("GROUND STATION")
        subtitle.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        
        branding_layout.addWidget(title)
        branding_layout.addWidget(subtitle)
        
        layout.addWidget(branding_container)
        
        # Navigation Items
        nav_items = [
            "Overview",
            "Live Feed",
            "Incidents",
            "Map",
            "Telemetry",
            "Reports",
            "Event Log",
            "Settings"
        ]
        
        for idx, name in enumerate(nav_items):
            btn = SidebarButton(name, idx)
            btn.clicked.connect(lambda checked, i=idx, n=name: self._on_button_clicked(i, n))
            self.buttons.append(btn)
            layout.addWidget(btn)
            
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer - System Status
        footer_container = QWidget()
        footer_container.setStyleSheet(f"border-top: 1px solid {Theme.BORDER}; background-color: transparent;")
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(20, 20, 20, 20)
        
        system_label = QLabel("SYSTEM")
        system_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        
        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)
        
        status_indicator = QLabel("● ONLINE")
        status_indicator.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 13px; font-weight: 600; border: none;")
        
        footer_layout.addWidget(system_label)
        footer_layout.addWidget(status_indicator)
        
        layout.addWidget(footer_container)
        
    def _on_button_clicked(self, page_index: int, page_name: str):
        self.set_active_page(page_index)
        self.page_selected.emit(page_index, page_name)
        
    def set_active_page(self, index: int):
        for btn in self.buttons:
            if btn.page_index == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
