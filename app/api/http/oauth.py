import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.postgres import get_db
from app.models.oauth_account import UserOAuthAccount
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _make_state() -> str:
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def _verify_state(state: str) -> None:
    try:
        jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except PyJWTError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        ) from err


@router.get("/google/login")
async def google_login():
    state = _make_state()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return {"url": f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"}


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    _verify_state(state)

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code with Google",
            )

        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_resp.json()['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user info from Google",
            )

    google_user = userinfo_resp.json()
    provider_user_id = google_user["sub"]
    email = google_user["email"]
    name = google_user.get("name") or email.split("@")[0]
    picture = google_user.get("picture")

    # 1. Existing OAuth link → get its user
    result = await db.execute(
        select(UserOAuthAccount).where(
            UserOAuthAccount.provider == "google",
            UserOAuthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        user = await db.get(User, oauth_account.user_id)
    else:
        # 2. Same email already registered (password signup) → link account
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # 3. Brand new user
            user = User(name=name, email=email, avatar_url=picture)
            db.add(user)
            await db.flush()  # populate user.id before FK insert

        db.add(
            UserOAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=provider_user_id,
            )
        )

    if picture and not user.avatar_url:
        user.avatar_url = picture

    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(
            subject=user.id, email=user.email, name=user.name
        ),
        "refresh_token": create_refresh_token(subject=user.id),
        "token_type": "bearer",
    }
