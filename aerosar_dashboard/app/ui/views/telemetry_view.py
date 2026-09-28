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
    CompanionComputerPanel
)
from app.ui.widgets.telemetry_graph import TelemetryGraphSection

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
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(14)

        title = QLabel("VEHICLE & SUBSYSTEM TELEMETRY")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: bold; letter-spacing: 0.8px;")
        layout.addWidget(title)

        layout.addStretch()

        callsign = QLabel("CALLSIGN: AEROSAR-01")
        callsign.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 600; font-family: monospace;")
        layout.addWidget(callsign)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {Theme.BORDER};")
        layout.addWidget(sep)

        self.conn_badge = QLabel("● LINK CONNECTED")
        self.conn_badge.setStyleSheet(f"""
            QLabel {{
                color: {Theme.STATUS_SUCCESS};
                background-color: rgba(34, 197, 94, 0.12);
                border: 1px solid rgba(34, 197, 94, 0.35);
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """)
        layout.addWidget(self.conn_badge)

    def update_connection(self, status: str):
        if status.upper() == "CONNECTED":
            self.conn_badge.setText("● LINK CONNECTED")
            self.conn_badge.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.STATUS_SUCCESS};
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
                    color: {Theme.STATUS_WARNING};
                    background-color: rgba(245, 158, 11, 0.12);
                    border: 1px solid rgba(245, 158, 11, 0.35);
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)


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
        self._setup_ui()
        self._init_data()
        self._start_live_updates()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(14)

        # 1. Top Header
        self.header_bar = TelemetryHeaderBar()
        root_layout.addWidget(self.header_bar)

        # 2. Scrollable Content Area for responsiveness across resolutions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #0D1219;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #252D38;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3B4758;
            }
        """)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        # --- Row 1: Flight Telemetry & 3D Local Position ---
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self.flight_panel = FlightTelemetryPanel()
        self.position_panel = PositionPanel()
        row1.addWidget(self.flight_panel, 1)
        row1.addWidget(self.position_panel, 1)
        content_layout.addLayout(row1)

        # --- Row 2: Power & Communication Link ---
        row2 = QHBoxLayout()
        row2.setSpacing(14)
        self.power_panel = PowerPanel()
        self.comm_panel = CommunicationPanel()
        row2.addWidget(self.power_panel, 1)
        row2.addWidget(self.comm_panel, 1)
        content_layout.addLayout(row2)

        # --- Row 3: Sensor Status, Flight Controller, Companion Computer ---
        row3 = QHBoxLayout()
        row3.setSpacing(14)
        self.sensor_panel = SensorStatusPanel()
        self.fc_panel = FlightControllerPanel()
        self.computer_panel = CompanionComputerPanel()
        row3.addWidget(self.sensor_panel, 1)
        row3.addWidget(self.fc_panel, 1)
        row3.addWidget(self.computer_panel, 1)
        content_layout.addLayout(row3)

        # --- Row 4: Historical PyQtGraph Graphs ---
        self.graph_section = TelemetryGraphSection()
        content_layout.addWidget(self.graph_section)

        scroll.setWidget(container)
        root_layout.addWidget(scroll, 1)

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
        self.power_panel.update_data(state.power)
        self.comm_panel.update_data(state.communication)
        self.sensor_panel.update_data(state.sensors)
        self.fc_panel.update_data(state.flight_controller)
        self.computer_panel.update_data(state.companion_computer)
        self.graph_section.update_history(state.history)
