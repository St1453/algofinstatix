"""
Database infrastructure components.

This package contains database-related infrastructure components such as
repositories, sessions, and exceptions that are shared across the application.
"""

from .exceptions_database import (  # noqa: F401
    BaseAppError,
    DatabaseError,
    NotFoundError,
)

__all__ = ["BaseAppError", "DatabaseError", "NotFoundError"]  # Public API
