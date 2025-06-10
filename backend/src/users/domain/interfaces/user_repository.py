"""User service interface for user management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.users.domain.entities.user import User
    from src.users.domain.schemas.user_schemas import (
        UserProfile,
        UserRegistrationInfo,
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
        ...

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
        ...

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
        ...

    @abstractmethod
    async def register_user(
        self, user_data: UserRegistrationInfo
    ) -> User:
        """Register a new user.

        Args:
            user_data: The user registration data

        Returns:
            User: The created user entity

        Raises:
            UserAlreadyExistsError: If a user with the email already exists
            ValueError: If the provided data is invalid
        """
        ...

    @abstractmethod
    async def update_user_by_id(
        self, user_id: str, update_data: UserProfile
    ) -> Optional[User]:
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
        ...

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
        ...
