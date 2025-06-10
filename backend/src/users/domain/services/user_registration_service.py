"""Service for handling user registration process.

This service handles the complete user registration flow including:
- Validating registration data
- Checking for existing users
- Creating new user accounts
- Assigning default roles
- Sending verification emails (placeholder)
"""

from __future__ import annotations

import logging
from typing import Callable

from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    UserRegistrationError,
)
from src.users.domain.interfaces.email_service import IEmailService
from src.users.domain.interfaces.password_service import IPasswordService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.interfaces.user_registration_service import (
    IUserRegistrationService,
)
from src.users.domain.schemas.user_schemas import (
    UserProfileResponse,
    UserRegisterRequest,
    UserRegistrationInfo,
)
from src.users.domain.value_objects.email import Email
from src.users.domain.value_objects.username import Username

logger = logging.getLogger(__name__)


class UserRegistrationService(IUserRegistrationService):
    """Service for handling user registration operations.

    This service is responsible for the complete user registration process,
    including validation, user creation, and initial setup.
    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        password_service: IPasswordService,
        email_service: IEmailService,
    ) -> None:
        """Initialize the user registration service.

        Args:
            uow_factory: Callable that returns a Unit of Work instance
            password_service: Service for password hashing and verification
            email_service: Service for sending emails
        """
        self._uow_factory = uow_factory
        self._password_service = password_service
        self._email_service = email_service
        self._uow: IUnitOfWork | None = None

    def _to_profile_response(self, user: User) -> UserProfileResponse:
        """Convert a User domain model to a UserProfileResponse.

        Args:
            user: The User domain model to convert

        Returns:
            UserProfileResponse: The converted profile response
        """
        return UserProfileResponse(
            id=str(user.id),
            email=str(user.email),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_picture=user.profile_picture,
            bio=user.bio,
        )

    async def register_user(
        self, user_data: UserRegisterRequest
    ) -> UserProfileResponse:
        """Register a new user.

        Note: This method should be called within a transaction context.

        Args:
            user_data: The user registration data

        Returns:
            UserProfileResponse: The created user's profile information

        Raises:
            EmailAlreadyExistsError: If the email is already registered
            UsernameAlreadyExistsError: If the username is already taken
            UserRegistrationError: If registration fails for any other reason
        """
        self._password_service.validate_password_strength(user_data.password)

        if not self._uow and not self._uow_factory:
            raise RuntimeError("UnitOfWork is not initialized")

        if not self._uow:
            self._uow = self._uow_factory()
            await self._uow.__aenter__()

        try:
            # Check if email already exists (case-insensitive check)
            # The Email value object will normalize the case for us
            email_obj = Email.from_string(user_data.email)
            if await self._uow.users.get_user_by_email(str(email_obj)):
                raise EmailAlreadyExistsError(
                    f"Email {email_obj} is already registered"
                )

            # Check if username already exists (case-insensitive check)
            # The Username value object will normalize the case for us
            username_obj = Username.from_string(user_data.username)
            if await self._uow.users.get_user_by_username(str(username_obj)):
                raise UsernameAlreadyExistsError(
                    f"Username {username_obj} is already taken"
                )

            # Create a copy of the user data with normalized email and username
            normalized_data = user_data.model_copy(
                update={"email": str(email_obj), "username": str(username_obj)}
            )

            try:
                # Create the user registration info
                user_reg_info = await self.from_register_request(normalized_data)
                user = await self._uow.users.register_user(user_reg_info)

                # Commit the transaction
                await self._uow.commit()

                # Convert to response model
                return self._to_profile_response(user)

            except Exception as e:
                await self._uow.rollback()
                raise UserRegistrationError(f"Failed to create user: {str(e)}") from e
            finally:
                if self._uow:
                    await self._uow.__aexit__(None, None, None)
                    self._uow = None

        except (
            EmailAlreadyExistsError,
            UsernameAlreadyExistsError,
            UserRegistrationError,
        ) as e:
            logger.warning(
                "User registration validation failed",
                extra={"email": user_data.email, "error": str(e)},
            )
            raise
        except Exception as e:
            logger.error(
                "User registration failed",
                exc_info=True,
                extra={"email": user_data.email, "error": str(e)},
            )
            raise UserRegistrationError(
                "Registration failed due to an unexpected error"
            ) from e

    async def from_register_request(
        self, register_request: UserRegisterRequest
    ) -> UserRegistrationInfo:
        """Create from registration request with hashed password.

        Args:
            register_request: The registration request containing user data

        Returns:
            UserRegistrationInfo: The user registration info with hashed password
        """
        hashed_password = await self._password_service.hash_password(
            register_request.password
        )
        return UserRegistrationInfo(
            email=register_request.email,
            first_name=register_request.first_name,
            last_name=register_request.last_name,
            username=register_request.username,
            profile_picture=register_request.profile_picture,
            bio=register_request.bio,
            hashed_password=hashed_password,
        )
