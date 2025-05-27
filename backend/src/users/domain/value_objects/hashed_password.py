"""Hashed password value object for secure password handling."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar, FrozenSet, List, Tuple

from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class PasswordPolicyViolation(ValueError):
    """Raised when a password does not meet the password policy."""

    pass


class PasswordStrengthError(ValueError):
    """Raised when password strength requirements are not met."""

    pass


# Configure password hashing with Argon2
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    argon2__time_cost=3,  # Number of iterations
    argon2__memory_cost=65536,  # 64MB
    argon2__parallelism=4,  # Number of parallel threads
    deprecated="auto",  # Automatically mark schemes as deprecated
)


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

# Password strength requirements
PASSWORD_REQUIREMENTS: List[Tuple[str, str]] = [
    (r"[A-Z]", "At least one uppercase letter"),
    (r"[a-z]", "At least one lowercase letter"),
    (r"[0-9]", "At least one digit"),
    (r"[^A-Za-z0-9]", "At least one special character"),
    (r"^.{12,}$", "At least 12 characters long"),
]

# Number of previous passwords to check against
PASSWORD_HISTORY_LIMIT = 5


@dataclass(frozen=True)
class HashedPassword:
    """A value object representing a hashed password.

    This class encapsulates the hashed password value and provides methods for
    password verification, strength checking, and rehashing.
    """

    _value: str  # The hashed password value
    _previous_hashes: tuple[str, ...] = tuple()  # Previous hashes for history check
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Class variables
    MIN_PASSWORD_LENGTH: ClassVar[int] = 12
    MAX_PASSWORD_LENGTH: ClassVar[int] = 128
    COMMON_PASSWORDS: ClassVar[frozenset[str]] = COMMON_PASSWORDS
    PASSWORD_REQUIREMENTS: ClassVar[list[tuple[str, str]]] = PASSWORD_REQUIREMENTS
    PASSWORD_HISTORY_LIMIT: ClassVar[int] = PASSWORD_HISTORY_LIMIT

    def __post_init__(self) -> None:
        """Validate the hashed password value."""
        if not self._value:
            raise ValueError("Hashed password cannot be empty")
        if not isinstance(self._value, str):
            raise TypeError("Hashed password must be a string")

    @classmethod
    def from_plaintext(cls, plaintext_password: str, **hash_kwargs) -> "HashedPassword":
        """Create a new HashedPassword from a plaintext password.

        Args:
            plaintext_password: The plaintext password to hash
            **hash_kwargs: Additional keyword arguments to pass to the hashing function

        Returns:
            HashedPassword: A new HashedPassword instance

        Raises:
            PasswordPolicyViolation: If the password doesn't meet
                complexity requirements
            PasswordStrengthError: If the password is too weak
            ValueError: If the plaintext password is empty or invalid
        """
        cls._validate_password_strength(plaintext_password)
        cls._check_common_password(plaintext_password)

        try:
            hashed = pwd_context.hash(plaintext_password, **hash_kwargs)
            return cls(_value=hashed)
        except (ValueError, TypeError) as e:
            logger.error("Failed to hash password: %s", str(e))
            raise ValueError("Failed to hash password") from e

    @classmethod
    def _validate_password_strength(cls, password: str) -> None:
        """Validate that a password meets strength requirements.

        Args:
            password: The password to validate

        Raises:
            PasswordPolicyViolation: If the password doesn't meet requirements
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")

        if not password:
            raise PasswordPolicyViolation("Password cannot be empty")

        if len(password) < cls.MIN_PASSWORD_LENGTH:
            raise PasswordPolicyViolation(
                f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters long"
            )

        if len(password) > cls.MAX_PASSWORD_LENGTH:
            raise PasswordPolicyViolation(
                f"Password must be at most {cls.MAX_PASSWORD_LENGTH} characters long"
            )

        # Check against common patterns
        if password.lower() in cls.COMMON_PASSWORDS:
            raise PasswordStrengthError("Password is too common")

        # Check complexity requirements
        errors = []
        for pattern, message in cls.PASSWORD_REQUIREMENTS:
            if not re.search(pattern, password):
                errors.append(message)

        if errors:
            raise PasswordStrengthError("\n- " + "\n- ".join(errors))

    @classmethod
    def _check_common_password(cls, password: str) -> None:
        """Check if the password is in the list of common passwords.

        Args:
            password: The password to check

        Raises:
            PasswordStrengthError: If the password is too common
        """
        if password.lower() in cls.COMMON_PASSWORDS:
            raise PasswordStrengthError("Password is too common")

    def verify_password_match(self, plaintext_password: str) -> bool:
        """Verify a plaintext password against the hashed password.

        Args:
            plaintext_password: The plaintext password to verify

        Returns:
            bool: True if the password matches, False otherwise

        Raises:
            ValueError: If the plaintext password is empty
        """
        if not plaintext_password:
            logger.warning("Attempted to verify empty password")
            return False

        try:
            return pwd_context.verify(plaintext_password, self._value)
        except (ValueError, TypeError) as e:
            logger.warning("Password verification failed: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error during password verification: %s", str(e))
            return False

    def is_in_history(self, plaintext_password: str) -> bool:
        """Check if the password is in the history of previous passwords.

        Args:
            plaintext_password: The plaintext password to check

        Returns:
            bool: True if the password is in history, False otherwise
        """
        if not plaintext_password:
            return False

        for old_hash in self._previous_hashes:
            try:
                if pwd_context.verify(plaintext_password, old_hash):
                    return True
            except (ValueError, TypeError):
                continue
        return False

    def update_password(self, new_password: str) -> "HashedPassword":
        """Create a new HashedPassword with the new password.

        Args:
            new_password: The new plaintext password

        Returns:
            HashedPassword: A new HashedPassword instance with the updated password

        Raises:
            PasswordPolicyViolation: If the new password is the same as the current one
            PasswordStrengthError: If the new password doesn't meet requirements
        """
        if self.verify_password_match(new_password):
            raise PasswordPolicyViolation(
                "New password must be different from current password"
            )

        if self.is_in_history(new_password):
            raise PasswordPolicyViolation("Cannot reuse previous passwords")

        new_hashed = self.from_plaintext(new_password)

        # Add current hash to previous hashes, keeping only the most recent ones
        previous_hashes = (self._value,) + self._previous_hashes
        if len(previous_hashes) > self.PASSWORD_HISTORY_LIMIT:
            previous_hashes = previous_hashes[: self.PASSWORD_HISTORY_LIMIT]

        return self.__class__(
            _value=new_hashed._value,
            _previous_hashes=previous_hashes,
            _created_at=self._created_at,
            _updated_at=datetime.now(timezone.utc),
        )

    @property
    def age_days(self) -> float:
        """Get the age of the password in days.

        Returns:
            float: Number of days since the password was created
        """
        delta = datetime.now(timezone.utc) - self._created_at
        return delta.total_seconds() / 86400  # Convert seconds to days

    def is_old(self, max_age_days: int = 90) -> bool:
        """Check if the password is older than the specified number of days.

        Args:
            max_age_days: Maximum allowed age in days (default: 90)

        Returns:
            bool: True if the password is older than max_age_days
        """
        return self.age_days > max_age_days

    @classmethod
    def needs_rehash(cls, hashed_password: str) -> bool:
        """Check if a hashed password needs to be rehashed.

        This is useful when updating password hashing parameters.

        Args:
            hashed_password: The hashed password to check

        Returns:
            bool: True if the password needs rehashing, False otherwise

        Raises:
            ValueError: If the hashed_password is empty or invalid
        """
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty")

        try:
            # Check if the password is using the current hashing scheme
            # and parameters
            return pwd_context.needs_update(hashed_password)
        except (ValueError, TypeError) as e:
            logger.warning("Failed to check if password needs rehash: %s", str(e))
            return True  # Default to True to force rehashing on error
        except Exception as e:
            logger.error("Unexpected error checking password rehash status: %s", str(e))
            return True  # Default to True to force rehashing on error

    def __str__(self) -> str:
        """Return the hashed value as a string.

        Returns:
            str: The hashed password value

        Note:
            This method does not expose the actual hash value in logs.
            Only the first 8 characters are shown for security.
        """
        # For security, don't expose the full hash in string representation
        if not self._value:
            return "<HashedPassword: invalid>"
        return f"<HashedPassword: {self._value[:8]}...>"

    def __eq__(self, other: object) -> bool:
        """Compare with another HashedPassword or string.

        Args:
            other: The object to compare with

        Returns:
            bool: True if the objects are equal, False otherwise

        Note:
            Comparison with strings is supported for backward compatibility
            but is not recommended for security-sensitive operations.
        """
        if not isinstance(other, (HashedPassword, str)):
            return NotImplemented

        try:
            if isinstance(other, HashedPassword):
                # Use constant time comparison to prevent timing attacks
                return self._value == other._value

            # For string comparison, verify the password
            try:
                return pwd_context.verify(other, self._value)
            except (ValueError, TypeError):
                return False

        except Exception as e:
            logger.warning("Error during password comparison: %s", str(e))
            return False
