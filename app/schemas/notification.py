from pydantic import BaseModel


class NotificationTokenUpsertRequest(BaseModel):
    token: str
    platform: str = "web"


class NotificationTokenDeleteRequest(BaseModel):
    token: str
