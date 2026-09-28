from typing import Optional
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QTimer, Signal

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

    def __init__(self, state_manager: Optional[StateManager] = None, provider: Optional[DataProvider] = None, interval_ms: int = 500):
        super().__init__()
        self.state_manager = state_manager or StateManager.instance()
        self.provider = provider
        self.interval_ms = interval_ms
        self._last_successful_sync: datetime = datetime.now()
        self._stale_threshold_seconds: float = 4.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def set_provider(self, provider: DataProvider):
        """Sets or replaces the underlying data provider."""
        self.provider = provider
        if self.state_manager and self.provider:
            self.state_manager.initialize_from_provider(self.provider)

    def set_interval(self, interval_ms: int):
        """Dynamically reconfigures loop rate (e.g. from Settings)."""
        self.interval_ms = max(50, interval_ms)
        if self._timer.isActive():
            self._timer.setInterval(self.interval_ms)

    def start(self):
        """Starts the central update heartbeat."""
        if not self._timer.isActive():
            # Initial sync
            if self.provider and self.state_manager:
                self.provider.step_simulation()
                self.state_manager.sync_from_provider(self.provider)
            self._timer.start(self.interval_ms)

    def stop(self):
        """Stops the central update loop."""
        if self._timer.isActive():
            self._timer.stop()

    def is_running(self) -> bool:
        return self._timer.isActive()

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
