import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.minio import ensure_bucket_exists
from app.core.pubsub import init_pubsub, shutdown_pubsub

_ALEMBIC_CFG = Config(Path(__file__).parent.parent / "alembic.ini")


def _run_migrations() -> None:
    command.upgrade(_ALEMBIC_CFG, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(_run_migrations)
    ensure_bucket_exists()
    await init_pubsub(app)
    yield
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
