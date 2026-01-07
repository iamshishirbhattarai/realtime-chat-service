from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.postgres_url, echo=True, future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
