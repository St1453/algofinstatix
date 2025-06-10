from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.shared.infrastructure.database.session import get_session_factory
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.infrastructure.database.factory import RepositoryFactory

T = TypeVar("T")


class UnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work.

    This class manages database transactions and provides access to repositories.
    It ensures that all operations within a unit of work are committed
    or rolled back together.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        """Initialize Unit of Work with an optional session factory.

        Args:
            session_factory: Optional session factory.
            If not provided, the default factory will be used.
        """
        self._session_factory = session_factory or get_session_factory()
        self._session: AsyncSession | None = None
        self._factory: RepositoryFactory | None = None
        self._is_closed = False

    async def __aenter__(self) -> UnitOfWork:
        if self._is_closed:
            raise RuntimeError("Cannot reuse a closed UnitOfWork")

        self._session = self._session_factory()
        self._factory = RepositoryFactory(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()

    @property
    def users(self):
        if self._factory is None or self._is_closed:
            raise RuntimeError("UnitOfWork is not initialized or already closed")
        return self._factory.users

    @property
    def tokens(self):
        if self._factory is None or self._is_closed:
            raise RuntimeError("UnitOfWork is not initialized or already closed")
        return self._factory.tokens

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._is_closed or self._session is None:
            raise RuntimeError("UnitOfWork is closed or not initialized")

        try:
            await self._session.commit()
        except Exception:
            await self.rollback()
            raise

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        if not self._is_closed and self._session is not None:
            await self._session.rollback()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Context manager for a database transaction.

        Yields:
            None

        Raises:
            RuntimeError: If the UnitOfWork is closed or not initialized
        """
        if self._is_closed or self._session is None:
            raise RuntimeError("UnitOfWork is closed or not initialized")

        async with self._session.begin():
            try:
                yield
            except Exception:
                await self.rollback()
                raise

    async def close(self) -> None:
        """Close the Unit of Work and release resources."""
        if not self._is_closed and self._session is not None:
            self._is_closed = True
            await self._session.close()
            self._session = None
            self._factory = None

    @classmethod
    async def create(
        cls: Type[T], session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> T:
        """Factory method to create and initialize a new Unit of Work.

        Args:
            session_factory: Optional session factory

        Returns:
            An initialized instance of UnitOfWork
        """
        uow = cls(session_factory)
        await uow.__aenter__()
        return uow
