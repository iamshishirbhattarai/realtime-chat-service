from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.postgres import get_db
from app.models.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationType,
)
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationOut
from app.schemas.message import MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationOut)
async def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if body.type == ConversationType.GROUP and not body.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group conversations require a name",
        )

    if body.type == ConversationType.DIRECT and len(body.participant_ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct conversations require exactly one participant",
        )

    conversation = Conversation(
        type=body.type,
        name=body.name,
    )
    db.add(conversation)
    await db.flush()  # Get conversation.id

    all_participant_ids = set(body.participant_ids) | {UUID(current_user.id)}
    for pid in all_participant_ids:
        db.add(
            ConversationParticipant(
                conversation_id=conversation.id, user_id=pid
            )
        )

    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == UUID(current_user.id))
    )
    conversations = result.scalars().all()
    return conversations


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: UUID,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[MessageOut]:
    member = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == UUID(current_user.id),
        )
    )
    if not member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant of this conversation",
        )

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post(
    "/{conversation_id}/participants", status_code=status.HTTP_204_NO_CONTENT
)
async def add_participant(
    conversation_id: UUID,
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.type != ConversationType.GROUP:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found",
        )

    db.add(
        ConversationParticipant(
            conversation_id=conversation_id, user_id=user_id
        )
    )
    await db.commit()
