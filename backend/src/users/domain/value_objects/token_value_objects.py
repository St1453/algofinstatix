"""Token-related value objects for the users domain.

This module contains value objects that represent various aspects of tokens
in the authentication and authorization system.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set


class TokenType(str):
    """Types of tokens supported by the system."""

    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    API = "api"


class TokenStatus(str):
    """Status of a token."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    USED = "used"


@dataclass
class TokenPayload:
    sub: str  # Subject (user ID)
    type: TokenType  # Token type
    jti: str  # Unique token ID
    iat: datetime  # Issued at
    exp: datetime  # Expiration time
    scopes: List[str] = field(default_factory=list)  # Permissions
    meta: Dict[str, Any] = field(default_factory=dict)  # Additional data


@dataclass(frozen=True)
class TokenString:
    """Value object for token string validation.

    Supports JWT tokens and UUID strings.
    """

    value: str
    JWT_PATTERN = r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$"
    UUID_PATTERN = (
        r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
    )
    OPAQUE_PATTERN = r"^[A-Za-z0-9-_]+$"

    def __post_init__(self):
        if not self.value:
            raise ValueError("Token value cannot be empty")

        if not (self._is_jwt() or self._is_uuid() or self._is_opaque()):
            raise ValueError("Invalid token format. Must be JWT, UUID, or opaque token")

    def _is_jwt(self) -> bool:
        """Check if the token is a valid JWT."""
        parts = self.value.split(".")
        if len(parts) != 3:
            return False

        # Check each part is valid base64url
        import base64
        import binascii

        for part in parts:
            try:
                # Add padding if needed
                part += "=" * (4 - len(part) % 4) % 4
                base64.urlsafe_b64decode(part)
            except (binascii.Error, TypeError):
                return False

        return True

    def _is_uuid(self) -> bool:
        """Check if the token is a valid UUID."""
        try:
            from uuid import UUID as UUIDValidator

            UUIDValidator(self.value)
            return True
        except (ValueError, AttributeError):
            return False

    def _is_opaque(self) -> bool:
        """Check if the token is a valid opaque token."""
        return bool(re.match(self.OPAQUE_PATTERN, self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TokenExpiry:
    """Value object representing token expiration."""

    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate the expiry time."""
        if self.expires_at.tzinfo is None:
            self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        if self.expires_at <= self.created_at:
            raise ValueError("Expiry time must be in the future")

    @classmethod
    def from_now(
        cls, seconds: int, created_at: Optional[datetime] = None
    ) -> "TokenExpiry":
        """Create an expiry from now plus the given seconds.

        Args:
            seconds: Number of seconds until expiry
            created_at: Optional creation time (defaults to now)

        Returns:
            A new TokenExpiry instance
        """
        created = created_at or datetime.now(timezone.utc)
        return cls(
            expires_at=created + timedelta(seconds=seconds),
            created_at=created,
        )

    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    def ttl_seconds(self) -> float:
        """Get time to live in seconds."""
        return (self.expires_at - datetime.now(timezone.utc)).total_seconds()


@dataclass(frozen=True)
class TokenScope:
    """Value object representing token scopes."""

    scopes: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate scopes."""
        if not isinstance(self.scopes, set):
            # Use object.__setattr__ to modify the frozen dataclass
            object.__setattr__(self, 'scopes', set(self.scopes or []))

    def has_scope(self, scope: str) -> bool:
        """Check if the token has the given scope."""
        return "*" in self.scopes or scope in self.scopes

    def has_any_scope(self, *scopes: str) -> bool:
        """Check if the token has any of the given scopes."""
        if "*" in self.scopes:
            return True
        return any(scope in self.scopes for scope in scopes)

    def has_all_scopes(self, *scopes: str) -> bool:
        """Check if the token has all of the given scopes."""
        if "*" in self.scopes:
            return True
        return all(scope in self.scopes for scope in scopes)

    def add(self, scope: str) -> "TokenScope":
        """Return a new TokenScope with the added scope."""
        new_scopes = self.scopes.copy()
        new_scopes.add(scope)
        return TokenScope(new_scopes)

    def remove(self, scope: str) -> "TokenScope":
        """Return a new TokenScope with the scope removed."""
        new_scopes = self.scopes.copy()
        new_scopes.discard(scope)
        return TokenScope(new_scopes)

    def __contains__(self, scope: str) -> bool:
        return self.has_scope(scope)

    def __iter__(self):
        return iter(self.scopes)

    def __len__(self) -> int:
        return len(self.scopes)


__all__ = [
    "TokenString",
    "TokenExpiry",
    "TokenScope",
]
