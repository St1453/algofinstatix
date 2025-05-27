import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.users.application.user_management import UserManagement
from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    UserRegisterRequest,
)
from src.users.presentation.dependencies import get_current_user_id

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
) -> UserProfile:
    """
    Get the current authenticated user's information.

    Args:
        user_id: The ID of the authenticated user (from token)

    Returns:
        UserProfile: Detailed user information
    """
    try:
        return await UserManagement().get_user_profile(user_id)
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        logger.exception("Unexpected error fetching user profile")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.put("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_current_user(
    user_data: UserProfile,
    user_id: UUID = Depends(get_current_user_id),
) -> UserProfile:
    """
    Update the current user's information.

    Args:
        user_data: The updated user data
        user_id: The ID of the authenticated user (from token)

    Returns:
        UserProfile: Updated user information
    """
    try:
        updated_user = await UserManagement().update_user_profile(
            user_id=str(user_id), update_data=user_data.model_dump(exclude_unset=True)
        )
        return UserProfile.model_validate(updated_user.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/me", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    """
    Change the current user's password.

    Args:
        password_data: Current and new password information
        user_id: The ID of the authenticated user (from token)
    """
    try:
        await UserManagement().change_password(
            user_id=str(user_id),
            password_data=password_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    """
    Delete the current user's account (soft delete).

    Args:
        user_id: The ID of the authenticated user (from token)
    """
    try:
        await UserManagement().delete_user_profile(str(user_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserRegisterRequest,
) -> UserProfile:
    """
    Register a new user.

    Args:
        user_data: User registration data including email, passwords, and
            optional fields

    Returns:
        UserProfile: The created user information
    """
    try:
        user = await UserManagement().register_user(user_data)
        return UserProfile.model_validate(user.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
