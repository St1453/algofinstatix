"""UserStatus value object for managing user account status."""

from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from typing import Any, Self


@dataclass(frozen=True)
class UserStatus:
    """Value object representing a user's account status.

    This class encapsulates all account status-related functionality including
    login attempts, account locking, and verification status.
    """

    is_enabled: bool = True
    is_verified: bool = False

    def email_is_verified(self) -> Self:
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

    def with_updates(self, **updates: Any) -> "UserStatus":
        """Create a new UserStatus with the specified updates.

        Args:
            **updates: Fields to update with their new values

        Returns:
            UserStatus: A new UserStatus instance with the updates applied
        """
        return dataclass_replace(self, **updates)
