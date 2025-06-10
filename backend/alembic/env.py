"""Alembic migration environment."""

import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import Column, MetaData, Table, Text, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import only the config, not the models to avoid circular imports
from src.core.config import get_settings

# Define a minimal metadata object for the tokens table
metadata = MetaData()

# Manually define the tokens table structure for migrations
Table(
    "tokens",
    metadata,
    Column("scopes", Text, comment="Comma-separated list of token scopes"),
    # Other columns will be added by existing migrations
)

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


settings = get_settings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the target metadata for autogenerate support
# This tells Alembic to use our manually defined metadata
target_metadata = metadata

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Get the database URL from settings.

    Returns:
        str: The database URL with asyncpg driver
    """
    url = settings.DATABASE_URL
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,  # Use our manually defined metadata
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using AsyncEngine."""
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("alembic")

    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an event loop
            if loop.is_running():
                # Create a new event loop in a separate thread
                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        lambda: asyncio.new_event_loop().run_until_complete(
                            run_migrations_online()
                        )
                    )
                    future.result()
            else:
                # Run in the existing loop
                loop.run_until_complete(run_migrations_online())
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(run_migrations_online())
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise
