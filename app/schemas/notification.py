from uuid import UUID

from pydantic import BaseModel


class NotificationTokenUpsertRequest(BaseModel):
    token: str
    device_id: UUID
    platform: str = "web"


class NotificationTokenDeleteRequest(BaseModel):
    token: str
