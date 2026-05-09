import asyncio
import json
from logging import getLogger
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select

from app.api.ws.rooms import ConversationManager
from app.core.auth import decode_access_token
from app.core.postgres import AsyncSessionLocal
from app.core.redis import get_pubsub
from app.models.conversation import ConversationParticipant
from app.models.message import Message

logger = getLogger(__name__)
room_manager = ConversationManager()
router = APIRouter()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket, conversation_id: UUID, token: str = Query(...)
):
    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
        email = payload["email"]
    except HTTPException:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        member = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == UUID(user_id),
            )
        )
        if not member.scalar_one_or_none():
            await websocket.close(code=4003)
            return

    await room_manager.join_conversation(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # save message
            async with AsyncSessionLocal() as db:
                msg = Message(
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    content=data,
                )
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

            payload_out = json.dumps(
                {
                    "sender_id": user_id,
                    "email": email,
                    "content": data,
                    "created_at": msg.created_at.isoformat(),
                }
            )

            await room_manager.publish(conversation_id, payload_out)
    except WebSocketDisconnect:
        await room_manager.leave_conversation(conversation_id, websocket)


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
