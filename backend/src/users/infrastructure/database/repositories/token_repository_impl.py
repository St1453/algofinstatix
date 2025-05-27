from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncContextManager, AsyncIterator, List, Optional, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.exceptions_database import (
    DatabaseError,
    NotFoundError,
)
from src.users.domain.entities.token import Token
from src.users.domain.interfaces.token_repository import ITokenRepository
from src.users.domain.value_objects.token_value_objects import TokenStatus, TokenType
from src.users.infrastructure.database.models.token_orm import TokenORM
from src.users.infrastructure.logging.database_logger import log_database_operation

# Configure logger
logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Any)  # Used for type hints in generic methods

# Type aliases
TokenList = List[Token]
TokenORMList = List[TokenORM]


class TokenRepositoryImpl(ITokenRepository):
    """SQLAlchemy implementation of the token repository.

    This implementation handles all database operations for Token entities
    using SQLAlchemy's async session.

    Example:
        ```python
        # Using with async context manager
        async with TokenRepositoryImpl.create(session_factory) as repo:
            token = await repo.get_by_token("some_token")
            # ...

        # Or manually managing lifecycle
        repo = TokenRepositoryImpl(session)
        try:
            # Use repo
            await repo.some_method()
        finally:
            await repo.close()
        ```
    """

    def __init__(self, session: AsyncSession):
        """Initialize with an async session.

        Args:
            session: SQLAlchemy async session. The repository takes ownership of
                this session and will close it when close() is called.
        """
        self._session = session
        self._is_closed = False

    @classmethod
    @asynccontextmanager
    async def create(
        cls, session_factory: AsyncContextManager[AsyncSession]
    ) -> AsyncIterator[TokenRepositoryImpl]:
        """Create a new repository instance with automatic session management.

        This factory method creates a repository that automatically manages the
        session lifecycle. The session will be closed when the context exits.

        Args:
            session_factory: An async context manager that yields an AsyncSession

        Yields:
            TokenRepositoryImpl: A new repository instance

        Example:
            ```python
            async with TokenRepositoryImpl.create(session_factory) as repo:
                # Use the repository
                token = await repo.get_by_token("some_token")
                # ...
            # Session is automatically closed here
            ```
        """
        async with session_factory as session:
            repo = cls(session)
            try:
                yield repo
            except Exception:
                # Rollback on error
                await session.rollback()
                raise
            finally:
                # Ensure the repository is properly closed
                await repo.close()

    @property
    def session(self) -> AsyncSession:
        """Get the database session.

        Returns:
            AsyncSession: The active database session

        Raises:
            DatabaseError: If the session is closed
        """
        if self._is_closed:
            raise DatabaseError("Session is closed")
        return self._session

    async def get_by_token(self, token: str) -> Optional[Token]:
        """Retrieve a token by its string value.

        Args:
            token: The token string to search for (already hashed)

        Returns:
            The token if found, None otherwise

        Raises:
            DatabaseError: If there's an error accessing the database
        """
        try:
            stmt = select(TokenORM).where(TokenORM.token == token)
            result: Result = await self.session.execute(stmt)
            token_orm: Optional[TokenORM] = result.scalar_one_or_none()
            return self._to_entity(token_orm) if token_orm else None

        except SQLAlchemyError as e:
            error_msg = f"Failed to fetch token: {e}"
            logger.exception(error_msg)
            raise DatabaseError(error_msg) from e

    def _build_token_conditions(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[TokenStatus] = None,
        token_type: Optional[TokenType] = None,
        not_expired: bool = False,
        exclude_token: Optional[str] = None,
    ) -> list[Any]:
        """Build SQL conditions for token queries.

        Args:
            user_id: Optional user ID to filter by
            status: Optional token status to filter by
            token_type: Optional token type to filter by
            not_expired: If True, only include non-expired tokens
            exclude_token: Optional token string to exclude

        Returns:
            list[Any]: List of SQL conditions to be used with and_()
        """
        conditions = []

        if user_id is not None:
            conditions.append(TokenORM.user_id == str(user_id))

        if status is not None:
            conditions.append(TokenORM.status == status)

        if token_type is not None:
            conditions.append(TokenORM.token_type == token_type)

        if not_expired:
            conditions.append(TokenORM.expires_at > datetime.now(timezone.utc))

        if exclude_token is not None:
            conditions.append(TokenORM.token != exclude_token)

        return conditions

    async def get_active_tokens_for_user(
        self, user_id: UUID, token_type: Optional[TokenType] = None
    ) -> TokenList:
        """Retrieve all active, non-expired tokens for a user.

        Args:
            user_id: The ID of the user to fetch tokens for
            token_type: Optional token type to filter by.
                If None, returns all active token types.

        Returns:
            List[Token]: List of active, non-expired token entities for the user.

        Raises:
            DatabaseError: If there's an error executing the database query.
            ValueError: If the provided user_id is invalid.
        """
        if not user_id or not isinstance(user_id, UUID):
            raise ValueError("Valid user_id is required")

        try:
            # Build conditions for the query
            conditions = self._build_token_conditions(
                user_id=user_id,
                status=TokenStatus.ACTIVE,
                token_type=token_type,
                not_expired=True,
            )

            # Execute query and convert results
            stmt = select(TokenORM).where(and_(*conditions))
            result: Result = await self.session.execute(stmt)

            return [
                self._to_entity(token_orm)
                for token_orm in result.scalars().all()
                if token_orm  # Ensure we don't process None values
            ]

        except SQLAlchemyError as e:
            error_msg = f"Failed to fetch active tokens for user {user_id}"
            logger.exception(error_msg)
            raise DatabaseError(error_msg) from e

    async def save_or_update_token(self, token: Token) -> Token:
        """Save a new token or update an existing one.

        This method handles both creating new tokens and updating existing ones.
        If the token already exists, it will be updated; otherwise, a new one
        will be created.

        Args:
            token: The token to save or update

        Returns:
            The saved or updated token

        Raises:
            DatabaseError: If there's an error during the save/update operation
        """
        try:
            token_orm = await self._get_token_orm(token.token)

            if token_orm is None:
                return await self._create_token(token)
            return await self._update_token(token_orm, token)

        except SQLAlchemyError as e:
            error_msg = f"Failed to save/update token: {e}"
            logger.exception(error_msg)
            raise DatabaseError(error_msg) from e

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
            DatabaseError: If there's an error during the refresh operation
            TokenNotFoundError: If the old token doesn't exist
        """
        try:
            # Start a transaction
            async with self.transaction():
                # Get the old token
                stmt = select(TokenORM).where(TokenORM.token == old_token)
                result = await self.session.execute(stmt)
                old_token_orm = result.scalar_one_or_none()
                if not old_token_orm:
                    raise NotFoundError(resource="token", identifier=old_token)

                # Mark old token as revoked
                old_token_orm.status = TokenStatus.REVOKED
                old_token_orm.updated_at = datetime.now(timezone.utc)

                # Save new token
                new_token_orm = self._to_orm(new_token)
                self.session.add(new_token_orm)
                await self.session.flush()

                return self._to_entity(new_token_orm)

        except SQLAlchemyError as e:
            logger.error(f"Error refreshing token: {e}")
            raise DatabaseError("Failed to refresh token") from e

    async def revoke_token(self, token: str) -> None:
        """Revoke a token by marking it as revoked.

        Args:
            token: The token string to revoke (already hashed)
        """
        try:
            stmt = (
                update(TokenORM)
                .where(TokenORM.token == token)
                .values(
                    status=TokenStatus.REVOKED, updated_at=datetime.now(timezone.utc)
                )
            )
            await self.session.execute(stmt)

        except SQLAlchemyError as e:
            logger.error(f"Error revoking token: {e}")
            raise DatabaseError("Failed to revoke token") from e

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
        try:
            conditions = [
                TokenORM.user_id == user_id,
                TokenORM.status == TokenStatus.ACTIVE,
            ]

            if token_type is not None:
                conditions.append(TokenORM.token_type == token_type)

            if exclude_token is not None:
                conditions.append(TokenORM.token != exclude_token)

            stmt = (
                update(TokenORM)
                .where(and_(TokenORM.user_id == user_id, *conditions))
                .values(
                    status=TokenStatus.REVOKED, updated_at=datetime.now(timezone.utc)
                )
                .returning(TokenORM.id)
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            return len(result.scalars().all())

        except SQLAlchemyError as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            raise DatabaseError("Failed to revoke tokens") from e

    async def delete_expired_tokens(self, cutoff: datetime) -> int:
        """Delete tokens that have expired before the given cutoff.

        Args:
            cutoff: The cutoff datetime

        Returns:
            int: Number of tokens deleted
        """
        try:
            stmt = (
                delete(TokenORM)
                .where(
                    and_(
                        TokenORM.expires_at < cutoff,
                        or_(
                            TokenORM.status == TokenStatus.EXPIRED,
                            TokenORM.status == TokenStatus.REVOKED,
                        ),
                    )
                )
                .returning(TokenORM.id)
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            log_database_operation(
                operation="DELETE",
                table_name="tokens",
                record_id=None,
                changes={
                    "cutoff": cutoff.isoformat(),
                },
                user_id=None,
            )

            logger.info(
                "Deleted expired tokens",
                extra={
                    "cutoff": cutoff.isoformat(),
                    "deleted_count": len(result.scalars().all()),
                },
            )

            return len(result.scalars().all())

        except SQLAlchemyError as e:
            logger.error(
                "Error deleting expired tokens",
                extra={"cutoff": cutoff.isoformat(), "error": str(e)},
                exc_info=True,
            )
            raise DatabaseError("Failed to delete expired tokens") from e

    async def update_last_used(self, token: str, last_used_at: datetime) -> None:
        """Update the last used timestamp for a token.

        Args:
            token: The token string to update (already hashed)
            last_used_at: The timestamp when the token was last used
        """
        try:
            stmt = (
                update(TokenORM)
                .where(TokenORM.token == token)
                .values(
                    last_used_at=last_used_at, updated_at=datetime.now(timezone.utc)
                )
            )
            await self.session.execute(stmt)

        except SQLAlchemyError as e:
            logger.error(f"Error updating last used for token: {e}")
            raise DatabaseError("Failed to update token last used timestamp") from e

    async def _get_token_orm(self, token: str) -> Optional[TokenORM]:
        """Get a token ORM by token string.

        Args:
            token: The token string to search for

        Returns:
            The TokenORM if found, None otherwise
        """
        stmt = select(TokenORM).where(TokenORM.token == token)
        result: Result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_token(self, token: Token) -> Token:
        """Create a new token in the database.

        Args:
            token: The token to create

        Returns:
            The created token
        """
        token_orm = self._to_orm(token)
        self.session.add(token_orm)
        await self.session.flush()
        logger.debug("Created new token: %s", token.token[:8] + "...")
        return self._to_entity(token_orm)

    async def _update_token(self, token_orm: TokenORM, token: Token) -> Token:
        """Update an existing token in the database.

        Args:
            token_orm: The ORM instance to update
            token: The updated token data

        Returns:
            The updated token
        """
        self._update_orm_from_orm(token_orm, token)
        await self.session.flush()
        logger.debug("Updated existing token: %s", token.token[:8] + "...")
        return self._to_entity(token_orm)

    @staticmethod
    def _to_entity(token_orm: Optional[TokenORM]) -> Optional[Token]:
        """Convert TokenORM to domain entity.

        Args:
            token_orm: The ORM model instance or None

        Returns:
            The domain entity or None if token_orm is None
        """
        if not token_orm:
            return None

        return Token(
            token=token_orm.token,
            user_id=token_orm.user_id,
            token_type=token_orm.token_type,
            expiry=token_orm.expires_at,
            created_at=token_orm.created_at,
            last_used_at=token_orm.last_used_at,
            status=token_orm.status,
            user_agent=token_orm.user_agent,
            ip_address=token_orm.ip_address,
            scopes=token_orm.scopes or [],
            parent_token_id=token_orm.parent_token_id,
            next_token_id=token_orm.next_token_id,
            revoked_at=token_orm.revoked_at,
            revocation_reason=token_orm.revocation_reason,
        )

    @staticmethod
    def _to_orm(token: Token) -> TokenORM:
        """Convert domain entity to TokenORM.

        Args:
            token: The domain entity

        Returns:
            TokenORM: The ORM model instance
        """
        return TokenORM(
            token=token.token,
            user_id=token.user_id,
            token_type=token.token_type,
            expires_at=token.expiry,
            created_at=token.created_at,
            last_used_at=token.last_used_at,
            status=token.status,
            user_agent=token.user_agent,
            ip_address=token.ip_address,
            scopes=token.scopes,
            parent_token_id=token.parent_token_id,
            next_token_id=token.next_token_id,
            revoked_at=token.revoked_at,
            revocation_reason=token.revocation_reason,
        )

    @staticmethod
    def _update_orm_from_orm(token_orm: TokenORM, token: Token) -> None:
        """Update TokenORM with values from domain entity.

        Args:
            token_orm: The ORM model instance to update
            token: The domain entity with updated values

        Note:
            This method updates the token_orm in-place with values from the token.
            The changes are not persisted to the database until the session is flushed.
        """
        token_orm.user_id = token.user_id
        token_orm.token_type = token.token_type
        token_orm.expires_at = token.expiry
        token_orm.status = token.status
        token_orm.last_used_at = token.last_used_at
        token_orm.user_agent = token.user_agent
        token_orm.ip_address = token.ip_address
        token_orm.scopes = token.scopes
        token_orm.parent_token_id = token.parent_token_id
        token_orm.next_token_id = token.next_token_id
        token_orm.revoked_at = token.revoked_at
        token_orm.revocation_reason = token.revocation_reason
        token_orm.updated_at = datetime.now(timezone.utc)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Provide a transactional scope around a series of operations.

        Yields:
            None

        Raises:
            DatabaseError: If there's an error during transaction
        """
        if self._is_closed:
            raise DatabaseError("Session is closed")

        async with self.session.begin():
            try:
                yield
            except SQLAlchemyError as e:
                logger.error(f"Transaction failed: {e}")
                await self.session.rollback()
                raise DatabaseError("Database transaction failed") from e

    async def close(self) -> None:
        """Close the repository and release resources.

        This method is idempotent and can be called multiple times.
        After closing, the repository can no longer be used.
        """
        if not self._is_closed:
            self._is_closed = True
            if self._session is not None:
                try:
                    await self._session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
                finally:
                    self._session = None

    async def __aenter__(self) -> TokenRepositoryImpl:
        """Support for async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up resources when exiting the async context."""
        await self.close()
