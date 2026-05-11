from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversations = relationship(
        "ConversationParticipant", back_populates="user"
    )
    messages = relationship("Message", back_populates="sender")
    attachments = relationship("Attachment", back_populates="uploader")
