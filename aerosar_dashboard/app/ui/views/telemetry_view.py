from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from app.ui.theme import Theme
from app.services.data_service import DataService
from app.models.telemetry import TelemetryState
from app.ui.widgets.telemetry_panels import (
    FlightTelemetryPanel, PositionPanel, PowerPanel,
    CommunicationPanel, SensorStatusPanel, FlightControllerPanel,
    CompanionComputerPanel, GPSTelemetryPanel
)
from app.ui.widgets.telemetry_graph import TelemetryGraphSection
from app.ui.responsive import ScreenSize

class TelemetryHeaderBar(QFrame):
    """
    Top status bar for the Telemetry console.
    Displays title, drone callsign, and connection indicator.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet(f"""
            TelemetryHeaderBar {{
                background-color: {Theme.SURFACE_ELEVATED};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(18, 0, 18, 0)
        self.layout.setSpacing(14)

        self.title = QLabel("VEHICLE & SUBSYSTEM TELEMETRY")
        self.title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; letter-spacing: 0.8px;")
        self.layout.addWidget(self.title)

        self.layout.addStretch()

        self.callsign = QLabel("CALLSIGN: AEROSAR-01")
        self.callsign.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 600; font-family: monospace;")
        self.layout.addWidget(self.callsign)

        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.Shape.VLine)
        self.sep.setStyleSheet(f"color: {Theme.BORDER};")
        self.layout.addWidget(self.sep)

        self.conn_badge = QLabel("● LINK CONNECTED")
        self.conn_badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.SUCCESS};
                background-color: rgba(34, 197, 94, 0.12);
                border: 1px solid rgba(34, 197, 94, 0.35);
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)
        self.layout.addWidget(self.conn_badge)

    def update_connection(self, status: str):
        if status.upper() == "CONNECTED":
            self.conn_badge.setText("● LINK CONNECTED")
            self.conn_badge.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.SUCCESS};
                    background-color: rgba(34, 197, 94, 0.12);
                    border: 1px solid rgba(34, 197, 94, 0.35);
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)
        else:
            self.conn_badge.setText(f"● {status}")
            self.conn_badge.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.WARNING};
                    background-color: rgba(245, 158, 11, 0.12);
                    border: 1px solid rgba(245, 158, 11, 0.35);
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)

    def set_responsive_state(self, state: ScreenSize):
        if state == ScreenSize.MINIMUM:
            self.title.hide()
            self.callsign.hide()
            self.sep.hide()
        else:
            self.title.show()
            self.callsign.show()
            self.sep.show()


class TelemetryView(QWidget):
    """
    Main Telemetry Console View conforming to Step 7 requirements:
    1. Header Bar: TELEMETRY | AEROSAR-01 | ● CONNECTED
    2. Primary Telemetry Row: Flight Telemetry & Position (LOCAL / SLAM)
    3. Power & Communication Row: Battery & Link metrics
    4. Hardware Subsystems Row: Sensor Status, Flight Controller (Display Only), Companion Computer
    5. Telemetry History Section: PyQtGraph Altitude, Speed, and Battery historical curves
    6. Non-blocking live telemetry updates
    """
    def __init__(self):
        super().__init__()
        self.data_service = DataService()
        self.current_state = None
        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(24, 20, 24, 20)
        self.root_layout.setSpacing(14)

        # 1. Top Header
        self.header_bar = TelemetryHeaderBar()
        self.root_layout.addWidget(self.header_bar)

        # 2. Scrollable Content Area for responsiveness across resolutions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {Theme.BACKGROUND};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.SURFACE_ELEVATED};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.BORDER};
            }}
        """)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(14)

        # Panels
        self.flight_panel = FlightTelemetryPanel()
        self.position_panel = PositionPanel()
        self.gps_panel = GPSTelemetryPanel()
        self.power_panel = PowerPanel()
        self.comm_panel = CommunicationPanel()
        self.sensor_panel = SensorStatusPanel()
        self.fc_panel = FlightControllerPanel()
        self.computer_panel = CompanionComputerPanel()
        self.graph_section = TelemetryGraphSection()

        # Add to layout based on initial grid (will be rearranged by responsive state)
        self._reflow_grid(ScreenSize.LARGE)

        scroll.setWidget(container)
        self.root_layout.addWidget(scroll, 1)

    def _reflow_grid(self, state: ScreenSize):
        # Clear layout safely (remove widgets but don't delete them)
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                self.grid_layout.removeWidget(item.widget())

        if state == ScreenSize.LARGE:
            # 3 columns
            self.grid_layout.addWidget(self.flight_panel, 0, 0)
            self.grid_layout.addWidget(self.position_panel, 0, 1)
            self.grid_layout.addWidget(self.gps_panel, 0, 2)
            
            self.grid_layout.addWidget(self.power_panel, 1, 0, 1, 1)
            self.grid_layout.addWidget(self.comm_panel, 1, 1, 1, 2)
            
            self.grid_layout.addWidget(self.sensor_panel, 2, 0)
            self.grid_layout.addWidget(self.fc_panel, 2, 1)
            self.grid_layout.addWidget(self.computer_panel, 2, 2)
            
            self.grid_layout.addWidget(self.graph_section, 3, 0, 1, 3)

        elif state == ScreenSize.STANDARD:
            # 2 columns
            self.grid_layout.addWidget(self.flight_panel, 0, 0)
            self.grid_layout.addWidget(self.position_panel, 0, 1)
            
            self.grid_layout.addWidget(self.gps_panel, 1, 0)
            self.grid_layout.addWidget(self.power_panel, 1, 1)
            
            self.grid_layout.addWidget(self.comm_panel, 2, 0, 1, 2)
            
            self.grid_layout.addWidget(self.sensor_panel, 3, 0)
            self.grid_layout.addWidget(self.fc_panel, 3, 1)
            
            self.grid_layout.addWidget(self.computer_panel, 4, 0, 1, 2)
            
            self.grid_layout.addWidget(self.graph_section, 5, 0, 1, 2)

        else: # COMPACT or MINIMUM
            # 1 column
            self.grid_layout.addWidget(self.flight_panel, 0, 0)
            self.grid_layout.addWidget(self.position_panel, 1, 0)
            self.grid_layout.addWidget(self.gps_panel, 2, 0)
            self.grid_layout.addWidget(self.power_panel, 3, 0)
            self.grid_layout.addWidget(self.comm_panel, 4, 0)
            self.grid_layout.addWidget(self.sensor_panel, 5, 0)
            self.grid_layout.addWidget(self.fc_panel, 6, 0)
            self.grid_layout.addWidget(self.computer_panel, 7, 0)
            self.grid_layout.addWidget(self.graph_section, 8, 0)

    def set_responsive_state(self, state: ScreenSize):
        if self.current_state == state:
            return
        self.current_state = state
        self.header_bar.set_responsive_state(state)
        self._reflow_grid(state)
        
        if state == ScreenSize.MINIMUM:
            self.root_layout.setContentsMargins(8, 10, 8, 10)
        else:
            self.root_layout.setContentsMargins(24, 20, 24, 20)

    def _init_data(self):
        state = self.data_service.get_telemetry_state()
        if state:
            self._apply_state(state)

    def _start_live_updates(self):
        self.data_service.telemetry_updated.connect(self._apply_state)

    def _apply_state(self, state: TelemetryState):
        self.header_bar.update_connection(state.communication.link_status)
        self.flight_panel.update_data(state.flight)
        self.position_panel.update_data(state.position)
        self.gps_panel.update_data(state.gps)
        self.power_panel.update_data(state.power)
        self.comm_panel.update_data(state.communication)
        self.sensor_panel.update_data(state.sensors)
        self.fc_panel.update_data(state.flight_controller)
        self.computer_panel.update_data(state.companion_computer)
        self.graph_section.update_history(state.history)
