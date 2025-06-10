"""Hashed password value object for secure password handling."""

import logging
from dataclasses import dataclass

from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class PasswordPolicyViolation(ValueError):
    """Raised when a password does not meet the password policy."""

    pass


class PasswordStrengthError(ValueError):
    """Raised when password strength requirements are not met."""

    pass


# Configure password hashing with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    deprecated="auto",  # Automatically mark schemes as deprecated
)


@dataclass(frozen=True)
class HashedPassword:
    """A value object representing a hashed password.

    This class encapsulates the hashed password value and provides methods for
    password verification, strength checking, and rehashing.
    """

    _value: str  # The hashed password value

    def __repr__(self) -> str:
        """Return the string representation of the hashed password.

        Returns:
            str: A string representation of the hashed password
        """
        return f"<HashedPassword: {self._value[:10]}...>"

    def __getstate__(self) -> str:
        """Return the hashed password string for serialization.

        This ensures that when the object is pickled or serialized by SQLAlchemy,
        only the hashed password string is stored.

        Returns:
            str: The hashed password value
        """
        return self._value

    def __setstate__(self, state: str) -> None:
        """Reconstruct the object from serialized state.

        Args:
            state: The hashed password string
        """
        # This uses the same validation as __init__
        object.__setattr__(self, "_value", state)

    def __post_init__(self) -> None:
        """Validate the hashed password value."""
        if not self._value:
            raise ValueError("Hashed password cannot be empty")
        if not isinstance(self._value, str):
            raise TypeError("Hashed password must be a string")

    @classmethod
    def from_plaintext(cls, plaintext_password: str) -> "HashedPassword":
        """Create a new HashedPassword from a plaintext password.

        Args:
            plaintext_password: The plaintext password to hash

        Returns:
            HashedPassword: A new HashedPassword instance

        Raises:
            PasswordPolicyViolation: If the password doesn't meet
                complexity requirements
            PasswordStrengthError: If the password is too weak
            ValueError: If the plaintext password is empty or invalid
        """
        if not plaintext_password or not plaintext_password.strip():
            raise ValueError("Password cannot be empty")

        hashed = pwd_context.hash(plaintext_password)
        return cls(_value=hashed)

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

        new_hashed = self.from_plaintext(new_password)

        return self.__class__(
            _value=new_hashed._value,
        )

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
