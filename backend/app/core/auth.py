from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from jose import jwt, ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | Any, expires_delta: int = None) -> str:
    if expires_delta:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta
        )
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: int = None) -> str:
    if expires_delta:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta
        )
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_refresh_token_expire_minutes
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_refresh_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_refresh_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from err
    except jwt.JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from err

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: missing subject",
        )

    return payload
