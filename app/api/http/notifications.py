from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.postgres import get_db
from app.models.notification_token import NotificationToken
from app.schemas.notification import (
    NotificationTokenDeleteRequest,
    NotificationTokenUpsertRequest,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def upsert_notification_token(
    body: NotificationTokenUpsertRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(NotificationToken).where(
            NotificationToken.token == body.token,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.user_id = current_user.id
        existing.device_id = body.device_id
        existing.platform = body.platform
        existing.last_seen_at = now
    else:
        new_token = NotificationToken(
            user_id=current_user.id,
            token=body.token,
            device_id=body.device_id,
            platform=body.platform,
            created_at=now,
            last_seen_at=now,
        )
        db.add(new_token)

    await db.commit()


@router.delete("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_token(
    body: NotificationTokenDeleteRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    await db.execute(
        delete(NotificationToken).where(
            NotificationToken.token == body.token,
            NotificationToken.user_id == current_user.id,
        )
    )
    await db.commit()
