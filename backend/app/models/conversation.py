from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    UUID as SQLAlchemyUUID,
)
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="conversations")


class Message(Base):
    __tablename__ = "messages"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    sender = Column(String, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("Conversation", back_populates="messages")
