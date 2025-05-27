"""SQLAlchemy ORM models for tokens."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base
from src.users.domain.value_objects.token_value_objects import TokenStatus, TokenType

if TYPE_CHECKING:
    from src.users.infrastructure.database.models.user_orm import UserORM


class TokenORM(Base):
    """ORM model for storing authentication and authorization tokens.

    This model maps to the 'tokens' table in the database.
    """

    __tablename__ = "tokens"
    __table_args__ = (
        # Index for faster lookups by token string
        Index("idx_tokens_token", "token"),
        # Index for finding active tokens for a user
        Index("idx_tokens_user_status", "user_id", "status"),
        # Index for token expiration checks
        Index("idx_tokens_expires_at", "expires_at"),
    )

    # Token string (hashed for security)
    token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
        doc="Hashed token string for security",
    )

    # Token type (access, refresh, etc.)
    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType, name="token_type_enum"),
        nullable=False,
        doc="Type of the token (access, refresh, etc.)",
    )

    # Token status
    status: Mapped[TokenStatus] = mapped_column(
        Enum(TokenStatus, name="token_status_enum"),
        nullable=False,
        default=TokenStatus.ACTIVE,
        doc="Current status of the token",
    )

    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user this token belongs to",
    )
    user: Mapped[UserORM] = relationship("UserORM", back_populates="tokens")

    # Token metadata
    scopes: Mapped[list[str]] = mapped_column(
        "scopes",
        type_=String(255),
        nullable=False,
        default=list,
        doc="Comma-separated list of scopes this token has access to",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="When the token was created",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When the token expires",
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the token was last used",
    )

    # Security info
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        doc="IP address that created the token",
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="User agent that created the token",
    )

    # For refresh tokens, store the parent access token ID
    parent_token_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=True,
        doc="For refresh tokens, the ID of the access token this refreshes",
    )

    # For refresh tokens, store the next token in the chain (if any)
    next_token_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="SET NULL"),
        nullable=True,
        doc="Next token in the refresh chain (if any)",
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the token was revoked (if applicable)",
    )

    revocation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Reason for revocation (if applicable)",
    )

    def __repr__(self) -> str:
        return (
            f"<TokenORM(id={self.id}, "
            f"type={self.token_type}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
            f"expires_at={self.expires_at.isoformat()})>"
        )
