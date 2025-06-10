"""Dependency injection module for users package.

This module provides all the necessary dependencies for the users package,
including domain services, application services, and HTTP dependencies.
"""

# HTTP dependencies
from .dependencies import (
    CurrentUserId,
    get_current_user_id,
    oauth2_scheme,
)

# Domain layer dependencies
from .domain import (
    AuthServiceDep,
    EmailServiceDep,
    PasswordServiceDep,
    TokenServiceDep,
    UserRegistrationServiceDep,
    UserServiceDep,
    get_auth_service,
    get_email_service,
    get_password_service,
    get_token_service,
    get_uow,
    get_user_registration_service,
    get_user_service,
)

# Application service dependencies
from .services import (
    UserAuthManagementDep,
    UserManagementDep,
    get_user_auth_management,
    get_user_management,
)

# Re-export for backward compatibility
__all__ = [
    # Domain layer
    "get_auth_service",
    "get_email_service",
    "get_password_service",
    "get_token_service",
    "get_uow",
    "get_user_registration_service",
    "get_user_service",
    "UserServiceDep",
    "AuthServiceDep",
    "TokenServiceDep",
    "PasswordServiceDep",
    "EmailServiceDep",
    "UserRegistrationServiceDep",
    # Application services
    "get_user_management",
    "get_user_auth_management",
    "UserManagementDep",
    "UserAuthManagementDep",
    # HTTP dependencies
    "get_current_user_id",
    "CurrentUserId",
    "oauth2_scheme",
]
