from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import get_settings

settings = get_settings()

# Async engine for production-quality performance  
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory with proper async configuration
SessionFactory = sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions - proper async implementation"""
    session = SessionFactory()
    try:
        yield session
    finally:
        await session.close() 