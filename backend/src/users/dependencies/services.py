"""Application service dependencies.

This module contains dependency providers for application services.
"""

import logging
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends

from src.users.application.user_auth_management import UserAuthManagement
from src.users.application.user_management import UserManagement
from src.users.dependencies.domain import (
    get_auth_service,
    get_email_service,
    get_password_service,
    get_token_service,
    get_uow,
    get_user_registration_service,
    get_user_service,
)


def get_uow_factory():
    """Create a function that returns a new UoW instance."""
    from src.shared.infrastructure.database.session import get_session_factory
    from src.users.infrastructure.database.unit_of_work import UnitOfWork
    
    def _create_uow():
        session_factory = get_session_factory()
        return UnitOfWork(session_factory=session_factory)
        
    return _create_uow

@asynccontextmanager
async def get_user_management() -> AsyncIterator[UserManagement]:
    """Get a UserManagement instance with all its dependencies.

    This is an async context manager that ensures proper cleanup of resources.
    It creates a new UserManagement instance with all required services and
    manages its lifecycle.

    Yields:
        UserManagement: Configured instance of UserManagement with all required services
    """
    # Create a new UoW factory for this request
    uow_factory = get_uow_factory()
    
    # Create the UserManagement instance with all dependencies
    user_management = UserManagement(
        uow_factory=uow_factory,
        user_service=get_user_service(),
        user_registration_service=get_user_registration_service(),
        token_service=get_token_service(),
        email_service=get_email_service(),
    )
    
    # Enter the UserManagement context
    async with user_management as um:
        try:
            yield um
        except Exception as e:
            # Log the error and re-raise
            logger = logging.getLogger(__name__)
            logger.error(f"Error in user management operation: {str(e)}", exc_info=True)
            raise


@asynccontextmanager
async def get_user_auth_management() -> AsyncIterator[UserAuthManagement]:
    """Get a UserAuthManagement instance with all its dependencies.

    This is an async context manager that ensures proper cleanup of resources.

    Yields:
        UserAuthManagement: Configured instance of UserAuthManagement 
        with all required services
    """
    user_auth_management = UserAuthManagement(
        uow=get_uow(),
        auth_service=get_auth_service(),
        token_service=get_token_service(),
        email_service=get_email_service(),
        user_service=get_user_service(),
        password_service=get_password_service(),
    )
    
    async with user_auth_management:
        yield user_auth_management


# Type aliases for FastAPI dependency injection
UserManagementDep = Annotated[UserManagement, Depends(get_user_management)]
UserAuthManagementDep = Annotated[UserAuthManagement, Depends(get_user_auth_management)]
