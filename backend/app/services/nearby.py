import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import DistributionCenter

EARTH_RADIUS_KM = 6371.0
DELIVERY_SPEED_KM_H = 40.0
MAX_DELIVERY_MINUTES = 60.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance in kilometres between two points
    on the Earth using the Haversine formula.
    """
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + (
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def mock_travel_minutes(distance_km: float) -> float:
    """Estimate travel time assuming constant 40 km/h average speed."""
    return (distance_km / DELIVERY_SPEED_KM_H) * 60


async def find_nearby_dcs(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float = 15.0,
) -> list[dict]:
    """
    Find active distribution centres within `radius_km` of (lat, lng).

    Two-pass strategy:
    1. Bounding-box SQL pre-filter (avoids full table scan).
    2. Exact Haversine check on the remaining candidates.

    Returns a list of dicts sorted by ascending distance.
    """
    # 1 degree latitude ≈ 111 km (constant)
    # 1 degree longitude ≈ 111 * cos(lat) km  (varies by latitude)
    lat_offset = radius_km / 111.0
    lng_offset = radius_km / (111.0 * math.cos(math.radians(lat)) + 1e-9)

    result = await db.execute(
        select(DistributionCenter).where(
            DistributionCenter.is_active,
            DistributionCenter.lat.between(lat - lat_offset, lat + lat_offset),
            DistributionCenter.lng.between(lng - lng_offset, lng + lng_offset),
        )
    )
    candidates = result.scalars().all()

    nearby = []
    for dc in candidates:
        dist = haversine_km(lat, lng, dc.lat, dc.lng)
        if dist <= radius_km:
            travel = mock_travel_minutes(dist)
            nearby.append(
                {
                    "dc": dc,
                    "distance_km": round(dist, 2),
                    "travel_minutes": round(travel, 1),
                    "can_deliver": travel <= MAX_DELIVERY_MINUTES,
                }
            )

    return sorted(nearby, key=lambda x: x["distance_km"])
