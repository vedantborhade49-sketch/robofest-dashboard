from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.ui.theme import Theme

class EventLogView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("EVENT LOG")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 24px; font-weight: bold; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Mission and system events.")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(desc)
