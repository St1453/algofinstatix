"""Shared logging infrastructure for the application.

This package provides centralized logging configuration and utilities for the
entire application.
"""

from .audit_logger import get_audit_logger
from .database_logger import get_database_logger

# Re-export common functions
get_audit_logger = get_audit_logger
get_database_logger = get_database_logger

__all__ = [
    "get_audit_logger",
    "get_database_logger",
]
