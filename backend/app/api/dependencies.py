from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CurrentUser(BaseModel):
    id: str
    email: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),  # noqa: B008
) -> CurrentUser:
    payload = decode_access_token(token)
    if not payload.get("email"):
        raise HTTPException(status_code=401, detail="Invalid token claims")
    return CurrentUser(id=payload["sub"], email=payload["email"])
