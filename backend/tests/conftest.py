"""Pytest configuration and shared fixtures."""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.main import app
from src.shared.infrastructure.database.base import Base

# Load environment variables from .env.test
load_dotenv(".env.test")

# Construct test database URL from environment variables
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:"
    f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}_test"
)

# Create test async engine and session factory
engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for each test case.
    This is required for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for each test and clean up afterwards.
    """
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a new session for the test
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def random_email() -> str:
    """Generate a random email for testing."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def random_username() -> str:
    """Generate a random username for testing."""
    return f"testuser_{uuid.uuid4().hex[:8]}"
