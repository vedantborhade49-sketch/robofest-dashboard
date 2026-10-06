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


class RealMAVLinkProvider(MAVLinkProvider):
    def __init__(self, connection_string: str, baud_rate: int = 115200):
        self.connection_string = connection_string
        self.baud_rate = baud_rate
        self.master = None
        self._warned_no_pymavlink = False
        
    def connect(self) -> bool:
        if not mavutil:
            if not self._warned_no_pymavlink:
                logger.error("pymavlink is not installed. Telemetry will be UNAVAILABLE.")
                print("pymavlink is not installed")
                self._warned_no_pymavlink = True
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
