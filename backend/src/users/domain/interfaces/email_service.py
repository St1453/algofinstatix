from src.users.domain.schemas.user_schemas import VerifyEmailRequest


class IEmailService:
    """Interface for email service."""

    async def send_verification_email(self, request: VerifyEmailRequest) -> None:
        """Send an email verification email to the user.

        Args:
            request: VerifyEmailRequest object containing email, token, and username

        Raises:
            HTTPException: If email sending fails
        """
        ...

    async def send_password_reset_email(self, request: VerifyEmailRequest) -> None:
        """Send a password reset email to the user.

        Args:
            request: VerifyEmailRequest object containing email, token, and username

        Raises:
            HTTPException: If email sending fails
        """
        ...
