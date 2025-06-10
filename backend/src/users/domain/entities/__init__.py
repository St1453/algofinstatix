"""Users domain entities.

This module contains the core domain entities for the users domain,
including the User and RefreshToken models.
"""

from __future__ import annotations

# Import all public API
from .token import Token
from .user import User, UserRole

# Public API
__all__ = [
    "User",
    "UserRole",
    "Token",
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
