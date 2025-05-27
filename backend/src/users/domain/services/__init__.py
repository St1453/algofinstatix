"""Users domain services.

This module contains the domain service implementations that encapsulate
complex business logic and orchestration for the users domain.
"""

from __future__ import annotations

# Import all public API
from .admin_user_service import AdminUserService  # noqa: F401
from .auth_service import AuthService  # noqa: F401
from .base_user_service import BaseUserService  # noqa: F401
from .password_service import PasswordService  # noqa: F401
from .user_service import UserService  # noqa: F401

# Public API
__all__ = [
    'AdminUserService',
    'AuthService',
    'BaseUserService',
    'PasswordService',
    'UserService',
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
