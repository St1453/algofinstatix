"""AlgoFinStatiX Backend Package.

This is the root package for the AlgoFinStatiX backend application.
It contains all the modules and subpackages for the application.
"""

from __future__ import annotations

import logging
from pathlib import Path

__version__ = "0.1.0"

# Public API
try:
    from src.core.config import get_settings

    __all__ = ["__version__", "get_settings"]
except ImportError:
    __all__ = ["__version__"]
    get_settings = None  # type: ignore[assignment]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Add file handler
file_handler = logging.FileHandler(log_dir / "app.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logging.getLogger().addHandler(file_handler)

# Set SQLAlchemy log level to WARNING to reduce noise
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
