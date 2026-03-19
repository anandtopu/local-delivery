import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# ── Write engine (primary) ────────────────────────────────────────────────────
write_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.APP_ENV == "dev",
)

# ── Read engine (replica — same host in dev) ──────────────────────────────────
read_engine = create_async_engine(
    settings.READ_DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False,
)

WriteSession = async_sessionmaker(write_engine, expire_on_commit=False, autoflush=False)
ReadSession = async_sessionmaker(read_engine, expire_on_commit=False, autoflush=False)


async def get_write_db():
    """FastAPI dependency — yields a write-capable session."""
    async with WriteSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_db():
    """FastAPI dependency — yields a read-only session (replica)."""
    async with ReadSession() as session:
        yield session


async def init_db() -> None:
    """Called during application startup to verify connectivity."""
    from sqlalchemy import text

    async with write_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("postgres write engine connected")

    async with read_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("postgres read engine connected")


async def close_db() -> None:
    """Called during application shutdown."""
    await write_engine.dispose()
    await read_engine.dispose()
    logger.info("postgres engines disposed")
