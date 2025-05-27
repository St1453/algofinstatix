from typing import Any, Dict, Optional


class BaseAppError(Exception):
    """Base exception class for all application exceptions.

    Attributes:
        message: The error message.
        error_code: A unique error code for this type of error.
        details: Additional details about the error.
        status_code: The HTTP status code to return for this error.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "unexpected_error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        """Initialize the base error.

        Args:
            message: A human-readable error message.
            error_code: A unique error code for this type of error.
            details: Additional details about the error.
            status_code: The HTTP status code to return for this error.
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for JSON serialization."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
            "success": False,
        }


class DatabaseError(BaseAppError):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "A database error occurred",
        error_code: str = "database_error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        """Initialize the database error.

        Args:
            message: A human-readable error message.
            error_code: A unique error code for this type of error.
            details: Additional details about the error.
            status_code: The HTTP status code to return for this error.
        """
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=status_code,
        )


class NotFoundError(DatabaseError):
    """Raised when a requested resource is not found in the database."""

    def __init__(
        self,
        resource: str = "resource",
        identifier: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the not found error.

        Args:
            resource: The name of the resource that was not found.
            identifier: The identifier that was used to look up the resource.
            details: Additional details about the error.
        """
        if identifier is not None:
            message = f"{resource} with ID {identifier} not found"
        else:
            message = f"{resource} not found"

        details = details or {}
        details["resource"] = resource
        if identifier is not None:
            details["identifier"] = identifier

        super().__init__(
            message=message,
            error_code="not_found",
            details=details,
            status_code=404,
        )
