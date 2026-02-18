"""Database connection management and health checks."""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import text

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global engine and session maker
engine = None
async_session_maker = None


async def init_db() -> None:
    """Initialize database connection pool."""
    global engine, async_session_maker
    
    try:
        engine = create_async_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.debug
        )
        
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database connection pool initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connection pool."""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connection pool closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
    """
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_health() -> dict:
    """
    Check database connectivity and return health status.
    
    Returns:
        dict: Health status with database connection state
    """
    if async_session_maker is None:
        return {
            "status": "unhealthy",
            "database": "not_initialized",
            "error": "Database connection pool not initialized"
        }
    
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
