"""HTTP dependencies for the users package.

This module contains FastAPI dependencies that handle HTTP-specific concerns
like authentication, request validation, and response formatting.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from src.users.dependencies.domain import TokenServiceDep
from src.users.domain.services.token_service import TokenType

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user_id(
    token_service: TokenServiceDep,
    token: str = Depends(oauth2_scheme),
) -> UUID:
    """Dependency to get the current user ID from the token.

    This dependency extracts and validates the JWT token from the Authorization header
    and returns the user ID if the token is valid.

    Raises:
        HTTPException: 401 if the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        is_valid, user = await token_service.verify_token(
            token=token, token_type=TokenType.ACCESS
        )
        if not is_valid or not user or not user.id:
            raise credentials_exception
        return user.id
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise credentials_exception from e


# Type alias for the current user ID dependency
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
