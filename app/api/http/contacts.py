from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.postgres import get_db
from app.models.contact import BlockedContact, Contact
from app.schemas.contact import ContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactOut])
async def list_contacts(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    await db.execute(
        delete(Contact).where(
            Contact.user_id == current_user.id,
            Contact.contact_id == contact_id,
        )
    )
    await db.commit()


@router.post("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    db.add(BlockedContact(user_id=current_user.id, blocked_user_id=user_id))
    await db.commit()


@router.delete(
    "/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT
)
async def unblock_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    await db.execute(
        delete(BlockedContact).where(
            BlockedContact.user_id == current_user.id,
            BlockedContact.blocked_user_id == user_id,
        )
    )
    await db.commit()
