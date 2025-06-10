"""Core user service for regular user operations using Unit of Work pattern."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, FrozenSet

from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    UserUpdateError,
)
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.interfaces.user_service import IUserService

logger = logging.getLogger(__name__)


class UserService(IUserService):
    """Service for core user operations using Unit of Work pattern."""

    def __init__(
        self,
        uow: IUnitOfWork,
    ) -> None:
        """Initialize with required dependencies.

        Args:
            uow: Unit of Work instance for managing transactions and repositories
            password_service: Service for password hashing and verification
        """
        self.uow = uow

    # Protected fields that cannot be updated through this method
    _PROTECTED_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "hashed_password",  # Use dedicated password update method
        }
    )

    # Status fields that are handled specially
    _STATUS_FIELDS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "is_enabled_account",
            "is_verified_email",
        }
    )

    async def get_user_by_id(self, user_id: str) -> User:
        """Get a user by their ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If the user is not found
        """
        return await self.uow.users.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User:
        """Get a user by their email address.

        Args:
            email: The email of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If no user exists with the given email
        """
        return await self.uow.users.get_user_by_email(email)

    async def get_my_profile(self, user_id: str) -> User:
        """Get the current user's profile.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If the user is not found
        """
        async with self.uow.transaction():
            user = await self.uow.users.get_user_by_id(user_id)
            if not user or user.deleted_at is not None:
                raise UserNotFoundError(f"User with ID {user_id} not found")

            return user

    async def update_my_profile(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> User:
        """Update the current user's profile.

        Args:
            user_id: The ID of the user to update
            update_data: The data to update

        Returns:
            User: The updated user

        Raises:
            UserNotFoundError: If the user is not found
            UserUpdateError: If the update fails
        """
        # Filter allowed fields
        allowed_fields = {
            "first_name",
            "last_name",
            "username",
            "profile_picture",
            "bio",
        }
        update_data = {
            k: v
            for k, v in update_data.items()
            if k in allowed_fields and v is not None
        }

        if not update_data:
            # No valid fields to update, just return the current user
            async with self.uow.transaction():
                user = await self.uow.users.get_user_by_id(user_id)
                if not user or user.deleted_at is not None:
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                return user

        async with self.uow.transaction():
            try:
                # Get existing user within transaction
                user = await self.uow.users.get_user_by_id(user_id)
                if not user or user.deleted_at is not None:
                    raise UserNotFoundError(f"User with ID {user_id} not found")

                # Update and save user
                updated_user = await self.uow.users.update_user_by_id(
                    user_id=user_id, update_data=update_data
                )
                if not updated_user:
                    raise UserUpdateError("Failed to update user profile")

                await self.uow.commit()
                return updated_user

            except Exception as e:
                await self.uow.rollback()
                logger.error(
                    "Failed to update user profile",
                    exc_info=True,
                    extra={"user_id": user_id, "error": str(e)},
                )
                if not isinstance(e, UserUpdateError):
                    raise UserUpdateError("Failed to update profile") from e
                raise

    async def delete_my_profile(self, user_id: str, password: str) -> bool:
        """Soft-delete the current user's profile after password verification.

        This performs a soft delete by setting the deleted_at timestamp.
        The user's data is preserved but marked as deleted.

        Args:
            user_id: ID of the user requesting deletion
            password: User's current password for verification

        Returns:
            bool: True if deletion was successful

        Raises:
            UserNotFoundError: If the user is not found
            InvalidCredentialsError: If the password is incorrect
            UserUpdateError: If the deletion fails
        """
        async with self.uow.transaction():
            try:
                # Get user and verify password within transaction
                user = await self.uow.users.get_user_by_id(user_id)
                if not user or user.deleted_at is not None:
                    raise UserNotFoundError(f"User with ID {user_id} not found")

                if not user.hashed_password.verify_password_match(password):
                    raise InvalidCredentialsError("Incorrect password")

                # Perform soft delete by setting deleted_at timestamp
                deleted_user = await self.uow.users.update_user_by_id(
                    user_id=user_id,
                    update_data={
                        "deleted_at": datetime.now(timezone.utc),
                        "is_enabled": False,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

                if not deleted_user:
                    raise UserUpdateError("Failed to delete user profile")

                await self.uow.commit()
                logger.info(
                    "User profile soft-deleted",
                    extra={"user_id": user_id},
                )
                return True

            except Exception as e:
                await self.uow.rollback()
                logger.error(
                    "Failed to delete user profile",
                    exc_info=True,
                    extra={"user_id": user_id, "error": str(e)},
                )
                if not isinstance(
                    e,
                    (
                        UserNotFoundError,
                        InvalidCredentialsError,
                        UserUpdateError,
                    ),
                ):
                    raise UserUpdateError("Failed to delete profile") from e
                raise
