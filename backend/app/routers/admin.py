import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_read_db, get_write_db
from app.db.redis_client import get_redis
from app.models.orm import DistributionCenter, Item, Order
from app.models.schemas import StatsResponse
from app.services.cache import flush_availability_cache

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/seed")
async def trigger_seed(write_db: AsyncSession = Depends(get_write_db)):
    """
    Trigger the data seed programmatically.
    Imports and runs the seed logic directly in the request context.
    """
    try:
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/seed_data.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        return {"status": "ok", "output": result.stdout[-1000:] if result.stdout else ""}
    except Exception as exc:
        logger.exception("seed failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cache/flush")
async def flush_cache(redis=Depends(get_redis)):
    """Flush all availability cache keys (avail:*) from Redis."""
    deleted = await flush_availability_cache(redis)
    return {"status": "ok", "keys_deleted": deleted}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(read_db: AsyncSession = Depends(get_read_db)):
    """Return aggregate counts from the database."""
    total_dcs_result = await read_db.execute(
        select(func.count(DistributionCenter.id)).where(DistributionCenter.is_active)
    )
    total_dcs = total_dcs_result.scalar_one() or 0

    total_items_result = await read_db.execute(
        select(func.count(Item.id)).where(Item.is_active)
    )
    total_items = total_items_result.scalar_one() or 0

    total_orders_result = await read_db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar_one() or 0

    orders_today_result = await read_db.execute(
        select(func.count(Order.id)).where(Order.placed_at >= text("CURRENT_DATE"))
    )
    orders_today = orders_today_result.scalar_one() or 0

    regions_result = await read_db.execute(
        select(func.count(func.distinct(DistributionCenter.region_id))).where(
            DistributionCenter.is_active
        )
    )
    active_regions = regions_result.scalar_one() or 0

    return StatsResponse(
        total_dcs=total_dcs,
        total_items=total_items,
        total_orders=total_orders,
        orders_today=orders_today,
        active_regions=active_regions,
    )
