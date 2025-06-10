from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional, Tuple
from uuid import UUID

from pydantic import EmailStr

if TYPE_CHECKING:
    from src.users.domain.entities.token import Token
    from src.users.domain.entities.user import User


class IAuthService(ABC):
    """Interface for authentication and token management."""

    @abstractmethod
    async def authenticate_user(
        self, email: EmailStr, password: str
    ) -> Tuple["User", Dict[str, str]]:
        """Authenticate a user with email and password."""
        ...

    @abstractmethod
    async def create_token_pair(
        self,
        user: "User",
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, "Token", "Token"]:
        """Create access and refresh token pair for a user.
        
        Args:
            user: The authenticated user
            request_info: Optional request metadata (e.g., user_agent, ip_address)
            
        Returns:
            Tuple containing:
            - access_token: JWT access token
            - refresh_token: Opaque refresh token
            - access_token_entity: Access token entity
            - refresh_token_entity: Refresh token entity
        """
        ...

    @abstractmethod
    async def refresh_token_pair(
        self,
        refresh_token: str,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, "Token", "Token"]:
        """Refresh an access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            request_info: Optional request metadata
            
        Returns:
            Tuple containing new access_token, refresh_token, and their entities
        """
        ...

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a specific token.
        
        Args:
            token: The token to revoke
            
        Returns:
            bool: True if token was successfully revoked
        """
        ...

    @abstractmethod
    async def revoke_all_tokens(self, user_id: UUID) -> int:
        """Revoke all tokens for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of tokens revoked
        """
        ...
