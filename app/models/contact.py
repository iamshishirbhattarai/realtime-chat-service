from datetime import datetime, timezone

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Contact(Base):
    __tablename__ = "contacts"

    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    contact_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="contacts"
    )
    contact = relationship("User", foreign_keys=[contact_id])


class BlockedContact(Base):
    __tablename__ = "blocked_contacts"

    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    blocked_user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="blocked_contacts"
    )
