"""User management application service.

This module provides the UserManagement class which serves as the main entry point
for all user-related operations, handling the coordination between the API layer
and the domain services.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict
from uuid import UUID

from fastapi import HTTPException, status

from src.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserUpdateError,
)
from src.users.domain.interfaces import (
    IEmailService,
    ITokenService,
    IUserRegistrationService,
    IUserService,
)
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.schemas.user_schemas import UserProfile, UserRegisterRequest
from src.users.domain.services.user_registration_service import UserRegistrationService
from src.users.domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class UserManagement:
    """Application service for user management operations.

    This class serves as the main entry point for user-related operations,
    handling the coordination between the API layer and the domain services.
    It strictly follows the Unit of Work pattern for transaction management.

    Features:
    - Transaction management via Unit of Work
    - Error handling and logging
    - Clean separation of concerns
    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        user_service: IUserService,
        user_registration_service: IUserRegistrationService,
        token_service: ITokenService,
        email_service: IEmailService,
    ) -> None:
        """Initialize with all required dependencies.

        Args:
            uow_factory: Callable that returns a new Unit of Work instance
            user_service: Service for user-related operations
            user_registration_service: Service for user registration operations
            token_service: Service for token operations
            email_service: Service for sending emails
        """
        self._uow_factory = uow_factory
        self._user_service = user_service
        self._user_registration_service = user_registration_service
        self._token_service = token_service
        self._email_service = email_service
        self._uow: IUnitOfWork | None = None

    @property
    def user_service(self) -> UserService:
        """Get the user service instance."""
        return self._user_service

    @property
    def user_registration_service(self) -> UserRegistrationService:
        """Get the user registration service instance."""
        return self._user_registration_service

    async def __aenter__(self) -> "UserManagement":
        """Context manager entry.

        Returns:
            UserManagement: The UserManagement instance
        """
        if self._uow is None and self._uow_factory:
            self._uow = self._uow_factory()
            await self._uow.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit, ensures proper cleanup.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self._uow:
            try:
                if exc_type is not None:  # If there was an exception
                    await self._uow.rollback()
                await self._uow.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                self._uow = None

    async def register_user(
        self,
        user_data: UserRegisterRequest,
    ) -> UserProfile:
        """Register a new user and send verification email.

        Args:
            user_data: User registration data

        Returns:
            UserResponse: The created user data

        Raises:
            HTTPException: If registration fails
        """
        try:
            if not self._uow:
                self._uow = self._uow_factory()

            async with self._uow.transaction():
                # Register the user
                user = await self.user_registration_service.register_user(user_data)
                """

                # Create email verification token
                verification_token = (
                    await self._token_service.create_email_verification_token(
                        user, {"user_agent": "user-registration"}
                    )
                )

                # Send verification email (in background)
                try:
                    await self._email_service.send_verification_email(
                        email=user.email,
                        token=verification_token,
                        username=user.username,
                    )
                except Exception as email_error:
                    logger.error(
                        "Failed to send verification email: %s",
                        str(email_error),
                        exc_info=True,
                    )
                    # Don't fail registration if email sending fails
                    # The user can request a new verification email later
                """

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
            if not self._uow:
                self._uow = self._uow_factory()

            async with self._uow.transaction():
                user = await self.user_service.get_user_by_id(user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with ID {user_id} not found",
                    )
                return UserProfile.model_validate(user.__dict__)
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e) or "User not found"
            ) from e

    async def update_user_profile(
        self,
        user_id: str,
        user_data: UserProfile,
    ) -> UserProfile:
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
            if not self._uow:
                self._uow = self._uow_factory()

            async with self._uow.transaction():
                # Get existing user
                existing_user = await self.user_service.get_user_by_id(user_id)
                if not existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with ID {user_id} not found",
                    )

                # Update user data
                updated_user = await self.user_service.update_my_profile(
                    user_id, user_data.model_dump(exclude_unset=True)
                )
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
            if not self._uow:
                self._uow = self._uow_factory()

            async with self._uow.transaction():
                # Check if user exists
                existing_user = await self.user_service.get_user_by_id(user_id)
                if not existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with ID {user_id} not found",
                    )

                # Soft delete the user
                await self.user_service.delete_my_profile(user_id)
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
