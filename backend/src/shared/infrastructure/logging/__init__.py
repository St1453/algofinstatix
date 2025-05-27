"""Shared logging infrastructure for the application.

This package provides centralized logging configuration and utilities for the entire application.
"""

from .database_logger import (
    log_audit_event,
    log_operation,
    log_slow_query,
    setup_database_logging,
)

__all__ = [
    "setup_database_logging",
    "log_operation",
    "log_slow_query",
    "log_audit_event",
]
