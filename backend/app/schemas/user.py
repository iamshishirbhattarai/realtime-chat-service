import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AvatarMimeType = Literal["image/jpeg", "image/png", "image/webp", "image/gif"]


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvatarPresignRequest(BaseModel):
    filename: str
    content_type: AvatarMimeType


class AvatarPresignResponse(BaseModel):
    object_key: str
    upload_url: str


class AvatarConfirmRequest(BaseModel):
    object_key: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
