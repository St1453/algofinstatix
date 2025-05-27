"""Email value object for user email addresses with validation."""

from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)
class Email:
    """Email value object for user email addresses with validation."""

    value: str

    def __post_init__(self) -> None:
        """Validate the email address during initialization."""
        try:
            # Use Pydantic's EmailStr for validation
            email = validate_email(self.value.strip().lower())
            # Use object.__setattr__ since the dataclass is frozen
            object.__setattr__(self, "value", email)
        except EmailNotValidError as e:
            raise ValueError("Invalid email format") from e

    @property
    def domain(self) -> str:
        """Get the domain part of the email."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get the local part of the email (before @)."""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
