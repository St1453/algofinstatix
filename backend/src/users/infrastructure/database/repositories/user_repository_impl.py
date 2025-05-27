from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, FrozenSet, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)
from src.users.domain.entities.user import User
from src.users.domain.interfaces.user_repository import IUserRepository
from src.users.domain.schemas.user_schemas_system import UserRegistrationInfo
from src.users.infrastructure.database.models.user_orm import UserORM


class UserRepositoryImpl(BaseRepository[UserORM], IUserRepository):
    """SQLAlchemy implementation of UserRepository.

    This implementation handles all database operations for User entities
    using SQLAlchemy's async session. It relies on the Unit of Work pattern
    for transaction management and extends BaseRepository for common CRUD operations.
    """

    @property
    def entity_name(self) -> str:
        """Return the name of the entity this repository manages."""
        return "User"

    # Protected fields that cannot be updated through this method
    _PROTECTED_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "hashed_password",  # Use dedicated password update method
            "mfa_secret",  # Use dedicated MFA methods
        }
    )

    # Status fields that are handled specially
    _STATUS_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "is_enabled_account",
            "is_verified_email",
            "failed_login_attempts",
            "locked_until",
            "password_changed_at",
            "last_login_at",
            "last_failed_login",
        }
    )

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy async session to use for database operations.
        """
        super().__init__(session=session)
        self._model = UserORM

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = select(self._model).where(
            self._model.id == user_id,
            self._model.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        return user_orm.to_entity() if user_orm else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address.

        Args:
            email: The email address of the user to retrieve.

        Returns:
            The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = select(self._model).where(
            self._model.email == email,
            self._model.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        return user_orm.to_entity() if user_orm else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by their username.

        Args:
            username: The username of the user to retrieve.

        Returns:
            The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = select(UserORM).where(
            UserORM.username == username,
            UserORM.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        return user_orm.to_entity() if user_orm else None

    async def create_user(self, user_data: UserRegistrationInfo) -> User:
        """Create a new user.

        Args:
            user_data: The user data to create the user with.

        Returns:
            The created User object.

        Raises:
            DatabaseError: If there's an error creating the user.
        """
        user_dict = user_data.model_dump()
        user_orm = UserORM(**user_dict)
        self._session.add(user_orm)
        await self._session.flush()
        await self._session.refresh(user_orm)
        return user_orm.to_entity()

    async def update_user(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> Optional[User]:
        """Update an existing user.

        Args:
            user_id: The ID of the user to update.
            update_data: Dictionary of fields to update.

        Returns:
            The updated User object, or None if the user was not found.

        Raises:
            DatabaseError: If there's an error updating the user.
        """
        # Filter out protected fields
        clean_data = {
            k: v for k, v in update_data.items() if k not in self._PROTECTED_FIELDS
        }

        if not clean_data:
            user_orm = await self._get_by_id(user_id)
            return user_orm.to_entity() if user_orm else None

        # Update the user
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id, UserORM.deleted_at.is_(None))
            .values(**clean_data, updated_at=datetime.now(timezone.utc))
            .returning(UserORM)
        )
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()

        if user_orm is None:
            return None

        await self._session.refresh(user_orm)
        return user_orm.to_entity()

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user.

        Performs a soft delete by setting the deleted_at timestamp.

        Args:
            user_id: The ID of the user to delete.

        Returns:
            bool: True if the user was deleted, False if the user was not found.

        Raises:
            DatabaseError: If there's an error deleting the user.
        """

        async def _delete() -> bool:
            # Perform soft delete by setting deleted_at
            stmt = (
                update(UserORM)
                .where(UserORM.id == user_id, UserORM.deleted_at.is_(None))
                .values(
                    deleted_at=datetime.now(timezone.utc),
                    is_enabled_account=False,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            result = await self._session.execute(stmt)
            return result.rowcount > 0

        return await self._execute_with_logging(
            operation="delete",
            operation_func=_delete,
            user_id=user_id,
        )
