"""Core user service for regular user operations."""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    InvalidCredentialsError,
    UserUpdateError,
)
from src.users.domain.services.base_user_service import BaseUserService

logger = logging.getLogger(__name__)


class UserService(BaseUserService):
    """Service for core user operations."""

    async def get_my_profile(self, user_id: str) -> User:
        """Get the current user's profile.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If the user is not found
        """
        return await self._get_user_by_id(user_id)

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
        # Get existing user
        user = await self._get_user_by_id(user_id)

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
            return user

        try:
            # Update and save user
            updated_user = await self.user_repository.update_user_by_id(
                user_id=user_id, update_data=update_data
            )
            if not updated_user:
                raise UserUpdateError("Failed to update user profile")

            return updated_user

        except Exception as e:
            logger.error(
                "Failed to update user profile",
                exc_info=True,
                extra={"user_id": user_id, "error": str(e)},
            )
            raise UserUpdateError("Failed to update profile") from e

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change a user's password with proper validation.

        Args:
            user_id: ID of the user changing their password
            current_password: Current password for verification
            new_password: New password to set

        Raises:
            UserNotFoundError: If user doesn't exist
            AccountLockedError: If account is locked
            InvalidCredentialsError: If current password is incorrect
        """
        user = await self._get_user_by_id(user_id)

        # Verify current password
        if not user.hashed_password.verify_password_match(current_password):
            raise InvalidCredentialsError("Current password is incorrect")

        # Update password
        try:
            user.hashed_password = user.hashed_password.update_password(new_password)
            await self.user_repository.update_user_by_id(
                user_id, {"hashed_password": user.hashed_password}
            )

        except Exception as e:
            logger.error(
                "Password change failed",
                exc_info=True,
                extra={"user_id": user_id, "error": str(e)},
            )
            raise UserUpdateError("Failed to change password") from e
