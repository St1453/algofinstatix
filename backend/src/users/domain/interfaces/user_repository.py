"""User service interface for user management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.users.domain.entities.user import User
from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    UserRegisterRequest,
)


class IUserRepository(ABC):
    """Interface for user management operations."""

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> User:
        """Retrieve a user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If no user exists with the given ID
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        """Retrieve a user by email.

        Args:
            email: The email of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If no user exists with the given email
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        """Retrieve a user by username.

        Args:
            username: The username of the user to retrieve

        Returns:
            User: The requested user

        Raises:
            UserNotFoundError: If no user exists with the given username
        """
        raise NotImplementedError

    @abstractmethod
    async def register_user(self, user_data: UserRegisterRequest) -> User:
        """Register a new user.

        Args:
            user_data: The user registration data

        Returns:
            User: The created user

        Raises:
            UserAlreadyExistsError: If a user with the email already exists
            ValueError: If the provided data is invalid
        """
        raise NotImplementedError

    @abstractmethod
    async def update_user_by_id(self, user_id: str, update_data: UserProfile) -> User:
        """Update the current user's profile.

        Args:
            user_id: The ID of the user to update
            update_data: Pydantic model of fields to update

        Returns:
            User: The updated user

        Raises:
            UserNotFoundError: If no user exists with the given ID
            UserUpdateError: If the update operation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_user_by_id(self, user_id: str) -> bool:
        """Delete the current user's profile.

        Args:
            user_id: The ID of the user to delete

        Returns:
            bool: True if the user was deleted, False otherwise

        Raises:
            UserNotFoundError: If no user exists with the given ID
        """
        raise NotImplementedError

    @abstractmethod
    async def change_password(
        self, user_id: str, password_data: ChangePasswordRequest
    ) -> None:
        """Change a user's password.

        Args:
            user_id: ID of the user changing their password
            password_data: Object containing current and new password

        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If current password is incorrect
            ValueError: If new password is invalid
        """
        raise NotImplementedError

    @abstractmethod
    async def count_users(
        self,
        is_enabled_account: Optional[bool] = None,
        role: Optional[str] = None,
        last_login_after: Optional[datetime] = None,
    ) -> int:
        """Count users with optional filters."""
        raise NotImplementedError

    @abstractmethod
    async def get_users_by_last_login(
        self, role: Optional[str] = None, last_login_after: Optional[datetime] = None
    ) -> List[User]:
        """Get users filtered by last login time and optionally by role."""
        raise NotImplementedError
