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
    altitude: float = 0.0           # meters
    speed: float = 0.0              # m/s
    vertical_speed: float = 0.0     # m/s
    heading: float = 0.0            # degrees
    roll: float = 0.0               # degrees
    pitch: float = 0.0              # degrees
    yaw: float = 0.0                # degrees

class PositionTelemetry(BaseModel):
    x: float = 0.0                  # meters (LOCAL / SLAM)
    y: float = 0.0                  # meters (LOCAL / SLAM)
    z: float = 0.0                  # meters (LOCAL / SLAM)
    frame: str = "LOCAL / SLAM"
    heading: float = 0.0            # degrees

class GPSTelemetry(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    satellites: int = 0
    fix_type: int = 0
    hdop: float = 0.0
    vdop: float = 0.0

class PowerTelemetry(BaseModel):
    battery_percent: float = 0.0    # %
    voltage: float = 0.0            # Volts
    current: float = 0.0            # Amperes
    power_watts: float = 0.0        # Watts (voltage * current)
    status: str = "UNKNOWN"         # GOOD | WARNING | CRITICAL

class CommunicationTelemetry(BaseModel):
    link_status: str = "DISCONNECTED"   # CONNECTED | DEGRADED | LOST
    signal_percent: float = 0.0         # %
    latency_ms: float = 0.0             # ms
    packet_loss_percent: float = 0.0    # %
    uplink: str = "DISCONNECTED"
    downlink: str = "DISCONNECTED"
    heartbeat_age: float = 0.0

class SensorStatus(BaseModel):
    imu: str = "UNKNOWN"
    barometer: str = "UNKNOWN"
    camera: str = "UNKNOWN"
    lidar: str = "UNKNOWN"
    gps: str = "UNKNOWN"
    slam: str = "UNKNOWN"

class FlightControllerStatus(BaseModel):
    status: str = "DISCONNECTED"
    autopilot: str = "UNKNOWN"
    mode: str = "UNKNOWN"
    armed: bool = False
    link: str = "DISCONNECTED"

class CompanionComputerStatus(BaseModel):
    device: str = "UNKNOWN"
    status: str = "DISCONNECTED"
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    temperature_c: float = 0.0
    ai_status: str = "UNKNOWN"
    camera_status: str = "UNKNOWN"
    lidar_status: str = "UNKNOWN"

class TelemetryHistoryPoint(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    altitude: float
    speed: float
    battery: float

class TelemetryState(BaseModel):
    flight: FlightTelemetry = Field(default_factory=FlightTelemetry)
    position: PositionTelemetry = Field(default_factory=PositionTelemetry)
    gps: GPSTelemetry = Field(default_factory=GPSTelemetry)
    power: PowerTelemetry = Field(default_factory=PowerTelemetry)
    communication: CommunicationTelemetry = Field(default_factory=CommunicationTelemetry)
    sensors: SensorStatus = Field(default_factory=SensorStatus)
    flight_controller: FlightControllerStatus = Field(default_factory=FlightControllerStatus)
    companion_computer: CompanionComputerStatus = Field(default_factory=CompanionComputerStatus)
    history: List[TelemetryHistoryPoint] = Field(default_factory=list)
