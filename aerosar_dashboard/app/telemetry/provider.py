import logging
import time
import math
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None

logger = logging.getLogger(__name__)

class MAVLinkProvider(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def read_message(self) -> Optional[Dict[str, Any]]:
        pass


class MockMAVLinkProvider(MAVLinkProvider):
    def __init__(self):
        self._connected = False
        self._start_time = time.time()
        self._last_msg_time = 0
        self._msg_index = 0
        
    def connect(self) -> bool:
        self._connected = True
        self._start_time = time.time()
        logger.info("Mock MAVLink connected")
        return True
        
    def disconnect(self):
        self._connected = False
        logger.info("Mock MAVLink disconnected")
        
    def is_connected(self) -> bool:
        return self._connected
        
    def read_message(self) -> Optional[Dict[str, Any]]:
        if not self._connected:
            return None
            
        now = time.time()
        if now - self._last_msg_time < 0.1: # 10Hz
            return None
            
        self._last_msg_time = now
        elapsed = now - self._start_time
        
        # Cycle through different message types
        self._msg_index = (self._msg_index + 1) % 5
        
        if self._msg_index == 0:
            return {
                "mavpackettype": "HEARTBEAT",
                "type": 2, # QUADROTOR
                "autopilot": 3, # ARDUPILOTMEGA
                "base_mode": 81, # ARMED + CUSTOM
                "custom_mode": 4, # GUIDED
                "system_status": 4 # ACTIVE
            }
        elif self._msg_index == 1:
            return {
                "mavpackettype": "GLOBAL_POSITION_INT",
                "lat": int((18.5204 + math.sin(elapsed * 0.01) * 0.001) * 1e7),
                "lon": int((73.8567 + math.cos(elapsed * 0.01) * 0.001) * 1e7),
                "alt": int((15.0 + math.sin(elapsed * 0.1)) * 1000),
                "relative_alt": int((15.0 + math.sin(elapsed * 0.1)) * 1000),
                "vx": 320,
                "vy": -120,
                "vz": 40,
                "hdg": int((90 + math.sin(elapsed * 0.1) * 10) * 100)
            }
        elif self._msg_index == 2:
            return {
                "mavpackettype": "ATTITUDE",
                "roll": 0.05 * math.sin(elapsed),
                "pitch": -0.02 * math.cos(elapsed),
                "yaw": math.radians(90 + math.sin(elapsed * 0.1) * 10)
            }
        elif self._msg_index == 3:
            return {
                "mavpackettype": "SYS_STATUS",
                "voltage_battery": int(15800 - elapsed * 10), # decreasing voltage
                "current_battery": 850,
                "battery_remaining": max(0, int(100 - elapsed / 10))
            }
        elif self._msg_index == 4:
            return {
                "mavpackettype": "GPS_RAW_INT",
                "fix_type": 3, # 3D fix
                "satellites_visible": int(12 + 2 * math.sin(elapsed * 0.5))
            }
        
        return None


class RealMAVLinkProvider(MAVLinkProvider):
    def __init__(self, connection_string: str, baud_rate: int = 115200):
        self.connection_string = connection_string
        self.baud_rate = baud_rate
        self.master = None
        
    def connect(self) -> bool:
        if not mavutil:
            logger.error("pymavlink is not installed")
            return False
            
        try:
            self.master = mavutil.mavlink_connection(self.connection_string, baud=self.baud_rate)
            logger.info(f"Connected to MAVLink at {self.connection_string}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MAVLink: {e}")
            return False
            
    def disconnect(self):
        if self.master:
            self.master.close()
            self.master = None
            logger.info("MAVLink disconnected")
            
    def is_connected(self) -> bool:
        return self.master is not None
        
    def read_message(self) -> Optional[Dict[str, Any]]:
        if not self.master:
            return None
            
        try:
            msg = self.master.recv_match(blocking=False)
            if msg:
                return msg.to_dict()
        except Exception as e:
            logger.warning(f"MAVLink read error: {e}")
            
        return None
