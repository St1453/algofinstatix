"""Database helper functions for testing."""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


async def create_test_instance(
    session: AsyncSession,
    model: Type[ModelType],
    data: Dict[str, Any],
    commit: bool = True,
) -> ModelType:
    """Create a test instance of a model.

    Args:
        session: The database session.
        model: The SQLAlchemy model class.
        data: Dictionary of data to create the instance with.
        commit: Whether to commit the transaction.

    Returns:
        The created model instance.
    """
    instance = model(**data)
    session.add(instance)
    if commit:
        await session.commit()
        await session.refresh(instance)
    return instance


async def get_test_instance(
    session: AsyncSession, model: Type[ModelType], id: Union[int, UUID, str]
) -> Optional[ModelType]:
    """Get a test instance by ID.

    Args:
        session: The database session.
        model: The SQLAlchemy model class.
        id: The ID of the instance to retrieve.

    Returns:
        The model instance if found, None otherwise.
    """
    stmt = select(model).where(model.id == id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_test_instances(
    session: AsyncSession, model: Type[ModelType], **filters: Any
) -> List[ModelType]:
    """List test instances with optional filtering.

    Args:
        session: The database session.
        model: The SQLAlchemy model class.
        **filters: Filters to apply to the query.

    Returns:
        A list of model instances.
    """
    stmt = select(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_test_instances(
    session: AsyncSession, model: Type[ModelType], **filters: Any
) -> int:
    """Delete test instances matching the given filters.

    Args:
        session: The database session.
        model: The SQLAlchemy model class.
        **filters: Filters to apply to the delete query.

    Returns:
        The number of rows deleted.
    """
    stmt = delete(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def clear_test_data(session: AsyncSession) -> None:
    """Clear all test data from the database.

    Args:
        session: The database session.
    """
    # Get all tables in reverse order to handle foreign key constraints
    from src.shared.infrastructure.database.base import metadata

    for table in reversed(metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()
