import threading
from typing import Optional, Deque
from datetime import datetime
from collections import deque
import logging

from app.models.spatial import SpatialState

logger = logging.getLogger(__name__)

class SpatialStateHistory:
    """
    Retains recent spatial states and provides temporal association lookups.
    Thread-safe for concurrent read (PerceptionWorker) and write (SpatialWorker).
    """
    def __init__(self, max_history_size: int = 100, max_age_seconds: float = 2.0):
        self._lock = threading.Lock()
        self._history: Deque[SpatialState] = deque(maxlen=max_history_size)
        self.max_age_seconds = max_age_seconds

    def add_state(self, state: SpatialState):
        """Adds a new spatial state to the history."""
        # Deep copy might be needed if the caller mutates it, but SpatialWorker 
        # creates a new SpatialState or updates an existing one? 
        # In SpatialService.update(), it mutates self.state.
        # We need a snapshot. We'll require caller to provide a safe snapshot 
        # or we can do a pydantic copy.
        snapshot = state.copy(deep=True) if hasattr(state, 'copy') else state
        with self._lock:
            self._history.append(snapshot)

    def get_state_at(self, timestamp: datetime) -> Optional[SpatialState]:
        """
        Returns the closest SpatialState to the given timestamp.
        Returns None if no state is available within max_age_seconds.
        """
        with self._lock:
            if not self._history:
                return None
            
            # Find the state with the minimum absolute time difference
            best_state = None
            min_diff = float('inf')

            for state in self._history:
                diff = abs((state.timestamp - timestamp).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    best_state = state
            
            if min_diff <= self.max_age_seconds:
                return best_state
            
            logger.warning(f"Spatial state stale. Min diff: {min_diff}s > {self.max_age_seconds}s")
            return None
