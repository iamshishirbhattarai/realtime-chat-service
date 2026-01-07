import pytest

@pytest.fixture(scope='session')
def db_connection():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('postgresql+asyncpg://user:password@localhost/dbname')
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()