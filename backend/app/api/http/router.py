from fastapi import APIRouter

from .attachments import router as attachments_router
from .conversation import router as conversation_router
from .login import router as login_router
from .users import router as users_router

router = APIRouter()

router.include_router(login_router)
router.include_router(conversation_router)
router.include_router(users_router)
router.include_router(attachments_router)
