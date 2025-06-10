import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.users.dependencies.dependencies import (
    CurrentUserId,
)
from src.users.dependencies.services import UserAuthManagementDep
from src.users.domain.schemas.token_schemas import TokenResponse
from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    VerifyEmailRequest,
)

# Configure logger
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    auth_management: UserAuthManagementDep,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    request_info = {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else "unknown",
    }

    async with auth_management as am:
        return await am.login(
            email=form_data.username,
            password=form_data.password,
            request_info=request_info,
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    auth_management: UserAuthManagementDep,
    refresh_token: str,
) -> None:
    """
    Logout the current user.
    """
    try:
        async with auth_management as am:
            await am.logout(refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    auth_management: UserAuthManagementDep,
    refresh_token: str,
) -> TokenResponse:
    """
    Refresh an access token using a refresh token.
    """
    try:
        async with auth_management as am:
            access_token, new_refresh_token = await am.refresh_tokens(refresh_token)
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    user_id: CurrentUserId,
    auth_management: UserAuthManagementDep,
) -> Dict[str, Any]:
    """
    Change the current user's password.

    This endpoint allows authenticated users to change their password by providing
    their current password and a new password with confirmation.

    Args:
        password_data: Contains current_password, new_password, and new_password_confirm
        user_id: The ID of the authenticated user (from JWT token)
        auth_management: Injected UserAuthManagement service

    Returns:
        Dict containing success status and message

    Raises:
        400: If current password is incorrect or new passwords don't match
        401: If user is not authenticated
        404: If user is not found
        500: For unexpected server errors
    """
    try:
        # Ensure the user is changing their own password
        if str(password_data.id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "Not authorized to change this user's password",
                },
            )

        async with auth_management as am:
            return await am.change_password(password_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/verify-email", response_model=UserProfile)
async def verify_email(
    request: VerifyEmailRequest,
    auth_management: UserAuthManagementDep,
) -> UserProfile:
    """
    Verify a user's email address using the verification token.

    Args:
        request: Contains the verification token

    Returns:
        UserProfile: The updated user profile with email verified

    Raises:
        400: If the token is invalid or expired
        404: If the user is not found
        500: For unexpected errors
    """
    try:
        async with auth_management as am:
            user = await am.verify_email(request)
            return UserProfile.model_validate(user.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    request: VerifyEmailRequest,
    auth_management: UserAuthManagementDep,
) -> dict[str, str]:
    """
    Resend the verification email to the specified email address.

    Args:
        request: Contains the email address to resend verification to

    Returns:
        dict: Success message

    Note:
        This endpoint always returns 202 Accepted for security reasons,
        even if the email doesn't exist in our system.
    """
    try:
        async with auth_management as am:
            await am.resend_verification_email(request.email)
        return {"message": "If the email exists, a verification email has been sent"}
    except Exception as e:
        # Still return 202 to prevent email enumeration
        logger.error(f"Error resending verification email: {str(e)}")
        return {"message": "If the email exists, a verification email has been sent"}
