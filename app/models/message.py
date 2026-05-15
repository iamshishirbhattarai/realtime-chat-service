from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy import Column, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "ix_messages_conversation_created_at",
            "conversation_id",
            "created_at",
        ),
    )

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    sender_id = Column(
        SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    attachments = relationship(
        "Attachment", back_populates="message", cascade="all, delete-orphan"
    )
