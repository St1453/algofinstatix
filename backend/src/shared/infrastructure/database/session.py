# src/shared/infrastructure/database/session.py
from contextlib import asynccontextmanager
from typing import AsyncIterator, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=NullPool if settings.TESTING else None,
)

# Create session factory
SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# For backward compatibility
async_session_factory = SessionFactory

# Type variable for dependency injection
T = TypeVar('T')


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory for creating new sessions."""
    return SessionFactory


@asynccontextmanager
async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Get a database session with automatic transaction management.
    
    This is a convenience function for simple use cases. For more complex scenarios,
    consider using the Unit of Work pattern directly.
    """
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
