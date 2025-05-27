"""Main FastAPI application module."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.shared.infrastructure.config import settings
from src.users.infrastructure.logging.database_logger import (
    log_slow_query,
    setup_database_logging,
)
from src.users.presentation import user_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    # Startup: Initialize database logging
    setup_database_logging(settings)

    # Set up SQLAlchemy event listeners
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.time())
        return statement, parameters

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        duration = time.time() - conn.info["query_start_time"].pop()
        log_slow_query(query=statement, duration=duration, parameters=parameters)

    yield
    # Shutdown: Cleanup code can go here
    pass


# Create FastAPI application with lifespan
app = FastAPI(
    title="AlgoFinStatix API",
    description="API for AlgoFinStatix financial analytics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    user_routes.router,
)


@app.get("/health", include_in_schema=False)
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: Status of the application
    """
    return {"status": "ok"}
