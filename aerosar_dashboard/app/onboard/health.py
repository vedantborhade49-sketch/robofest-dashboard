import logging
import platform
import time
from typing import Dict, Any, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """
    Monitors system resources on the onboard computer (Raspberry Pi).
    Provides graceful fallbacks for laptop development environments.
    """
    def __init__(self):
        self.os_info = platform.system()
        self.is_raspberry_pi = self._check_if_pi()
        
    def _check_if_pi(self) -> bool:
        if self.os_info != "Linux":
            return False
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                model = f.read().lower()
                return 'raspberry pi' in model
        except Exception:
            return False

    def get_cpu_usage(self) -> float:
        if HAS_PSUTIL:
            return psutil.cpu_percent(interval=None)
        return 0.0

    def get_memory_usage(self) -> float:
        if HAS_PSUTIL:
            return psutil.virtual_memory().percent
        return 0.0

    def get_disk_usage(self) -> float:
        if HAS_PSUTIL:
            return psutil.disk_usage('/').percent
        return 0.0

    def get_temperature(self) -> float:
        """Reads CPU temperature, handling platform differences."""
        if not HAS_PSUTIL:
            return 0.0
            
        try:
            # works on Linux / Raspberry Pi
            temps = psutil.sensors_temperatures()
            if not temps:
                return 0.0
            for name, entries in temps.items():
                if name.startswith('cpu') or name == 'coretemp':
                    return entries[0].current
        except Exception:
            pass
            
        # Fallback for Pi if psutil sensor doesn't catch it
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return float(f.read()) / 1000.0
        except Exception:
            pass
            
        return 0.0

    def get_health_report(self) -> Dict[str, Any]:
        """Generates a complete health snapshot."""
        return {
            "timestamp": time.time(),
            "cpu_percent": self.get_cpu_usage(),
            "memory_percent": self.get_memory_usage(),
            "disk_percent": self.get_disk_usage(),
            "temperature_c": self.get_temperature(),
            "is_pi": self.is_raspberry_pi,
            "os": self.os_info
        }
