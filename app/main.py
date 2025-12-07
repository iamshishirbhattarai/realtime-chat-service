from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.ws.websocket import router as ws_router
from app.core.pubsub import init_pubsub, shutdown_pubsub


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PubSub on startup
    await init_pubsub(app)
    yield
    # Shutdown PubSub on shutdown
    await shutdown_pubsub(app)


app = FastAPI(lifespan=lifespan)
app.include_router(ws_router)
