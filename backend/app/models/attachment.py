from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
    )
    uploader_id = Column(
        SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    object_key = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    message = relationship("Message", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")
