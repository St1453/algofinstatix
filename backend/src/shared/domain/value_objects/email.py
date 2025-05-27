"""Email value object for domain models."""

from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email

from ..exceptions import ValidationError


@dataclass(frozen=True)
class Email:
    """Email value object that ensures email validity."""

    value: str

    def __post_init__(self):
        """Validate the email address on initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the email address."""
        try:
            # Validate and normalize the email
            email_info = validate_email(self.value, check_deliverability=False)
            # Use the normalized form
            object.__setattr__(self, "value", email_info.normalized)
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def create(cls, email: str) -> "Email":
        """Create a new Email instance.

        Args:
            email: The email address as a string

        Returns:
            A new Email instance

        Raises:
            ValidationError: If the email is invalid
        """
        return cls(email)
