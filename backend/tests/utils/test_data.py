"""Test data generation utilities."""

import random
import string
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def random_email(domain: str = "example.com") -> str:
    """Generate a random email address."""
    return f"test_{random_string(8)}_{int(datetime.now(timezone.utc).timestamp())}@{domain}"


def random_username(prefix: str = "testuser") -> str:
    """Generate a random username."""
    return f"{prefix}_{random_string(6)}_{int(datetime.now(timezone.utc).timestamp() % 10000)}"


def create_user_dict(
    email: Optional[str] = None,
    username: Optional[str] = None,
    password: str = "Testpass123!",
    first_name: str = "Test",
    last_name: str = "User",
    **extra: Any,
) -> Dict[str, Any]:
    """Create a dictionary with user data for testing."""
    return {
        "email": email or random_email(),
        "username": username or random_username(),
        "password1": password,
        "password2": password,
        "first_name": first_name,
        "last_name": last_name,
        **extra,
    }


def create_user_create(
    email: Optional[str] = None,
    username: Optional[str] = None,
    password: str = "Testpass123!",
    first_name: str = "Test",
    last_name: str = "User",
    **extra: Any,
) -> Dict[str, Any]:
    """Create a user create dictionary for API requests."""
    return {
        "email": email or random_email(),
        "username": username or random_username(),
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        **extra,
    }


def create_user_update(
    first_name: Optional[str] = "Updated",
    last_name: Optional[str] = "Name",
    username: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Create a user update dictionary for API requests."""
    return {
        "first_name": first_name,
        "last_name": last_name,
        "username": username or f"updated_{random_string(6)}",
        **extra,
    }


def create_password_change(
    current_password: str = "Testpass123!",
    new_password: str = "NewPassword123!",
    confirm_password: Optional[str] = None,
) -> Dict[str, str]:
    """Create a password change dictionary for API requests."""
    if confirm_password is None:
        confirm_password = new_password
    return {
        "current_password": current_password,
        "new_password": new_password,
        "confirm_password": confirm_password,
    }
