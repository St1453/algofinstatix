"""Authentication service for user authentication and session management."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError, jwt
from pydantic import EmailStr

from src.core.config import settings
from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from src.users.domain.interfaces.user_repository import IUserRepository
from src.users.domain.services.base_user_service import BaseUserService
from src.users.domain.value_objects.hashed_password import HashedPassword

logger = logging.getLogger(__name__)


class AuthService(BaseUserService):
    """Service handling user authentication and session management."""

    def __init__(
        self,
        user_repository: IUserRepository,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
        access_token_expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ):
        """Initialize auth service with configuration."""
        super().__init__(user_repository)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    async def authenticate_user(
        self,
        email: EmailStr,
        password: str,
        require_verified_email: bool = True,
    ) -> User:
        """Authenticate a user with email and password.

        Args:
            email: User's email
            password: Plain text password
            require_verified_email: Whether to require email verification

        Returns:
            User: Authenticated user

        Raises:
            UserNotFoundError: If user doesn't exist
            AccountNotVerifiedError: If email verification is required but not completed
            AccountLockedError: If account is locked due to too many failed attempts
            InvalidCredentialsError: If credentials are invalid
            AuthenticationError: For other authentication errors
        """
        try:
            # Get user by email
            user = await self._get_user_by_email(email)

            # Check if account is locked
            if user.status.is_locked:
                logger.warning("Login attempt for locked account: %s", email)
                raise AccountLockedError(
                    f"Account is locked. Please try again later or reset your password."
                )

            # Check email verification
            if require_verified_email and not user.status.is_verified:
                logger.info("Login attempt with unverified email: %s", email)
                raise AccountNotVerifiedError(
                    "Please verify your email before logging in"
                )

            # Verify password
            if not user.hashed_password.verify(password):
                # Record failed attempt
                user.status.record_failed_login()
                await self.user_repository.update_user(user.id, {"status": user.status})
                
                remaining = user.status.remaining_attempts
                error_msg = f"Invalid credentials. {remaining} attempts remaining."
                logger.warning(
                    "Failed login attempt for user %s. %s attempts remaining.",
                    email,
                    remaining,
                )
                raise InvalidCredentialsError(error_msg)

            # Authentication successful - update last login
            user.status.record_successful_login()
            await self.user_repository.update_user(user.id, {
                "last_login_at": datetime.now(timezone.utc),
                "status": user.status
            })
            
            logger.info("Successful login for user: %s", email)
            return user

        except (UserNotFoundError, AccountNotVerifiedError, AccountLockedError, InvalidCredentialsError):
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during authentication for %s: %s",
                email,
                str(e),
                exc_info=True,
            )
            raise AuthenticationError("An error occurred during authentication") from e

    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for the user.
        
        Args:
            user: User to create token for
            
        Returns:
            str: JWT access token
        """
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta
        
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
            "type": "access",
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(self, token: str) -> Tuple[bool, Optional[User]]:
        """Verify a JWT token and return the associated user.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Tuple[bool, Optional[User]]: (is_valid, user)
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                return False, None
                
            try:
                user = await self._get_user_by_id(user_id)
                return True, user
            except UserNotFoundError:
                return False, None
                
        except JWTError:
            return False, None
