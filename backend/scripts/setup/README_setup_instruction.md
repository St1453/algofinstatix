# Database Management Scripts

This directory contains scripts for managing the database for the AlgoFinStatiX application.

## Setup

1. Ensure you have the following environment variables set in your `.env` file:
   ```
   POSTGRES_SERVER=localhost
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=algofinstatix
   POSTGRES_PORT=5432
   ```

2. Make sure you have PostgreSQL running and accessible with the provided credentials.

## Scripts

### `init_db.py`

Initializes the database and runs migrations.

```bash
python -m scripts.init_db
```

### `seed_db.py`

Seeds the database with initial test data.

```bash
python -m scripts.seed_db
```

### `setup_db.py`

Runs both database initialization and seeding in sequence.

```bash
python -m scripts.setup_db
```

### `test_db.py`

Tests the database connection and creates the database if it doesn't exist.

```bash
python -m scripts.test_db
```

### `clean_test_db.py`

Cleans the database by dropping all tables and creating a new schema.

```bash
python -m scripts.clean_test_db
```

## Usage

1. First, make sure your virtual environment is activated and all dependencies are installed.

2. Run the setup script to initialize and seed the database:
   ```bash
   python -m scripts.setup_db
   ```

3. The script will:
   - Create the database if it doesn't exist
   - Run all pending migrations
   - Seed the database with test users

## Test Users

After seeding, the following test users will be available:

- **Admin User**
  - Email: admin@example.com
  - Password: admin123
  - Username: admin

- **Test User**
  - Email: test@example.com
  - Password: test123
  - Username: testuser

## Notes

- All database operations are idempotent, so you can safely run the scripts multiple times.
- The scripts use environment variables for configuration, so make sure they are properly set.
- For production use, make sure to change the default passwords.
