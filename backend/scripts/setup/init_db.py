"""Database initialization and migration utilities."""

import asyncio
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.shared.infrastructure.config import settings
from src.shared.infrastructure.database.session import get_async_session


async def create_database() -> None:
    """Create the database if it doesn't exist."""
    # Create a synchronous engine to connect to the postgres database
    from sqlalchemy import create_engine
    
    # Get the database URL without the database name
    db_url_parts = settings.DATABASE_URL.split('/')
    db_name = db_url_parts[-1]
    base_url = '/'.join(db_url_parts[:-1])
    
    # Connect to the postgres database to create our database
    engine = create_engine(f"{base_url}/postgres")
    conn = engine.connect()
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
    
    # Check if database exists
    result = conn.execute(
        text(
            "SELECT 1 FROM pg_database WHERE datname = :dbname"
        ),
        {"dbname": db_name}
    )
    
    if not result.scalar():
        # Create the database
        conn.execute(
            text(f"CREATE DATABASE {db_name} ENCODING 'utf8'")
        )
        print(f"Created database: {db_name}")
    else:
        print(f"Database {db_name} already exists")
    
    conn.close()
    engine.dispose()


def run_migrations() -> None:
    """Run database migrations."""
    print("Running database migrations...")
    
    # Get the directory that this file is in
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "alembic")
    config = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    
    # Set the migration directory
    config.set_main_option("script_location", str(migrations_dir))
    
    # Run the migrations
    command.upgrade(config, "head")
    print("Migrations completed successfully")


async def init_database() -> None:
    """Initialize the database and run migrations."""
    print("Initializing database...")
    
    # Create the database if it doesn't exist
    await create_database()
    
    # Run migrations
    run_migrations()
    
    print("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_database())
