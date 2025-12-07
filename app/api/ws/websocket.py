import asyncio
from logging import getLogger

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.ws.rooms import ConversationManager
from app.core.redis import get_pubsub

logger = getLogger(__name__)
room_manager = ConversationManager()
router = APIRouter()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await room_manager.join_room(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await room_manager.publish(conversation_id, data)
    except WebSocketDisconnect:
        await room_manager.leave_room(conversation_id, websocket)


async def pubsub_listener():
    pubsub = get_pubsub()
    try:
        await pubsub.psubscribe("conversation:*")
        print("PubSub listener started")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                print("Redis message:", message)  # debug log
                channel = message["channel"]
                data = message["data"]
                conversation_id = channel.replace("conversation:", "")
                await room_manager.broadcast(conversation_id, data)

            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        logger.info("PubSub listener shutting down...")
        await pubsub.close()
        raise
    except Exception as e:
        logger.error(f"PubSub listener error: {e}")
        raise
