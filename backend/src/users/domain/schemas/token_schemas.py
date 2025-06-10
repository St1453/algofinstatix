"""
Pydantic schemas for token-related requests and responses.

This module defines the data models used for token management,
authentication, and authorization in the system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    """Base schema for token data."""

    token_type: str = Field(..., description="Type of the token")
    scopes: List[str] = Field(
        default_factory=list, description="List of scopes this token has access to"
    )
    expires_at: Optional[datetime] = Field(
        None, description="When the token expires (ISO 8601 format)"
    )


class TokenCreate(TokenBase):
    """Schema for token creation.

    This is used when generating new tokens for authentication.
    """

    user_id: str = Field(..., description="ID of the user this token belongs to")
    expires_in: Optional[int] = Field(
        None,
        gt=0,
        description="Token lifetime in seconds. If not provided, default will be used",
    )
    user_agent: Optional[str] = Field(
        None, description="User agent that created the token"
    )
    ip_address: Optional[str] = Field(
        None, description="IP address that created the token"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "token_type": "access",
                "expires_in": 3600,
                "scopes": ["read", "write"],
                "user_agent": "Mozilla/5.0...",
                "ip_address": "192.168.1.1",
            }
        }
    }


class TokenResponse(TokenBase):
    """Schema for token response.

    This is what's returned to the client after successful authentication.
    """

    access_token: str = Field(..., description="The access token string")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token (if applicable)"
    )
    token_type: str = Field("bearer", description="Type of the token")
    expires_in: Optional[int] = Field(
        None, description="Number of seconds until the token expires"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "scopes": ["read", "write"],
            }
        }
    }


class TokenPayload(BaseModel):
    """Schema for the payload of a JWT token.

    This represents the data that will be encoded in the token.
    """

    sub: str = Field(..., description="Subject (user ID)")
    scopes: List[str] = Field(
        default_factory=list, description="List of scopes this token has access to"
    )
    exp: Optional[datetime] = Field(
        None, description="Expiration time (as UTC timestamp)"
    )
    iat: Optional[datetime] = Field(
        None, description="Issued at time (as UTC timestamp)"
    )
    jti: Optional[str] = Field(None, description="Unique identifier for the token")
    token_type: Optional[str] = Field(None, description="Type of the token")


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request.

    Used when refreshing an access token using a refresh token.
    """

    refresh_token: str = Field(..., description="The refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class TokenRevokeRequest(BaseModel):
    """Schema for token revocation request.

    Used when revoking a token (usually for logout).
    """

    token: str = Field(..., description="The token to revoke")

    model_config = {
        "json_schema_extra": {
            "example": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class TokenInDB(TokenBase):
    """Schema for token data as stored in the database."""

    id: str = Field(..., description="Unique identifier for the token")
    user_id: str = Field(..., description="ID of the user this token belongs to")
    token: str = Field(..., description="The actual token string")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the token was created",
    )
    last_used_at: Optional[datetime] = Field(
        None, description="When the token was last used"
    )
    revoked: bool = Field(False, description="Whether the token has been revoked")
    user_agent: Optional[str] = Field(
        None, description="User agent that created the token"
    )
    ip_address: Optional[str] = Field(
        None, description="IP address that created the token"
    )

    class Config:
        from_attributes = True


class TokenVerificationResult:
    """Result of token verification."""

    is_valid: bool
    user_id: Optional[str] = None
    token: Optional[str] = None
    payload: Optional[Dict] = None
    error: Optional[str] = None


class TokenList(BaseModel):
    """Schema for listing tokens with pagination."""

    items: List[TokenInDB] = Field(..., description="List of tokens")
    total: int = Field(..., description="Total number of tokens")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
