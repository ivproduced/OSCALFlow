"""
Database Configuration and Connection Management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import structlog

from core.config import settings

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG_MODE,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def init_db():
    """Initialize database and create tables"""
    try:
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("database_initialized", message="Database tables created successfully")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("database_closed", message="Database connections closed")


async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
