import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.attachment import AttachmentOut


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    attachments: list[AttachmentOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}
