from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_read_db, get_write_db
from app.models.orm import Inventory, Item
from app.models.schemas import InventoryResponse, ItemCreate, ItemResponse

router = APIRouter()


@router.get("", response_model=list[ItemResponse])
async def list_items(
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    read_db: AsyncSession = Depends(get_read_db),
):
    """List items, optionally filtered by category."""
    stmt = select(Item).where(Item.is_active).offset(skip).limit(limit)
    if category:
        stmt = stmt.where(Item.category == category)
    result = await read_db.execute(stmt)
    return result.scalars().all()


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    read_db: AsyncSession = Depends(get_read_db),
):
    """Get a single item."""
    result = await read_db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/{item_id}/inventory", response_model=list[InventoryResponse])
async def get_item_inventory(
    item_id: int,
    read_db: AsyncSession = Depends(get_read_db),
):
    """Get inventory levels for an item across all DCs."""
    result = await read_db.execute(select(Inventory).where(Inventory.item_id == item_id))
    return result.scalars().all()


@router.post("", response_model=ItemResponse, status_code=201)
async def create_item(
    payload: ItemCreate,
    write_db: AsyncSession = Depends(get_write_db),
):
    """Create a new item."""
    item = Item(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        unit_price_cents=payload.unit_price_cents,
        weight_grams=payload.weight_grams,
        is_active=payload.is_active,
    )
    write_db.add(item)
    await write_db.flush()
    await write_db.refresh(item)
    return item
