from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from .repositories.token_repository_impl import TokenRepositoryImpl
from .repositories.user_repository_impl import UserRepositoryImpl

if TYPE_CHECKING:
    from .unit_of_work import UnitOfWork


class RepositoryFactory:
    """Factory for creating repositories with a shared session."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repositories: Dict[Type, Any] = {}

    @property
    def tokens(self) -> TokenRepositoryImpl:
        """Get a token repository instance."""
        if TokenRepositoryImpl not in self._repositories:
            self._repositories[TokenRepositoryImpl] = TokenRepositoryImpl(self._session)
        return self._repositories[TokenRepositoryImpl]

    @property
    def users(self) -> UserRepositoryImpl:
        """Get a user repository instance."""
        if UserRepositoryImpl not in self._repositories:
            self._repositories[UserRepositoryImpl] = UserRepositoryImpl(self._session)
        return self._repositories[UserRepositoryImpl]

    def create_uow(self) -> "UnitOfWork":
        """Create a new Unit of Work instance."""
        from .unit_of_work import UnitOfWork

        return UnitOfWork(self._session)
