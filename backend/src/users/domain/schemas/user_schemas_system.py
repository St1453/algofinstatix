"""
Pydantic schemas for user-related requests and responses.

This module defines the data models used for request validation and response formatting
in the user management system.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, Field

from src.users.domain.schemas.user_schemas import (
    ChangePasswordRequest,
    UserProfile,
    UserRegisterRequest,
)
from src.users.domain.value_objects.hashed_password import HashedPassword

# Type variable for model validation
ModelData = TypeVar("ModelData", bound=dict)


# user response models below


class UserProfileResponse(UserProfile):
    """Base schema with common user fields.
    it can be used when user is updated or registered
    """

    id: str = Field(
        ...,
        description="User's unique identifier",
        example="550e8400-e29b-41d4-a716-446655440000",
    )


class ChangePasswordResponse(BaseModel):
    """Schema for changing password request.

    Used when a user wants to change their own password.
    Requires the current password for verification.
    """

    user_id: str

    new_hashed_password: HashedPassword

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "new_hashed_password": "NewSecurePass123!",
            }
        }
    }

    @classmethod
    def from_change_password_request(
        cls, user_id: str, change_password_request: ChangePasswordRequest
    ) -> "ChangePasswordResponse":
        """Create from change password request."""
        return cls(
            user_id=user_id,
            new_hashed_password=HashedPassword.from_raw_password(
                change_password_request.new_password
            ),
        )


class UserRegistrationInfo(UserProfile):
    """Schema for user registration with hashed password.
    This schema is used when a new user registers.
    It is used by infrastructure layer to create a new user.
    """

    hashed_password: HashedPassword

    @classmethod
    def from_register_request(
        cls, register_request: UserRegisterRequest
    ) -> "UserRegistrationInfo":
        """Create from registration request with hashed password."""
        return cls(
            email=register_request.email,
            hashed_password=HashedPassword.from_raw_password(register_request.password),
            first_name=register_request.first_name,
            last_name=register_request.last_name,
            username=register_request.username,
            profile_picture=register_request.profile_picture,
            user_intro=register_request.user_intro,
        )
