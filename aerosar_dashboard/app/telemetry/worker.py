import time
import logging
from PySide6.QtCore import QThread, Signal

from app.telemetry.service import TelemetryService
from app.telemetry.provider import MockMAVLinkProvider, RealMAVLinkProvider
from app.models.settings import DashboardSettings
from app.core.state_manager import StateManager
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

logger = logging.getLogger(__name__)

class TelemetryWorker(QThread):
    def __init__(self, settings: DashboardSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._running = False
        self.service = None
        self._setup_service()

    def _setup_service(self):
        try:
            # We can use new settings fields: mavlink_provider, mavlink_connection_string
            provider_type = getattr(self.settings, "mavlink_provider", "mock").lower()
            
            if provider_type == "real":
                conn_str = getattr(self.settings, "mavlink_connection_string", "udp:127.0.0.1:14550")
                baud = getattr(self.settings, "mavlink_baud_rate", 115200)
                provider = RealMAVLinkProvider(connection_string=conn_str, baud_rate=baud)
            else:
                provider = MockMAVLinkProvider()
                
            self.service = TelemetryService(provider)
        except Exception as e:
            logger.error(f"Failed to setup TelemetryService: {e}")
            self.service = None

    def run(self):
        if not self.service:
            logger.error("TelemetryWorker started without a valid service")
            return
            
        self._running = True
        logger.info("TelemetryWorker starting...")
        
        # Connect
        connected = self.service.provider.connect()
        if not connected:
            logger.error("TelemetryWorker failed to connect provider")
        
        update_interval = getattr(self.settings, "telemetry_update_interval_ms", 100) / 1000.0

        while self._running:
            try:
                if not self.service.provider.is_connected():
                    # Attempt reconnect every second
                    self.service.provider.connect()
                    time.sleep(1.0)
                    continue
                    
                updated_state = self.service.update()
                
                if updated_state:
                    # Update StateManager
                    state_mgr = StateManager.instance()
                    state_mgr._state.telemetry = updated_state
                    
                    # Also update Drone state for Overview compatibility
                    if state_mgr._state.drone:
                        state_mgr._state.drone.altitude = updated_state.flight.altitude
                        state_mgr._state.drone.speed = updated_state.flight.speed
                        state_mgr._state.drone.heading = updated_state.flight.heading
                        state_mgr._state.drone.battery = updated_state.power.battery_percent
                        state_mgr._state.drone.signal_strength = updated_state.communication.signal_percent
                        
                        if updated_state.communication.link_status == "CONNECTED":
                            state_mgr._state.drone.status = updated_state.flight_controller.mode
                        else:
                            state_mgr._state.drone.status = updated_state.communication.link_status
                            
                        state_mgr.drone_updated.emit(state_mgr._state.drone)
                        
                    state_mgr.telemetry_updated.emit(updated_state)
                    state_mgr.state_updated.emit(state_mgr._state)
                    
                    # Also publish via event bus for WebSocket
                    event_bus.publish(
                        EventType.TELEMETRY_UPDATE,
                        payload=updated_state.model_dump(),
                        mission_id=state_mgr.get_mission().mission_id if state_mgr.get_mission() else "SAR-001"
                    )
            except Exception as e:
                logger.error(f"Error in TelemetryWorker loop: {e}")
                
            time.sleep(update_interval)

        if self.service:
            self.service.provider.disconnect()
        logger.info("TelemetryWorker stopped.")

    def stop(self):
        self._running = False
        self.wait()
