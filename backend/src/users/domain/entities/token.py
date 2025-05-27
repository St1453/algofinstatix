"""Token domain model for authentication and authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar, Optional, final
from uuid import UUID

from src.users.domain.value_objects.token_value_objects import (
    TokenExpiry,
    TokenScope,
    TokenStatus,
    TokenString,
    TokenType,
)

# Constants for default token lifetimes (in seconds)
DEFAULT_ACCESS_TOKEN_LIFETIME: int = 3600  # 1 hour
DEFAULT_REFRESH_TOKEN_LIFETIME: int = 604800  # 7 days


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

    # Class-level constants
    MIN_TOKEN_LIFETIME: ClassVar[int] = 60  # 1 minute
    MAX_TOKEN_LIFETIME: ClassVar[int] = 2592000  # 1 month

    # Core token data (required fields)
    token: TokenString
    user_id: str
    token_type: TokenType
    expiry: TokenExpiry

    # Token status
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

    @classmethod
    def create_access_token(
        cls,
        user_id: str,
        expires_in: int = DEFAULT_ACCESS_TOKEN_LIFETIME,
        scopes: Optional[list[str]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        parent_token_id: Optional[UUID] = None,
    ) -> Token:
        """Create a new access token.

        Args:
            user_id: ID of the user this token belongs to
            expires_in: Time in seconds until the token expires (default: 1 hour)
            scopes: List of scopes this token has access to
            user_agent: User agent that created the token
            ip_address: IP address that created the token
            parent_token_id: Optional ID of the parent refresh token

        Returns:
            Token: A new access token instance

        Raises:
            ValueError: If user_id is empty or expires_in is invalid
        """
        if not user_id:
            raise ValueError("User ID cannot be empty")

        cls._validate_token_lifetime(expires_in)

        now = datetime.now(timezone.utc)
        return cls(
            token=TokenString(),
            user_id=user_id,
            token_type=TokenType.ACCESS,
            expiry=TokenExpiry.from_now(expires_in, now),
            created_at=now,
            scopes=TokenScope(set(scopes) if scopes else set()),
            user_agent=user_agent,
            ip_address=ip_address,
            parent_token_id=parent_token_id,
        )

    @classmethod
    def create_refresh_token(
        cls,
        user_id: str,
        expires_in: int = DEFAULT_REFRESH_TOKEN_LIFETIME,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        parent_token_id: Optional[UUID] = None,
    ) -> Token:
        """Create a new refresh token.

        Args:
            user_id: ID of the user this token belongs to
            expires_in: Time in seconds until the token expires (default: 7 days)
            user_agent: User agent that created the token
            ip_address: IP address that created the token
            parent_token_id: Optional ID of the parent access token

        Returns:
            Token: A new refresh token instance

        Raises:
            ValueError: If user_id is empty or expires_in is invalid
        """
        if not user_id:
            raise ValueError("User ID cannot be empty")

        cls._validate_token_lifetime(expires_in)

        now = datetime.now(timezone.utc)
        return cls(
            token=TokenString(),
            user_id=user_id,
            token_type=TokenType.REFRESH,
            expiry=TokenExpiry.from_now(expires_in, now),
            created_at=now,
            user_agent=user_agent,
            ip_address=ip_address,
            parent_token_id=parent_token_id,
        )

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

    # Helper methods
    @classmethod
    def _validate_token_lifetime(cls, expires_in: int) -> None:
        """Validate that the token lifetime is within acceptable bounds.

        Args:
            expires_in: Requested token lifetime in seconds

        Raises:
            ValueError: If the lifetime is outside acceptable bounds
        """
        if not (cls.MIN_TOKEN_LIFETIME <= expires_in <= cls.MAX_TOKEN_LIFETIME):
            raise ValueError(
                f"Token lifetime must be between {cls.MIN_TOKEN_LIFETIME} and "
                f"{cls.MAX_TOKEN_LIFETIME} seconds"
            )

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
