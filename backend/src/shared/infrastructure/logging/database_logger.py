"""Database logging configuration and utilities.

This module provides structured logging for database operations, including:
- SQL query logging
- Operation timing and monitoring
- Slow query detection

Note: Audit logging has been moved to audit_logger.py
"""

import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Literal, Optional, Union

from src.core.config import get_settings
from src.core.formatter import StructuredFormatter


class DatabaseLogger:
    """Concrete implementation of DatabaseLogger using structured JSON logging.

    This class provides detailed logging for all database operations including
    create, read, update, and delete operations with comprehensive context.
    """

    def __init__(self, settings=None):
        """Initialize the structured logger."""
        self.settings = settings or get_settings()
        self._setup_loggers()

        # Define sensitive fields that should be redacted from logs
        self._sensitive_fields = {
            "password",
            "token",
            "secret",
            "api_key",
            "access_key",
            "private_key",
            "credit_card",
            "ssn",
            "social_security",
        }

    def _setup_loggers(self) -> None:
        """Set up all required loggers."""
        self._ensure_log_directories_exist()

        self.operation_logger = self._create_logger(
            "database.operations", self.settings.LOG_DB_OPERATIONS, logging.INFO
        )
        self.slow_query_logger = self._create_logger(
            "database.slow_queries", self.settings.LOG_DB_SLOW, logging.WARNING
        )
        self.error_logger = self._create_logger(
            "database.errors", self.settings.LOG_DB_ERROR, logging.ERROR
        )

    def _ensure_log_directories_exist(self) -> None:
        """Ensure all log directories exist."""
        log_dirs = [
            os.path.dirname(self.settings.LOG_DB_OPERATIONS),
            os.path.dirname(self.settings.LOG_DB_SLOW),
            os.path.dirname(self.settings.LOG_DB_ERROR),
        ]
        for log_dir in log_dirs:
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

    def _create_logger(self, name: str, log_file: str, level: int) -> logging.Logger:
        """Create and configure a logger with file handler."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Don't add handlers if they already exist
        if logger.handlers:
            return logger

        formatter = StructuredFormatter()

        # File handler
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler for development
        if self.settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def _redact_sensitive_data(self, data: Any) -> Any:
        """Recursively redact sensitive data from dictionaries and lists.

        Args:
            data: The data to process (dict, list, or other types).

        Returns:
            The processed data with sensitive values redacted.
        """
        if isinstance(data, dict):
            return {
                k: "[REDACTED]"
                if any(s in k.lower() for s in self._sensitive_fields)
                else self._redact_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._redact_sensitive_data(item) for item in data]
        return data

    def _log_event(
        self, level: int, message: str, **context: Any
    ) -> None:
        """Internal method to log an event with structured context.
        
        Args:
            level: Logging level (e.g., logging.INFO, logging.ERROR)
            message: The log message
            **context: Additional context to include in the log
        """
        # Redact any sensitive data from context
        safe_context = self._redact_sensitive_data(context)
        
        # Add timestamp
        safe_context["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Log with the specified level
        self.operation_logger.log(level, message, extra={"context": safe_context})

    def log_operation(
        self,
        operation: str,
        entity: str,
        entity_id: Optional[Union[str, int, list[Union[str, int]]]] = None,
        duration: Optional[float] = None,
        status: Literal["success", "error"] = "success",
        **context: Any,
    ) -> None:
        """Log a database operation with structured context.
        
        Args:
            operation: The operation being performed (e.g., 'create', 'update')
            entity: The entity being operated on (e.g., 'user', 'order')
            entity_id: Optional ID(s) of the entity
            duration: Optional duration of the operation in seconds
            status: Operation status ("success" or "error")
            **context: Additional context to include in the log
        """
        log_data = {
            "operation": operation,
            "entity": entity,
            "status": status,
            **context,  # Include any additional context
        }
        
        # Only add non-None values
        if entity_id is not None:
            log_data["entity_id"] = entity_id
            
        if duration is not None:
            log_data["duration"] = f"{duration:.6f}s"
        
        # Determine log level and message based on status
        if status == "success":
            self._log_event(
                level=logging.INFO,
                message=f"{operation} {entity} completed successfully",
                **log_data,
            )
        else:  # error
            self._log_event(
                level=logging.ERROR,
                message=f"{operation} {entity} failed",
                **log_data,
            )

    def log_slow_query(
        self, query: str, duration: float, threshold: float = 1.0, **kwargs: Any
    ) -> None:
        """Log slow database queries with detailed context.
        
        Args:
            query: The SQL query that was slow
            duration: How long the query took in seconds
            threshold: Threshold in seconds above which to log the query
            **kwargs: Additional context about the query
        """
        if duration > threshold:
            safe_query = query
            for field in self._sensitive_fields:
                if field in safe_query.lower():
                    # This is a simple redaction - in production you might want
                    # to use a proper SQL parser to handle this more accurately
                    safe_query = safe_query.replace(field, "[REDACTED]")

            
            self._log_event(
                level=logging.WARNING,
                message=f"Slow query detected (took {duration:.3f}s)",
                query=safe_query[:1000],  # Truncate very long queries
                duration_seconds=duration,
                threshold_seconds=threshold,
                **self._redact_sensitive_data(kwargs),
            )


_db_logger = DatabaseLogger(get_settings())


def get_database_logger() -> DatabaseLogger:
    """Get or create the database logger instance."""
    return _db_logger
