from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple, Union
from uuid import UUID

from src.users.domain.schemas.token_schemas import TokenVerificationResult

if TYPE_CHECKING:
    from src.users.domain.entities.token import Token, TokenType
    from src.users.domain.entities.user import User


class ITokenService(ABC):
    """Interface for token service operations."""

    @abstractmethod
    async def create_email_verification_token(
        self,
        user: "User",
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, "Token"]:
        """Create an email verification token for the user."""
        ...

    @abstractmethod
    async def create_access_token(
        self,
        user: "User",
        scopes: Optional[Set[str]] = None,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, "Token"]:
        """Create a JWT access token for the user."""
        ...

    @abstractmethod
    async def create_refresh_token(
        self,
        user: "User",
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, "Token"]:
        """Create a JWT refresh token for the user."""
        ...

    @abstractmethod
    async def verify_token(
        self, token_str: str, token_type: Optional["TokenType"] = None
    ) -> "TokenVerificationResult":
        """Verify a JWT token and return the verification result."""
        ...

    @abstractmethod
    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """Generate a new access token using a valid refresh token."""
        ...

    @abstractmethod
    async def revoke_token(
        self, token_identifier: Union[str, UUID], reason: str = "User logged out"
    ) -> bool:
        """Revoke a token by its string value or ID."""
        ...

    @abstractmethod
    async def revoke_user_tokens(
        self, user_id: UUID, reason: str = "User initiated logout"
    ) -> int:
        """Revoke all active tokens for a user."""
        ...
