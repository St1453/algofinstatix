"""Base repository class with enhanced logging and error handling."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Generic, Optional, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.exceptions_database import DatabaseError
from src.shared.infrastructure.logging.database_logger import (
    DatabaseLogger,
    get_database_logger,
)

# Type variables for generic repository
ModelT = TypeVar("ModelT")
T = TypeVar("T")  # For generic return types


class BaseRepository(Generic[ModelT], ABC):
    """Base repository class with common CRUD operations and logging.

    This class provides a foundation for all repositories with:
    - Standardized logging
    - Error handling
    - Performance monitoring
    - Common CRUD operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize the base repository.

        Args:
            session: The database session to use for operations.
        """
        self._session = session
        self._logger: Optional[DatabaseLogger] = None

    @property
    def logger(self) -> DatabaseLogger:
        """Get the database logger instance.

        Returns:
            DatabaseLogger: The configured database logger.
        """
        if self._logger is None:
            self._logger = get_database_logger()
        return self._logger

    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Return the name of the entity this repository manages.

        Returns:
            str: The name of the entity (e.g., 'user', 'token').
        """
        pass

    async def _execute_with_logging(
        self,
        operation: str,
        operation_func: Callable[..., Awaitable[T]],
        *args,
        log_success: bool = True,
        **kwargs,
    ) -> T:
        """Execute a database operation with structured logging and error handling.

        Args:
            operation: Name of the operation being performed (e.g., 'create', 'update').
            operation_func: The function that performs the actual database operation.
            *args: Positional arguments to pass to the operation function.
            log_success: Whether to log successful operations.
            **kwargs: Keyword arguments to pass to the operation function.

        Returns:
            The result of the operation function.

        Raises:
            DatabaseError: If the operation fails.
        """
        start_time = time.monotonic()
        entity_id = kwargs.get("id")

        try:
            # Execute the operation
            result = await operation_func(*args, **kwargs)
            duration = time.monotonic() - start_time

            # Log slow queries
            if duration > 1.0:  # 1 second threshold for slow queries
                self.logger.log_slow_query(
                    query=f"{self.entity_name}.{operation}",
                    duration=duration,
                    threshold=1.0,
                    entity=self.entity_name,
                    operation=operation,
                    entity_id=entity_id,
                )

            # Log successful operation if enabled
            if log_success:
                self.logger.log_operation(
                    operation=operation,
                    entity=self.entity_name,
                    entity_id=entity_id,
                    duration=duration,
                    status="success",
                )

            return result

        except SQLAlchemyError as e:
            duration = time.monotonic() - start_time

            # Log the error with context
            self.logger.log_operation(
                operation=operation,
                entity=self.entity_name,
                entity_id=entity_id,
                duration=duration,
                status="error",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Re-raise with a more specific error
            raise DatabaseError(
                f"Failed to {operation} {self.entity_name.lower()}: {str(e)}"
            ) from e
