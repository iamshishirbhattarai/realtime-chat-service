from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.minio import generate_presigned_put_url, remove_object
from app.core.postgres import get_db
from app.core.redis import is_user_online
from app.models.user import User
from app.schemas.user import (
    AvatarConfirmRequest,
    AvatarPresignRequest,
    AvatarPresignResponse,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
async def search_users(
    q: str,
    _: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(User)
        .where(
            or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )
        .limit(20)
    )
    return result.scalars().all()


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    user = await db.get(User, UUID(current_user.id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/me", response_model=UserOut)
async def update_profile(
    body: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if not body.name and not body.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nothing to update",
        )

    user = await db.get(User, UUID(current_user.id))

    if body.name:
        user.name = body.name
    if body.email:
        user.email = body.email

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use",
        )

    await db.refresh(user)
    return user


@router.post("/me/avatar/presign", response_model=AvatarPresignResponse)
async def presign_avatar_upload(
    body: AvatarPresignRequest,
    _: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    object_key, upload_url = generate_presigned_put_url(body.filename)
    return AvatarPresignResponse(object_key=object_key, upload_url=upload_url)


@router.post("/me/avatar/confirm", response_model=UserOut)
async def confirm_avatar_upload(
    body: AvatarConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    user = await db.get(User, UUID(current_user.id))

    if user.avatar_url:
        remove_object(user.avatar_url)

    user.avatar_url = body.object_key
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}/presence")
async def get_user_presence(
    user_id: UUID,
    _: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    online = await is_user_online(str(user_id))
    return {"user_id": user_id, "online": online}
