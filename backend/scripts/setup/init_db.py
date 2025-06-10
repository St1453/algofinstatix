"""Database initialization and migration utilities."""

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.config import get_settings  # noqa: E402

settings = get_settings()


async def create_database() -> None:
    """Create the database if it doesn't exist."""
    # Create an asynchronous engine to connect to the postgres database

    # Get database connection details from settings
    db_name = settings.POSTGRES_DB
    db_user = settings.POSTGRES_USER
    db_password = settings.POSTGRES_PASSWORD
    db_host = settings.POSTGRES_SERVER
    db_port = settings.POSTGRES_PORT

    # Create the connection URL for the postgres database
    # Using a direct connection string to avoid encoding issues
    postgres_url = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    print(
        f"Connecting to database with URL: postgresql+psycopg2://{db_user}:****@{db_host}:{db_port}/{db_name}"
    )

    # Connect to the postgres database to create our database
    engine = create_engine(postgres_url, pool_pre_ping=True)
    conn = engine.connect()
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")

    # Check if database exists
    result = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :dbname"), {"dbname": db_name}
    )

    if not result.scalar():
        # Create the database
        conn.execute(text(f"CREATE DATABASE {db_name} ENCODING 'utf8'"))
        print(f"Created database: {db_name}")
    else:
        print(f"Database {db_name} already exists")

    conn.close()
    engine.dispose()


async def run_migrations() -> None:
    """Run database migrations."""
    print("Running database migrations...")

    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Set the paths for Alembic configuration and migration files
    migrations_dir = os.path.join(project_root, "alembic")
    config_file = os.path.join(project_root, "alembic.ini")

    # Load the Alembic configuration
    config = Config(config_file)

    # Set the migration directory and database URL
    config.set_main_option("script_location", str(migrations_dir))

    # Set the SQLAlchemy URL in the config
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    # Run the migrations using the standard Alembic API
    command.upgrade(config, "head")

    print("Migrations completed successfully")


async def init_database() -> None:
    """Initialize the database and run migrations."""
    print("Initializing database...")

    # Create the database if it doesn't exist
    await create_database()

    # Run migrations
    await run_migrations()

    print("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_database())
