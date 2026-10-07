from PySide6.QtCore import QObject, Signal, Slot
from typing import Optional
import logging

from app.spatial.service import SpatialService
from app.models.spatial import SpatialState
from app.spatial.history import SpatialStateHistory

logger = logging.getLogger(__name__)

class SpatialWorker(QObject):
    started = Signal()
    stopped = Signal()
    spatial_state_updated = Signal(object)  # SpatialState

    def __init__(self, service: SpatialService, history: SpatialStateHistory):
        super().__init__()
        self.service = service
        self.history = history
        self._running = False

    @Slot()
    def start(self):
        self._running = True
        self.service.start()
        self.started.emit()

    @Slot()
    def stop(self):
        self._running = False
        self.service.stop()
        self.stopped.emit()

    @Slot()
    def process_update(self):
        """Called periodically to process spatial updates (LiDAR, SLAM)"""
        if not self._running:
            return
            
        try:
            state = self.service.update()
            
            # Keep history updated
            self.history.add_state(state)
            
            # Emit updated state back to UI or central state manager
            self.spatial_state_updated.emit(state)
        except Exception as e:
            logger.error(f"Error in SpatialWorker process_update: {e}")
