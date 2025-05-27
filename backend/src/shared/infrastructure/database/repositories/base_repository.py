"""Base repository class with enhanced logging and error handling."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.exceptions_database import DatabaseError
from src.shared.infrastructure.logging.database_logger import (
    DatabaseLogger,
    get_database_logger,
)

# Type variables for generic repository
ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")
T = TypeVar("T")  # For generic return types


class BaseRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT], ABC):
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
            from src.core.config import get_settings

            self._logger = get_database_logger(get_settings())
        return self._logger

    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Return the name of the entity this repository manages.

        Returns:
            str: The name of the entity (e.g., 'user', 'token').
        """
        pass

    def with_logging(
        self,
        operation: str,
        log_success: bool = True,
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """Add structured logging to repository methods.

        Example:
            @with_logging(operation="create")
            async def create(self, entity_data: dict) -> ModelT:
                return await self._create(entity_data)

        Args:
            operation: The operation name (e.g., 'create', 'update').
            log_success: Whether to log successful operations.

        Returns:
            A decorator that adds logging to the wrapped method.
        """

        def decorator(
            method: Callable[..., Awaitable[T]],
        ) -> Callable[..., Awaitable[T]]:
            async def wrapper(*args, **kwargs) -> T:
                entity_id = kwargs.get("id")
                start_time = time.monotonic()

                try:
                    result = await method(*args, **kwargs)
                    duration = time.monotonic() - start_time

                    # Log slow operations
                    if duration > 1.0:  # 1 second threshold
                        self.logger.log_slow_query(
                            query=f"{self.entity_name}.{operation}",
                            duration=duration,
                            threshold=1.0,
                            entity=self.entity_name,
                            operation=operation,
                            entity_id=entity_id,
                        )

                    # Log success if enabled
                    if log_success:
                        self.logger.log_operation(
                            operation=operation,
                            entity=self.entity_name,
                            entity_id=entity_id,
                            duration=duration,
                            status="success",
                        )

                    return result

                except Exception as e:
                    duration = time.monotonic() - start_time

                    # Log the error
                    self.logger.log_operation(
                        operation=operation,
                        entity=self.entity_name,
                        entity_id=entity_id,
                        duration=duration,
                        status="error",
                        error=str(e),
                        error_type=type(e).__name__,
                    )

                    # Re-raise the exception
                    raise

            return wrapper

        return decorator

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

    # Common CRUD operations that can be reused by child classes

    @with_logging(operation="create")
    async def _create_entity(
        self, model_class: Type[ModelT], create_data: Dict[str, Any], **kwargs: Any
    ) -> ModelT:
        """Create a new entity in the database.

        Args:
            model_class: The SQLAlchemy model class.
            create_data: Dictionary of data to create the entity with.
            **kwargs: Additional context for logging.

        Returns:
            The created entity.
        """
        entity = model_class(**create_data)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    @with_logging(operation="update")
    async def _update_entity(
        self,
        model_class: Type[ModelT],
        entity_id: Any,
        update_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Optional[ModelT]:
        """Update an existing entity.

        Args:
            model_class: The SQLAlchemy model class.
            entity_id: The ID of the entity to update.
            update_data: Dictionary of fields to update.
            **kwargs: Additional context for logging.

        Returns:
            The updated entity, or None if not found.

        Raises:
            DatabaseError: If the update operation fails.
        """
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(model_class)
            .where(model_class.id == entity_id)
            .values(update_data)
            .returning(model_class)
        )

        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def _delete_entity(
        self,
        model_class: Type[ModelT],
        entity_id: Any,
        hard_delete: bool = False,
        **kwargs: Any,
    ) -> bool:
        """Delete an entity.

        Args:
            model_class: The SQLAlchemy model class.
            entity_id: The ID of the entity to delete.
            hard_delete: If True, permanently delete the record.
                If False, perform a soft delete.
            **kwargs: Additional context for logging.

        Returns:
            bool: True if the entity was deleted, False otherwise.

        Raises:
            DatabaseError: If the delete operation fails.
        """
        if hard_delete:
            from sqlalchemy import delete as sql_delete

            stmt = sql_delete(model_class).where(model_class.id == entity_id)
            result = await self._session.execute(stmt)
            return result.rowcount > 0

        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(model_class)
            .where(model_class.id == entity_id)
            .values(deleted_at=datetime.now(timezone.utc), is_active=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_by_model(self, id: str) -> Optional[ModelT]:
        """Retrieve an entity by its ID.

        Args:
            id: The ID of the entity to retrieve.

        Returns:
            Optional[ModelT]: The entity if found, None otherwise.

        Raises:
            DatabaseError: If there's an error executing the query.
        """
        try:
            return await self._get_by_id(id)
        except Exception as e:
            self.logger.error(
                "Error getting %s with ID %s: %s",
                self.entity_name,
                id,
                str(e),
                exc_info=True,
            )
            raise DatabaseError(
                f"Error getting {self.entity_name}",
                error=str(e),
                entity_id=id,
            ) from e

    async def _get_by_id(self, id: str) -> Optional[ModelT]:
        """Internal method to retrieve an entity by its ID without logging.

        Args:
            id: The ID of the entity to retrieve.

        Returns:
            Optional[ModelT]: The entity if found, None otherwise.
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
