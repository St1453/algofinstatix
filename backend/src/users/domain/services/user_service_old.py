"""Service layer for user operations with role-based permissions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from pydantic import EmailStr

from src.users.domain.entities.user import Permission, User, UserRole
from src.users.domain.exceptions import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    PasswordPolicyViolation,
    PasswordStrengthError,
    PasswordTooWeakError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserRegistrationError,
    UserUpdateError,
)
from src.users.domain.interfaces.user_repository import IUserRepository
from src.users.domain.schemas.admin_user_schemas import AdminUserCreate, AdminUserUpdate
from src.users.domain.schemas.user_schemas import UserProfile, UserRegisterRequest
from src.users.domain.value_objects.hashed_password import HashedPassword
from src.users.domain.value_objects.user_status import UserStatus

# Configure logger
logger = logging.getLogger(__name__)


class UserService:
    """Service handling business logic for user operations
    with role-based permissions.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: HashedPassword,
    ) -> None:
        """Initialize the UserService with required dependencies.

        Args:
            user_repository: Implementation of IUserRepository for data access
        """
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: str) -> User:
        """Retrieve a user by ID with permission checks.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If the user is not found or is deleted
        """

        user = await self.user_repository.get_user_by_id(user_id)
        if not user or user.deleted_at is not None:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Check permissions
        if user and str(user.id) != user_id:
            if not user.has_permission(UserRole.has_permission(Permission.READ_ANY)):
                raise PermissionError(
                    "Insufficient permissions to view this user's information"
                )

        return user

    async def get_user_by_email(
        self, email: EmailStr, current_user: Optional[User] = None
    ) -> User:
        """Retrieve a user by email with permission checks.

        Args:
            email: The email of the user to retrieve
            current_user: The currently authenticated user (for permission checks)

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If no user exists with the given email
            PermissionError: If current user doesn't have permission to view this user
        """
        user = await self.user_repository.get_user_by_email(email)

        # Check permissions
        if current_user and str(current_user.id) != str(user.id):
            if not current_user.has_permission(
                UserRole.has_permission(Permission.READ_ANY)
            ):
                raise PermissionError("Not authorized to view this user")

        return user

    async def register_user(
        self,
        user_data: Union[UserRegisterRequest, AdminUserCreate],
        current_user: Optional[User] = None,
    ) -> User:
        """Register a new user with proper permission checks.

        Args:
            user_data: User registration data
            current_user: The currently authenticated user (for permission checks)

        Returns:
            User: The newly created user

        Raises:
            PermissionError: If user doesn't have permission to create accounts
            UserAlreadyExistsError: If a user with the email already exists
            UserRegistrationError: If user registration fails
        """
        try:
            # Permission checks
            has_permission = current_user and current_user.has_permission(
                UserRole.has_permission(Permission.CREATE_ACCOUNT)
            )
            if not has_permission:
                raise PermissionDeniedError(
                    "Insufficient permissions to create accounts"
                )

            # Check for existing user
            existing_user = await self.user_repository.get_user_by_email(
                user_data.email, include_deleted=False
            )
            if existing_user:
                raise UserAlreadyExistsError(
                    f"Email {user_data.email} already registered"
                )

            # Create user data
            user_dict = user_data.model_dump(exclude={"password"})

            # Create hashed password using the HashedPassword value object
            try:
                hashed_password = HashedPassword.from_plaintext(user_data.password)
            except (PasswordPolicyViolation, PasswordStrengthError) as e:
                error_msg = f"Password does not meet requirements: {str(e)}"
                raise UserRegistrationError(error_msg) from e

            user_dict.update(
                {
                    "hashed_password": hashed_password,
                    "is_enabled_account": getattr(
                        user_data, "is_enabled_account", True
                    ),
                    "is_verified_email": getattr(user_data, "is_verified_email", False),
                    "roles": getattr(user_data, "roles", {UserRole.USER}),
                }
            )

            return await self.user_repository.register_user(user_dict)

        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(
                "Error creating user: %s",
                str(e),
                exc_info=True,
                extra={"email": user_data.email, "error_type": type(e).__name__},
            )
            raise UserRegistrationError("Failed to create user") from e

    async def update_user(
        self,
        user_id: str,
        update_data: Union[UserProfile, AdminUserUpdate, Dict[str, Any]],
        current_user: Optional[User] = None,
    ) -> User:
        """Update a user's information with permission checks.

        Args:
            user_id: The ID of the user to update
            update_data: The data to update (can be dict or Pydantic model)
            current_user: The currently authenticated user (for permission checks)

        Returns:
            User: The updated user

        Raises:
            UserNotFoundError: If no user exists with the given ID
            PermissionError: If user doesn't have permission to update this user
            UserUpdateError: If the update operation fails or data is invalid
        """
        # Check permissions
        if current_user and str(current_user.id) != user_id:
            if not current_user.has_permission(
                UserRole.has_permission(Permission.UPDATE_ANY)
            ):
                raise PermissionError("Not authorized to update this user")

        try:
            # Convert Pydantic model to dict if needed
            if not isinstance(update_data, dict):
                update_dict = update_data.model_dump(exclude_unset=True)

            # Remove protected fields
            protected_fields = ["id", "created_at", "updated_at", "deleted_at"]
            update_data = {
                k: v
                for k, v in update_dict.items()
                if k not in protected_fields and v is not None
            }

            # If no valid fields to update, return current user
            if not update_data:
                return await self.get_user_by_id(user_id)

            # Additional validations for regular profile updates
            if not current_user or not current_user.has_permission(
                Permission.UPDATE_ANY
            ):
                # Regular user can only update their own profile with limited fields
                allowed_fields = {
                    "first_name",
                    "last_name",
                    "username",
                    "profile_picture",
                    "user_intro",
                }
                update_data = {
                    k: v for k, v in update_data.items() if k in allowed_fields
                }

                # Validate username uniqueness
                if "username" in update_data:
                    try:
                        existing_user = await self.user_repository.get_user_by_username(
                            update_data["username"]
                        )
                        if existing_user and str(existing_user.id) != user_id:
                            raise UserUpdateError("Username is already taken")
                    except UserNotFoundError:
                        pass  # Username is available

                # Validate profile picture URL if provided
                if "profile_picture" in update_data and update_data["profile_picture"]:
                    if not self._is_valid_url(update_data["profile_picture"]):
                        raise UserUpdateError("Invalid profile picture URL")

            # Update user
            updated_user = await self.user_repository.update_user_by_id(
                user_id=user_id, update_data=update_data
            )

            if not updated_user:
                raise UserUpdateError("Failed to update user")

            return updated_user

        except UserNotFoundError as e:
            logger.warning("User not found for update", extra={"user_id": user_id})
            raise UserNotFoundError(f"User not found: {str(e)}") from e
        except UserUpdateError:
            raise
        except Exception as e:
            logger.error(
                "Failed to update user",
                exc_info=True,
                extra={"user_id": user_id, "update_data": update_data},
            )
            raise UserUpdateError(
                "An unexpected error occurred while updating user"
            ) from e

    async def delete_user(self, user_id: str, current_user: User) -> bool:
        """Delete a user by ID with proper permission checks.

        Args:
            user_id: The ID of the user to delete
            current_user: The currently authenticated user

        Returns:
            bool: True if deletion was successful

        Raises:
            UserNotFoundError: If the user is not found
            PermissionError: If the current user doesn't have permission
                to delete this user
        """
        # Verify user exists and check permissions
        if not await self.user_repository.get_user_by_id(user_id):
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Check permissions
        if str(current_user.id) != user_id:
            if not current_user.has_permission(Permission.DELETE_ANY):
                raise PermissionError("Insufficient permissions to delete other users")
        elif not current_user.has_permission(Permission.DELETE_OWN):
            raise PermissionError("Insufficient permissions to delete account")

        # Soft delete the user
        await self.user_repository.update_user_by_id(
            user_id=user_id, update_data={"deleted_at": datetime.now(timezone.utc)}
        )
        return True

    def _is_valid_url(self, url: str) -> bool:
        """Validate that a string is a valid URL."""
        try:
            from urllib.parse import urlparse

            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _validate_my_profile_update(self, update_data: UserProfile) -> Dict[str, Any]:
        """Validate and sanitize user profile update data using Pydantic model.

        Args:
            update_data: Raw update data dictionary

        Returns:
            Dict[str, Any]: Validated and sanitized update data

        Raises:
            ValueError: If validation fails
        """

        try:
            # Convert back to dict, excluding unset and None values
            validated_data = update_data.model_dump(
                exclude_unset=True, exclude_none=True
            )

            # Remove any remaining protected fields that shouldn't be updated
            protected_fields = {
                "id",
                "hashed_password",
                "is_enabled_account",
                "is_verified_email",
                "roles",
                "email_verified",
                "password_changed_at",
                "created_at",
                "updated_at",
                "deleted_at",
            }

            return {
                k: v for k, v in validated_data.items() if k not in protected_fields
            }

        except Exception as e:
            logger.warning(
                "Profile update validation failed",
                extra={"error": str(e), "update_data_keys": list(update_data.keys())},
            )
            raise ValueError(f"Invalid profile data: {str(e)}") from e

    async def authenticate_user(
        self,
        email: str,
        password: str,
        require_verified_email: bool = True,
    ) -> User | None:
        """Authenticate a user with email and password.

        Args:
            email: User's email
            password: Plain text password
            require_verified_email: Whether to require email verification

        Returns:
            User: Authenticated User instance

        Raises:
            UserNotFoundError: If user doesn't exist
            AccountNotVerifiedError: If email verification is required but not completed
            AccountLockedError: If account is locked due to too many failed attempts
            InvalidCredentialsError: If credentials are invalid
        """
        try:
            # Get user by email
            user = await self.user_repository.get_user_by_email(email)
            if not user or user.deleted_at is not None:
                logger.warning("Login attempt with non-existent email: %s", email)
                raise UserNotFoundError(f"User with email {email} not found")

            # Check if account is locked
            if user.status.is_locked:
                logger.warning("Login attempt for locked account: %s", email)
                raise AccountLockedError(
                    f"Account is locked. Please try again in "
                    f"{UserStatus.ACCOUNT_LOCKOUT_MINUTES} minutes."
                )

            # Check email verification
            if require_verified_email and not user.status.is_verified:
                logger.info("Login attempt with unverified email: %s", email)
                raise AccountNotVerifiedError(
                    "Please verify your email before logging in"
                )

            # Verify password using the HashedPassword value object
            try:
                if not user.hashed_password.verify(password):
                    # Record failed attempt and update user
                    updated_user = user.status.record_failed_login()
                    await self.user_repository.update_user_by_id(updated_user.id)

                    remaining = (
                        UserStatus.MAX_LOGIN_ATTEMPTS
                        - updated_user.failed_login_attempts
                    )
                    if remaining <= 0:
                        logger.warning(
                            "Account locked due to too many failed attempts: %s",
                            email,
                        )
                        raise AccountLockedError(
                            f"Account locked. Please try again in "
                            f"{UserStatus.ACCOUNT_LOCKOUT_MINUTES} minutes."
                        )

                    error_msg = f"Invalid password. {remaining} attempts remaining."
                    logger.warning(
                        "Failed login attempt for user %s. %s attempts remaining.",
                        email,
                        remaining,
                        extra={"user_id": user.id},
                    )
                    raise InvalidCredentialsError(error_msg)
            except (ValueError, TypeError) as e:
                logger.error("Password verification error: %s", str(e))
                raise InvalidCredentialsError("Invalid credentials") from e

            # Authentication successful - update last login
            updated_user = user.status.record_successful_login()
            await self.user_repository.update_user_by_id(updated_user.id)
            logger.info("Successful login for user: %s", email)
            return updated_user

        except (
            UserNotFoundError,
            AccountNotVerifiedError,
            AccountLockedError,
            InvalidCredentialsError,
        ) as e:
            logger.debug(
                "Authentication failed: %s",
                str(e),
                extra={"email": email, "error_type": type(e).__name__},
            )
            raise

        except Exception as e:
            logger.error(
                "Unexpected error during authentication for %s: %s",
                email,
                str(e),
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )
            raise AuthenticationError("An error occurred during authentication") from e

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        require_current_password: bool = True,
    ) -> None:
        """Change a user's password with proper validation.

        Args:
            user_id: ID of the user changing their password
            current_password: Current password for verification
            new_password: New password to set
            require_current_password: Whether to require current password
                for verification

        Raises:
            UserNotFoundError: If user doesn't exist
            AccountLockedError: If account is locked
            InvalidCredentialsError: If current password is incorrect
            PasswordTooWeakError: If new password requirements not met
            PasswordReuseError: If new password was used recently
        """
        user = await self.get_user_by_id(user_id)

        # Check if account is locked
        if user.status.is_locked:
            locked_msg = (
                f"Account is locked. Please try again in "
                f"{UserStatus.ACCOUNT_LOCKOUT_MINUTES} minutes."
            )
            raise AccountLockedError(locked_msg)

        try:
            # Update the password using the User entity's method
            updated_user = user.hashed_password.update_password(
                new_password=new_password,
            )

            # Save the updated user
            await self.user_repository.update_user_by_id(updated_user.id)

        except (PasswordPolicyViolation, PasswordStrengthError) as e:
            raise PasswordTooWeakError(str(e))
        except Exception as e:
            # Log the error and re-raise
            logger.error(
                "Error changing password for user %s: %s",
                user_id,
                str(e),
                extra={"error_type": type(e).__name__},
            )
            raise
