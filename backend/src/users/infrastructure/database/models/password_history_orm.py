"""SQLAlchemy ORM model for password history tracking."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .user_orm import UserORM


class PasswordHistoryORM(Base):
    """Tracks user password history for security compliance."""

    __tablename__ = "password_history"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier for the password history entry",
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the user who owns this password entry",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed password value at the time of change",
    )
    password_changed_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc),
        nullable=False,
        doc="When the password was set",
    )

    # Relationship
    user: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="password_history",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PasswordHistoryORM(id={self.id}, "
            f"user_id={self.user_id}, "
            f"password_changed_at={self.password_changed_at})>"
        )
