"""Type definitions for dependency injection."""

from typing import Protocol, TypeVar, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@runtime_checkable
class IUnitOfWork(Protocol):
    """Protocol for Unit of Work pattern."""

    session: AsyncSession
    session_factory: async_sessionmaker[AsyncSession]

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    async def close(self) -> None:
        """Close the current session."""
        ...

    async def __aenter__(self) -> 'IUnitOfWork':
        """Async context manager entry."""
        ...

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        ...


# Type variable for the Unit of Work
UOW = TypeVar('UOW', bound=IUnitOfWork)
