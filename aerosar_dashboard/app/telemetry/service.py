import logging
import time
import math
from typing import Optional, Dict, Any, Callable
from pydantic import ValidationError

from app.models.telemetry import (
    TelemetryState, FlightTelemetry, PositionTelemetry, PowerTelemetry,
    CommunicationTelemetry, SensorStatus, FlightControllerStatus
)
from app.telemetry.provider import MAVLinkProvider

logger = logging.getLogger(__name__)

class TelemetryService:
    def __init__(self, provider: MAVLinkProvider):
        self.provider = provider
        self.state = TelemetryState()
        self._last_heartbeat = 0.0
        self._heartbeat_timeout = 3.0 # seconds
        self._packet_count = 0
        self._start_time = time.time()

    def update(self) -> Optional[TelemetryState]:
        """
        Polls the MAVLink provider for new messages and updates the TelemetryState.
        Returns the updated state if changes occurred, otherwise None.
        """
        if not self.provider.is_connected():
            return None

        state_changed = False
        msgs_processed = 0

        # Read all available messages up to a limit
        while msgs_processed < 50:
            msg = self.provider.read_message()
            if not msg:
                break

            self._packet_count += 1
            if self._parse_message(msg):
                state_changed = True
            msgs_processed += 1

        # Check heartbeat status
        now = time.time()
        hb_age = now - self._last_heartbeat
        
        link_status = "LOST"
        if hb_age < self._heartbeat_timeout:
            link_status = "CONNECTED"
        elif hb_age < self._heartbeat_timeout * 3:
            link_status = "DEGRADED"

        if self.state.communication.link_status != link_status:
            self.state.communication.link_status = link_status
            state_changed = True
            
        self.state.communication.heartbeat_age = hb_age

        if state_changed:
            return self.state
        return None

    def _parse_message(self, msg: Dict[str, Any]) -> bool:
        msg_type = msg.get("mavpackettype")
        if not msg_type:
            return False

        changed = False
        
        if msg_type == "HEARTBEAT":
            self._last_heartbeat = time.time()
            # ArduPilot is typically type 2 (QUADROTOR) or 1 (FIXED_WING) etc. Autopilot 3 is ARDUPILOTMEGA.
            if msg.get("autopilot") == 3:
                self.state.flight_controller.autopilot = "ARDUPILOT"
            
            base_mode = msg.get("base_mode", 0)
            custom_mode = msg.get("custom_mode", 0)
            
            armed = (base_mode & 128) != 0 # MAV_MODE_FLAG_SAFETY_ARMED
            if self.state.flight_controller.armed != armed:
                self.state.flight_controller.armed = armed
                changed = True
                
            # Mode mapping (simplified for copter/rover)
            mode_map = {0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUIDED", 5: "LOITER", 6: "RTL", 9: "LAND"}
            mode = mode_map.get(custom_mode, f"MODE_{custom_mode}")
            
            if self.state.flight_controller.mode != mode:
                self.state.flight_controller.mode = mode
                changed = True
                
        elif msg_type == "GLOBAL_POSITION_INT":
            lat = msg.get("lat", 0) / 1e7
            lon = msg.get("lon", 0) / 1e7
            alt = msg.get("alt", 0) / 1000.0
            relative_alt = msg.get("relative_alt", 0) / 1000.0
            hdg = msg.get("hdg", 0) / 100.0
            vx = msg.get("vx", 0) / 100.0
            vy = msg.get("vy", 0) / 100.0
            vz = msg.get("vz", 0) / 100.0
            
            self.state.flight.altitude = relative_alt
            self.state.flight.vertical_speed = -vz # negative Z is up in NED
            self.state.flight.speed = (vx**2 + vy**2)**0.5
            self.state.flight.heading = hdg
            
            self.state.gps.latitude = lat
            self.state.gps.longitude = lon
            self.state.gps.altitude = alt
            
            # Note: We do NOT overwrite PositionTelemetry (x,y,z) with lat/lon!
            # PositionTelemetry is strictly for SLAM / LOCAL coordinates as per architecture.
            changed = True
            
        elif msg_type == "ATTITUDE":
            self.state.flight.roll = math.degrees(msg.get("roll", 0))
            self.state.flight.pitch = math.degrees(msg.get("pitch", 0))
            self.state.flight.yaw = math.degrees(msg.get("yaw", 0))
            changed = True
            
        elif msg_type == "SYS_STATUS":
            voltage = msg.get("voltage_battery", 0) / 1000.0
            current = msg.get("current_battery", 0) / 100.0
            battery_rem = msg.get("battery_remaining", 0)
            
            if battery_rem > -1:
                self.state.power.battery_percent = battery_rem
            self.state.power.voltage = voltage
            self.state.power.current = current if current >= 0 else 0
            self.state.power.power_watts = self.state.power.voltage * self.state.power.current
            
            if self.state.power.battery_percent < 15:
                self.state.power.status = "CRITICAL"
            elif self.state.power.battery_percent < 30:
                self.state.power.status = "WARNING"
            else:
                self.state.power.status = "GOOD"
                
            changed = True
            
        elif msg_type == "GPS_RAW_INT":
            self.state.gps.satellites = msg.get("satellites_visible", 0)
            self.state.gps.fix_type = msg.get("fix_type", 0)
            changed = True
            
        return changed
