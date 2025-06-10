from abc import ABC, abstractmethod


class IPasswordService(ABC):
    """Interface for password service operations."""

    @abstractmethod
    async def hash_password(self, plain_password: str) -> str:
        """Hash a plain text password."""
        ...

    @abstractmethod
    async def verify_password(
        self, user_id: str, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify a plain text password against a hashed password."""
        ...

    @abstractmethod
    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """Change a user's password with proper validation."""
        ...

    @abstractmethod
    def validate_password_strength(self, password: str) -> None:
        """Validate that a password meets strength requirements."""
        ...

    @abstractmethod
    def generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password."""
        ...
