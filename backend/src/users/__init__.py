"""Users domain package.

This package contains all components related to the users domain,
including domain models, application services, and infrastructure.
"""
from __future__ import annotations

# Export subpackages
__all__ = ["application", "domain", "infrastructure", "presentation"]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)
