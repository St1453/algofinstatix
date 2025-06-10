"""Script to list all tables in the database."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

from src.core.config import get_settings

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def list_database_tables():
    """List all tables in the database."""
    settings = get_settings()

    # Create database URL (use psycopg2 driver for synchronous operations)
    db_url = settings.DATABASE_URL.replace("asyncpg", "psycopg2")

    print(
        f"Connecting to database: {db_url.replace(settings.POSTGRES_PASSWORD, '****')}"
    )

    try:
        # Create engine
        engine = create_engine(db_url, pool_pre_ping=True)

        # Create inspector
        inspector = inspect(engine)

        # Get all table names
        table_names = inspector.get_table_names()

        if not table_names:
            print("No tables found in the database.")
            return

        print("\nTables in the database:")
        print("-" * 50)
        for table_name in table_names:
            # Get columns for each table
            columns = inspector.get_columns(table_name)
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 7))
            for column in columns:
                print(f"  {column['name']}: {column['type']}")

        # Check for alembic_version table
        if "alembic_version" in table_names:
            print("\nAlembic version table exists.")

    except Exception as e:
        print(f"Error connecting to the database: {e}")
    finally:
        if "engine" in locals():
            engine.dispose()


if __name__ == "__main__":
    list_database_tables()
