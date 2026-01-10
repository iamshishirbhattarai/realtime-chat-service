from fastapi import APIRouter

from app.api.http.router import router as http_router
from app.api.ws.websocket import router as ws_router

router = APIRouter()

router.include_router(http_router)
router.include_router(ws_router)
