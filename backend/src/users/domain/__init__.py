"""Users domain package.

This package contains the core domain models, value objects, interfaces,
and services for the users domain.
"""
from __future__ import annotations

# Import all public API
from .entities.user import User  # noqa: F401
from .exceptions import (  # noqa: F401
    UserAlreadyExistsError,
    UserAuthenticationError,
    UserError,
    UserNotAuthorizedError,
    UserNotFoundError,
    UserUpdateError,
    UserValidationError,
)
from .interfaces.user_repository import IUserRepository  # noqa: F401
from .services.user_service import UserService  # noqa: F401

__all__ = [
    # Models
    "User",
    # Interfaces
    "IUserRepository",
    # Services
    "UserService",
    # Exceptions
    "UserError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserUpdateError",
    "UserAuthenticationError",
    "UserNotAuthorizedError",
    "UserValidationError",
]  # Public API
