from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    UUID as SQLAlchemyUUID,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class UserOAuthAccount(Base):
    __tablename__ = "user_oauth_accounts"

    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )
