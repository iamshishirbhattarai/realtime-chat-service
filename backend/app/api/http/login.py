from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.core.postgres import get_db
from app.core.redis import blacklist_token, is_token_blacklisted
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/signup")
async def signup(
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008, FBT001
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(User).filter(User.email == form_data.username)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=form_data.username,
        hashed_password=hash_password(form_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"msg": "User created successfully"}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=user.id, email=user.email)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(
    request: RefreshRequest,
):
    if await is_token_blacklisted(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    payload = decode_refresh_token(request.refresh_token)
    user_id = payload["sub"]
    ttl = payload["exp"] - int(datetime.now(timezone.utc).timestamp())
    await blacklist_token(request.refresh_token, max(ttl, 1))

    email = payload.get("email", "")
    new_access_token = create_access_token(subject=user_id, email=email)
    new_refresh_token = create_refresh_token(subject=user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    body: RefreshRequest,
):
    payload = decode_refresh_token(body.refresh_token)
    ttl = payload["exp"] - int(datetime.now(timezone.utc).timestamp())
    await blacklist_token(body.refresh_token, max(ttl, 1))
    return {"msg": "Logged out successfully"}
