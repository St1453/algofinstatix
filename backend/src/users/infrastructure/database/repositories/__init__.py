"""
Users repository implementations.

This module contains the concrete implementations of the repository interfaces
defined in the domain layer.
"""

from .user_repository_impl import UserRepositoryImpl  # noqa: F401

__all__ = ["UserRepositoryImpl"]  # Public API
