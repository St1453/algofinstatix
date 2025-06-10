"""
Pydantic schemas for user-related requests and responses.

This module defines the data models used for request validation and response formatting
in the user management system.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class UserProfile(BaseModel):
    """Schema representing a user's profile information.
    it can be used when user is updated or registered
    """

    email: str = Field(
        ..., description="User's email address", example="user@example.com"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's first name",
        example="John",
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's last name",
        example="Doe",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="""User's username 
        (alphanumeric with underscores and hyphens only, 3-32 chars)""",
        example="johndoe123",
    )
    profile_picture: Optional[str] = Field(
        None,
        description="URL to the user's profile picture",
        example="https://example.com/profile.jpg",
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief introduction about the user",
        example="Software developer and open source enthusiast",
    )

    @field_validator("email", mode="before")
    def normalize_and_validate_email(cls, v: Any) -> str:
        """Validate and normalize email address.

        Args:
            v: The email string to validate

        Returns:
            str: Normalized email address in lowercase

        Raises:
            ValueError: If email is empty or invalid
        """
        if not v:
            raise ValueError("Email is required")
        return str(v)

    @field_validator("username", mode="before")
    def validate_username(cls, v: Any) -> str:
        """Validate and normalize username.

        Args:
            v: The username string to validate

        Returns:
            str: Normalized username in lowercase

        Raises:
            ValueError: If username is empty or invalid
        """
        if not v:
            raise ValueError("Username is required")
        return str(v)


class AuthenticatedUserRequest(BaseModel):
    """Base schema with common user fields.
    it contains id field.
    """

    id: str = Field(
        ...,
        description="User's unique identifier",
        example="550e8400-e29b-41d4-a716-446655440000",
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="""User's username 
        (alphanumeric with underscores and hyphens only, 3-32 chars)""",
        example="johndoe123",
    )

    @field_validator("username", mode="before")
    def validate_username(cls, v: Any) -> str:
        """Validate and normalize username.

        Args:
            v: The username string to validate

        Returns:
            str: Normalized username in lowercase

        Raises:
            ValueError: If username is empty or invalid
        """
        if not v:
            raise ValueError("Username is required")
        return str(v)

    # try to use access token later


class UserRegisterRequest(UserProfile):
    """Schema for user registration request.

    This is used when a new user registers through the public API.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "Password must be 8-128 chars with at least one uppercase, "
            "one lowercase, one number, and one special character"
        ),
        example="SecurePass123!",
    )
    password_confirm: str = Field(
        ..., description="Must match the password field", example="SecurePass123!"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            }
        }
    }

    @field_validator("password_confirm")
    def passwords_match(cls, v: str, info: Any) -> str:
        """Ensure password and password_confirm match."""
        if (
            hasattr(info, "data")
            and isinstance(info.data, dict)
            and "password" in info.data
            and v != info.data["password"]
        ):
            raise ValueError("Passwords do not match")
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login request.
    This schema is used when a user logs in through the public API.
    """

    email: str = Field(
        ..., description="User's email address", example="user@example.com"
    )
    password: str = Field(
        ..., description="User's password", example="YourSecurePassword123!"
    )

    @field_validator("email", mode="before")
    def normalize_login_email(cls, v: Any) -> str:
        """Normalize and validate email during login.

        Args:
            v: The email string to validate

        Returns:
            str: Normalized email address in lowercase

        Raises:
            ValueError: If email is empty or invalid
        """
        if not v:
            raise ValueError("Email is required")
        return str(v)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "YourSecurePassword123!",
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Schema for changing password request.

    Used when a user wants to change their own password.
    Requires the current password for verification.
    """

    id: str = Field(..., description="User's unique identifier")

    current_password: str = Field(
        ...,
        description="User's current password for verification",
        example="CurrentSecurePass123!",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "New password (8-128 chars, must include uppercase, "
            "lowercase, number, and special character)"
        ),
        example="NewSecurePass123!",
    )
    new_password_confirm: str = Field(
        ...,
        description="Must match the new_password field",
        example="NewSecurePass123!",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "new_password_confirm": "NewSecurePass123!",
            }
        }
    }

    @field_validator("id", mode="before")
    def validate_id(cls, v: Any) -> str:
        """Validate and normalize user ID."""
        if not v:
            raise ValueError("User ID is required")
        return str(v)

    @field_validator("current_password", mode="before")
    def validate_current_password(cls, v: Any) -> str:
        """Validate and normalize current password."""
        if not v:
            raise ValueError("Current password is required")
        return str(v)

    @field_validator("new_password", mode="before")
    def validate_new_password(cls, v: Any) -> str:
        """Validate and normalize new password."""
        if not v:
            raise ValueError("New password is required")
        return str(v)

    @field_validator("new_password_confirm", mode="before")
    def validate_new_password_confirm(cls, v: Any) -> str:
        """Validate and normalize new password confirmation."""
        if not v:
            raise ValueError("New password confirmation is required")
        return str(v)

    @field_validator("new_password_confirm")
    def passwords_match(cls, v: str, info: Any) -> str:
        """Ensure new password and confirmation match."""
        if (
            hasattr(info, "data")
            and isinstance(info.data, dict)
            and "new_password" in info.data
            and v != info.data["new_password"]
        ):
            raise ValueError("New passwords do not match")
        return v


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""

    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    token: str = Field(..., description="Verification token received via email")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "token": "your-verification-token",
            }
        }
    }


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

    new_hashed_password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "new_hashed_password": "NewSecurePass123!",
            }
        }
    }


class UserRegistrationInfo(UserProfile):
    """Schema for user registration.
    This schema is used when a new user registers.
    It is used by infrastructure layer to create a new user.
    """

    hashed_password: str
