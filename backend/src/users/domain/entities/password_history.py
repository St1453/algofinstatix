"""Domain entity for password history tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional


class PasswordHistory:
    """Represents a historical password entry for a user."""

    def __init__(
        self,
        id: str,
        user_id: str,
        hashed_password: str,
        changed_at: datetime,
    ) -> None:
        """Initialize a new password history entry.

        Args:
            id: Unique identifier for the history entry
            user_id: ID of the user this entry belongs to
            hashed_password: The hashed password value
            changed_at: When the password was changed to this value
        """
        self.id = id
        self.user_id = user_id
        self.hashed_password = hashed_password
        self.changed_at = changed_at

    @classmethod
    def create(
        cls,
        user_id: str,
        hashed_password: str,
        changed_at: Optional[datetime] = None,
    ) -> PasswordHistory:
        """Factory method to create a new password history entry.

        Args:
            user_id: ID of the user
            hashed_password: The new hashed password
            changed_at: Optional timestamp (defaults to now)

        Returns:
            PasswordHistory: A new password history instance
        """
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hashed_password=hashed_password,
            changed_at=changed_at or datetime.now(timezone.utc),
        )

    def __eq__(self, other: object) -> bool:
        """Check if this password history entry is equal to another.
        
        Args:
            other: The other object to compare with
            
        Returns:
            bool: True if the objects are equal, False otherwise
        """
        if not isinstance(other, PasswordHistory):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Return a hash value for this password history entry.
        
        Returns:
            int: The hash value
        """
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a string representation of the password history entry.
        
        Returns:
            str: String representation
        """
        return (
            f"<PasswordHistory(id={self.id}, "
            f"user_id={self.user_id}, "
            f"changed_at={self.changed_at.isoformat()})>"
        )

    def is_expired(self, expiry_days: int) -> bool:
        """Check if this password history entry is expired.
        
        Args:
            expiry_days: Number of days after which the password expires
            
        Returns:
            bool: True if expired, False otherwise
        """
        if not expiry_days:
            return False
            
        expiry_date = self.changed_at + timedelta(days=expiry_days)
        return datetime.now(timezone.utc) > expiry_date
