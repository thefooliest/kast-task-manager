from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.core.config import settings

# Async engine — chosen to avoid blocking the FastAPI event loop on DB I/O.
# See SOLUTION.md for the full rationale.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections are alive before using them
    pool_recycle=300,     # Recycle connections after 5 min to avoid stale handles
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields a DB session per request, ensuring cleanup on exit."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()