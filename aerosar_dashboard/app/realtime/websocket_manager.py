import logging
from typing import List
from fastapi import WebSocket
from app.realtime.events import RealTimeEvent

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Client connected via WebSocket")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("Client disconnected from WebSocket")

    async def broadcast(self, event: RealTimeEvent):
        event_json = event.model_dump_json()
        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_text(event_json)
            except Exception as e:
                logger.warning(f"Error sending message to client: {e}")
                disconnected_clients.append(connection)
        
        for client in disconnected_clients:
            self.disconnect(client)
