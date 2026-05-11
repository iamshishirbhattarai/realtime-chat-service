from logging import getLogger

from fastapi import WebSocket

from app.core.redis import redis_client

logger = getLogger(__name__)


class ConversationManager:
    def __init__(self):
        self.conversations: dict[str, set[WebSocket]] = {}

    def create_conversation(self, conversation_id: str):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = set()

    async def join_conversation(
        self, conversation_id: str, websocket: WebSocket
    ):
        self.create_conversation(conversation_id)
        self.conversations[conversation_id].add(websocket)
        await websocket.accept()

    async def leave_conversation(
        self, conversation_id: str, websocket: WebSocket
    ):
        if (
            conversation_id in self.conversations
            and websocket in self.conversations[conversation_id]
        ):
            self.conversations[conversation_id].remove(websocket)

    async def broadcast(self, conversation_id: str, message: str):
        if conversation_id not in self.conversations:
            return
        connection_snapshot = list(self.conversations[conversation_id])
        dead_connections = set()
        for connection in connection_snapshot:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                dead_connections.add(connection)
        for connection in dead_connections:
            self.conversations[conversation_id].remove(connection)

    async def publish(self, conversation_id: str, message: str):
        logger.info(f"Publishing to Redis: {conversation_id}, {message}")
        await redis_client.publish(f"conversation:{conversation_id}", message)

    async def disconnect(self, websocket: WebSocket):
        for conversation in self.conversations.values():
            if websocket in conversation:
                conversation.remove(websocket)
