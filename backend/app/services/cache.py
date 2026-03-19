"""
Redis cache-aside helpers for inventory availability.

Key format: avail:dc:{dc_id}:item:{item_id}
TTL: 60 seconds (configurable via REDIS_AVAILABILITY_TTL)
"""

from app.core.config import get_settings

settings = get_settings()
AVAILABILITY_TTL: int = settings.REDIS_AVAILABILITY_TTL


def availability_key(dc_id: int, item_id: int) -> str:
    return f"avail:dc:{dc_id}:item:{item_id}"


async def get_cached_quantity(redis, dc_id: int, item_id: int) -> tuple[int | None, bool]:
    """
    Returns (quantity, cache_hit).
    If the key is absent in Redis, returns (None, False).
    """
    val = await redis.get(availability_key(dc_id, item_id))
    if val is None:
        return None, False
    return int(val), True


async def set_cached_quantity(redis, dc_id: int, item_id: int, qty: int) -> None:
    """Cache a quantity with the configured TTL."""
    await redis.setex(availability_key(dc_id, item_id), AVAILABILITY_TTL, qty)


async def invalidate_dc_item(redis, dc_id: int, item_id: int) -> None:
    """Remove the cached entry so the next read fetches from DB."""
    await redis.delete(availability_key(dc_id, item_id))


async def flush_availability_cache(redis) -> int:
    """Delete all avail:* keys. Returns the count of deleted keys."""
    keys = await redis.keys("avail:*")
    if keys:
        return int(await redis.delete(*keys))
    return 0
