"""Token domain model for authentication and authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, final
from uuid import UUID, uuid4

from src.users.domain.value_objects.token_value_objects import (
    TokenExpiry,
    TokenScope,
    TokenStatus,
    TokenString,
    TokenType,
)


@final
@dataclass(frozen=True)
class Token:
    """Immutable domain entity representing an authentication/authorization token.

    This model enforces business rules and invariants related to token management,
    including token relationships, validation, and lifecycle management.

    Attributes:
        token: The token string value object (hashed or encrypted)
        user_id: ID of the user this token belongs to
        token_type: Type of the token (access, refresh, etc.)
        expiry: Token expiration information
        created_at: When the token was created (UTC)
        last_used_at: When the token was last used (UTC, optional)
        status: Current status of the token (active, revoked, etc.)
        user_agent: User agent that created the token (optional)
        ip_address: IP address that created the token (optional)
        scopes: Token scope information
        parent_token_id: For refresh tokens, the ID of the access token this refreshes
        next_token_id: Next token in the refresh chain (for refresh token rotation)
        revoked_at: When the token was revoked (UTC, optional)
        revocation_reason: Reason for revocation (optional)
    """

    # Core token data (required fields)
    token: TokenString
    user_id: str
    token_type: TokenType
    expiry: TokenExpiry

    # Optional fields with defaults
    id: Optional[str] = None
    status: TokenStatus = field(default=TokenStatus.ACTIVE)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), compare=False
    )
    last_used_at: Optional[datetime] = field(default=None, compare=False)

    # Token relationships
    parent_token_id: Optional[UUID] = field(default=None, compare=False)
    next_token_id: Optional[UUID] = field(default=None, compare=False)

    # Security metadata
    user_agent: Optional[str] = field(default=None, compare=False)
    ip_address: Optional[str] = field(default=None, compare=False)
    scopes: TokenScope = field(default_factory=TokenScope, compare=False)

    # Revocation info
    revoked_at: Optional[datetime] = field(default=None, compare=False)
    revocation_reason: Optional[str] = field(default=None, compare=False)

    # Additional metadata
    meta: Dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def create(
        cls,
        token: TokenString,
        user_id: str,
        token_type: TokenType,
        expiry: TokenExpiry,
        scopes: Optional[set[str]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Token:
        """Create a new token instance.

        Args:
            token: The token string value object
            user_id: ID of the user this token belongs to
            token_type: Type of the token (access, refresh, etc.)
            expiry: When the token expires
            scopes: Set of scopes this token has access to
            user_agent: User agent that created the token
            ip_address: IP address that created the token
            meta: Additional metadata for the token

        Returns:
            Token: A new token instance
        """
        now = datetime.now(timezone.utc)
        # Create the token with all provided parameters
        token_instance = cls(
            token=token,
            user_id=user_id,
            token_type=token_type,
            expiry=expiry,
            scopes=TokenScope(scopes or set()),
            user_agent=user_agent,
            ip_address=ip_address,
            meta=meta or {},
            created_at=now,
        )
        return token_instance

    # Properties
    @property
    def expires_at(self) -> datetime:
        """Get the expiration time of the token.

        Returns:
            datetime: When the token expires in UTC
        """
        return self.expiry.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired.

        Returns:
            bool: True if the token has expired, False otherwise
        """
        return self.expiry.is_expired

    @property
    def is_revoked(self) -> bool:
        """Check if the token has been revoked.

        Returns:
            bool: True if the token is revoked, False otherwise
        """
        return self.status == TokenStatus.REVOKED or self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (active, not expired, and not revoked).

        Returns:
            bool: True if the token is valid, False otherwise
        """
        return (
            self.status == TokenStatus.ACTIVE
            and not self.is_expired
            and not self.is_revoked
        )

    # Token operations
    def revoke(self, reason: Optional[str] = None) -> Token:
        """Create a new token instance with revoked status.

        Args:
            reason: Optional reason for revocation

        Returns:
            Token: New token instance with revoked status
        """
        now = datetime.now(timezone.utc)
        return self.with_updates(
            status=TokenStatus.REVOKED,
            revoked_at=now,
            revocation_reason=reason,
        )

    def generate_opaque_token_string(self):
        # Generate an opaque token of uuid pattern
        return uuid4()

    def mark_used(self) -> Token:
        """Create a new token instance with updated last_used_at timestamp.

        Returns:
            Token: New token instance with updated last_used_at
        """
        return self.with_updates(last_used_at=datetime.now(timezone.utc))

    def link_to_token(self, next_token_id: UUID) -> Token:
        """Create a new token instance linked to another token in a refresh chain.

        Args:
            next_token_id: ID of the next token in the refresh chain

        Returns:
            Token: New token instance with updated next_token_id
        """
        if self.token_type != TokenType.REFRESH:
            raise ValueError("Only refresh tokens can be linked to other tokens")
        return self.with_updates(next_token_id=next_token_id)

    def with_updates(self, **kwargs) -> Token:
        """Create a new Token with updated fields.

        This follows the immutable object pattern by creating a new instance
        with the updated fields while maintaining immutability.

        Args:
            **kwargs: Fields to update and their new values

        Returns:
            Token: A new Token instance with updated fields

        Raises:
            ValueError: If attempting to modify immutable fields
        """
        # Prevent modification of immutable fields
        immutable_fields = {"token", "user_id", "token_type", "expiry", "created_at"}
        if any(field in kwargs for field in immutable_fields):
            raise ValueError("Cannot modify immutable token fields")

        # Create a new instance with updated fields
        return type(self)(**{**self.__dict__, **kwargs})
