from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import ClassVar, FrozenSet, List, Optional
from uuid import UUID

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.exceptions_database import NotFoundError
from src.shared.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)
from src.users.domain.entities.token import Token
from src.users.domain.interfaces.token_repository import ITokenRepository
from src.users.domain.value_objects.token_value_objects import TokenStatus, TokenType
from src.users.infrastructure.database.models.token_orm import TokenORM

logger = logging.getLogger(__name__)


class TokenRepositoryImpl(BaseRepository[TokenORM], ITokenRepository):
    """SQLAlchemy implementation of the token repository.

    This implementation handles all database operations for Token entities
    using SQLAlchemy's async session. It relies on the Unit of Work pattern
    for transaction management and extends BaseRepository for common CRUD operations.
    """

    # Fields that are allowed to be updated after token creation
    UPDATABLE_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "last_used_at",  # For tracking last usage
            "status",  # For status changes (active, revoked, etc.)
            "scopes",  # For scope modifications
            "expires_at",  # For token lifetime extension
            "revoked_at",  # For revocation timestamp
            "revocation_reason",  # Reason for revocation
            "user_agent",  # For client tracking
            "ip_address",  # For security auditing
            "meta",  # For additional metadata
        }
    )

    @property
    def entity_name(self) -> str:
        """Return the name of the entity this repository manages."""
        return "Token"

    # Protected fields that cannot be updated through this method
    _PROTECTED_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "token",  # Token value should never change
            "token_type",  # Type should be immutable
            "user_id",  # Token should never be reassigned to another user
        }
    )

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy async session to use for database operations.
        """
        super().__init__(session=session)

    async def get_by_token(self, token: str) -> Optional[Token]:
        """Get a token by its value.

        Args:
            token: The token value to search for.

        Returns:
            The Token object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        return await self._execute_with_logging(
            operation="get_by_token", operation_func=self._get_by_token, token=token
        )

    async def _get_by_token(self, token: str) -> Optional[Token]:
        """Internal implementation of get_by_token."""
        stmt = select(TokenORM).where(TokenORM.token == token)
        result = await self._session.execute(stmt)
        token_orm = result.scalar_one_or_none()
        return TokenORM.to_entity(token_orm) if token_orm else None

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
        return await self._execute_with_logging(
            operation="get_active_tokens_for_user",
            operation_func=self._get_active_tokens_for_user,
            user_id=user_id,
            token_type=token_type,
        )

    async def _get_active_tokens_for_user(
        self, user_id: UUID, token_type: Optional[TokenType] = None
    ) -> List[Token]:
        """Internal implementation of get_active_tokens_for_user."""
        stmt = select(TokenORM).where(
            TokenORM.user_id == user_id,
            TokenORM.status == TokenStatus.ACTIVE,
        )
        if token_type:
            stmt = stmt.where(TokenORM.token_type == token_type)
        result = await self._session.execute(stmt)
        token_orm_list = result.scalars().all()
        return [TokenORM.to_entity(token_orm) for token_orm in token_orm_list]

    async def create_token(self, token: Token) -> Token:
        """Create a new token.

        Args:
            token: The token to create.

        Returns:
            The created token with updated fields.

        Raises:
            DatabaseError: If there's an error creating the token.
        """
        return await self._execute_with_logging(
            operation="create", operation_func=self._create_token, entity=token
        )

    async def _create_token(self, token: Token) -> Token:
        """Internal implementation of create."""
        token_orm = TokenORM.from_entity(token)
        self._session.add(token_orm)
        return TokenORM.to_entity(token_orm)

    async def update_token(self, token: Token) -> Token:
        """Update an existing token.

        Args:
            token: The token with updated values.

        Returns:
            The updated token.

        Raises:
            NotFoundError: If the token doesn't exist.
            DatabaseError: If there's an error updating the token.
        """
        return await self._execute_with_logging(
            operation="update", operation_func=self._update_token, entity=token
        )

    async def _update_token(self, token: Token) -> Token:
        """Internal implementation of update.

        Only allows updating specific fields that are safe to modify.
        This prevents accidental or malicious modification of critical fields.

        Args:
            token: The token with updated values.

        Returns:
            The updated token.

        Raises:
            NotFoundError: If the token doesn't exist.
            ValueError: If trying to update protected fields.
        """
        existing = await self._session.get(TokenORM, token.id)
        if not existing:
            raise NotFoundError(f"Token with ID {token.id} not found")

        # Get the updated ORM instance
        updated_orm = TokenORM.from_entity(token)

        # Only update allowed fields
        for column in TokenORM.__table__.columns:
            column_name = column.name
            if column_name in self._PROTECTED_FIELDS:
                # Skip protected fields completely
                continue

            if column_name not in self.UPDATABLE_FIELDS:
                # Verify the field hasn't been changed
                current_value = getattr(existing, column_name)
                new_value = getattr(updated_orm, column_name)
                if current_value != new_value:
                    raise ValueError(f"Cannot update protected field: {column_name}. ")
                continue

            # Update the field if it's in the allowed set
            setattr(existing, column_name, getattr(updated_orm, column_name, None))

        # Special handling for status changes
        if existing.status != updated_orm.status:
            if updated_orm.status == TokenStatus.REVOKED and not existing.revoked_at:
                existing.revoked_at = datetime.now(timezone.utc)

        return TokenORM.to_entity(existing)

    async def refresh_token(self, old_token: str, new_token: Token) -> Token:
        """Refresh a token by updating it with a new one.

        Args:
            old_token: The old token string to be replaced (already hashed)
            new_token: The new token to save

        Returns:
            Token: The newly saved token

        Raises:
            TokenNotFoundError: If the old token doesn't exist
        """
        return await self._execute_with_logging(
            operation="refresh_token",
            operation_func=self._refresh_token,
            old_token=old_token,
            new_token=new_token,
        )

    async def _refresh_token(self, old_token: str, new_token: Token) -> Token:
        """Internal implementation of refresh_token."""
        stmt = (
            update(TokenORM)
            .where(TokenORM.token == old_token)
            .values(
                token=new_token.token,
                token_type=new_token.token_type,
                expires_at=new_token.expires_at,
                last_used_at=new_token.last_used_at,
                ip_address=new_token.ip_address,
                user_agent=new_token.user_agent,
                scopes=new_token.scopes,
                parent_token_id=new_token.parent_token_id,
                next_token_id=new_token.next_token_id,
                meta=new_token.meta or {},
            )
        )
        await self._session.execute(stmt)
        return await self._get_by_token(new_token.token)

    async def revoke_token(self, token: str) -> None:
        """Revoke a token by marking it as revoked.

        Args:
            token: The token string to revoke (already hashed)
        """
        return await self._execute_with_logging(
            operation="revoke_token", operation_func=self._revoke_token, token=token
        )

    async def _revoke_token(self, token: str) -> None:
        """Internal implementation of revoke_token."""
        stmt = (
            update(TokenORM)
            .where(TokenORM.token == token)
            .values(
                status=TokenStatus.REVOKED,
                revoked_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)

    async def revoke_tokens(self, user_id: UUID, token_type: TokenType = None) -> int:
        """Revoke all tokens for a user, optionally filtered by type.

        Args:
            user_id: The ID of the user whose tokens to revoke.
            token_type: Optional token type to filter by.

        Returns:
            The number of tokens that were revoked.

        Raises:
            DatabaseError: If there's an error revoking the tokens.
        """
        return await self._execute_with_logging(
            operation="revoke_tokens",
            operation_func=self._revoke_tokens,
            user_id=user_id,
            token_type=token_type,
        )

    async def _revoke_tokens(self, user_id: UUID, token_type: TokenType = None) -> int:
        """Internal implementation of revoke_tokens."""
        conditions = [TokenORM.user_id == user_id]
        if token_type:
            conditions.append(TokenORM.token_type == token_type)

        stmt = (
            update(TokenORM)
            .where(and_(*conditions))
            .values(status=TokenStatus.REVOKED, updated_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        # Don't commit here - let UoW handle it
        return result.rowcount

    async def delete_expired_tokens(self, expiry_date: datetime) -> int:
        """Delete tokens that expired before the given date.

        Args:
            expiry_date: The date before which tokens are considered expired.

        Returns:
            The number of tokens that were deleted.

        Raises:
            DatabaseError: If there's an error deleting the tokens.
        """
        return await self._execute_with_logging(
            operation="delete_expired_tokens",
            operation_func=self._delete_expired_tokens,
            expiry_date=expiry_date,
        )

    async def _delete_expired_tokens(self, expiry_date: datetime) -> int:
        """Internal implementation of delete_expired_tokens."""
        stmt = delete(TokenORM).where(TokenORM.expires_at < expiry_date)
        result = await self._session.execute(stmt)
        # Don't commit here - let UoW handle it
        return result.rowcount

    async def update_last_used(self, token: str, last_used_at: datetime) -> None:
        """Update the last used timestamp for a token.

        Args:
            token: The token string to update (already hashed)
            last_used_at: The timestamp when the token was last used
        """
        return await self._execute_with_logging(
            operation="update_last_used",
            operation_func=self._update_last_used,
            token=token,
            last_used_at=last_used_at,
        )

    async def _update_last_used(self, token: str, last_used_at: datetime) -> None:
        """Internal implementation of update_last_used."""
        stmt = (
            update(TokenORM)
            .where(TokenORM.token == token)
            .values(last_used_at=last_used_at)
        )
        await self._session.execute(stmt)
