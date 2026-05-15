import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.attachment import AttachmentOut


class WSEventType(str, enum.Enum):
    MESSAGE = "message"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"
    PRESENCE = "presence"
    READ = "read"


class WSIncomingEvent(BaseModel):
    type: WSEventType
    content: str | None = None
    attachment_ids: list[UUID] = Field(default_factory=list)
    message_id: UUID | None = None


class WSMessageEvent(BaseModel):
    type: WSEventType = WSEventType.MESSAGE
    message_id: UUID
    user_id: UUID
    content: str
    attachments: list[AttachmentOut] = Field(default_factory=list)
    created_at: datetime


class WSTypingEvent(BaseModel):
    type: WSEventType = WSEventType.TYPING
    user_id: UUID


class WSPresenceEvent(BaseModel):
    type: WSEventType = WSEventType.PRESENCE
    user_id: UUID
    status: str


class WSReadEvent(BaseModel):
    type: WSEventType = WSEventType.READ
    user_id: UUID
    conversation_id: UUID
    last_read_message_id: UUID
