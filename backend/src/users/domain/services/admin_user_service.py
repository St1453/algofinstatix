"""Admin user service for administrative user operations."""

from __future__ import annotations

import logging

from src.users.domain.entities.user import Permission, User, UserRole
from src.users.domain.exceptions import (
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserRegistrationError,
    UserUpdateError,
)
from src.users.domain.schemas.admin_user_schemas import AdminUserCreate, AdminUserUpdate
from src.users.domain.services.base_user_service import BaseUserService

logger = logging.getLogger(__name__)


class AdminUserService(BaseUserService):
    """Service for admin user management operations."""

    async def create_user(self, user_data: AdminUserCreate, created_by: User) -> User:
        """Create a new user with admin permissions.

        Args:
            user_data: User creation data
            created_by: Admin user performing the action

        Returns:
            User: The created user

        Raises:
            PermissionDeniedError: If user lacks permission
            UserAlreadyExistsError: If user with email exists
            UserRegistrationError: If registration fails
        """
        if not created_by.has_permission(Permission.CREATE_USER):
            raise PermissionDeniedError("Insufficient permissions to create users")

        try:
            # Check for existing user
            try:
                await self._get_user_by_email(user_data.email)
                raise UserAlreadyExistsError(
                    f"Email {user_data.email} already registered"
                )
            except UserNotFoundError:
                pass  # Expected - user doesn't exist yet

            # Create user
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["roles"] = getattr(user_data, "roles", {UserRole.USER})

            return await self.user_repository.register_user(user_dict)

        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(
                "Failed to create user",
                exc_info=True,
                extra={"email": user_data.email, "error": str(e)},
            )
            raise UserRegistrationError("Failed to create user") from e

    async def update_user(
        self, user_id: str, update_data: AdminUserUpdate, updated_by: User
    ) -> User:
        """Update a user with admin permissions.

        Args:
            user_id: ID of user to update
            update_data: Data to update
            updated_by: Admin user performing the update

        Returns:
            User: The updated user

        Raises:
            PermissionDeniedError: If user lacks permission
            UserNotFoundError: If user not found
            UserUpdateError: If update fails
        """
        if not updated_by.has_permission(Permission.UPDATE_ANY):
            raise PermissionDeniedError("Insufficient permissions to update users")

        try:
            # Get existing user
            user = await self._get_user_by_id(user_id)

            # Convert to dict and filter None values
            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

            # Update and save
            updated_user = await self.user_repository.update_user_by_id(
                user_id=user.id, update_data=update_dict
            )

            if not updated_user:
                raise UserUpdateError("Failed to update user")

            return updated_user

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to update user",
                exc_info=True,
                extra={"user_id": user_id, "error": str(e)},
            )
            raise UserUpdateError("Failed to update user") from e

    async def delete_user(self, user_id: str, deleted_by: User) -> bool:
        """Delete a user with admin permissions.

        Args:
            user_id: ID of user to delete
            deleted_by: Admin user performing the deletion

        Returns:
            bool: True if deletion was successful

        Raises:
            PermissionDeniedError: If user lacks permission
            UserNotFoundError: If user not found
        """
        if not deleted_by.has_permission(Permission.DELETE_ANY):
            raise PermissionDeniedError("Insufficient permissions to delete users")

        await self.user_repository.delete_user_by_id(user_id)

        return True
