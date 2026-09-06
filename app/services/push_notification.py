import asyncio
import logging
from uuid import UUID

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from sqlalchemy import delete, select

from app.core.firebase import get_firebase_app
from app.core.postgres import AsyncSessionLocal
from app.core.redis import is_user_online
from app.models.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationType,
)
from app.models.notification_token import NotificationToken

logger = logging.getLogger(__name__)


def _send_multicast_sync(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str],
) -> list[str]:
    app = get_firebase_app()

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        tokens=tokens,
    )
    response = messaging.send_each_for_multicast(message, app=app)

    dead_tokens: list[str] = []
    for token, resp in zip(tokens, response.responses, strict=True):
        if resp.success:
            continue
        exc = resp.exception
        if isinstance(exc, messaging.UnregisteredError):
            dead_tokens.append(token)
            continue
        if isinstance(exc, FirebaseError) and exc.code in (
            "INVALID_ARGUMENT",
            "NOT_FOUND",
        ):
            dead_tokens.append(token)
    return dead_tokens


async def send_chat_push_for_message(
    conversation_id: UUID,
    message_id: UUID,
    sender_id: UUID,
    sender_name: str,
    content: str,
) -> None:
    try:
        async with AsyncSessionLocal() as db:
            conversation = await db.get(Conversation, conversation_id)
            if not conversation:
                return

            participant_rows = await db.execute(
                select(ConversationParticipant.user_id).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id != sender_id,
                )
            )
            recipient_ids = [row[0] for row in participant_rows.all()]
            online_statuses = await asyncio.gather(
                *(is_user_online(str(uid)) for uid in recipient_ids)
            )
            recipient_ids = [
                uid
                for uid, online in zip(
                    recipient_ids, online_statuses, strict=True
                )
                if not online
            ]
            if not recipient_ids:
                return

            token_rows = await db.execute(
                select(NotificationToken.token).where(
                    NotificationToken.user_id.in_(recipient_ids)
                )
            )
            tokens = list({row[0] for row in token_rows.all()})

        if not tokens:
            return

        message_body = content.strip() or "Sent an attachment"

        if conversation.type == ConversationType.GROUP and conversation.name:
            title = conversation.name
            body = f"{sender_name}: {message_body}"
        else:
            title = sender_name
            body = message_body

        dead_tokens = await asyncio.to_thread(
            _send_multicast_sync,
            tokens,
            title,
            body,
            {
                "type": "chat_message",
                "conversation_id": str(conversation_id),
                "message_id": str(message_id),
                "sender_id": str(sender_id),
            },
        )
        if dead_tokens:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    delete(NotificationToken).where(
                        NotificationToken.token.in_(dead_tokens)
                    )
                )
                await db.commit()
    except Exception:
        logger.exception(
            "Error sending push notification for message %s", message_id
        )
