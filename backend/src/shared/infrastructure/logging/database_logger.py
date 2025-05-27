"""Database logging configuration and utilities.

This module provides structured logging for database operations, including:
- SQL query logging
- Operation timing and monitoring
- Slow query detection

Note: Audit logging has been moved to audit_logger.py
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Optional, TypeVar, Union

from src.core.config import get_settings
from src.core.formatter import StructuredFormatter

# Type variable for generic function return type
T = TypeVar("T")


class DatabaseLogger(ABC):
    """Abstract base class for database logging operations."""

    @abstractmethod
    async def log_operation(
        self,
        operation: str,
        entity: str,
        entity_id: Optional[Union[str, int, list]] = None,
        duration: Optional[float] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database operation.

        Args:
            operation: Type of operation (create, read, update, delete).
            entity: Name of the database table/entity.
            entity_id: ID or list of IDs of the affected record(s).
            duration: Operation duration in seconds.
            status: Operation status (success, error, warning).
            **context: Additional context about the operation.
        """
        pass

    @abstractmethod
    async def log_slow_query(
        self, query: str, duration: float, threshold: float = 1.0, **kwargs: Any
    ) -> None:
        """Log a slow database query.

        Args:
            query: The SQL query that was executed.
            duration: Query execution time in seconds.
            threshold: Threshold in seconds to consider a query as slow.
            **kwargs: Additional query context.
        """
        pass

    @abstractmethod
    async def log_create(
        self,
        entity: str,
        entity_id: Optional[Union[str, int]] = None,
        duration: Optional[float] = None,
        status: str = "success",
        warnings: Optional[list] = None,
        **context: Any,
    ) -> None:
        """Log a database create operation.

        Args:
            entity: Name of the database table/entity.
            entity_id: Auto-incremented ID or primary key of the created record.
            duration: Operation duration in seconds.
            status: Operation status (success, error).
            warnings: List of SQLAlchemy warnings, if any.
            **context: Additional context about the operation.
        """
        pass

    @abstractmethod
    async def log_read(
        self,
        entity: str,
        query_params: Optional[dict] = None,
        duration: Optional[float] = None,
        row_count: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database read operation.

        Args:
            entity: Name of the database table/entity.
            query_params: Parameters used in the query (excluding sensitive data).
            duration: Query execution time in seconds.
            row_count: Number of rows returned.
            status: Operation status (success, not_found, error).
            **context: Additional context about the query.
        """
        pass

    @abstractmethod
    async def log_update(
        self,
        entity: str,
        entity_id: Union[str, int, list],
        duration: Optional[float] = None,
        rows_affected: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database update operation.

        Args:
            entity: Name of the database table/entity.
            entity_id: ID or list of IDs of the updated record(s).
            duration: Operation duration in seconds.
            rows_affected: Number of rows affected by the update.
            status: Operation status (success, not_found, error).
            **context: Additional context about the update.
        """
        pass

    @abstractmethod
    async def log_delete(
        self,
        entity: str,
        entity_id: Union[str, int, list],
        duration: Optional[float] = None,
        rows_deleted: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database delete operation.

        Args:
            entity: Name of the database table/entity.
            entity_id: ID or list of IDs of the deleted record(s).
            duration: Operation duration in seconds.
            rows_deleted: Number of rows deleted.
            status: Operation status (success, not_found, error, constraint_error).
            **context: Additional context about the deletion.
        """
        pass


class StructuredLogger(DatabaseLogger):
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
        self, event_type: str, category: str, message: str, **context: Any
    ) -> None:
        """Internal method to log an event with structured context."""
        # Redact any sensitive data from context
        safe_context = self._redact_sensitive_data(context)

        log_context = {
            "event_type": event_type,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **safe_context,
        }
        self.operation_logger.info(message, extra={"context": log_context})

    async def log_operation(
        self,
        operation: str,
        entity: str,
        entity_id: Optional[Union[str, int, list[Union[str, int]]]] = None,
        duration: Optional[float] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a generic database operation with structured context.

        This is a low-level method that other logging methods can use.
        """
        log_data = {
            "entity_id": entity_id,
            "duration": f"{duration:.6f}s" if duration is not None else None,
            **context,
        }

        base_context = {
            "operation": operation,
            "entity": entity,
            "status": status,
            **log_data
        }

        if status == "error":
            self._log_event(
                "database_operation",
                "error",
                f"Database {operation} operation failed",
                **base_context
            )
        elif status == "slow":
            self._log_event(
                "database_operation",
                "performance",
                f"Slow database {operation} operation",
                **base_context
            )
        else:
            self._log_event(
                "database_operation",
                "info",
                f"Database {operation} operation",
                **base_context
            )

    async def log_create(
        self,
        entity: str,
        entity_id: Optional[Union[str, int]] = None,
        duration: Optional[float] = None,
        status: str = "success",
        warnings: Optional[list] = None,
        **context: Any,
    ) -> None:
        """Log a database create operation."""
        await self.log_operation(
            operation="create",
            entity=entity,
            entity_id=entity_id,
            duration=duration,
            status=status,
            warnings=warnings,
            **context,
        )

    async def log_read(
        self,
        entity: str,
        query_params: Optional[dict] = None,
        duration: Optional[float] = None,
        row_count: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database read operation."""
        await self.log_operation(
            operation="read",
            entity=entity,
            duration=duration,
            status=status,
            query_params=query_params,
            row_count=row_count,
            **context,
        )

    async def log_update(
        self,
        entity: str,
        entity_id: Union[str, int, list],
        duration: Optional[float] = None,
        rows_affected: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database update operation."""
        await self.log_operation(
            operation="update",
            entity=entity,
            entity_id=entity_id,
            duration=duration,
            status=status,
            rows_affected=rows_affected,
            **context,
        )

    async def log_delete(
        self,
        entity: str,
        entity_id: Union[str, int, list],
        duration: Optional[float] = None,
        rows_deleted: Optional[int] = None,
        status: str = "success",
        **context: Any,
    ) -> None:
        """Log a database delete operation."""
        await self.log_operation(
            operation="delete",
            entity=entity,
            entity_id=entity_id,
            duration=duration,
            status=status,
            rows_deleted=rows_deleted,
            **context,
        )

    async def log_slow_query(
        self, query: str, duration: float, threshold: float = 1.0, **kwargs: Any
    ) -> None:
        """Log slow database queries with detailed context."""
        if duration > threshold:
            safe_query = query
            for field in self._sensitive_fields:
                if field in safe_query.lower():
                    # This is a simple redaction - in production you might want
                    # to use a proper SQL parser to handle this more accurately
                    safe_query = safe_query.replace(field, "[REDACTED]")


            log_context = {
                "query": safe_query[:1000],  # Truncate very long queries
                "duration": f"{duration:.6f}s",
                "threshold": f"{threshold}s",
                **self._redact_sensitive_data(kwargs),
            }

            
            self._log_event(
                "slow_query",
                "performance",
                f"Slow query detected (took {duration:.3f}s, threshold: {threshold}s)",
                **log_context
            )


_db_logger = StructuredLogger(get_settings())


def get_database_logger() -> DatabaseLogger:
    """Get or create the database logger instance."""
    return _db_logger
