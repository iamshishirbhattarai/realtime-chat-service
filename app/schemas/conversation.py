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
    joined_at: datetime
    last_read_message_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    type: ConversationType
    name: str | None
    created_at: datetime
    participants: list[ParticipantOut]

    model_config = {"from_attributes": True}
