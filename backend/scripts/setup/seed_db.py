"""Database seeding script."""

import asyncio
import sys
from pathlib import Path

from passlib.context import CryptContext

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.shared.infrastructure.database.session import get_async_session  # noqa: E402
from src.users.infrastructure.models.user_orm import UserORM  # noqa: E402

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_users() -> None:
    """Seed the database with initial user data."""
    print("Seeding users...")
    
    # Get an async session
    async with get_async_session() as session:
        # Check if admin user already exists
        existing_admin = await session.execute(
            "SELECT 1 FROM users WHERE email = :email",
            {"email": "admin@example.com"}
        )
        
        if not existing_admin.scalar_one_or_none():
            # Create admin user
            admin_user = UserORM(
                email="admin@example.com",
                password=pwd_context.hash("admin123"),
                username="admin",
                first_name="Admin",
                last_name="User",
            )
            session.add(admin_user)
            print("Created admin user")
        
        # Check if test user already exists
        existing_test = await session.execute(
            "SELECT 1 FROM users WHERE email = :email",
            {"email": "test@example.com"}
        )
        
        if not existing_test.scalar_one_or_none():
            # Create test user
            test_user = UserORM(
                email="test@example.com",
                password=pwd_context.hash("test123"),
                username="testuser",
                first_name="Test",
                last_name="User",
            )
            session.add(test_user)
            print("Created test user")
        
        await session.commit()
    
    print("Database seeding completed")


async def main() -> None:
    """Run the database seeder."""
    print("Starting database seeding...")
    await seed_users()


if __name__ == "__main__":
    asyncio.run(main())
