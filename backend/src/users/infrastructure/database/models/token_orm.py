"""SQLAlchemy ORM models for tokens."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base
from src.users.domain.entities.token import Token
from src.users.domain.value_objects.token_value_objects import TokenStatus

if TYPE_CHECKING:
    from .user_orm import UserORM


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

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Primary key for the token",
    )

    # Token string (hashed for security)
    token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
        doc="Hashed token string for security",
    )

    # Token type (access, refresh, etc.)
    token_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Type of the token (access, refresh, etc.)",
    )

    # Token status
    status: Mapped[str] = mapped_column(
        String(32),
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
    user: Mapped["UserORM"] = relationship(
        "UserORM", back_populates="tokens", lazy="selectin"
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

    # Scopes associated with the token
    scopes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Comma-separated list of scopes",
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

    # Revocation info
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

    # Additional metadata
    meta: Mapped[Dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),
        nullable=True,
        doc="Additional metadata for the token",
        default=dict,
    )

    def __repr__(self) -> str:
        return (
            f"<TokenORM(id={self.id}, "
            f"type={self.token_type}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
            f"expires_at={self.expires_at.isoformat()})>"
        )

    @classmethod
    def from_entity(cls, token: "Token") -> "TokenORM":
        """Create ORM model from domain model.

        Args:
            token: The domain model token instance

        Returns:
            TokenORM: A new ORM instance with data from the domain model
        """

        return cls(
            id=token.id,
            token=token.token,
            token_type=token.token_type,
            user_id=token.user_id,
            status=token.status,
            scopes=(
                ",".join(sorted(list(token.scopes.scopes)))
                if token.scopes and token.scopes.scopes
                else None
            ),
            created_at=token.created_at,
            expires_at=token.expiry.expires_at,
            last_used_at=token.last_used_at,
            ip_address=token.ip_address,
            user_agent=token.user_agent,
            parent_token_id=token.parent_token_id,
            next_token_id=token.next_token_id,
            revoked_at=token.revoked_at,
            revocation_reason=token.revocation_reason,
            meta=token.meta or {},
        )

    def to_entity(self) -> "Token":
        """Convert ORM model to domain model.

        Returns:
            Token: A domain model instance with data from the ORM
        """
        # Prepare scopes. Assumes self.scopes is a comma-separated string attribute
        # on the ORM instance. If not present or empty, scopes_set remains None.
        scopes_set: Optional[set[str]] = None
        if self.scopes:
            scopes_list = [
                s.strip() for s in self.scopes.split(",") if s.strip()
            ]
            if scopes_list:
                scopes_set = set(scopes_list)
        
        token_entity = Token.create(
            token_str=self.token,
            user_id=str(self.user_id),
            token_type=self.token_type,
            expires_at=self.expires_at,
            scopes=scopes_set,
            user_agent=self.user_agent,
            ip_address=self.ip_address,
            parent_token_id=self.parent_token_id,
            meta=self.meta or {},
        )

        # Manually set fields not handled by Token.create() or to override defaults.
        # Token is a frozen dataclass, so use object.__setattr__.

        if self.id is not None:
            object.__setattr__(token_entity, "id", str(self.id))
        
        object.__setattr__(token_entity, "created_at", self.created_at)
        object.__setattr__(token_entity, "status", self.status)
        
        if self.last_used_at is not None:
            object.__setattr__(token_entity, "last_used_at", self.last_used_at)
        
        if self.next_token_id is not None:
            object.__setattr__(token_entity, "next_token_id", self.next_token_id)
            
        if self.revoked_at is not None:
            object.__setattr__(token_entity, "revoked_at", self.revoked_at)
            
        if self.revocation_reason is not None:
            object.__setattr__(
                token_entity, "revocation_reason", self.revocation_reason
            )

        return token_entity
