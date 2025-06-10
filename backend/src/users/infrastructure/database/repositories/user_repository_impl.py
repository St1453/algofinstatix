from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.exceptions_database import (
    DatabaseError,
    NotFoundError,
)
from src.shared.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)
from src.users.domain.entities.user import User
from src.users.domain.interfaces.user_repository import IUserRepository
from src.users.domain.schemas.user_schemas import UserRegistrationInfo
from src.users.infrastructure.database.models.user_orm import UserORM

logger = logging.getLogger(__name__)


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

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy async session to use for database operations.
        """
        super().__init__(session=session)

    async def get_user_by_id(
        self,
        user_id: str,
    ) -> Optional[User]:
        """Retrieve a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            Optional[User]: The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = (
            select(UserORM)
            .where(UserORM.id == user_id)
            .where(UserORM.deleted_at.is_(None))
        )

        # wrapper function that accepts the expected parameters but ignores them
        async def execute_query(*args, **kwargs):
            return await self._session.execute(stmt)

        try:
            result = await self._execute_with_logging(
                operation="read",
                operation_func=execute_query,
                log_success=False,
                id=user_id,
            )
            user_orm = result.scalar_one_or_none()
            if user_orm is None:
                raise NotFoundError(
                    resource="User", identifier=user_id, details={"user_id": user_id}
                )
            return UserORM.to_entity(user_orm)
        except NotFoundError:
            return None
        except Exception as e:
            self.logger.log_operation(
                operation="get_user_by_id",
                entity="users",
                status="error",
                user_id=user_id,
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to get user by ID: {str(e)}", details={"user_id": user_id}
            ) from e

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """Retrieve a user by their email address.

        Args:
            email: The email address of the user to retrieve.

        Returns:
            Optional[User]: The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = (
            select(UserORM)
            .where(UserORM.email == email)
            .where(UserORM.deleted_at.is_(None))
        )

        # wrapper function that accepts the expected parameters but ignores them
        async def execute_query(*args, **kwargs):
            return await self._session.execute(stmt)

        try:
            result = await self._execute_with_logging(
                operation="read",
                operation_func=execute_query,
                log_success=False,
                id=f"email:{email}",
            )
            user_orm = result.scalar_one_or_none()
            if user_orm is None:
                return None
            return UserORM.to_entity(user_orm)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise NotFoundError(
                resource="User", identifier=email, details={"email": email}
            )

    async def get_user_by_username(
        self,
        username: str,
    ) -> bool:
        """Retrieve a user by their username.

        Args:
            username: The username of the user to retrieve.

        Returns:
            Optional[User]: The User object if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        stmt = (
            select(UserORM)
            .where(UserORM.username == username)
            .where(UserORM.deleted_at.is_(None))
        )

        # wrapper function that accepts the expected parameters but ignores them
        async def execute_query(*args, **kwargs):
            return await self._session.execute(stmt)

        try:
            result = await self._execute_with_logging(
                operation="read",
                operation_func=execute_query,
                log_success=False,
                id=f"username:{username}",
            )
            user_orm = result.scalar_one_or_none()
            if user_orm is None:
                return False
            return True
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise NotFoundError(
                resource="User", identifier=username, details={"username": username}
            )

    async def register_user(
        self,
        user_data: UserRegistrationInfo,
    ) -> User:
        """Register a new user.

        Args:
            user_data: The user data to create the user with.
                     UserRegistrationInfo (with hashed password).

        Returns:
            User: The created user entity.

        Raises:
            DatabaseError: If there's an error creating the user.
        """
        try:
            # Convert UserRegistrationInfo to UserORM
            user_orm = UserORM(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                hashed_password=user_data.hashed_password,
                profile_picture=user_data.profile_picture,
                bio=user_data.bio,
            )

            # Add to session and flush to get the ID
            self._session.add(user_orm)
            await self._session.flush()
            await self._session.refresh(user_orm)

            # Log the successful registration
            self.logger.log_operation(
                operation="user_registration",
                entity="users",
                status="success",
                user_id=user_orm.id,
                email=user_orm.email,
            )

            # Convert to domain model and return
            return UserORM.to_entity(user_orm)

        except Exception as e:
            # Log error with available context
            error_details = {
                "email": user_data.email,
                "error": str(e),
                "error_type": e.__class__.__name__,
            }
            if user_orm and hasattr(user_orm, "id"):
                error_details["user_id"] = user_orm.id

            self.logger.log_operation(
                operation="user_registration",
                entity="users",
                status="error",
                **error_details,
            )
            raise DatabaseError(
                f"Failed to create user: {str(e)}", details=error_details
            ) from e

    @override
    async def update_user_by_id(self, user_data: User) -> bool:
        """Update a user by ID.

        Args:
            user_id: The ID of the user to update
            update_data: The updated user profile data

        Returns:
            bool: True if the user was updated successfully.

        Raises:
            UserNotFoundError: If no user exists with the given ID
            DatabaseError: If there's an error updating the user
        """

        try:
            # What fields can be updated is written below
            user_orm = UserORM(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                profile_picture=user_data.profile_picture,
                bio=user_data.bio,
                is_verified_email=user_data.status.is_verified,
                is_enabled_account=user_data.status.is_enabled,
                updated_at=user_data.updated_at,
                deleted_at=user_data.deleted_at,
                roles=user_data.roles,
            )

            # Add to session and commit
            self._session.query(UserORM).filter(UserORM.id == user_data.id).update(
                user_orm.model_dump()
            )
            await self._session.flush()
            await self._session.refresh(user_orm)

            # Log the successful registration
            self.logger.log_operation(
                operation="user_update",
                entity="users",
                status="success",
                user_id=user_orm.id,
                email=user_orm.email,
            )

            return True
        except Exception as e:
            # Log error with available context
            error_details = {
                "email": user_data.email,
                "error": str(e),
                "error_type": e.__class__.__name__,
            }
            if user_orm and hasattr(user_orm, "id"):
                error_details["user_id"] = user_orm.id

            self.logger.log_operation(
                operation="user_update",
                entity="users",
                status="error",
                **error_details,
            )
            raise DatabaseError(
                f"Failed to update user: {str(e)}", details=error_details
            ) from e

    async def delete_user_by_id(self, user_id: str) -> bool:
        """Delete a user by ID.

        Args:
            user_id: The ID of the user to delete

        Raises:
            UserNotFoundError: If no user exists with the given ID
            DatabaseError: If there's an error deleting the user
        """
        try:
            # wrapper function that accepts the expected parameters but ignores them
            async def execute_query(*args, **kwargs):
                self._session.query(UserORM).filter(UserORM.id == user_id).update(
                    {"deleted_at": datetime.now(timezone.utc)}
                )
                await self._session.flush()

            # Execute the query with logging
            await self._execute_with_logging(
                operation="delete",
                operation_func=execute_query,
                log_success=True,
                id=user_id,
            )
            return True
        except Exception as e:
            # Log error with available context
            error_details = {
                "error": str(e),
                "error_type": e.__class__.__name__,
            }
            if user_id:
                error_details["user_id"] = user_id

            self.logger.log_operation(
                operation="user_delete",
                entity="users",
                status="error",
                **error_details,
            )
            raise DatabaseError(
                f"Failed to delete user: {str(e)}", details=error_details
            ) from e
