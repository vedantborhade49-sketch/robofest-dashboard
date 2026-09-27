import os

base_dir = "d:/robofest builds/python dashboard/aerosar_dashboard"

directories = [
    "app/core",
    "app/models",
    "app/data",
    "app/services",
    "app/ui/views",
    "app/ui/widgets",
    "app/assets/icons",
    "tests"
]

files = {
    "requirements.txt": """PySide6>=6.5.0
pydantic>=2.0.0
pyqtgraph>=0.13.0
""",
    ".gitignore": """__pycache__/
*.pyc
.venv/
venv/
env/
.idea/
.vscode/
""",
    "README.md": """# STALLION AEROSAR \u2014 Ground Station Dashboard

This is the Ground Station Dashboard for the STALLION AEROSAR project (autonomous search-and-rescue drone operating in GPS-denied/confined environments).

## Current Development Stage
**Phase 1**: Initial project architecture, environment setup, and application skeleton. The UI currently displays a simple empty dark-themed window, establishing the foundation for future modules.

## Technology Stack
- **Python 3.11+**
- **PySide6** (Qt6 for UI)
- **Pydantic** (Data modeling)
- **PyQtGraph** (Fast graphing, to be used for telemetry/visualizations)

## Architecture Overview
The application follows a clean modular architecture ensuring the UI does not directly depend on the data source.
`UI -> Data Service -> Data Provider (Mock/Live)`

## Installation & Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\\Scripts\\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```
""",
    "main.py": """import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
""",
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/config.py": """class Config:
    DEBUG = True
    APP_NAME = "STALLION AEROSAR"
    VERSION = "0.1.0"
""",
    "app/core/constants.py": """# System-wide constants
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
""",
    "app/models/__init__.py": "",
    "app/models/mission.py": """from pydantic import BaseModel

class Mission(BaseModel):
    mission_id: str
    mission_status: str
    elapsed_time: float
    search_progress: float
    connection_status: str
""",
    "app/models/drone.py": """from pydantic import BaseModel

class Drone(BaseModel):
    drone_id: str
    status: str
    battery: float
    altitude: float
    speed: float
    heading: float
    signal_strength: float
""",
    "app/models/camera.py": """from pydantic import BaseModel

class Camera(BaseModel):
    connected: bool
    fps: float
    latency: float
""",
    "app/models/ai.py": """from pydantic import BaseModel

class AIStatus(BaseModel):
    status: str
    model_name: str
    inference_fps: float
    detections_count: int
""",
    "app/models/incident.py": """from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Location(BaseModel):
    x: float
    y: float
    z: float

class Incident(BaseModel):
    incident_id: str
    type: str
    confidence: float
    timestamp: datetime
    status: str
    location: Location
    evidence_image: Optional[str] = None
""",
    "app/models/telemetry.py": """from pydantic import BaseModel
from .incident import Location

class Telemetry(BaseModel):
    altitude: float
    speed: float
    heading: float
    battery: float
    signal: float
    position: Location
""",
    "app/models/system.py": """from pydantic import BaseModel

class SystemHealth(BaseModel):
    cpu_usage: float
    memory_usage: float
    temperature: float
    communication_status: str
""",
    "app/models/event.py": """from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    timestamp: datetime
    event_type: str
    message: str
    severity: str
""",
    "app/data/__init__.py": "",
    "app/data/provider.py": """from abc import ABC, abstractmethod
from typing import Optional
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth

class DataProvider(ABC):
    \"\"\"Abstract base class for all data providers.\"\"\"
    
    @abstractmethod
    def get_mission(self) -> Optional[Mission]:
        pass

    @abstractmethod
    def get_drone(self) -> Optional[Drone]:
        pass

    @abstractmethod
    def get_camera(self) -> Optional[Camera]:
        pass

    @abstractmethod
    def get_ai_status(self) -> Optional[AIStatus]:
        pass
        
    @abstractmethod
    def get_telemetry(self) -> Optional[Telemetry]:
        pass
        
    @abstractmethod
    def get_system_health(self) -> Optional[SystemHealth]:
        pass
""",
    "app/data/mock_provider.py": """from .provider import DataProvider
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.camera import Camera
from app.models.ai import AIStatus
from app.models.telemetry import Telemetry
from app.models.system import SystemHealth
from app.models.incident import Location

class MockDataProvider(DataProvider):
    \"\"\"Provides mock data for UI development and testing.\"\"\"
    
    def get_mission(self) -> Mission:
        return Mission(
            mission_id="M-2026-ALPHA",
            mission_status="IN_PROGRESS",
            elapsed_time=1240.5,
            search_progress=45.0,
            connection_status="CONNECTED"
        )

    def get_drone(self) -> Drone:
        return Drone(
            drone_id="STALLION-01",
            status="FLYING",
            battery=78.5,
            altitude=45.2,
            speed=12.4,
            heading=275.0,
            signal_strength=92.0
        )

    def get_camera(self) -> Camera:
        return Camera(
            connected=True,
            fps=30.0,
            latency=120.0
        )

    def get_ai_status(self) -> AIStatus:
        return AIStatus(
            status="ACTIVE",
            model_name="aerosar-yolo-v8-opt",
            inference_fps=15.0,
            detections_count=3
        )
        
    def get_telemetry(self) -> Telemetry:
        return Telemetry(
            altitude=45.2,
            speed=12.4,
            heading=275.0,
            battery=78.5,
            signal=92.0,
            position=Location(x=10.5, y=20.1, z=45.2)
        )
        
    def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            cpu_usage=45.0,
            memory_usage=60.0,
            temperature=55.0,
            communication_status="NOMINAL"
        )
""",
    "app/services/__init__.py": "",
    "app/services/data_service.py": """from app.data.provider import DataProvider
from app.data.mock_provider import MockDataProvider

class DataService:
    \"\"\"
    Service layer that acts as an intermediary between the UI and the data provider.
    This architecture ensures UI logic is decoupled from data sources.
    \"\"\"
    
    def __init__(self, provider: DataProvider = None):
        # Default to mock provider for development
        self._provider = provider or MockDataProvider()
        
    def get_mission_data(self):
        return self._provider.get_mission()

    def get_drone_data(self):
        return self._provider.get_drone()
        
    def get_telemetry_data(self):
        return self._provider.get_telemetry()
""",
    "app/ui/__init__.py": "",
    "app/ui/main_window.py": """from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.core.constants import WINDOW_WIDTH, WINDOW_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("STALLION AEROSAR \u2014 Ground Station")
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
        placeholder = QLabel("STALLION AEROSAR\\nGround Station Initialization...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Temporary placeholder styling
        placeholder.setStyleSheet("color: #64748b; font-size: 28px; font-weight: bold;")
        
        self.main_layout.addWidget(placeholder)
        
    def _apply_dark_theme(self):
        # Professional aerospace dark theme foundation
        dark_style = \"\"\"
        QMainWindow {
            background-color: #0b1120;
        }
        QWidget {
            background-color: #0b1120;
            color: #e2e8f0;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif;
        }
        \"\"\"
        self.setStyleSheet(dark_style)
""",
    "app/ui/views/__init__.py": "",
    "app/ui/widgets/__init__.py": "",
    "tests/__init__.py": ""
}

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Project setup complete.")
