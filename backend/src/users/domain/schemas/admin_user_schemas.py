# admin_user_schemas.py
from datetime import datetime
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from src.users.domain.entities.user import UserRole
from src.users.domain.schemas.user_schemas import UserProfile


class AdminUserCreate(UserProfile):
    """Admin-specific user creation with role assignment"""

    password: str
    is_enabled_account: bool = True
    is_verified_email: bool = False
    roles: Set[UserRole] = Field(default_factory=lambda: {UserRole.USER})


class AdminUserUpdate(BaseModel):
    """Admin-specific user updates"""

    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_enabled_account: Optional[bool] = None
    is_verified_email: Optional[bool] = None
    roles: Optional[Set[UserRole]] = None


class AdminUserResponse(UserProfile):
    """Extended response with admin-only fields"""

    id: str
    is_enabled_account: bool
    is_verified_email: bool
    roles: Set[UserRole]
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class UpdateUserRolesRequest(BaseModel):
    """Request model for updating user roles."""

    roles: List[UserRole] = Field(
        ...,
        description="List of roles to assign to the user",
        example=["user", "admin"],
    )
