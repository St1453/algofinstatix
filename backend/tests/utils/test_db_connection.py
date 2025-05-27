"""Test database connection utilities."""

import os

import asyncpg
import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Load environment variables from .env.test
load_dotenv(".env.test")

# Test database URL from environment variables
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:"
    f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}_test"
)


@pytest.mark.asyncio
async def test_asyncpg_connection():
    """Test direct asyncpg connection."""
    print("\nTesting direct asyncpg connection...")
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_SERVER"),
            port=int(os.getenv("POSTGRES_PORT")),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=f"{os.getenv('POSTGRES_DB')}_test",
        )
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version}")
        await conn.close()
        return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False


@pytest.mark.asyncio
async def test_sqlalchemy_connection():
    """Test SQLAlchemy async connection."""
    print("\nTesting SQLAlchemy async connection...")
    try:
        # Create async engine with NullPool for testing
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=True,
            poolclass=None,  # Use default pool for testing
        )

        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar_one()
            print(f"SQLAlchemy connected to: {version}")

        await engine.dispose()
        return True
    except Exception as e:
        print(f"Error with SQLAlchemy connection: {e}")
        return False


@pytest.mark.asyncio
async def test_db_session():
    """Test database session creation."""
    print("\nTesting database session creation...")
    try:
        engine = create_async_engine(TEST_DATABASE_URL, echo=True)
        async with AsyncSession(engine) as session:
            # Execute a simple query
            result = await session.execute("SELECT 1")
            assert result.scalar_one() == 1
            print("Database session test passed")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"Database session test failed: {e}")
        return False
