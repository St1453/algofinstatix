"""User management application service.

This module provides the UserManagement class which serves as the main entry point
for all user-related operations, handling the coordination between the API layer
and the domain services.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.session import get_db
from src.users.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserUpdateError,
)
from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    UserRegisterRequest,
)
from src.users.domain.services.user_service import UserService
from src.users.domain.value_objects.hashed_password import HashedPassword
from src.users.domain.value_objects.password_utils import generate_temp_password
from src.users.domain.value_objects.user_status import UserStatus
from src.users.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)

# Configure logger
logger = logging.getLogger(__name__)
T = TypeVar("T")  # For generic type hints


class UserManagement:
    """Application service for user management operations.

    This class serves as the main entry point for user-related operations,
    handling the coordination between the API layer and the domain services.

    Features:
    - Transaction management
    - Error handling and logging
    - Session lifecycle management
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with an optional database session.

        Args:
            db_session: Optional SQLAlchemy async session. If not provided,
                      a new one will be created when needed.
        """
        self._session = db_session
        self._user_repository: Optional[UserRepositoryImpl] = None
        self._user_service: Optional[UserService] = None
        self._user_status: Optional[UserStatus] = None

    @property
    def user_repository(self) -> UserRepositoryImpl:
        """Lazy initialization of user repository."""
        if self._user_repository is None:
            if self._session is None:
                self._session = get_db()
            self._user_repository = UserRepositoryImpl(self._session)
        return self._user_repository

    @property
    def user_service(self) -> UserService:
        """Lazy initialization of user service."""
        if self._user_service is None:
            self._user_service = UserService(self.user_repository)
        return self._user_service

    @property
    def user_status(self) -> UserStatus:
        """Lazy initialization of user status."""
        if self._user_status is None:
            self._user_status = UserStatus()
        return self._user_status

    @classmethod
    async def create(cls, session: Optional[AsyncSession] = None) -> "UserManagement":
        """Create a new UserManagement instance.

        Args:
            session: Optional existing session. If None, a new one will be created.

        Returns:
            UserManagement: A new instance of UserManagement
        """
        return cls(session)

    async def __aenter__(self) -> "UserManagement":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit, ensures proper cleanup."""
        if self._user_repository is not None:
            await self._user_repository.close()

    async def is_healthy(self) -> bool:
        """Check if the database connection is healthy.

        Returns:
            bool: True if the database is responsive

        Raises:
            HTTPException: If health check fails
        """
        try:
            if self._user_repository is None:
                self._user_repository = UserRepositoryImpl(await get_db().__anext__())
            return await self._user_repository.is_healthy()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection is not available",
            ) from e

    # User CRUD Operations

    async def register_user(
        self,
        user_data: UserRegisterRequest,
    ) -> UserProfile:
        """Register a new user.

        Args:
            user_data: User registration data

        Returns:
            UserResponse: The created user data

        Raises:
            HTTPException: If registration fails
        """
        try:
            user = await self.user_service.register_user(user_data)
            return UserProfile.model_validate(user.__dict__)
        except UserAlreadyExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e

    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get a user by their ID.

        Args:
            user_id: ID of the user to retrieve

        Returns:
            UserProfile: The user's profile information

        Raises:
            HTTPException: If user is not found
        """
        try:
            user = await self.user_service.get_user_by_id(str(user_id))
            return UserProfile.model_validate(user.__dict__)
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e) or "User not found"
            ) from e

    async def update_user_profile(
        self,
        user_id: str,
        user_data: UserProfile,
    ) -> Dict:
        """Update the current user's profile information.

        Args:
            user_id: ID of the user to update
            user_data: User profile data to update

        Returns:
            UserProfile: The updated user data

        Raises:
            HTTPException:
                - 404 if user not found
                - 400 if update data is invalid
                - 500 for other errors
        """
        try:
            updated_user = await self.user_service.update_user(user_id, user_data)
            return UserProfile.model_validate(updated_user.__dict__)

        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e) or "User not found"
            ) from e

        except UserUpdateError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e) or "Invalid profile data",
            ) from e

        except Exception as e:
            logger.error(
                "Unexpected error updating profile",
                exc_info=True,
                extra={"user_id": user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while updating your profile",
            ) from e

    async def delete_user_profile(self, user_id: str) -> Dict[str, str]:
        """Delete the current user's profile.

        Performs a soft delete by setting the deleted_at timestamp.
        The user's data is retained but marked as deleted.

        Args:
            user_id: ID of the user to delete

        Returns:
            Dict: {"message": "Profile deleted successfully"}

        Raises:
            HTTPException:
                - 404 if user not found
                - 500 for other errors
        """
        try:
            # Verify user exists and has permission
            await self.user_service.get_user_by_id(user_id)

            # Perform soft delete
            success = await self.user_service.delete_user(user_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete profile",
                )

            return {"message": "Profile deleted successfully"}

        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e) or "User not found"
            ) from e

        except HTTPException:
            raise

        except Exception as e:
            logger.error(
                "Failed to delete profile", exc_info=True, extra={"user_id": user_id}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting your profile",
            ) from e

    # Authentication & Authorization

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[UserProfile]:
        """Authenticate a user with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            UserResponse if authentication succeeds, None otherwise

        Raises:
            HTTPException: If authentication fails
        """
        try:
            user = await self.user_service.authenticate_user(email, password)
            # Record the successful login
            # make sure to return tokens when authentication is successful

            # returning UserProfile is temporary for now
            if user:
                await self.user_status.record_successful_login(str(user.id))
                return UserProfile.model_validate(user.__dict__)
            return None
        except (UserNotFoundError, InvalidCredentialsError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            ) from e

    async def change_password(
        self, user_id: str, password_data: ChangePasswordRequest
    ) -> Dict[str, str]:
        """Change the current user's password.

        Args:
            user_id: The ID of the user changing their password
            password_data: Object containing current and new password

        Returns:
            Dict with success message

        Raises:
            HTTPException: If password change fails
        """
        try:
            await self.user_service.change_password(
                user_id=user_id,
                current_password=password_data.current_password,
                new_password=password_data.new_password,
            )
            return {"message": "Password updated successfully"}

        except (UserNotFoundError, InvalidCredentialsError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except Exception as e:
            logger.error(f"Failed to change password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while changing password",
            ) from e


async def verify_email(self, user_id: str) -> UserProfile:
    """Mark a user's email as verified.

    Args:
        user_id: ID of the user to verify

    Returns:
        UserProfile: The updated user profile

    Raises:
        HTTPException:
            - 404 if user not found
            - 400 if verification fails
            - 500 for unexpected errors
    """
    try:
        # Get the user
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Use domain model's verify_email method
        verified_user = user.verify_email()

        # Save changes
        await self.user_repository.update_user(verified_user)

        logger.info(f"Email verified for user ID: {user_id}")
        return UserProfile.model_validate(verified_user.__dict__)

    except UserNotFoundError as e:
        logger.warning(f"User not found for email verification: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        logger.warning(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying email",
        ) from e


async def reset_password(self, user_id: str) -> Dict[str, str]:
    """Reset a user's password to a temporary value.

    Args:
        user_id: The ID of the user to reset the password for

    Returns:
        Dict with success message and temporary password

    Raises:
        HTTPException:
            - 404 if user not found
            - 500 for unexpected errors
    """
    try:
        # Generate a new temporary password
        temp_password = generate_temp_password()

        # Get the user
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Update user's password using the domain model
        hashed_password = HashedPassword.from_plaintext(temp_password)
        updated_user = user.with_updates(hashed_password=hashed_password)

        # Save changes
        await self.user_repository.update_user(updated_user)

        logger.info(f"Password reset for user ID: {user_id}")
        return {
            "message": "Password reset successful",
            "temporary_password": temp_password,
        }

    except UserNotFoundError as e:
        logger.warning(f"User not found for password reset: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting password",
        ) from e
