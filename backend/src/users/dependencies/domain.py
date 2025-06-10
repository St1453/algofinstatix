"""Domain layer dependencies.

This module provides factory functions for creating domain service instances
with their required dependencies.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends
from typing_extensions import Annotated

from src.core.config import get_settings

# Import interfaces for type hints
from src.users.domain.interfaces import (
    IAuthService,
    IEmailService,
    IPasswordService,
    ITokenService,
    IUserRegistrationService,
    IUserService,
)

if TYPE_CHECKING:
    from .types import UOW


@lru_cache(maxsize=1)
def get_uow() -> UOW:
    """Get a cached Unit of Work instance.

    Returns:
        IUnitOfWork: A Unit of Work instance
    """
    from src.shared.infrastructure.database.session import get_session_factory
    from src.users.infrastructure.database.unit_of_work import UnitOfWork

    session_factory = get_session_factory()
    return UnitOfWork(session_factory=session_factory)


@lru_cache(maxsize=1)
def get_user_service() -> IUserService:
    """Get a cached UserService instance.

    Returns:
        IUserService: Configured instance of UserService with all dependencies
    """
    from src.users.domain.services.user_service import UserService

    uow = get_uow()
    return UserService(uow)


@lru_cache(maxsize=1)
def get_auth_service() -> IAuthService:
    """Get a cached AuthService instance.

    Returns:
        IAuthService: Configured instance of AuthService with all dependencies
    """
    from src.users.domain.services.auth_service import AuthService

    uow = get_uow()
    token_service = get_token_service()
    password_service = get_password_service()
    return AuthService(
        password_service=password_service, token_service=token_service, uow=uow
    )


@lru_cache(maxsize=1)
def get_token_service() -> ITokenService:
    """Get a cached TokenService instance.

    Returns:
        ITokenService: Configured instance of TokenService with security settings
    """
    from src.users.domain.services.token_service import TokenService

    settings = get_settings()
    return TokenService(
        uow=get_uow(),
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_token_expire_seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        refresh_token_expire_seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    )


@lru_cache(maxsize=1)
def get_password_service() -> IPasswordService:
    """Get a cached PasswordService instance.

    Returns:
        PasswordService: Configured instance of PasswordService with all dependencies
    """
    from src.users.domain.services.password_service import PasswordService

    uow = get_uow()
    return PasswordService(uow=uow)


@lru_cache(maxsize=1)
def get_email_service() -> IEmailService:
    """Get a cached EmailService instance.

    Returns:
        EmailService: Configured instance of EmailService with email settings
    """
    from src.users.domain.services.email_service import EmailService

    settings = get_settings()
    return EmailService(
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_HOST_USER,
        smtp_password=settings.SMTP_HOST_PASSWORD,
        base_url=settings.BASE_URL,
        sender_email=settings.SMTP_HOST_USER,
        sender_name="AlgoFinStatix",
    )


def get_uow_factory():
    """Create a function that returns a new UoW instance."""
    from src.shared.infrastructure.database.session import get_session_factory
    from src.users.infrastructure.database.unit_of_work import UnitOfWork
    
    def _create_uow():
        session_factory = get_session_factory()
        return UnitOfWork(session_factory=session_factory)
        
    return _create_uow

@lru_cache(maxsize=1)
def get_user_registration_service() -> IUserRegistrationService:
    """Get a cached UserRegistrationService instance.

    Returns:
        UserRegistrationService: Configured instance of UserRegistrationService
    """
    from src.users.domain.services.user_registration_service import (
        UserRegistrationService,
    )

    email_service = get_email_service()
    password_service = get_password_service()
    return UserRegistrationService(
        uow_factory=get_uow_factory(),
        password_service=password_service,
        email_service=email_service
    )


# Type aliases for FastAPI dependency injection
UserServiceDep = Annotated[IUserService, Depends(get_user_service)]
AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]
TokenServiceDep = Annotated[ITokenService, Depends(get_token_service)]
PasswordServiceDep = Annotated[IPasswordService, Depends(get_password_service)]
EmailServiceDep = Annotated[IEmailService, Depends(get_email_service)]
UserRegistrationServiceDep = Annotated[
    IUserRegistrationService,
    Depends(get_user_registration_service),
]
# Re-export for backward compatibility
__all__ = [
    "UserServiceDep",
    "AuthServiceDep",
    "TokenServiceDep",
    "PasswordServiceDep",
    "EmailServiceDep",
    "UserRegistrationServiceDep",
    "UOW",
    "get_uow",
    "get_user_service",
    "get_auth_service",
    "get_token_service",
    "get_password_service",
    "get_email_service",
    "get_user_registration_service",
]
