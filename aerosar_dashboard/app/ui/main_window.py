from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.core.constants import WINDOW_WIDTH, WINDOW_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("STALLION AEROSAR — Ground Station")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        self._setup_ui()
        self._apply_dark_theme()
        
    def _setup_ui(self):
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder for initial step
        placeholder = QLabel("STALLION AEROSAR\nGround Station Initialization...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Temporary placeholder styling
        placeholder.setStyleSheet("color: #64748b; font-size: 28px; font-weight: bold;")
        
        self.main_layout.addWidget(placeholder)
        
    def _apply_dark_theme(self):
        # Professional aerospace dark theme foundation
        dark_style = """
        QMainWindow {
            background-color: #0b1120;
        }
        QWidget {
            background-color: #0b1120;
            color: #e2e8f0;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif;
        }
        """
        self.setStyleSheet(dark_style)
