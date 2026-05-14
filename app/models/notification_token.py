from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class NotificationToken(Base):
    __tablename__ = "notification_tokens"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    token = Column(String, nullable=False, unique=True)
    platform = Column(String, nullable=False, default="web")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="notification_tokens")
