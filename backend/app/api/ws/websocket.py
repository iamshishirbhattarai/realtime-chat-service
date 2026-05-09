import asyncio
from logging import getLogger
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import ValidationError
from sqlalchemy import select

from app.api.ws.rooms import ConversationManager
from app.core.auth import decode_access_token
from app.core.postgres import AsyncSessionLocal
from app.core.redis import (
    get_pubsub,
    refresh_user_presence,
    set_user_offline,
    set_user_online,
)
from app.models.conversation import ConversationParticipant
from app.models.message import Message
from app.schemas.ws import (
    WSEventType,
    WSIncomingEvent,
    WSMessageEvent,
    WSPresenceEvent,
    WSTypingEvent,
)

logger = getLogger(__name__)
room_manager = ConversationManager()
router = APIRouter()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket, conversation_id: UUID, token: str = Query(...)
):
    try:
        payload = decode_access_token(token)
        user_uuid = UUID(payload["sub"])
    except HTTPException:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        member = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_uuid,
            )
        )
        if not member.scalar_one_or_none():
            await websocket.close(code=4003)
            return

    conv_id_str = str(conversation_id)
    await room_manager.join_conversation(conv_id_str, websocket)
    await set_user_online(str(user_uuid))
    await room_manager.publish(
        conv_id_str,
        WSPresenceEvent(user_id=user_uuid, status="online").model_dump_json(),
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = WSIncomingEvent.model_validate_json(data)
            except ValidationError:
                logger.debug("Invalid WS payload from %s: %s", user_uuid, data)
                continue

            await refresh_user_presence(str(user_uuid))

            if event.type in (WSEventType.TYPING, WSEventType.STOP_TYPING):
                await room_manager.publish(
                    conv_id_str,
                    WSTypingEvent(
                        type=event.type, user_id=user_uuid
                    ).model_dump_json(),
                )

            elif event.type == WSEventType.MESSAGE:
                content = (event.content or "").strip()
                if not content:
                    continue

                async with AsyncSessionLocal() as db:
                    msg = Message(
                        conversation_id=conversation_id,
                        sender_id=user_uuid,
                        content=content,
                    )
                    db.add(msg)
                    await db.commit()
                    await db.refresh(msg)

                await room_manager.publish(
                    conv_id_str,
                    WSMessageEvent(
                        user_id=user_uuid,
                        content=content,
                        created_at=msg.created_at,
                    ).model_dump_json(),
                )

    except WebSocketDisconnect:
        pass
    finally:
        await room_manager.leave_conversation(conv_id_str, websocket)
        await set_user_offline(str(user_uuid))
        await room_manager.publish(
            conv_id_str,
            WSPresenceEvent(
                user_id=user_uuid, status="offline"
            ).model_dump_json(),
        )


async def pubsub_listener():
    pubsub = get_pubsub()
    try:
        await pubsub.psubscribe("conversation:*")
        print("PubSub listener started")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
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
