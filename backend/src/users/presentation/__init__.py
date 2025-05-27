"""
Users presentation layer.

This package contains the API routes and request/response models
for the users domain.
"""

from .user_routes import router as user_router  # noqa: F401

__all__ = ["user_router"]  # Public API
