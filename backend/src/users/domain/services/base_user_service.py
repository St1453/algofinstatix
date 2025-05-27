"""Base service with common user-related functionality."""

from __future__ import annotations

import logging
from typing import Generic, TypeVar

from pydantic import EmailStr

from src.users.domain.entities.user import User
from src.users.domain.exceptions import UserNotFoundError
from src.users.domain.interfaces.user_repository import IUserRepository

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseUserService(Generic[T]):
    """Base service with common user-related functionality."""

    def __init__(self, user_repository: IUserRepository):
        """Initialize base service with required dependencies."""
        self.user_repository = user_repository

    async def _get_user_by_id(self, user_id: str) -> User:
        """Get a user by ID with basic validation."""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user or user.deleted_at is not None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    async def _get_user_by_email(self, email: EmailStr) -> User:
        """Get a user by email with basic validation."""
        user = await self.user_repository.get_user_by_email(email)
        if not user or user.deleted_at is not None:
            raise UserNotFoundError(f"User with email {email} not found")
        return user
