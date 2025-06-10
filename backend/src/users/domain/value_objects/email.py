"""Email value object for user email addresses with validation."""

from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)
class Email:
    """Email value object for user email addresses with validation.
    
    Email addresses are case-insensitive and are always stored in lowercase.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize the email address during initialization."""
        if not self.value:
            raise ValueError("Email cannot be empty")
            
        try:
            # Validate and normalize the email (including case normalization)
            validated = validate_email(self.value.strip(), check_deliverability=False)
            # Store the normalized email in lowercase
            object.__setattr__(self, "value", validated.email.lower())
        except EmailNotValidError as e:
            raise ValueError("Invalid email format") from e

    @classmethod
    def from_string(cls, value: str) -> "Email":
        """Create an Email instance from a string."""
        return cls(value)

    @property
    def domain(self) -> str:
        """Get the domain part of the email (after @)."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get the local part of the email (before @)."""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()

    def __hash__(self) -> int:
        return hash(self.value.lower())
