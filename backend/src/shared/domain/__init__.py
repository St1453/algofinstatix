"""
Shared domain models and interfaces.

This package contains domain models, value objects, and interfaces that are shared
across multiple domains in the application.
"""

from .value_objects import Email  # noqa: F401

__all__ = ["Email"]  # Public API
