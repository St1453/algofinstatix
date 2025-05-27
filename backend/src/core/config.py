"""Application configuration settings."""

import os
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    TESTING: bool = os.getenv("TESTING", "False").lower() in ("true", "1", "t")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # Log file paths
    LOG_APP: str = f"{LOG_DIR}/app/app.log"
    LOG_DEBUG: str = f"{LOG_DIR}/app/debug.log"
    LOG_ERROR: str = f"{LOG_DIR}/app/error.log"
    LOG_ACCESS: str = f"{LOG_DIR}/access/access.log"
    LOG_ACCESS_ERROR: str = f"{LOG_DIR}/access/errors.log"
    LOG_DB_OPERATIONS: str = f"{LOG_DIR}/database/operations.log"
    LOG_DB_SLOW: str = f"{LOG_DIR}/database/slow_queries.log"
    LOG_DB_ERROR: str = f"{LOG_DIR}/database/errors.log"
    LOG_AUDIT: str = f"{LOG_DIR}/audit/security.log"

    # Log rotation
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT: int = 5
    LOG_ENCODING: str = "utf-8"

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info):
        """Assemble the database connection string."""
        if isinstance(v, str):
            return v

        values = info.data
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT")
        db_name = values.get("POSTGRES_DB")

        if not all([user, password, host, port, db_name]):
            return None

        # URL encode the password
        from urllib.parse import quote_plus

        encoded_password = quote_plus(password)

        # Build the database URL as a string
        db_url = (
            f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{db_name}"
        )
        return db_url

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    REFRESH_SECRET_KEY: str = os.getenv(
        "REFRESH_SECRET_KEY", "your-refresh-secret-key-here"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Environment
    ENV: str = os.getenv("ENV", "development")

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        """Pydantic config."""

        case_sensitive = True
        env_file = ".env"


# Global settings instance
_settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return _settings
