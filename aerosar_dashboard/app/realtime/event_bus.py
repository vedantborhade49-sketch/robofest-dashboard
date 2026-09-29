import asyncio
import logging
from typing import Any, Dict, Optional
from app.realtime.events import RealTimeEvent, EventType
from app.realtime.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self._loop = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def publish(self, event_type: EventType, payload: Dict[str, Any], mission_id: Optional[str] = None):
        event = RealTimeEvent(
            event_type=event_type,
            payload=payload,
            mission_id=mission_id
        )
        logger.info(f"Publishing event {event_type} - {event.event_id}")
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.connection_manager.broadcast(event))
        except RuntimeError:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self.connection_manager.broadcast(event), self._loop)
            else:
                try:
                    asyncio.run(self.connection_manager.broadcast(event))
                except Exception as e:
                    logger.error(f"Failed to broadcast synchronously: {e}")

# Global instance for the application
event_bus = EventBus()
