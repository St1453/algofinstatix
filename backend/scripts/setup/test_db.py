import asyncio
import os

import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env.test
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env.test"))

# Get database credentials from environment variables
DB_HOST = os.getenv("POSTGRES_SERVER")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")


async def test_connection():
    try:
        # Test connection to PostgreSQL server
        conn = await asyncpg.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres",  # Connect to default 'postgres' database first
        )
        print("✅ Successfully connected to PostgreSQL server!")

        # Check if the database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )

        if db_exists:
            print(f"✅ Database '{DB_NAME}' exists!")
        else:
            print(f"❌ Database '{DB_NAME}' does not exist!")
            create_db = input(
                f"Would you like to create the database '{DB_NAME}'? (y/n): "
            )
            if create_db.lower() == "y":
                await conn.execute(f"CREATE DATABASE {DB_NAME}")
                print(f"✅ Database '{DB_NAME}' created successfully!")
            else:
                print("Skipping database creation.")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if "conn" in locals():
            await conn.close()


if __name__ == "__main__":
    asyncio.run(test_connection())
