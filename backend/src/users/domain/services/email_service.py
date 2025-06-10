"""Email service implementation using SMTP and template manager."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from fastapi import HTTPException, status

from src.core.templating.templating import template_manager
from src.users.domain.interfaces.email_service import IEmailService
from src.users.domain.schemas.user_schemas import VerifyEmailRequest

logger = logging.getLogger(__name__)


class EmailService(IEmailService):
    """Email service implementation using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        base_url: str,
        use_tls: bool = True,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
    ):
        """Initialize the email service with SMTP settings.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            base_url: Base URL for generating absolute URLs in emails
            use_tls: Whether to use TLS for SMTP connection
            sender_email: Sender email address (defaults to smtp_user if not provided)
            sender_name: Sender display name
        """
        self.base_url = base_url.rstrip("/")
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.smtp_username = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.sender_email = sender_email or smtp_user or "noreply@algofinstatix.com"
        self.sender_name = sender_name or "AlgoFinStatiX"

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
    ) -> None:
        """Send an email using the specified template.

        Args:
            to_email: Recipient's email address
            subject: Email subject
            template_name: Name of the template file (without .html)
            context: Context variables for the template

        Raises:
            HTTPException: If email sending fails
        """
        try:
            # Add common context variables
            context.update(
                {
                    "site_name": self.sender_name,
                    "base_url": self.base_url,
                }
            )

            # Render the email body from template
            template_path = f"emails/{template_name}.html"
            logger.debug(
                "Rendering template: %s with context: %s",
                template_path,
                {k: v for k, v in context.items() if k != "token"},
            )
            html_content = template_manager.render_template(template_path, context)

            # Simple HTML to text conversion
            text_content = (
                html_content.replace("<br>", "\n")
                .replace("</p>", "\n\n")
                .replace("<strong>", "")
                .replace("</strong>", "")
                .replace("<a ", " (")
                .replace("</a>", ")")
                .replace('href="', "")
                .split('">')[0]
                + "\n"  # Extract URL from <a> tags
            )

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.sender_name, self.sender_email))
            msg["To"] = to_email

            # Attach both text and HTML versions
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                logger.info("Email sent to %s", to_email)

        except Exception as e:
            logger.error("Failed to send email: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email",
            ) from e

    async def send_verification_email(self, request: VerifyEmailRequest) -> None:
        """Send an email verification email to the user."""
        verification_url = f"{self.base_url}/auth/verify-email?token={request.token}"
        await self._send_email(
            to_email=request.email,
            subject="Verify Your Email Address",
            template_name="verification",
            context={
                "username": request.username or "User",
                "verification_url": verification_url,
                "token": request.token,
            },
        )

    async def send_password_reset_email(self, request: VerifyEmailRequest) -> None:
        """Send a password reset email to the user."""
        reset_url = f"{self.base_url}/auth/reset-password?token={request.token}"
        await self._send_email(
            to_email=request.email,
            subject="Reset Your Password",
            template_name="password_reset",
            context={
                "username": request.username or "User",
                "reset_url": reset_url,
                "token": request.token,
            },
        )
