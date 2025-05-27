import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables from .env.test
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env.test"))

# Get database credentials from environment variables
DB_HOST = os.getenv("POSTGRES_SERVER")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")

# Create database URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


async def clean_database():
    engine = create_async_engine(DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
                )
            )
            print("✅ Database cleaned successfully!")
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(clean_database())
