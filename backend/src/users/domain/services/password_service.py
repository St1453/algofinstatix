"""Service for password-related operations including generation and validation."""

from __future__ import annotations

# Standard library
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

# Third-party
from sqlalchemy import func, select

# Local application
from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    InvalidCredentialsError,
    PasswordReuseError,
    PasswordTooWeakError,
    UserNotFoundError,
)
from src.users.domain.interfaces.user_repository import IUserRepository
from src.users.domain.value_objects.hashed_password import HashedPassword

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.users.infrastructure.database.models.password_history_orm import (
        PasswordHistoryORM,
    )

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password management including generation, validation, and history."""

    def __init__(
        self,
        user_repository: IUserRepository,
        session_factory: type[AsyncSession],
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        password_history_size: int = 5,
        password_expiry_days: int = 90,
    ):
        """Initialize password service with configuration.

        Args:
            user_repository: Repository for user data access
            session_factory: Async session factory for database access
            min_length: Minimum password length
            require_uppercase: Whether to require uppercase letters
            require_lowercase: Whether to require lowercase letters
            require_digits: Whether to require digits
            require_special: Whether to require special characters
            password_history_size: Number of previous passwords to remember
            password_expiry_days: Number of days before password expires
        """
        self.user_repository = user_repository
        self.session_factory = session_factory
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.password_history_size = password_history_size
        self.password_expiry_days = password_expiry_days

    def generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password.

        The password will contain at least one lowercase letter, one uppercase letter,
        one digit, and one special character.

        Args:
            length: Length of the password to generate (default: 12)

        Returns:
            str: A randomly generated secure password

        Raises:
            ValueError: If length is less than minimum required length
        """
        if length < self.min_length:
            raise ValueError(
                f"Password length must be at least {self.min_length} characters"
            )

        # Define character sets
        lowercase = string.ascii_lowercase if self.require_lowercase else ""
        uppercase = string.ascii_uppercase if self.require_uppercase else ""
        digits = string.digits if self.require_digits else ""
        special = string.punctuation if self.require_special else ""

        # Ensure at least one of each required character type
        required_chars = []
        if self.require_lowercase:
            required_chars.append(secrets.choice(lowercase))
        if self.require_uppercase:
            required_chars.append(secrets.choice(uppercase))
        if self.require_digits:
            required_chars.append(secrets.choice(digits))
        if self.require_special:
            required_chars.append(secrets.choice(special))

        # Fill the rest with random characters
        remaining_length = length - len(required_chars)
        all_chars = lowercase + uppercase + digits + special
        remaining_chars = [secrets.choice(all_chars) for _ in range(remaining_length)]

        # Combine and shuffle
        password_chars = required_chars + remaining_chars
        secrets.SystemRandom().shuffle(password_chars)

        return "".join(password_chars)

    def validate_password_strength(self, password: str) -> None:
        """Validate that a password meets strength requirements.

        Args:
            password: The password to validate

        Raises:
            PasswordTooWeakError: If password doesn't meet requirements
        """
        if len(password) < self.min_length:
            raise PasswordTooWeakError(
                f"Password must be at least {self.min_length} characters long"
            )

        if self.require_uppercase and not any(c.isupper() for c in password):
            raise PasswordTooWeakError(
                "Password must contain at least one uppercase letter"
            )

        if self.require_lowercase and not any(c.islower() for c in password):
            raise PasswordTooWeakError(
                "Password must contain at least one lowercase letter"
            )

        if self.require_digits and not any(c.isdigit() for c in password):
            raise PasswordTooWeakError("Password must contain at least one digit")

        if self.require_special and not any(c in string.punctuation for c in password):
            raise PasswordTooWeakError(
                "Password must contain at least one special character"
            )

    async def is_password_reused(self, user_id: str, new_password_hash: str) -> bool:
        """Check if the new password was used before.

        Args:
            user_id: ID of the user
            new_password_hash: The new password hash to check

        Returns:
            bool: True if password was used before, False otherwise
        """
        if not self.password_history_size:
            return False

        async with self.session_factory() as session:
            # Query the password history table directly
            result = await session.execute(
                select(PasswordHistoryORM)
                .where(PasswordHistoryORM.user_id == user_id)
                .where(PasswordHistoryORM.hashed_password == str(new_password_hash))
                .limit(1)
            )
            return result.scalars().first() is not None

    async def update_password(
        self,
        user_id: str,
        new_password: str,
        current_password: Optional[str] = None,
        require_current_password: bool = True,
    ) -> None:
        """Update a user's password with validation.

        Args:
            user_id: ID of the user
            new_password: New password to set
            current_password: Current password for verification
            require_current_password: Whether to require current password

        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If current password is incorrect
            PasswordTooWeakError: If new password doesn't meet requirements
            PasswordReuseError: If new password was used recently
        """
        # Get user
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Verify current password if required
        if require_current_password and current_password is not None:
            if not user.hashed_password.verify(current_password):
                raise InvalidCredentialsError("Current password is incorrect")

        # Validate new password strength
        self.validate_password_strength(new_password)

        # Check if password was used before
        new_hashed = HashedPassword.from_plaintext(new_password)
        if await self.is_password_reused(user_id, new_hashed):
            raise PasswordReuseError("Cannot reuse a previously used password")

        # Update password and save
        user.hashed_password = new_hashed
        user.password_changed_at = datetime.now(timezone.utc)

        # Update password history
        self._update_password_history(user, new_hashed)

        await self.user_repository.update_user_by_id(user_id, user)

    async def _update_password_history(
        self, user: User, new_hashed: HashedPassword
    ) -> None:
        """Update the user's password history with the new password.

        Args:
            user: The user to update
            new_hashed: The new hashed password
        """
        from src.users.infrastructure.database.models.password_history_orm import (
            PasswordHistoryORM,
        )

        async with self.session_factory() as session:
            # Create new history entry
            history_entry = PasswordHistoryORM(
                user_id=user.id,
                hashed_password=str(new_hashed),
                changed_at=datetime.now(timezone.utc),
            )
            session.add(history_entry)

            # Get current count
            count = await session.scalar(
                select(func.count(PasswordHistoryORM.id)).where(
                    PasswordHistoryORM.user_id == user.id
                )
            )

            # If we've reached max history, delete the oldest
            if count > self.password_history_size:
                oldest = await session.execute(
                    select(PasswordHistoryORM)
                    .where(PasswordHistoryORM.user_id == user.id)
                    .order_by(PasswordHistoryORM.changed_at.asc())
                    .limit(count - self.password_history_size)
                )
                for entry in oldest.scalars():
                    await session.delete(entry)

            await session.commit()

    def is_password_expired(self, user: User) -> bool:
        """Check if the user's password has expired.

        Args:
            user: The user to check

        Returns:
            bool: True if password is expired, False otherwise
        """
        if not user.status.password_changed_at or not self.password_expiry_days:
            return False

        expiry_date = user.status.password_changed_at + timedelta(
            days=self.password_expiry_days
        )
        return datetime.now(timezone.utc) > expiry_date
