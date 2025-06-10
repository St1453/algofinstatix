"""Username value object for users with validation."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Username:
    """Username value object for users with validation.

    Username rules:
    - 3 to 32 characters long
    - Can contain letters, numbers, underscores, and hyphens
    - Must start with a letter
    - No spaces or special characters
    - Case-insensitive (stored in lowercase)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize the username during initialization."""
        if not self.value:
            raise ValueError("Username cannot be empty")

        # Trim whitespace and convert to lowercase
        username = self.value.strip().lower()

        # Length validation
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username) > 32:
            raise ValueError("Username cannot be longer than 32 characters")

        # Character set validation
        if not re.match(r"^[a-z][a-z0-9_-]*$", username):
            raise ValueError(
                "Username must start with a letter and can only contain "
                "letters, numbers, underscores, and hyphens"
            )

        # Store the normalized username
        object.__setattr__(self, "value", username)

    def __str__(self) -> str:
        return self.value
        
    @classmethod
    def from_string(cls, value: str) -> "Username":
        """Create a Username instance from a string."""
        return cls(value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Username, str)):
            return False
        if isinstance(other, str):
            return self.value == other.lower()
        return self.value == other.value
        
    def __hash__(self) -> int:
        return hash(self.value)
