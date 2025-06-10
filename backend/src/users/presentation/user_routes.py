import logging

from fastapi import APIRouter, HTTPException, status

from src.users.dependencies.dependencies import (
    CurrentUserId,
)
from src.users.dependencies.services import UserManagementDep
from src.users.domain.schemas.user_schemas import (
    UserProfile,
    UserRegisterRequest,
)

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    user_management: UserManagementDep,
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
        async with user_management as um:
            user = await um.register_user(user_data)
            return UserProfile.model_validate(user.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_id: CurrentUserId,
    user_management: UserManagementDep,
) -> UserProfile:
    """
    Get the current authenticated user's information.

    Args:
        user_id: The ID of the authenticated user (from token)

    Returns:
        UserProfile: Detailed user information
    """
    try:
        async with user_management as um:
            user = await um.get_user_profile(user_id)
            return UserProfile.model_validate(user.__dict__)
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
    user_id: CurrentUserId,
    user_management: UserManagementDep,
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
        async with user_management as um:
            user = await um.update_user_profile(user_id, user_data)
            return UserProfile.model_validate(user.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user_id: CurrentUserId,
    user_management: UserManagementDep,
) -> None:
    """
    Delete the current user's account (soft delete).

    Args:
        user_id: The ID of the authenticated user (from token)
    """
    try:
        async with user_management as um:
            await um.delete_user_profile(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
