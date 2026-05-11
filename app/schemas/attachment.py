from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

AllowedMimeType = Literal[
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/webm",
    "audio/mpeg",
    "audio/ogg",
    "application/pdf",
    "application/zip",
    "text/plain",
]


class AttachmentOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size: int
    download_url: str
    created_at: datetime


class PresignUploadRequest(BaseModel):
    filename: str
    content_type: AllowedMimeType


class PresignUploadResponse(BaseModel):
    object_key: str
    upload_url: str


class ConfirmUploadRequest(BaseModel):
    object_key: str
    filename: str
    content_type: AllowedMimeType
    size: int
