import asyncio
from uuid import UUID

from firebase_admin import messaging
from sqlalchemy import select

from app.core.firebase import get_firebase_app
from app.core.postgres import AsyncSessionLocal
from app.models.conversation import ConversationParticipant
from app.models.notification_token import NotificationToken


def _send_push_sync(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> None:
    app = get_firebase_app()

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )
            messaging.send(message, app=app)
        except Exception as e:
            continue


async def send_chat_push_for_message(
    conversation_id: UUID,
    message_id: UUID,
    sender_id: UUID,
    sender_name: str,
    content: str,
) -> None:
    async with AsyncSessionLocal() as db:
        participant_rows = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id != sender_id,
            )
        )
        receipent_ids = [row[0] for row in participant_rows.all()]
        if not receipent_ids:
            return

        token_rows = await db.execute(
            select(NotificationToken.token).where(
                NotificationToken.user_id.in_(receipent_ids)
            )
        )
        tokens = list({row[0] for row in token_rows.all()})

    if not tokens:
        return

    body = content.strip() or "Sent an attachment"
    await asyncio.to_thread(
        _send_push_sync,
        tokens,
        sender_name,
        body,
        {
            "type": "chat_message",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "sender_id": str(sender_id),
        },
    )
