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
from app.core.minio import generate_presigned_get_url
from app.core.postgres import AsyncSessionLocal
from app.core.redis import (
    get_pubsub,
    refresh_user_presence,
    set_user_offline,
    set_user_online,
)
from app.models.attachment import Attachment
from app.models.conversation import ConversationParticipant
from app.models.message import Message
from app.schemas.attachment import AttachmentOut
from app.schemas.ws import (
    WSEventType,
    WSIncomingEvent,
    WSMessageEvent,
    WSPresenceEvent,
    WSReadEvent,
    WSTypingEvent,
)
from app.services.push_notification import send_chat_push_for_message

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
            elif event.type == WSEventType.READ:
                if not event.last_read_message_id:
                    continue
                async with AsyncSessionLocal() as db:
                    msg = await db.get(Message, event.last_read_message_id)
                    if not msg or msg.conversation_id != conversation_id:
                        continue
                    participant = await db.execute(
                        select(ConversationParticipant).where(
                            ConversationParticipant.conversation_id
                            == conversation_id,
                            ConversationParticipant.user_id == user_uuid,
                        )
                    )
                    p = participant.scalar_one_or_none()
                    if p:
                        p.last_read_message_id = event.last_read_message_id
                        await db.commit()
                        await room_manager.publish(
                            conv_id_str,
                            WSReadEvent(
                                user_id=user_uuid,
                                conversation_id=conversation_id,
                                last_read_message_id=event.last_read_message_id,
                            ).model_dump_json(),
                        )
            elif event.type == WSEventType.MESSAGE:
                content = (event.content or "").strip()
                if not content and not event.attachment_ids:
                    continue

                async with AsyncSessionLocal() as db:
                    msg = Message(
                        conversation_id=conversation_id,
                        sender_id=user_uuid,
                        content=content,
                    )
                    db.add(msg)
                    await db.flush()

                    attachment_outs = []
                    if event.attachment_ids:
                        result = await db.execute(
                            select(Attachment).where(
                                Attachment.id.in_(event.attachment_ids),
                                Attachment.uploader_id == user_uuid,
                                Attachment.message_id.is_(None),
                            )
                        )
                        for att in result.scalars().all():
                            att.message_id = msg.id
                            attachment_outs.append(
                                AttachmentOut(
                                    id=att.id,
                                    filename=att.filename,
                                    content_type=att.content_type,
                                    size=att.size,
                                    download_url=generate_presigned_get_url(
                                        att.object_key
                                    ),
                                    created_at=att.created_at,
                                )
                            )

                    await db.commit()
                    await db.refresh(msg)

                await room_manager.publish(
                    conv_id_str,
                    WSMessageEvent(
                        message_id=msg.id,
                        user_id=user_uuid,
                        content=content,
                        attachments=attachment_outs,
                        created_at=msg.created_at,
                    ).model_dump_json(),
                )
                try:
                    asyncio.create_task(
                        send_chat_push_for_message(
                            conversation_id=conversation_id,
                            message_id=msg.id,
                            sender_id=user_uuid,
                            sender_name=payload.get("name", "Unknown"),
                            content=content,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to send push notification: {e}")
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
