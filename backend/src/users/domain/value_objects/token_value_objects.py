"""Token-related value objects for the users domain.

This module contains value objects that represent various aspects of tokens
in the authentication and authorization system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class TokenType(str, PyEnum):
    """Types of tokens supported by the system."""

    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    API = "api"


class TokenStatus(str, PyEnum):
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
    """Value object representing a token string.

    This encapsulates the token value and provides validation and generation.
    """

    _value: str = field(init=False, repr=False)

    # Token format: UUID4 by default
    TOKEN_PATTERN = (
        r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
    )

    def __init__(self, value: Optional[str] = None):
        """Initialize with an existing token or generate a new one.

        Args:
            value: Optional token string. If None, generates a new UUID4 token.

        Raises:
            ValueError: If the provided token is invalid.
        """
        if value is None:
            value = str(uuid4())

        if not self._is_valid_token(value):
            raise ValueError("Invalid token format")

        object.__setattr__(self, "_value", value)

    @classmethod
    def generate(cls) -> TokenString:
        """Generate a new token."""
        return cls()

    @classmethod
    def _is_valid_token(cls, token: str) -> bool:
        """Validate the token format."""
        return bool(re.match(cls.TOKEN_PATTERN, token, re.IGNORECASE))

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (TokenString, str)):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(self._value)


@dataclass(frozen=True)
class TokenExpiry:
    """Value object representing token expiration."""

    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the expiry time."""
        if not self.expires_at.tzinfo:
            raise ValueError("expires_at must be timezone-aware")
        if not self.created_at.tzinfo:
            raise ValueError("created_at must be timezone-aware")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be in the future")

    @classmethod
    def from_now(
        cls, seconds: int, created_at: Optional[datetime] = None
    ) -> TokenExpiry:
        """Create an expiry from now plus the given seconds."""
        created = created_at or datetime.now(timezone.utc)
        expires_at = created + timedelta(seconds=seconds)
        return cls(expires_at=expires_at, created_at=created)

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def ttl_seconds(self) -> int:
        """Get time to live in seconds."""
        return int((self.expires_at - datetime.now(timezone.utc)).total_seconds())


@dataclass(frozen=True)
class TokenScope:
    """Value object representing token scopes."""

    scopes: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Validate scopes."""
        if not all(isinstance(scope, str) for scope in self.scopes):
            raise ValueError("All scopes must be strings")

    def has_scope(self, scope: str) -> bool:
        """Check if the token has the given scope."""
        return scope in self.scopes

    def has_any_scope(self, *scopes: str) -> bool:
        """Check if the token has any of the given scopes."""
        return any(scope in self.scopes for scope in scopes)

    def has_all_scopes(self, *scopes: str) -> bool:
        """Check if the token has all of the given scopes."""
        return all(scope in self.scopes for scope in scopes)

    def add(self, scope: str) -> TokenScope:
        """Return a new TokenScope with the added scope."""
        new_scopes = set(self.scopes)
        new_scopes.add(scope)
        return TokenScope(new_scopes)

    def remove(self, scope: str) -> TokenScope:
        """Return a new TokenScope with the scope removed."""
        new_scopes = set(self.scopes)
        new_scopes.discard(scope)
        return TokenScope(new_scopes)

    def __contains__(self, scope: str) -> bool:
        return scope in self.scopes

    def __iter__(self):
        return iter(self.scopes)

    def __len__(self) -> int:
        return len(self.scopes)


__all__ = [
    "TokenString",
    "TokenExpiry",
    "TokenScope",
]
