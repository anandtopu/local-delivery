import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.postgres import get_read_db, get_write_db
from app.db.redis_client import get_redis
from app.main import app
from app.models.orm import Base

# ── Use an in-memory SQLite DB for tests ──────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis():
    """A mock Redis client with async get/set/setex/delete/keys/ping."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.keys = AsyncMock(return_value=[])
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with overridden DB and Redis dependencies."""

    async def override_write_db():
        yield db_session

    async def override_read_db():
        yield db_session

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_write_db] = override_write_db
    app.dependency_overrides[get_read_db] = override_read_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
