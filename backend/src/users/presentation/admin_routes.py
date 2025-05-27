import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.users.application.admin_user_management import AdminUserManagement
from src.users.domain.exceptions import UserNotFoundError
from src.users.domain.schemas.admin_user_schemas import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    UpdateUserRolesRequest,
)
from src.users.presentation.dependencies import get_current_admin_user

# Configure logger
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.post(
    "/",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def create_user(
    user_data: AdminUserCreate,
) -> AdminUserResponse:
    """
    Create a new user (Admin only).

    - **user_data**: User details including email, name, and password
    - **Requires admin privileges**
    """

    async with AdminUserManagement() as admin_mgmt:
        try:
            return await admin_mgmt.create_user(user_data)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{user_id}/roles",
    response_model=AdminUserUpdate,
    status_code=status.HTTP_200_OK,
    summary="Update user roles (Admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def update_user_roles(
    user_id: UUID,
    roles_data: UpdateUserRolesRequest,
) -> AdminUserUpdate:
    """
    Update roles for a specific user.

    - **user_id**: ID of the user to update
    - **roles**: List of roles to assign to the user
    - **Requires admin privileges**
    """

    async with AdminUserManagement() as admin_mgmt:
        try:
            return await admin_mgmt.update_user_roles(str(user_id), roles_data.roles)
        except UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error updating user roles: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{user_id}",
    response_model=AdminUserResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get user details (Admin only)",
)
async def get_user(
    user_id: UUID,
) -> AdminUserResponse:
    """
    Get detailed information about a user.

    - **user_id**: ID of the user to retrieve
    - **Requires admin privileges**
    """

    async with AdminUserManagement() as admin_mgmt:
        try:
            return await admin_mgmt.get_user_by_id(str(user_id))
        except UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{user_id}/enable",
    response_model=AdminUserUpdate,
    dependencies=[Depends(get_current_admin_user)],
    summary="Enable a user account (Admin only)",
)
async def enable_user(
    user_id: UUID,
) -> AdminUserUpdate:
    """
    Enable a user account.

    - **user_id**: ID of the user to enable
    - **Requires admin privileges**
    """

    async with AdminUserManagement() as admin_mgmt:
        try:
            return await admin_mgmt.enable_user(str(user_id))
        except UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{user_id}/disable",
    response_model=AdminUserUpdate,
    dependencies=[Depends(get_current_admin_user)],
    summary="Disable a user account (Admin only)",
)
async def disable_user(
    user_id: UUID,
) -> AdminUserUpdate:
    """
    Disable a user account.

    - **user_id**: ID of the user to disable
    - **Requires admin privileges**
    """

    async with AdminUserManagement() as admin_mgmt:
        try:
            return await admin_mgmt.disable_user(str(user_id))
        except UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
