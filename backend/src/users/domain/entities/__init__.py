"""Users domain entities.

This module contains the core domain entities for the users domain,
including the User and RefreshToken models.
"""

from __future__ import annotations

# Import all public API
from .user import User, UserRole  # noqa: F401
from .user_metrics import UserMetrics  # noqa: F401

# Public API
__all__ = [
    "User",
    "UserRole",
    "UserMetrics",
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
