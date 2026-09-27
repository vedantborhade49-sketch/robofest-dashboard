from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .incident import Location

class Telemetry(BaseModel):
    """Legacy model for backwards compatibility with Overview and Map views."""
    altitude: float
    speed: float
    heading: float
    battery: float
    signal: float
    position: Location

class FlightTelemetry(BaseModel):
    altitude: float = 14.8           # meters
    speed: float = 3.2               # m/s
    vertical_speed: float = 0.4      # m/s
    heading: float = 127.0           # degrees
    roll: float = 0.8                # degrees
    pitch: float = -1.2              # degrees
    yaw: float = 127.0               # degrees

class PositionTelemetry(BaseModel):
    x: float = 12.4                  # meters (LOCAL / SLAM)
    y: float = 8.7                   # meters (LOCAL / SLAM)
    z: float = 14.8                  # meters (LOCAL / SLAM)
    frame: str = "LOCAL / SLAM"
    heading: float = 127.0           # degrees

class PowerTelemetry(BaseModel):
    battery_percent: float = 82.0    # %
    voltage: float = 15.7            # Volts
    current: float = 8.4             # Amperes
    power_watts: float = 131.9       # Watts (voltage * current)
    status: str = "GOOD"             # GOOD | WARNING | CRITICAL

class CommunicationTelemetry(BaseModel):
    link_status: str = "CONNECTED"   # CONNECTED | DEGRADED | LOST
    signal_percent: float = 87.0     # %
    latency_ms: float = 38.0         # ms
    packet_loss_percent: float = 0.2 # %
    uplink: str = "CONNECTED"
    downlink: str = "CONNECTED"

class SensorStatus(BaseModel):
    imu: str = "READY"
    barometer: str = "READY"
    camera: str = "READY"
    lidar: str = "STANDBY"
    gps: str = "NOT REQUIRED"        # Confined/GPS-denied robotics architecture
    slam: str = "STANDBY"

class FlightControllerStatus(BaseModel):
    status: str = "CONNECTED"
    autopilot: str = "ARDUPILOT"
    mode: str = "GUIDED"
    armed: bool = False
    link: str = "CONNECTED"

class CompanionComputerStatus(BaseModel):
    device: str = "RASPBERRY PI 5"
    status: str = "ONLINE"
    cpu_percent: float = 34.0
    ram_percent: float = 42.0
    temperature_c: float = 51.0
    ai_status: str = "READY"
    camera_status: str = "READY"
    lidar_status: str = "STANDBY"

class TelemetryHistoryPoint(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    altitude: float
    speed: float
    battery: float

class TelemetryState(BaseModel):
    flight: FlightTelemetry = Field(default_factory=FlightTelemetry)
    position: PositionTelemetry = Field(default_factory=PositionTelemetry)
    power: PowerTelemetry = Field(default_factory=PowerTelemetry)
    communication: CommunicationTelemetry = Field(default_factory=CommunicationTelemetry)
    sensors: SensorStatus = Field(default_factory=SensorStatus)
    flight_controller: FlightControllerStatus = Field(default_factory=FlightControllerStatus)
    companion_computer: CompanionComputerStatus = Field(default_factory=CompanionComputerStatus)
    history: List[TelemetryHistoryPoint] = Field(default_factory=list)
