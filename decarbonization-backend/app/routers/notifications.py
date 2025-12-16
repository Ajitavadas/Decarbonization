"""
Notifications Router (Phase 2.3)
Handles WebSocket connections for real-time user interaction.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict
import logging
from datetime import datetime, timezone

from app.schemas.schemas import NotificationMessage, FlaggedEvent
from app.services.interrogator_service import InterrogatorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["notifications"])

class ConnectionManager:
    """Manages active WebSocket connections"""
    def __init__(self):
        # Map user_id to list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: NotificationMessage, user_id: str):
        if user_id in self.active_connections:
            data = message.model_dump_json()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(data)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    # Cleanup dead connection if needed, but disconnect handles most

    async def broadcast(self, message: NotificationMessage):
        data = message.model_dump_json()
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(data)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")

# Global manager instance
manager = ConnectionManager()
interrogator_service = InterrogatorService()

@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for client messages
            # For now we just acknowledge receipt
            data = await websocket.receive_text()
            logger.info(f"Received message from {user_id}: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
        manager.disconnect(websocket, user_id)

async def notify_flagged_event(user_id: str, event: FlaggedEvent) -> NotificationMessage:
    """
    Triggered when an event is flagged.
    Generates a prompt using InterrogatorService and pushes to WebSocket.
    """
    logger.info(f"Processing flagged event {event.event_id} for user {user_id}")
    
    # 1. Generate conversational prompt
    prompt_text = await interrogator_service.generate_user_prompt(event)
    
    # 2. Create notification message
    message = NotificationMessage(
        type="prompt",
        user_id=user_id,
        content=prompt_text,
        event_ref=event.event_id,
        timestamp=datetime.now(timezone.utc),
        metadata={"severity": event.severity, "event_type": event.event_type}
    )
    
    # 3. Push to user
    await manager.send_personal_message(message, user_id)
    
    return message

@router.post("/test-trigger/{user_id}")
async def test_trigger(user_id: str, event: FlaggedEvent):
    """
    Test endpoint to manually trigger the Interrogator flow.
    Simulates the Auditor flagging an event.
    """
    try:
        msg = await notify_flagged_event(user_id, event)
        return {"status": "sent", "message": msg}
    except Exception as e:
        logger.error(f"Test trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
