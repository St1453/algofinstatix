"""Setup database: initialize and seed with test data."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.init_db import init_database
from scripts.seed_db import main as seed_database


async def setup_database() -> None:
    """Initialize and seed the database."""
    print("=== Setting up database ===")
    
    # Initialize database and run migrations
    await init_database()
    
    # Seed with test data
    await seed_database()
    
    print("=== Database setup complete ===")


if __name__ == "__main__":
    asyncio.run(setup_database())
