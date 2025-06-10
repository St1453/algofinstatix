"""Pytest configuration and fixtures for user domain tests."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.users.infrastructure.database.models.user_orm import UserORM

# Test database URL (using in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine and session factory
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncTestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create a new database session for a test."""
    # Create all tables
    from src.shared.infrastructure.database.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a new session
    session = AsyncTestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # Clean up tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def user_orm_fixture(db_session: AsyncSession):
    """Create a test user ORM instance."""
    user = UserORM(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password="hashed_password",
        is_enabled_account=True,
        is_verified_email=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
