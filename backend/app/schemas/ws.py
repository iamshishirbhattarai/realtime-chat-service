import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WSEventType(str, enum.Enum):
    MESSAGE = "message"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"
    PRESENCE = "presence"


class WSIncomingEvent(BaseModel):
    type: WSEventType
    content: str | None = None


class WSMessageEvent(BaseModel):
    type: WSEventType = WSEventType.MESSAGE
    user_id: UUID
    content: str
    created_at: datetime


class WSTypingEvent(BaseModel):
    type: WSEventType
    user_id: UUID


class WSPresenceEvent(BaseModel):
    type: WSEventType = WSEventType.PRESENCE
    user_id: UUID
    status: str
