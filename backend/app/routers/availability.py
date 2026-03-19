import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_read_db
from app.db.redis_client import get_redis
from app.models.schemas import AvailabilityResponse
from app.services import availability as availability_service

router = APIRouter()


@router.get("", response_model=AvailabilityResponse)
async def check_availability(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of the delivery address"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of the delivery address"),
    item_ids: str = Query(..., description="Comma-separated item IDs, e.g. 1,2,3"),
    radius_km: float = Query(15.0, ge=1, le=100, description="Search radius in kilometres"),
    read_db: AsyncSession = Depends(get_read_db),
    redis=Depends(get_redis),
):
    """
    Check item availability at distribution centres within `radius_km` of the given coordinates.

    - Uses **Haversine** formula for accurate great-circle distance.
    - Results come from a Redis cache-aside (TTL 60 s); `cache_status` reflects HIT/MISS/PARTIAL.
    - Only DCs that can deliver within 60 minutes (assuming 40 km/h avg speed) are flagged.
    """
    start = time.monotonic()
    ids = [int(x.strip()) for x in item_ids.split(",") if x.strip()]
    results, cache_status = await availability_service.check_availability(
        lat=lat,
        lng=lng,
        item_ids=ids,
        radius_km=radius_km,
        read_db=read_db,
        redis=redis,
    )
    ms = round((time.monotonic() - start) * 1000, 2)
    return AvailabilityResponse(
        results=results,
        query_lat=lat,
        query_lng=lng,
        cache_status=cache_status,
        response_ms=ms,
    )
