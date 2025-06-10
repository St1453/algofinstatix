from abc import ABC, abstractmethod
from typing import Any, Dict

from src.users.domain.entities.user import User


class IUserService(ABC):
    """Interface for user service operations."""

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> User:
        """Get a user by their ID."""
        ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        """Get a user by their email address."""
        ...

    @abstractmethod
    async def get_my_profile(self, user_id: str) -> User:
        """Get the current user's profile."""
        ...

    @abstractmethod
    async def update_my_profile(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> User:
        """Update the current user's profile."""
        ...

    @abstractmethod
    async def delete_my_profile(self, user_id: str, password: str) -> bool:
        """Soft-delete the current user's profile after password verification."""
        ...
