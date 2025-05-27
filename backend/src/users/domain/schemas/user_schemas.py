"""
Pydantic schemas for user-related requests and responses.

This module defines the data models used for request validation and response formatting
in the user management system.
"""

from __future__ import annotations

from typing import Optional, TypeVar

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# Type variable for model validation
ModelData = TypeVar("ModelData", bound=dict)


class UserProfile(BaseModel):
    """Schema representing a user's profile information.
    it can be used when user is updated or registered
    """

    email: EmailStr = Field(
        ..., description="User's email address", example="user@example.com"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's first name",
        example="John",
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User's last name", example="Doe"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="User's username (alphanumeric with underscores and hyphens only)",
        example="johndoe123",
    )
    profile_picture: Optional[str] = Field(
        None,
        description="URL to the user's profile picture",
        example="https://example.com/profile.jpg",
    )
    user_intro: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief introduction about the user",
        example="Software developer and open source enthusiast",
    )

    @field_validator("email", mode="before")
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        try:
            validate_email(v)
        except EmailNotValidError as e:
            raise ValueError(str(e))
        return v


# user request models below


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
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="User's username (alphanumeric with underscores and hyphens only)",
        example="johndoe123",
    )

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

    @field_validator("password")
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator(mode="before")
    def passwords_match(cls, values: dict) -> dict:
        """Ensure password and password_confirm match."""
        if values["password"] != values["password_confirm"]:
            raise ValueError("Passwords do not match")
        return values


class UserLoginRequest(BaseModel):
    """Schema for user login request.
    This schema is used when a user logs in through the public API.
    """

    email: EmailStr = Field(
        ..., description="User's email address", example="user@example.com"
    )
    password: str = Field(
        ..., description="User's password", example="YourSecurePassword123!"
    )

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
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "new_password_confirm": "NewSecurePass123!",
            }
        }
    }

    @model_validator(mode="after")
    def new_passwords_match(self) -> "ChangePasswordRequest":
        """Ensure new password and confirmation match."""
        if self.new_password != self.new_password_confirm:
            raise ValueError("New passwords do not match")
        return self

    @field_validator("new_password")
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password strength.

        Ensures password meets security requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one number
        - Contains at least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        special_chars = "!@#$%^&*()_+{}|:<>?`~-=[]\\;',./\""
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        return v
