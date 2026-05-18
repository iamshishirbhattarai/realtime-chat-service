from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, get_current_user
from app.core.minio import generate_presigned_get_url
from app.core.postgres import get_db
from app.models.contact import (
    BlockedContact,
    Contact,
)
from app.models.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationStatus,
    ConversationType,
)
from app.models.message import Message
from app.models.user import User
from app.schemas.attachment import AttachmentOut
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    MarkReadRequest,
)
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

    current_user_uuid = UUID(current_user.id)
    all_participant_ids = set(body.participant_ids) | {current_user_uuid}

    # reject self-conversation
    if (
        body.type == ConversationType.DIRECT
        and body.participant_ids[0] == current_user_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a direct conversation with yourself",
        )

    # validate all participant UUIDs exist
    result = await db.execute(
        select(User.id).where(User.id.in_(all_participant_ids))
    )
    found_ids = {row[0] for row in result.all()}
    missing = all_participant_ids - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users not found: {[str(m) for m in missing]}",
        )

    # reject duplicate direct conversations
    if body.type == ConversationType.DIRECT:
        other_user_id = body.participant_ids[0]

        is_blocked = await db.execute(
            select(BlockedContact).where(
                or_(
                    and_(
                        BlockedContact.user_id == current_user_uuid,
                        BlockedContact.blocked_user_id == other_user_id,
                    ),
                    and_(
                        BlockedContact.user_id == other_user_id,
                        BlockedContact.blocked_user_id == current_user_uuid,
                    ),
                )
            )
        )
        if is_blocked.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot send message to this user",
            )

        is_contact = await db.execute(
            select(Contact).where(
                Contact.user_id == current_user_uuid,
                Contact.contact_id == other_user_id,
            )
        )
        conv_status = (
            ConversationStatus.ACCEPTED
            if is_contact.scalar_one_or_none()
            else ConversationStatus.PENDING
        )
        existing = await db.execute(
            select(Conversation.id)
            .join(ConversationParticipant)
            .where(
                Conversation.type == ConversationType.DIRECT,
                ConversationParticipant.user_id == current_user_uuid,
                Conversation.id.in_(
                    select(ConversationParticipant.conversation_id).where(
                        ConversationParticipant.user_id == other_user_id
                    )
                ),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Direct conversation with this user already exists",
            )
    else:
        conv_status = ConversationStatus.ACCEPTED

    conversation = Conversation(
        type=body.type, name=body.name, status=conv_status
    )
    db.add(conversation)
    await db.flush()

    for pid in all_participant_ids:
        db.add(
            ConversationParticipant(
                conversation_id=conversation.id, user_id=pid
            )
        )

    await db.commit()
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation.id)
        .options(selectinload(Conversation.participants).selectinload(ConversationParticipant.user))
    )
    return ConversationOut.from_conversation(result.scalar_one())


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(
            ConversationParticipant.user_id == UUID(current_user.id),
            Conversation.status == ConversationStatus.ACCEPTED,
        )
        .options(
            selectinload(Conversation.participants).selectinload(
                ConversationParticipant.user
            )
        )
    )
    return [ConversationOut.from_conversation(c) for c in result.scalars().all()]


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: UUID,
    limit: int = 50,
    before: datetime | None = None,
    before_id: UUID | None = None,
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

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.attachments))
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )

    if before and before_id:
        query = query.where(
            or_(
                Message.created_at < before,
                and_(
                    Message.created_at == before,
                    Message.id < before_id,
                ),
            )
        )
    elif before:
        query = query.where(Message.created_at < before)

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        MessageOut(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            content=msg.content,
            created_at=msg.created_at,
            attachments=[
                AttachmentOut(
                    id=att.id,
                    filename=att.filename,
                    content_type=att.content_type,
                    size=att.size,
                    download_url=generate_presigned_get_url(att.object_key),
                    created_at=att.created_at,
                )
                for att in msg.attachments
            ],
        )
        for msg in messages
    ]


@router.post(
    "/{conversation_id}/participants",
    status_code=status.HTTP_204_NO_CONTENT,
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

    if not await db.get(User, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.add(
        ConversationParticipant(
            conversation_id=conversation_id, user_id=user_id
        )
    )
    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a participant",
        ) from err


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_conversation_read(
    conversation_id: UUID,
    body: MarkReadRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    msg = await db.get(Message, body.last_read_message_id)
    if not msg or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid last_read_message_id",
        )
    member = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == UUID(current_user.id),
        )
    )
    member = member.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant of this conversation",
        )

    member.last_read_message_id = body.last_read_message_id
    await db.commit()


@router.get("/requests", response_model=list[ConversationOut])
async def list_conversation_requests(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(
            ConversationParticipant.user_id == UUID(current_user.id),
            Conversation.status == ConversationStatus.PENDING,
        )
        .options(
            selectinload(Conversation.participants).selectinload(
                ConversationParticipant.user
            )
        )
    )
    convos = result.scalars().all()
    return [ConversationOut.from_conversation(c) for c in convos]


@router.post(
    "/{conversation_id}/accept", status_code=status.HTTP_204_NO_CONTENT
)
async def accept_conversation_request(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.status != ConversationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation request not found",
        )

    participants = await db.execute(
        select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id
        )
    )
    participant_ids = [row[0] for row in participants.all()]

    for uid in participant_ids:
        for cid in participant_ids:
            if uid != cid:
                db.add(Contact(user_id=uid, contact_id=cid))

    conv.status = ConversationStatus.ACCEPTED
    await db.commit()
