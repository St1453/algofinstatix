"""Shared components across the application.

This package contains shared domain models, interfaces, and infrastructure
components that are used across multiple domains.
"""
from __future__ import annotations

__all__ = ["domain", "infrastructure"]  # Export subpackages

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
