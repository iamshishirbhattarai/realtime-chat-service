import pytest


@pytest.fixture(scope="session")
async def db_connection():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(
        "postgresql+asyncpg://user:password@localhost/dbname"
    )
    Session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with Session() as session:
        yield session

    await engine.dispose()
