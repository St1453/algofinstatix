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

    # Base URL for api requests
    BASE_URL: str = os.getenv("BASE_URL")

    # Base Templates Directory
    BASE_TEMPLATE_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # src/core
        "templating",
        "base_templates",
    )

    # SMTP
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: str = os.getenv("SMTP_PORT")
    SMTP_HOST_USER: str = os.getenv("SMTP_HOST_USER")
    SMTP_HOST_PASSWORD: str = os.getenv("SMTP_HOST_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "False").lower() in (
        "true",
        "1",
        "t",
    )
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "False").lower() in (
        "true",
        "1",
        "t",
    )

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info):
        """Assemble the database connection string."""
        # If DATABASE_URL is explicitly set, use it
        if isinstance(v, str) and v.strip() and "${" not in v:
            return v

        # Otherwise, construct from individual components
        values = info.data
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT")
        db_name = values.get("POSTGRES_DB")

        # Validate all required components are present
        if not all([user, password, host, port, db_name]):
            missing = [
                field
                for field, value in [
                    ("POSTGRES_USER", user),
                    ("POSTGRES_PASSWORD", password),
                    ("POSTGRES_SERVER", host),
                    ("POSTGRES_PORT", port),
                    ("POSTGRES_DB", db_name),
                ]
                if not value
            ]
            raise ValueError(
                f"Missing required database configuration: {', '.join(missing)}"
            )

        # URL encode the password
        from urllib.parse import quote_plus

        encoded_password = quote_plus(str(password))

        # Build the database URL as a string
        return f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{db_name}"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    REFRESH_SECRET_KEY: str = os.getenv(
        "REFRESH_SECRET_KEY", "your-refresh-secret-key-here"
    )
    ALGORITHM: str = "HS256"

    # Token expiration times in seconds
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 7 days in seconds
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 30  # 30 days in seconds

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

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
