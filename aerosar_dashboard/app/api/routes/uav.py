from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
import logging
import json
import time

from app.models.communication import UAVMessage
from app.realtime.event_bus import event_bus
from app.realtime.events import EventType

logger = logging.getLogger(__name__)

router = APIRouter()

# Ground Station vehicle tracking
class VehicleState:
    def __init__(self):
        self.connected = False
        self.last_seen = 0.0
        self.messages_received = 0
        self.messages_lost = 0
        self.last_sequence = -1

# For now, track a single vehicle
vehicle_state = VehicleState()

@router.websocket("/ws")
async def uav_websocket_endpoint(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for UAVs to connect to the Ground Station.
    """
    await websocket.accept()
    vehicle_state.connected = True
    vehicle_state.last_seen = time.time()
    
    logger.info("UAV Connected to Ground Station via WebSocket")
    
    try:
        while True:
            data = await websocket.receive_text()
            vehicle_state.last_seen = time.time()
            
            try:
                # 1. Parse and Validate Envelope
                payload_dict = json.loads(data)
                msg = UAVMessage(**payload_dict)
                
                # 2. Sequence checking
                vehicle_state.messages_received += 1
                if vehicle_state.last_sequence != -1 and msg.sequence_number != vehicle_state.last_sequence + 1:
                    logger.warning(f"Sequence gap detected! Expected {vehicle_state.last_sequence + 1}, got {msg.sequence_number}")
                    vehicle_state.messages_lost += max(0, msg.sequence_number - vehicle_state.last_sequence - 1)
                vehicle_state.last_sequence = msg.sequence_number
                
                # 3. Handle specific messages like HEARTBEAT
                if msg.message_type == "HEARTBEAT":
                    pass # Just updates last_seen
                else:
                    # Route to event bus and state manager
                    try:
                        event_type = EventType(msg.message_type)
                        event_bus.publish(event_type, msg.payload, msg.mission_id)
                    except ValueError:
                        logger.warning(f"Unknown event type received from UAV: {msg.message_type}")
                        
                # 4. Acknowledge Reliable Messages
                if msg.delivery_class == "RELIABLE":
                    ack_msg = UAVMessage(
                        message_type="ACK",
                        sequence_number=0, # ground station sequence
                        payload={"message_id": msg.message_id}
                    )
                    await websocket.send_text(ack_msg.model_dump_json())
                    
            except ValidationError as e:
                logger.error(f"Invalid message format from UAV: {e}")
            except json.JSONDecodeError:
                logger.error("Received non-JSON message from UAV")
                
    except WebSocketDisconnect:
        logger.warning("UAV Disconnected from Ground Station")
        vehicle_state.connected = False
