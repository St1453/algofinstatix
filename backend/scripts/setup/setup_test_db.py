"""Script to set up the test database."""

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


def find_dotenv() -> Path:
    """Find the .env.test file in the project root."""
    # Start from the current file's directory and go up until we find the project root
    current = Path(__file__).parent.absolute()
    root_marker = "pyproject.toml"  # Assuming this marks the project root

    while current != current.parent:
        if (current / root_marker).exists():
            env_path = current / ".env.test"
            if env_path.exists():
                return env_path
        current = current.parent

    # If not found, return the default location relative to the script
    return Path(__file__).parent.parent.parent / ".env.test"


# Load environment variables from .env.test file
env_path = find_dotenv()
load_dotenv(dotenv_path=env_path, override=True)

# Database configuration from environment variables
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_SERVER", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
TEST_DB_NAME = "algofinstatix_test"

# Connection string for the default 'postgres' database
DEFAULT_DB_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
)
# Connection string for the test database
TEST_DB_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
)


async def database_exists(conn, dbname):
    """Check if a database exists."""
    result = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
    return result is not None


async def create_database():
    """Create the test database if it doesn't exist."""
    # Connect to the default 'postgres' database
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres",
    )

    try:
        # Check if database exists
        db_exists = await database_exists(conn, TEST_DB_NAME)

        if not db_exists:
            print(f"Creating database {TEST_DB_NAME}...")
            # Create the database with UTF-8 encoding
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}" ENCODING "UTF8"')
            print(f"Database {TEST_DB_NAME} created successfully.")
        else:
            print(f"Database {TEST_DB_NAME} already exists.")

        # Connect to the test database to verify
        test_conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=TEST_DB_NAME,
        )
        await test_conn.close()
        print(f"Successfully connected to database {TEST_DB_NAME}.")

    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_database())
