import uuid
from datetime import datetime

from pydantic import BaseModel


class ContactOut(BaseModel):
    contact_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class BlockRequest(BaseModel):
    user_id: uuid.UUID
