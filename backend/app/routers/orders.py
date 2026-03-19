import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.postgres import get_read_db, get_write_db
from app.db.redis_client import get_redis
from app.models.orm import Order
from app.models.schemas import OrderResponse, PlaceOrderRequest
from app.services.orders import InsufficientInventoryError, place_order

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    payload: PlaceOrderRequest,
    write_db: AsyncSession = Depends(get_write_db),
    redis=Depends(get_redis),
):
    """
    Place an order using a **SERIALIZABLE** PostgreSQL transaction.

    - Locks inventory rows with `SELECT FOR UPDATE`
    - Checks quantities
    - Creates the order + order items
    - Decrements inventory
    - Invalidates Redis cache entries for affected (dc_id, item_id) pairs

    Returns HTTP 409 on insufficient inventory or serialization failure.
    """
    try:
        order = await place_order(
            write_db=write_db,
            redis=redis,
            customer_id=payload.customer_id,
            dc_id=payload.dc_id,
            items=payload.items,
        )
        return order
    except InsufficientInventoryError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "insufficient_inventory",
                "item_id": exc.item_id,
                "available": exc.available,
                "requested": exc.requested,
            },
        ) from exc
    except Exception as exc:
        # asyncpg raises this string in the exception message for serialization failures
        if "serializ" in str(exc).lower() or "40001" in str(exc):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "serialization_failure",
                    "message": "Transaction serialization failure, please retry",
                },
            ) from exc
        logger.exception("unexpected error placing order", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    read_db: AsyncSession = Depends(get_read_db),
):
    """List orders (paginated), newest first."""
    result = await read_db.execute(
        select(Order)
        .options(selectinload(Order.order_items))
        .order_by(Order.placed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    read_db: AsyncSession = Depends(get_read_db),
):
    """Retrieve a single order by UUID."""
    result = await read_db.execute(
        select(Order).options(selectinload(Order.order_items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
