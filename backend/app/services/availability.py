"""
Availability service: cache-aside pattern on top of Haversine DC lookup.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Inventory, Item
from app.models.schemas import AvailabilityResult
from app.services.cache import get_cached_quantity, set_cached_quantity
from app.services.nearby import find_nearby_dcs


async def check_availability(
    lat: float,
    lng: float,
    item_ids: list[int],
    radius_km: float,
    read_db: AsyncSession,
    redis,
) -> tuple[list[AvailabilityResult], str]:
    """
    Return availability results for `item_ids` within `radius_km` of (lat, lng).

    Cache behaviour:
    - HIT     — all quantities came from Redis
    - MISS    — all quantities came from PostgreSQL (cache populated after)
    - PARTIAL — mix of cache hits and misses
    """
    nearby_dcs = await find_nearby_dcs(read_db, lat, lng, radius_km)
    if not nearby_dcs:
        return [], "MISS"

    # Batch-fetch all requested item metadata (active only)
    items_result = await read_db.execute(
        select(Item).where(Item.id.in_(item_ids), Item.is_active == True)
    )
    items_map: dict[int, Item] = {item.id: item for item in items_result.scalars().all()}

    results: list[AvailabilityResult] = []
    cache_hits = 0
    cache_misses = 0

    for entry in nearby_dcs:
        dc = entry["dc"]
        for item_id in item_ids:
            if item_id not in items_map:
                continue

            qty, hit = await get_cached_quantity(redis, dc.id, item_id)
            if hit:
                cache_hits += 1
            else:
                cache_misses += 1
                inv_result = await read_db.execute(
                    select(Inventory.quantity).where(
                        Inventory.dc_id == dc.id,
                        Inventory.item_id == item_id,
                    )
                )
                qty = inv_result.scalar_one_or_none() or 0
                # Populate cache for next read
                await set_cached_quantity(redis, dc.id, item_id, qty)

            if qty is not None and qty > 0:
                item = items_map[item_id]
                results.append(
                    AvailabilityResult(
                        dc_id=dc.id,
                        dc_name=dc.name,
                        region_id=dc.region_id,
                        item_id=item_id,
                        item_name=item.name,
                        quantity=qty,
                        travel_minutes=entry["travel_minutes"],
                        distance_km=entry["distance_km"],
                        can_deliver_in_1h=entry["can_deliver"],
                    )
                )

    total = cache_hits + cache_misses
    if total == 0:
        cache_status = "MISS"
    elif cache_misses == 0:
        cache_status = "HIT"
    elif cache_hits == 0:
        cache_status = "MISS"
    else:
        cache_status = "PARTIAL"

    return results, cache_status
