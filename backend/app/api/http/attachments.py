from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.core.minio import (
    generate_presigned_get_url,
    generate_presigned_put_url,
)
from app.core.postgres import get_db
from app.models.attachment import Attachment
from app.schemas.attachment import (
    AttachmentOut,
    ConfirmUploadRequest,
    PresignUploadRequest,
    PresignUploadResponse,
)

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.post("/presign-upload", response_model=PresignUploadResponse)
async def presign_upload(
    body: PresignUploadRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    object_key, upload_url = generate_presigned_put_url(body.filename)
    return PresignUploadResponse(object_key=object_key, upload_url=upload_url)


@router.post(
    "/confirm",
    response_model=AttachmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_upload(
    body: ConfirmUploadRequest,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    attachment = Attachment(
        uploader_id=current_user.id,
        object_key=body.object_key,
        filename=body.filename,
        content_type=body.content_type,
        size=body.size,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return AttachmentOut(
        id=attachment.id,
        filename=attachment.filename,
        content_type=attachment.content_type,
        size=attachment.size,
        download_url=generate_presigned_get_url(attachment.object_key),
        created_at=attachment.created_at,
    )
