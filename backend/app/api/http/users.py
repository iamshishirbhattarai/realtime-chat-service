from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.postgres import get_db
from app.core.redis import is_user_online
from app.models.user import User
from app.schemas.user import UserOut

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


@router.get("/{user_id}/presence")
async def get_user_presence(
    user_id: UUID,
    _: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    online = await is_user_online(str(user_id))
    return {"user_id": user_id, "online": online}
