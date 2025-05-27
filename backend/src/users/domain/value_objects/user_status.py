"""UserStatus value object for managing user account status."""

from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Self


@dataclass(frozen=True)
class UserStatus:
    """Value object representing a user's account status.

    This class encapsulates all account status-related functionality including
    login attempts, account locking, and verification status.
    """

    is_enabled: bool = True
    is_verified: bool = False
    last_login_at: Optional[datetime] = None
    last_failed_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    # Constants for account security settings
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    @property
    def is_locked(self) -> bool:
        """Check if the account is currently locked."""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.now(timezone.utc)

    def record_successful_login(self) -> Self:
        """Record a successful login attempt and return a new UserStatus instance."""
        return dataclass_replace(
            self,
            last_login_at=datetime.now(timezone.utc),
            failed_login_attempts=0,
            locked_until=None,
            last_failed_login=None,
        )

    def record_password_change(self) -> Self:
        """Record a password change and return a new UserStatus instance.

        Returns:
            UserStatus: New instance with updated password change timestamp
        """
        return dataclass_replace(
            self,
            password_changed_at=datetime.now(timezone.utc),
        )

    def record_failed_login(self) -> Self:
        """Record a failed login attempt and return a new UserStatus instance."""
        new_attempts = self.failed_login_attempts + 1
        locked_until = None

        if new_attempts >= self.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.ACCOUNT_LOCKOUT_MINUTES
            )

        return dataclass_replace(
            self,
            failed_login_attempts=new_attempts,
            locked_until=locked_until,
            last_failed_login=datetime.now(timezone.utc),
        )

    def is_email_verified(self) -> Self:
        """Mark the email as verified and return a new UserStatus instance."""
        if self.is_verified:
            return self
        return dataclass_replace(self, is_verified=True)

    def enable_account(self) -> Self:
        """Enable the user account and return a new UserStatus instance."""
        if self.is_enabled:
            return self
        return dataclass_replace(self, is_enabled=True)

    def disable_account(self) -> Self:
        """Disable the user account and return a new UserStatus instance."""
        if not self.is_enabled:
            return self
        return dataclass_replace(self, is_enabled=False)

    def get_remaining_attempts(self) -> int:
        """Get the number of remaining login attempts before lockout."""
        return max(0, self.MAX_LOGIN_ATTEMPTS - self.failed_login_attempts)

    def get_lockout_time_remaining(self) -> Optional[timedelta]:
        """Get the remaining lockout time if the account is locked."""
        if not self.is_locked or not self.locked_until:
            return None
        return self.locked_until - datetime.now(timezone.utc)

    def reset_login_attempts(self) -> Self:
        """Reset failed login attempts and return a new UserStatus instance."""
        if self.failed_login_attempts == 0 and self.locked_until is None:
            return self
        return dataclass_replace(
            self, failed_login_attempts=0, locked_until=None, last_failed_login=None
        )

    def with_updates(self, **updates: Any) -> "UserStatus":
        """Create a new UserStatus with the specified updates.

        Args:
            **updates: Fields to update with their new values

        Returns:
            UserStatus: A new UserStatus instance with the updates applied
        """
        return dataclass_replace(self, **updates)
