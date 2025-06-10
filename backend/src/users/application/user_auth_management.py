"""User authentication management application service.

This module provides the UserAuthManagement class which handles all
authentication-related operations, including login, logout, token management,
and email verification.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import HTTPException, status

from src.users.domain.exceptions import TokenError, UserNotFoundError
from src.users.domain.interfaces.auth_service import IAuthService
from src.users.domain.interfaces.email_service import IEmailService
from src.users.domain.interfaces.password_service import IPasswordService
from src.users.domain.interfaces.token_service import ITokenService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.interfaces.user_service import IUserService
from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    VerifyEmailRequest,
)
from src.users.domain.value_objects.token_value_objects import TokenType

logger = logging.getLogger(__name__)


class UserAuthManagement:
    """Application service for user authentication operations.

    This class handles all authentication-related operations including:
    - User login/logout
    - Token management (access/refresh)
    - Email verification
    - Password management

    It strictly follows the Unit of Work pattern for transaction management.
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        auth_service: IAuthService,
        token_service: ITokenService,
        user_service: IUserService,
        password_service: IPasswordService,
        email_service: IEmailService,
    ):
        """Initialize with all required dependencies.

        Args:
            uow: Unit of Work instance for managing transactions and repositories
            auth_service: Service for authentication operations
            token_service: Service for token operations
            user_service: Service for user-related operations
            password_service: Service for password hashing and verification
            email_service: Service for sending emails
        """
        self._uow = uow
        self._auth_service = auth_service
        self._token_service = token_service
        self._user_service = user_service
        self._password_service = password_service
        self._email_service = email_service

    @property
    def auth_service(self) -> IAuthService:
        """Get the auth service instance."""
        return self._auth_service

    @property
    def password_service(self) -> IPasswordService:
        """Get the password service instance."""
        return self._password_service

    @property
    def token_service(self) -> ITokenService:
        """Get the token service instance."""
        return self._token_service

    @property
    def user_service(self) -> IUserService:
        """Get the user service instance."""
        return self._user_service

    @property
    def email_service(self) -> IEmailService:
        """Get the email service instance."""
        return self._email_service

    async def __aenter__(self) -> "UserAuthManagement":
        """Context manager entry."""
        await self._uow.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit, ensures proper cleanup."""
        await self._uow.__aexit__(exc_type, exc_val, exc_tb)
        await self._uow.close()

    async def login(
        self,
        email: str,
        password: str,
        request_info: Dict[str, str],
    ) -> Dict[str, Any]:
        """Login a user with email and password.

        Args:
            email: User's email
            password: User's password
            request_info: Dictionary containing request information
                like user_agent and ip_address

        Returns:
            Dict containing access_token, refresh_token, and token_type

        Raises:
            HTTPException: If authentication fails or email is not verified
        """
        try:
            async with self._uow.transaction():
                # Authenticate user
                user, token_data = await self.auth_service.authenticate_user(
                    email, password, request_info
                )
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect email or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # Check if email is verified
                if not user.status.is_verified:
                    # Create a new verification token
                    verification_token = (
                        await self.token_service.create_email_verification_token(
                            user, request_info
                        )
                    )

                    # Send verification email (in background)
                    try:
                        await self.email_service.send_verification_email(
                            email=user.email,
                            token=verification_token,
                            username=user.username,
                        )
                    except Exception as email_error:
                        logger.error(
                            "Failed to send verification email: %s",
                            str(email_error),
                            exc_info=True,
                        )

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="""Email not verified. 
                        A new verification link has been sent to your email.""",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                return token_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed for {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token to use for refreshing

        Returns:
            Dict containing new access_token and refresh_token

        Raises:
            HTTPException: If refresh fails
        """
        try:
            async with self._uow.transaction():
                result = await self.token_service.refresh_access_token(refresh_token)
                access_token, new_refresh_token = result
                if not access_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid refresh token",
                    )
                return {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token refresh failed: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh token",
            ) from e

    async def logout(self, refresh_token: str) -> Dict[str, str]:
        """Logout the current user.

        Args:
            refresh_token: The refresh token to use for logging out

        Returns:
            Dict: {"message": "Successfully logged out"}

        Raises:
            HTTPException: If logout fails
        """
        try:
            async with self._uow.transaction():
                await self.token_service.revoke_token(refresh_token)
                return {"message": "Successfully logged out"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Logout failed: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout",
            ) from e

    async def change_password(self, data: ChangePasswordRequest) -> Dict[str, Any]:
        """Change the current user's password.

        This method handles the password change process including:
        - Verifying the current password
        - Updating to the new password
        - Invalidating existing sessions

        Args:
            data: ChangePasswordRequest containing:
                - id: User's unique identifier
                - current_password: Current password for verification
                - new_password: New password to set
                - new_password_confirm: Confirmation of new password

        Returns:
            Dict containing success message and user ID

        Raises:
            HTTPException:
                - 400: If current password is incorrect or new passwords don't match
                - 404: If user is not found
                - 500: For unexpected errors
        """
        try:
            async with self._uow.transaction():
                # Get user by ID
                user = await self.user_service.get_my_profile(data.id)
                if not user:
                    raise UserNotFoundError(f"User with ID {data.id} not found")

                # Verify current password matches
                if not await self.password_service.verify_password(
                    data.current_password, user.hashed_password
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "invalid_current_password",
                            "message": "The current password is incorrect"
                        }
                    )

                # Verify new password and confirmation match
                if data.new_password != data.new_password_confirm:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "password_mismatch",
                            "message": "New password and confirmation do not match"
                        }
                    )

                # Hash new password
                new_hashed_password = self.password_service.hash_password(
                    data.new_password
                )

                # Update user with new password
                await self.user_service.update_my_profile(
                    user.id, {"hashed_password": new_hashed_password}
                )

                # Invalidate all existing sessions
                await self.token_service.revoke_user_tokens(user.id)


                logger.info(f"Password changed successfully for user {user.id}")
                return {
                    "success": True,
                    "data": {
                        "message": "Password updated successfully",
                        "user_id": str(user.id)
                    }
                }


        except HTTPException:
            raise
        except UserNotFoundError as e:
            logger.warning(f"User not found during password change: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "user_not_found",
                    "message": str(e)
                }
            ) from e
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "password_change_failed",
                    "message": "An error occurred while changing the password"
                }
            ) from e

    async def verify_email(self, token: VerifyEmailRequest) -> UserProfile:
        """Verify a user's email using a verification token.

        Args:
            token: Verification token received via email

        Returns:
            UserProfile: The updated user profile

        Raises:
            HTTPException:
                - 400 if token is invalid or expired
                - 404 if user not found
                - 500 for unexpected errors
        """
        try:
            async with self._uow.transaction():
                # Verify and decode token
                payload = await self.token_service.verify_token(
                    token.token, TokenType.EMAIL_VERIFICATION
                )
                if not payload or "sub" not in payload:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid or expired verification token",
                    )

                user_id = payload["sub"]
                user = await self.user_service.get_my_profile(user_id)
                if not user:
                    raise UserNotFoundError("User not found")

                # Skip if already verified
                if user.status.is_verified:
                    return UserProfile.model_validate(user.__dict__)

                # Update user's email verification status
                updated_user = await self.user_service.update_my_profile(
                    user_id, {"status": user.status.with_updates(is_verified=True)}
                )

                # Revoke the used token
                await self.token_service.revoke_token(token.token)

                return UserProfile.model_validate(updated_user.__dict__)

        except TokenError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Email verification failed: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email",
            ) from e

    async def resend_verification_email(self, email: str) -> Dict[str, str]:
        """Resend email verification for a user.

        This method will:
        1. Find the user by email
        2. Revoke any existing email verification tokens
        3. Create a new verification token
        4. Send a verification email

        Args:
            email: The email address of the user

        Returns:
            Dict: {"message": "Verification email resent"}

        Note:
            This method is designed to not leak info about whether an email exists.
            It will always return success even if the email doesn't exist.
        """
        try:
            async with self._uow.transaction():
                # Find user by email
                user = await self.user_service.get_user_by_email(email)
                if not user:
                    # Don't reveal if the email exists or not
                    logger.info("Email not found during verification resend: %s", email)
                    return {"message": "A verification link has been sent"}

                # Check if email is already verified
                if user.status.is_verified:
                    logger.info("Email already verified: %s", email)
                    return {"message": "A verification link has been sent"}

                # Revoke any existing verification tokens
                await self.token_service.revoke_user_tokens(
                    user_id=user.id, token_type=TokenType.EMAIL_VERIFICATION
                )

                # Create a new verification token
                verification_token = (
                    await self.token_service.create_email_verification_token(
                        user, {"user_agent": "resend-verification"}
                    )
                )

                # Send verification email with the new token
                try:
                    await self.email_service.send_verification_email(
                        email=user.email,
                        token=verification_token,
                        username=user.username,
                    )
                    logger.info("Verification email sent to: %s", user.email)
                except Exception as email_error:
                    logger.error(
                        "Failed to send verification email to %s: %s",
                        user.email,
                        str(email_error),
                        exc_info=True,
                    )
                    # Don't fail the request if email sending fails

                return {"message": "A verification link has been sent"}

        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to resend verification email: %s",
                str(e),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend verification email",
            ) from e
