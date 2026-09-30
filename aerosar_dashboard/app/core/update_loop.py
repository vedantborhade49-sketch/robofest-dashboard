from typing import Optional
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QTimer, Signal, QCoreApplication

from app.core.state_manager import StateManager
from app.data.provider import DataProvider

class CentralUpdateLoop(QObject):
    """
    Central real-time update loop for the AEROSAR ground station dashboard.
    Maintains a single controlled clock heartbeat driving the physical/sensor
    simulation in DataProvider, syncing updates into StateManager, and detecting
    communication link staleness. Eliminates uncontrolled timers inside individual UI pages.
    """
    tick_completed = Signal()
    link_stale_changed = Signal(bool)

    _instance: Optional["CentralUpdateLoop"] = None

    def __init__(self, state_manager: Optional[StateManager] = None, provider: Optional[DataProvider] = None, interval_ms: int = 500, spatial_service=None):
        super().__init__()
        self.state_manager = state_manager or StateManager.instance()
        self.provider = provider
        self.spatial_service = spatial_service
        self.interval_ms = interval_ms
        self._last_successful_sync: datetime = datetime.now()
        self._stale_threshold_seconds: float = 4.0

        # Create a QTimer only when a Qt application/event-loop exists.
        # In unit tests there may be no Q(Core)Application which makes timers
        # unreliable and can cause thread shutdown warnings. Defer timer
        # creation until start() when an application instance is present.
        self._timer = None

    def set_provider(self, provider: DataProvider):
        """Sets or replaces the underlying data provider."""
        self.provider = provider
        if self.state_manager and self.provider:
            self.state_manager.initialize_from_provider(self.provider)

    def set_interval(self, interval_ms: int):
        """Dynamically reconfigures loop rate (e.g. from Settings)."""
        self.interval_ms = max(50, interval_ms)
        if self._timer is not None and self._timer.isActive():
            self._timer.setInterval(self.interval_ms)

    def start(self):
        """Starts the central update heartbeat."""
        # If no Qt application is present (e.g. running unit tests), avoid
        # creating and starting a QTimer since there is no event loop to drive it.
        if QCoreApplication.instance() is None:
            # Perform a single synchronous initial sync and return; callers
            # can invoke trigger_immediate_tick() to advance the loop manually.
            if self.provider and self.state_manager:
                self.provider.step_simulation()
                self.state_manager.sync_from_provider(self.provider)
            return

        # Ensure timer exists and is parented correctly to this QObject
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._on_tick)

        if not self._timer.isActive():
            # Initial sync
            if self.provider and self.state_manager:
                self.provider.step_simulation()
                self.state_manager.sync_from_provider(self.provider)
            self._timer.start(self.interval_ms)

    def stop(self):
        """Stops the central update loop."""
        if self._timer is not None and self._timer.isActive():
            self._timer.stop()

    def is_running(self) -> bool:
        return self._timer.isActive() if self._timer is not None else False

    def trigger_immediate_tick(self):
        """Executes a single synchronous step cycle on demand."""
        self._on_tick()

    def _on_tick(self):
        """Heartbeat step: advances provider simulation and synchronizes state."""
        if not self.provider or not self.state_manager:
            return

        try:
            # 1. Step physical/sensor simulation
            self.provider.step_simulation()

            # 2. Sync to StateManager
            self.state_manager.sync_from_provider(self.provider)
            
            # 3. Update spatial service if available
            if self.spatial_service:
                spatial_state = self.spatial_service.update()
                self.state_manager.update_spatial(spatial_state)
                
                # Publish to real-time event flow
                from app.realtime.event_bus import event_bus
                from app.realtime.events import EventType
                try:
                    payload = {
                        "sensor_status": spatial_state.sensor_status,
                        "slam_status": spatial_state.slam_status,
                        "slam_quality": spatial_state.slam_quality,
                    }
                    if spatial_state.current_pose:
                        payload["pose"] = spatial_state.current_pose.dict()
                    event_bus.publish(EventType.SPATIAL_UPDATE, payload=payload)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not publish spatial event: {e}")

            self._last_successful_sync = datetime.now()

            # Clear staleness if was stale
            if self.state_manager.get_state() and self.state_manager.get_state().is_stale:
                self.state_manager.set_stale(False)
                self.link_stale_changed.emit(False)

        except Exception as e:
            # Fail gracefully: check for staleness rather than crashing
            now = datetime.now()
            if (now - self._last_successful_sync).total_seconds() > self._stale_threshold_seconds:
                if self.state_manager.get_state() and not self.state_manager.get_state().is_stale:
                    self.state_manager.set_stale(True)
                    self.link_stale_changed.emit(True)

        self.tick_completed.emit()
