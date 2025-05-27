from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


class IUnitOfWork(ABC):
    """Interface for the Unit of Work pattern."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Provide a transactional scope around a series of operations."""
        pass


class UnitOfWork(IUnitOfWork):
    """Implementation of the Unit of Work pattern."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._is_closed = False

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._is_closed:
            raise RuntimeError("Unit of Work is closed")
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        if not self._is_closed:
            await self._session.rollback()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Provide a transactional scope around a series of operations."""
        if self._is_closed:
            raise RuntimeError("Unit of Work is closed")

        async with self._session.begin():
            try:
                yield
            except Exception:
                await self.rollback()
                raise

    async def close(self) -> None:
        """Close the Unit of Work."""
        if not self._is_closed:
            self._is_closed = True
            await self._session.close()
