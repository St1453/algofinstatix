"""Service for password management including generation, validation, and history."""

from __future__ import annotations

import logging
import re
import secrets
import string
from datetime import datetime, timezone
from typing import FrozenSet, List, Optional, Tuple

from passlib.context import CryptContext

from src.users.domain.exceptions import (
    InvalidCredentialsError,
    PasswordPolicyViolation,
    PasswordTooWeakError,
    UserNotFoundError,
    UserUpdateError,
)
from src.users.domain.interfaces.password_service import IPasswordService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.schemas.user_schemas import ChangePasswordRequest

logger = logging.getLogger(__name__)

# Common password patterns to check against
COMMON_PASSWORDS: FrozenSet[str] = frozenset(
    {
        "password",
        "123456",
        "qwerty",
        "letmein",
        "welcome",
        "admin",
        "password1",
        "12345678",
        "123123",
        "111111",
        "iloveyou",
        "sunshine",
        "princess",
        "admin123",
        "welcome1",
        "password123",
        "adminadmin",
        "qwerty123",
        "admin1234",
    }
)

# Default password hashing scheme
DEFAULT_HASH_SCHEME = "bcrypt"
DEFAULT_HASH_ROUNDS = 12

# Password strength requirements
PASSWORD_REQUIREMENTS: List[Tuple[str, str]] = [
    (r"[A-Z]", "At least one uppercase letter"),
    (r"[a-z]", "At least one lowercase letter"),
    (r"[0-9]", "At least one digit"),
    (r"[^A-Za-z0-9]", "At least one special character"),
    (r"^.{8,}$", "At least 8 characters long"),
]
min_length: int = 8
max_length: int = 128
require_uppercase: bool = True
require_lowercase: bool = True
require_numbers: bool = True
require_special: bool = True


class PasswordService(IPasswordService):
    """Service for password management including generation, validation, and history."""

    def __init__(
        self,
        uow: IUnitOfWork,
        password_history_size: int = 5,
        password_expiry_days: Optional[int] = 90,
    ) -> None:
        """Initialize the password service with configuration.

        Args:
            uow: Unit of Work instance
            password_history_size: Number of previous passwords to remember (default: 5)
            password_expiry_days: Number of days before password expires (default: 90)
        """
        self.uow = uow
        self.password_history_size = password_history_size
        self.password_expiry_days = password_expiry_days

        # Configure password hashing
        self.pwd_context = CryptContext(
            schemes=[DEFAULT_HASH_SCHEME],
            deprecated="auto",
            **{"bcrypt__rounds": DEFAULT_HASH_ROUNDS},
        )

    def generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password.

        The password will contain at least one of each required character type.

        Args:
            length: Length of the password to generate (default: 12)

        Returns:
            str: Generated password

        Raises:
            ValueError: If length is less than required minimum or invalid
        """
        if length < min_length:
            raise ValueError(
                f"Password length must be at least {min_length} characters"
            )

        if length > max_length:
            raise ValueError(f"Password length must not exceed {max_length} characters")

        # Define character sets
        lowercase = string.ascii_lowercase if require_lowercase else ""
        uppercase = string.ascii_uppercase if require_uppercase else ""
        numbers = string.digits if require_numbers else ""
        special = string.punctuation if require_special else ""

        all_chars = lowercase + uppercase + numbers + special
        if not all_chars:
            raise ValueError("At least one character type must be required")

        # Ensure at least one of each required character type
        password = []
        if require_lowercase:
            password.append(secrets.choice(lowercase))
        if require_uppercase:
            password.append(secrets.choice(uppercase))
        if require_numbers:
            password.append(secrets.choice(numbers))
        if require_special:
            password.append(secrets.choice(special))

        # Fill the rest of the password with random characters
        remaining_length = length - len(password)
        if remaining_length > 0:
            password.extend(secrets.choice(all_chars) for _ in range(remaining_length))

        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
        return "".join(password)

    def validate_password_strength(self, password: str) -> None:
        """Validate that a password meets strength requirements.

        Args:
            password: The password to validate

        Raises:
            PasswordPolicyViolation: If the password doesn't meet requirements
        """
        if not password:
            raise PasswordPolicyViolation("Password cannot be empty")

        if len(password) < min_length:
            raise PasswordPolicyViolation(
                f"Password must be at least {min_length} characters long"
            )

        if len(password) > max_length:
            raise PasswordPolicyViolation(
                f"Password must not exceed {max_length} characters"
            )

        # Check for common passwords
        if password.lower() in COMMON_PASSWORDS:
            raise PasswordTooWeakError("Password is too common")

        # Check against requirements
        if require_uppercase and not re.search(r"[A-Z]", password):
            raise PasswordPolicyViolation(
                "Password must contain at least one uppercase letter"
            )

        if require_lowercase and not re.search(r"[a-z]", password):
            raise PasswordPolicyViolation(
                "Password must contain at least one lowercase letter"
            )

        if require_numbers and not re.search(r"[0-9]", password):
            raise PasswordPolicyViolation("Password must contain at least one number")

        if require_special and not re.search(r"[^A-Za-z0-9]", password):
            raise PasswordPolicyViolation(
                "Password must contain at least one special character"
            )

    async def hash_password(self, plain_password: str) -> str:
        """Hash a plain text password.

        Args:
            plain_password: The plain text password to hash

        Returns:
            A new HashedPassword instance

        Raises:
            PasswordPolicyViolation: If the password is invalid or too weak
        """
        self.validate_password_strength(plain_password)
        return self.pwd_context.hash(plain_password)

    async def verify_password(
        self, user_id: str, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify a plain text password against a hashed password.

        Args:
            user_id: ID of the user to verify
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against

        Returns:
            bool: True if the password matches, False otherwise

        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If the plain password or hashed password is empty
        """
        if not plain_password:
            raise ValueError("Password cannot be empty")
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty")

        # Verify the password against the hash
        is_valid = self.pwd_context.verify(plain_password, hashed_password)

        # Update hash if needed (e.g., if using a newer hashing algorithm)
        if is_valid and self.pwd_context.needs_update(hashed_password):
            async with self.uow.transaction():
                user = await self.uow.users.get_user_by_id(user_id)
                if user:
                    user.password = await self.hash_password(plain_password)
                    await self.uow.commit()

        return is_valid

    async def change_password(
        self, change_password_request: ChangePasswordRequest
    ) -> bool:
        """Change a user's password with proper validation.

        Args:
            user_id: ID of the user changing their password
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            bool: True if password was changed successfully

        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If current password is incorrect
            PasswordTooWeakError: If new password doesn't meet requirements
            UserUpdateError: If password update fails
        """
        self.validate_password_strength(change_password_request.new_password)

        async with self.uow.transaction():
            # Get user and verify current password
            user = await self.uow.users.get_user_by_id(change_password_request.id)
            if not user or getattr(user, "deleted_at", None) is not None:
                raise UserNotFoundError(
                    f"User with ID {change_password_request.id} not found"
                )

            # Verify current password
            if not await self.verify_password(
                change_password_request.id,
                change_password_request.current_password,
                user.hashed_password,
            ):
                raise InvalidCredentialsError("Current password is incorrect")

            # Check if new password is different from current
            if await self.verify_password(
                change_password_request.id,
                change_password_request.new_password,
                user.hashed_password,
            ):
                raise PasswordTooWeakError(
                    "New password must be different from current password"
                )

            try:
                # Hash and update the password
                user.hashed_password = await self.hash_password(
                    change_password_request.new_password
                )
                # Update password change timestamp if the field exists
                if hasattr(user, "password_changed_at"):
                    user.password_changed_at = datetime.now(timezone.utc)

                # Update password history if implemented
                if hasattr(user, "password_history"):
                    history = getattr(user, "password_history", []) or []
                    history.append(user.hashed_password)
                    if len(history) > self.password_history_size:
                        history = history[-self.password_history_size :]
                    user.password_history = history

                await self.uow.commit()
                return True

            except Exception as e:
                await self.uow.rollback()
                logger.error(
                    "Password change failed",
                    exc_info=True,
                    extra={"user_id": change_password_request.id, "error": str(e)},
                )
                raise UserUpdateError("Failed to update password") from e


# need to add reset password functionality later
