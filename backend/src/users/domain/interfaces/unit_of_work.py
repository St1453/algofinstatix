from abc import abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from src.users.domain.interfaces.token_repository import ITokenRepository
    from src.users.domain.interfaces.user_repository import IUserRepository

T = TypeVar("T")


class IUnitOfWork(Protocol):
    """Interface for Unit of Work pattern.

    The Unit of Work pattern maintains a list of objects affected by a transaction.
    """

    @property
    @abstractmethod
    def users(self) -> "IUserRepository":
        """Access the user repository."""
        ...

    @property
    @abstractmethod
    def tokens(self) -> "ITokenRepository":
        """Access the token repository."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes made in this unit of work."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back all changes made in this unit of work."""
        ...

    @asynccontextmanager
    @abstractmethod
    async def transaction(self) -> AsyncIterator[None]:
        """Context manager for transaction management.

        Yields:
            None: The context manager yields control to the block
            within the transaction.

        Raises:
            Exception: Any exception that occurs during the transaction.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the unit of work and release any resources.

        This should be called when the unit of work is no longer needed.
        """
        ...
