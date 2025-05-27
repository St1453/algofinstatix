"""Token repository interface for token persistence operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.users.domain.entities.token import Token
from src.users.domain.value_objects.token_value_objects import TokenType


class ITokenRepository(ABC):
    """Interface for token persistence operations.

    This interface defines the contract for token repository implementations
    that handle persistence operations for Token entities.
    """

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[Token]:
        """Retrieve a token by its string value.

        Args:
            token: The token string to search for (already hashed)

        Returns:
            Optional[Token]: The token if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active_tokens_for_user(
        self, user_id: UUID, token_type: Optional[TokenType] = None
    ) -> List[Token]:
        """Retrieve all active tokens for a user, optionally filtered by token type.

        Args:
            user_id: The ID of the user
            token_type: Optional token type to filter by

        Returns:
            List[Token]: List of active tokens for the user
        """
        raise NotImplementedError

    @abstractmethod
    async def save_or_update_token(self, token: Token) -> Token:
        """Save a new token or update an existing one.

        This method handles both creating new tokens and updating existing ones.
        If the token already exists, it will be updated; otherwise, a new one
        will be created.

        Args:
            token: The token to save or update

        Returns:
            Token: The saved or updated token
        """
        raise NotImplementedError

    @abstractmethod
    async def refresh_token(self, old_token: str, new_token: Token) -> Token:
        """Replace an existing token with a new one.

        This is typically used for token rotation, where an old token is replaced
        with a new one (e.g., refreshing an access token).

        Args:
            old_token: The token string to be replaced (already hashed)
            new_token: The new token to save

        Returns:
            Token: The newly saved token

        Raises:
            TokenNotFoundError: If the old token doesn't exist
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Revoke a token by marking it as revoked.

        Args:
            token: The token string to revoke (already hashed)
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_tokens_for_user(
        self,
        user_id: UUID,
        token_type: Optional[TokenType] = None,
        exclude_token: Optional[str] = None,
    ) -> int:
        """Revoke all tokens for a user, optionally filtered by token type.

        Args:
            user_id: The ID of the user
            token_type: Optional token type to filter by
            exclude_token: Optional token string to exclude from revocation

        Returns:
            int: Number of tokens revoked
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_expired_tokens(self, cutoff: datetime) -> int:
        """Delete tokens that have expired before the given cutoff.

        Args:
            cutoff: The cutoff datetime

        Returns:
            int: Number of tokens deleted
        """
        raise NotImplementedError

    @abstractmethod
    async def update_last_used(self, token: str, last_used_at: datetime) -> None:
        """Update the last used timestamp for a token.

        Args:
            token: The token string to update (already hashed)
            last_used_at: The timestamp when the token was last used
        """
        raise NotImplementedError
