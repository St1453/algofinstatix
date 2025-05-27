from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TypeVar, override

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.domain.entities.user import Permission, User
from src.users.domain.exceptions import (
    UserNotFoundError,
    UserUpdateError,
)
from src.users.domain.schemas.admin_user_schemas import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    UpdateUserRolesRequest,
)
from src.users.domain.services.user_service import UserService

from .user_management import UserManagement

# Configure logger
logger = logging.getLogger(__name__)
T = TypeVar("T")  # For generic type hints


class AdminUserManagement(UserManagement):
    """Application service for admin user management operations.

    This class extends UserManagement to provide admin-specific user management
    functionality with elevated privileges.

    Features:
    - Admin-specific user operations
    - Transaction management
    - Enhanced error handling and logging
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with an optional database session.

        Args:
            db_session: Optional SQLAlchemy async session. If not provided,
                      a new one will be created when needed.
        """
        super().__init__(db_session)
        self._admin_user_service: Optional[UserService] = None

    @property
    def admin_user_service(self) -> UserService:
        """Lazy initialization of admin user service."""
        if self._admin_user_service is None:
            self._admin_user_service = UserService(self.user_repository)
        return self._admin_user_service

    async def __aenter__(self) -> "AdminUserManagement":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit, ensures proper cleanup."""
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self.admin_user_service = UserService(self.user_repository)

    async def get_user_by_id(self, user_id: str) -> AdminUserResponse:
        """Get a user by ID."""
        try:
            user = await self.admin_user_service.get_user_by_id(user_id)
            return AdminUserResponse.model_validate(user.__dict__)
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

    async def create_user(
        self, user_data: AdminUserCreate, current_user: User
    ) -> AdminUserResponse:
        """Create a new user with admin privileges."""
        if not current_user.has_permission(Permission.CREATE_USER):
            raise PermissionError("Insufficient permissions to create users")

        try:
            user = await self.user_service.register_user(user_data, current_user)
            return AdminUserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_enabled_account=user.is_enabled_account,
                is_verified_email=user.is_verified_email,
                roles=user.roles,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at,
            )
        except Exception as e:
            logger.error(f"Error in admin user creation: {e}")
            raise

    @override
    async def update_user(
        self,
        user_id: str,
        update_data: Dict[str, Any],
    ) -> AdminUserUpdate:
        """Update any user attribute (admin only).

        Args:
            user_id: ID of the user to update
            update_data: Dictionary of fields to update

        Returns:
            AdminUserUpdateResponse: The updated user data

        Raises:
            HTTPException:
                - 404 if user not found
                - 400 if update data is invalid
                - 500 for other errors
        """
        try:
            # Get existing user first (validates user exists)
            await self.admin_user_service.get_user_by_id(user_id)

            # Convert Pydantic model to dict if needed
            if not isinstance(update_data, dict):
                update_data = update_data.model_dump(exclude_unset=True)

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            # Update user with all provided fields
            updated_user = await self.user_repository.update_user_by_id(
                user_id=user_id, update_data=update_data
            )

            if not updated_user:
                raise UserUpdateError("Failed to update user")

            return AdminUserUpdate.model_validate(updated_user.__dict__)

        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e) or "User not found"
            ) from e
        except UserUpdateError as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e) or "Invalid update data",
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error updating user {user_id}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the user",
            ) from e

    async def update_user_roles(
        self,
        user_id: str,
        roles_data: UpdateUserRolesRequest,
    ) -> AdminUserUpdate:
        """
        Update roles for a specific user.

        - **user_id**: ID of the user to update
        - **roles**: List of roles to assign to the user

        Requires admin privileges.
        """
        try:
            return await self.update_user_roles(user_id=user_id, roles=roles_data.roles)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_user(self, user_id: str) -> Dict[str, str]:
        """Delete a user."""
        try:
            await self.user_service.delete_user(user_id)
            return {"message": "User deleted successfully"}
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the user",
            ) from e

    async def enable_user(self, user_id: str) -> AdminUserUpdate:
        """Enable a user account.

        Args:
            user_id: ID of the user to enable

        Returns:
            AdminUserResponse: The updated user data
        """
        try:
            await User.enable_account(user_id)
            updated_user = await self.admin_user_service.get_user_by_id(user_id)
            return AdminUserUpdate.model_validate(updated_user.__dict__)
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

    async def disable_user(self, user_id: str) -> AdminUserUpdate:
        """Disable a user account.

        Args:
            user_id: ID of the user to disable

        Returns:
            AdminUserResponse: The updated user data
        """
        try:
            await User.disable_account(user_id)
            updated_user = await self.admin_user_service.get_user_by_id(user_id)
            return AdminUserUpdate.model_validate(updated_user.__dict__)
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
