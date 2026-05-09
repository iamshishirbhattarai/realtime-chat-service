from fastapi import APIRouter

from .conversation import router as conversation_router
from .login import router as login_router
from .users import router as users_router

router = APIRouter()

router.include_router(login_router)
router.include_router(conversation_router)
router.include_router(users_router)
