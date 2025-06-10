"""Users domain services.

This module contains the domain service implementations that encapsulate
complex business logic and orchestration for the users domain.
"""

from __future__ import annotations

# Import all public API
from .auth_service import AuthService  # noqa: F401
from .email_service import EmailService, IEmailService  # noqa: F401
from .password_service import PasswordService  # noqa: F401
from .token_service import TokenService  # noqa: F401
from .user_registration_service import UserRegistrationService  # noqa: F401
from .user_service import UserService  # noqa: F401

# Public API
__all__ = [
    "AuthService",
    "EmailService",
    "IEmailService",
    "PasswordService",
    "TokenService",
    "UserRegistrationService",
    "UserService",
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
