from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.pubsub import init_pubsub, shutdown_pubsub


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PubSub on startup
    await init_pubsub(app)
    yield
    # Shutdown PubSub on shutdown
    await shutdown_pubsub(app)


app = FastAPI(lifespan=lifespan)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
