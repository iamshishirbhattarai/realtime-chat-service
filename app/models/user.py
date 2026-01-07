from uuid import uuid4

from datetime import datetime, timezone

from sqlalchemy import Column, String, UUID as SQLAlchemyUUID
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(
        String,
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
