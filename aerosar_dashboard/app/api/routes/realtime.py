from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.realtime.event_bus import event_bus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await event_bus.connection_manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client in this one-way monitoring socket,
            # but we need to receive to detect disconnects.
            data = await websocket.receive_text()
            logger.debug(f"Received unexpected message from client: {data}")
    except WebSocketDisconnect:
        event_bus.connection_manager.disconnect(websocket)
