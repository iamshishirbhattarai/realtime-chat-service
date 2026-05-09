import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    UUID as SQLAlchemyUUID,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ConversationType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(Enum(ConversationType), nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    participants = relationship(
        "ConversationParticipant", back_populates="conversation"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        order_by="Message.created_at",
    )


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("conversations.id"),
        primary_key=True,
    )
    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
    )
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="conversations")
