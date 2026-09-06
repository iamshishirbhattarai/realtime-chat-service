import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.conversation import ConversationType


class ConversationCreate(BaseModel):
    type: ConversationType
    name: str | None = None  # required if group
    participant_ids: list[
        uuid.UUID
    ]  # for direct: one id; for group: one or more


class MarkReadRequest(BaseModel):
    last_read_message_id: uuid.UUID


class ParticipantOut(BaseModel):
    user_id: uuid.UUID
    name: str = ""
    email: str = ""
    avatar_url: str | None = None
    joined_at: datetime
    last_read_message_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_participant(cls, p: object) -> "ParticipantOut":
        return cls(
            user_id=p.user_id,
            name=p.user.name if p.user else "",
            email=p.user.email if p.user else "",
            avatar_url=p.user.avatar_url if p.user else None,
            joined_at=p.joined_at,
            last_read_message_id=p.last_read_message_id,
        )


class ConversationOut(BaseModel):
    id: uuid.UUID
    type: ConversationType
    name: str | None
    created_at: datetime
    participants: list[ParticipantOut]

    model_config = {"from_attributes": True}

    @classmethod
    def from_conversation(cls, c: object) -> "ConversationOut":
        return cls(
            id=c.id,
            type=c.type,
            name=c.name,
            created_at=c.created_at,
            participants=[ParticipantOut.from_participant(p) for p in c.participants],
        )
