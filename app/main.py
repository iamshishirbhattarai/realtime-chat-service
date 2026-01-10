from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.pubsub import init_pubsub, shutdown_pubsub
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PubSub on startup
    await init_pubsub(app)
    yield
    # Shutdown PubSub on shutdown
    await shutdown_pubsub(app)


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
