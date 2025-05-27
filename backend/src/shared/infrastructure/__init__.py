"""
Shared infrastructure components.

This package contains infrastructure implementations that are shared across
multiple domains, such as database connections, configuration, and external services.
"""

from .config import settings  # noqa: F401
from .database.session import get_db  # noqa: F401

__all__ = ["settings", "get_db"]  # Public API
