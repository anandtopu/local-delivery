import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Called during application startup."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    assert _redis_client is not None
    await _redis_client.ping()
    logger.info("redis connected", url=settings.REDIS_URL)


async def close_redis() -> None:
    """Called during application shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    logger.info("redis connection closed")


def get_redis_client() -> aioredis.Redis:
    """Return the singleton Redis client (not a FastAPI dependency)."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialised — call init_redis() first")
    return _redis_client


async def get_redis():
    """FastAPI dependency — yields the Redis client."""
    yield get_redis_client()
