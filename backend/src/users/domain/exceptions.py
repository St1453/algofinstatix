"""Custom exceptions for the users domain.

This module defines all custom exceptions used throughout the users domain.
Exceptions are organized hierarchically for better error handling and categorization.
"""

from __future__ import annotations


class UserError(Exception):
    """Base exception for all user-related errors."""

    pass


class UserNotFoundError(UserError):
    """Raised when a user is not found in the system."""

    pass


class UserAlreadyExistsError(UserError):
    """Raised when trying to create a user that already exists."""

    pass


class UsernameAlreadyExistsError(UserError):
    """Raised when trying to create a user that already exists."""

    pass


class UserUpdateError(UserError):
    """Raised when an error occurs during user update."""

    pass


class UserAuthenticationError(UserError):
    """Raised when user authentication fails."""

    pass


class UserNotAuthorizedError(UserError):
    """Raised when a user is not authorized to perform an action."""

    pass


class UserValidationError(UserError):
    """Raised when user data validation fails."""

    pass


class UserRegistrationError(UserError):
    """Raised when user registration fails."""

    pass


class AccountError(UserError):
    """Base exception for account-related errors."""

    pass


class AccountNotVerifiedError(AccountError):
    """Raised when an account email is not verified."""

    pass


class AccountDisabledError(AccountError):
    """Raised when an account has been disabled by an administrator."""

    pass


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class TokenError(AuthenticationError):
    """Base exception for token-related errors."""

    pass


class InvalidTokenError(TokenError):
    """Raised when a token is invalid."""

    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""

    pass


class TokenTypeError(TokenError):
    """Raised when a token is of the wrong type."""

    pass


class TokenRevokedError(TokenError):
    """Raised when a token has been revoked."""

    pass


class TokenGenerationError(TokenError):
    """Raised when token generation fails."""

    pass


class TokenValidationError(TokenError):
    """Raised when token validation fails."""

    pass


class TokenRefreshError(TokenError):
    """Raised when token refresh fails."""

    pass


class PasswordError(AuthenticationError):
    """Base exception for password-related errors."""

    pass


class InvalidPasswordError(PasswordError):
    """Raised when a password is invalid."""

    pass


class PasswordTooWeakError(PasswordError):
    """Raised when a password doesn't meet strength requirements."""

    pass


class PasswordReuseError(PasswordError):
    """Raised when a password was used recently and can't be reused."""

    pass


class PasswordExpiredError(PasswordError):
    """Raised when a password has expired and needs to be changed."""

    pass


class PasswordHashingError(PasswordError):
    """Raised when password hashing fails."""

    pass


class InvalidCredentialsError(PasswordError):
    """Raised when invalid credentials are provided."""

    pass


class PasswordResetError(PasswordError):
    """Raised when password reset fails."""

    pass


class PasswordPolicyViolation(PasswordError):
    """Raised when a password policy is violated."""

    pass


class PasswordStrengthError(PasswordError):
    """Raised when a password strength is not met."""

    pass


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class RateLimitExceededError(SecurityError):
    """Raised when rate limit is exceeded."""

    pass


class PermissionDeniedError(SecurityError):
    """Raised when a user doesn't have permission to perform an action."""

    pass


class SessionError(SecurityError):
    """Base exception for session-related errors."""

    pass


class SessionExpiredError(SessionError):
    """Raised when a user session has expired."""

    pass


class SessionRevokedError(SessionError):
    """Raised when a user session has been revoked."""

    pass


class ValidationError(ValueError):
    """Base exception for validation errors."""

    pass


class EmailError(ValidationError):
    """Raised when there's an error with an email address."""

    pass


class InvalidEmailError(EmailError):
    """Raised when an email address is invalid."""

    pass


class EmailAlreadyExistsError(EmailError):
    """Raised when an email address is already in use."""

    pass


class EmailVerificationError(EmailError):
    """Raised when email verification fails."""

    pass
