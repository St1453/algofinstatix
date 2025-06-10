"""Authentication and token management service."""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple
from uuid import UUID

from pydantic import EmailStr

from src.users.domain.entities.token import Token
from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    AccountDisabledError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    TokenError,
)
from src.users.domain.interfaces.auth_service import IAuthService
from src.users.domain.interfaces.password_service import IPasswordService
from src.users.domain.interfaces.token_service import ITokenService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


class AuthService(IAuthService):
    """Handles authentication and token management.

    This service is responsible for:
    - User authentication
    - Token pair generation and validation
    - Token revocation
    """

    def __init__(
        self,
        password_service: IPasswordService,
        token_service: ITokenService,
        uow: IUnitOfWork,
    ) -> None:
        """Initialize with required dependencies.

        Args:
            password_service: Password service for hashing/verification
            token_service: Service for token operations
            uow: Unit of Work for transaction management
        """
        self.password_service = password_service
        self.token_service = token_service
        self.uow = uow

    async def authenticate_user(
        self,
        email: EmailStr,
        password: str,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[User, Dict[str, str]]:
        """Authenticate a user with email and password and create a new session.

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (User, token_data) if authentication is successful

        Raises:
            InvalidCredentialsError: If email or password is incorrect
            AccountDisabledError: If the account is disabled
            AuthenticationError: If authentication fails for any other reason
        """
        try:
            async with self.uow.transaction():
                # Get user by email
                user = await self.uow.users.get_user_by_email(email)
                if not user:
                    logger.warning("Login attempt with non-existent email: %s", email)
                    raise InvalidCredentialsError("Invalid email or password")

                # Check if account is enabled
                if not user.status.is_enabled:
                    logger.warning("Login attempt for disabled account: %s", email)
                    raise AccountDisabledError("Account is disabled")

                # Verify password
                if not await self.password_service.verify_password(
                    password, user.hashed_password
                ):
                    logger.warning("Invalid password for user: %s", email)
                    raise InvalidCredentialsError("Invalid email or password")

                # Check if email is verified if required
                if not user.status.is_verified:
                    logger.warning("Login attempt with unverified email: %s", email)
                    raise AccountNotVerifiedError("Please verify your email first")

                # Generate token pair
                token_data = await self.create_token_pair(user)
                access_token, refresh_token, _, _ = token_data

                return user, {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                }

        except (InvalidCredentialsError, AccountDisabledError, AccountNotVerifiedError):
            # Re-raise expected exceptions
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during authentication for %s: %s",
                email,
                str(e),
            )
            raise AuthenticationError("An error occurred during authentication") from e

    async def create_token_pair(
        self,
        user: User,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, Token, Token]:
        """Create access and refresh token pair for a user.

        Args:
            user: The authenticated user
            request_info: Optional request metadata (e.g., user_agent, ip_address)

        Returns:
            Tuple containing:
            - access_token: JWT access token
            - refresh_token: Opaque refresh token
            - access_token_entity: Access token entity
            - refresh_token_entity: Refresh token entity
        """
        try:
            # Create refresh token first
            refresh_result = await self.token_service.create_refresh_token(
                user=user,
                request_info=request_info,
            )
            refresh_token_str, refresh_token = refresh_result

            # Create access token with refresh token ID
            access_result = await self.token_service.create_access_token(
                user=user,
                refresh_token_id=refresh_token.id,
                request_info=request_info,
            )
            access_token_str, access_token = access_result

            return {
                "access_token": access_token_str,
                "refresh_token": refresh_token_str,
                "token_type": "bearer",
            }

        except Exception as e:
            logger.error(
                "Error creating token pair for user %s: %s",
                user.id,
                str(e),
                exc_info=True,
            )
            raise AuthenticationError("Failed to create token pair") from e

    async def refresh_token_pair(
        self,
        refresh_token: str,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, Token, Token]:
        """Refresh an access token using a valid refresh token.

        Args:
            refresh_token: Valid refresh token
            request_info: Optional request metadata

        Returns:
            Tuple containing new access_token, refresh_token, and their entities

        Raises:
            TokenError: If refresh token is invalid or expired
            AuthenticationError: If refresh fails
        """
        try:
            async with self.uow.transaction():
                # Verify and get refresh token entity
                token_entity = await self.uow.tokens.get_by_token(refresh_token)
                if not token_entity or token_entity.is_revoked:
                    raise TokenError("Invalid or expired refresh token")

                # Get user associated with the token
                user = await self.uow.users.get_user_by_id(token_entity.user_id)
                if not user:
                    raise TokenError("User not found")

                # Revoke the old refresh token
                await self.token_service.revoke_token(refresh_token)

                # Create new token pair
                return await self.create_token_pair(user, request_info)

        except TokenError:
            raise
        except Exception as e:
            logger.error(
                "Error refreshing token: %s",
                str(e),
                exc_info=True,
            )
            raise AuthenticationError("Failed to refresh token") from e

    async def revoke_token(self, token: str) -> bool:
        """Revoke a specific token.

        Args:
            token: The token to revoke

        Returns:
            bool: True if token was successfully revoked
        """
        try:
            return await self.token_service.revoke_token(token)
        except Exception as e:
            logger.error(
                "Error revoking token: %s",
                str(e),
                exc_info=True,
            )
            return False

    async def revoke_all_tokens(self, user_id: UUID) -> int:
        """Revoke all tokens for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Number of tokens revoked
        """
        try:
            return await self.token_service.revoke_user_tokens(user_id)
        except Exception as e:
            logger.error(
                "Error revoking all tokens for user %s: %s",
                user_id,
                str(e),
                exc_info=True,
            )
            return 0
