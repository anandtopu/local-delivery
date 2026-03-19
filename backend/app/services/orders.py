"""
Order placement service.

Uses SERIALIZABLE isolation level to prevent overselling under concurrent load:
  1. SET TRANSACTION ISOLATION LEVEL SERIALIZABLE
  2. SELECT ... FOR UPDATE on each inventory row (pessimistic lock)
  3. Validate quantity >= requested
  4. INSERT order + order_items
  5. UPDATE inventory (decrement)
  6. COMMIT
  7. (best-effort) invalidate Redis cache keys
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Inventory, Item, Order, OrderItem
from app.models.schemas import OrderItemRequest
from app.services.cache import invalidate_dc_item


class InsufficientInventoryError(Exception):
    def __init__(self, item_id: int, available: int, requested: int) -> None:
        self.item_id = item_id
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient inventory for item {item_id}: "
            f"have {available}, need {requested}"
        )


async def place_order(
    write_db: AsyncSession,
    redis,
    customer_id: str,
    dc_id: int,
    items: list[OrderItemRequest],
) -> Order:
    """
    Place an order atomically.

    Raises:
        InsufficientInventoryError — if any item lacks sufficient stock.
        asyncpg.exceptions.SerializationFailureError — let the caller handle.
    """
    from sqlalchemy import text

    await write_db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

    # ── Phase 1: Lock all inventory rows ─────────────────────────────────────
    locked_inventories: dict[int, Inventory] = {}
    for item_req in items:
        result = await write_db.execute(
            select(Inventory)
            .where(Inventory.dc_id == dc_id, Inventory.item_id == item_req.item_id)
            .with_for_update()
        )
        inv = result.scalar_one_or_none()
        if inv is None or inv.quantity < item_req.quantity:
            raise InsufficientInventoryError(
                item_req.item_id,
                inv.quantity if inv else 0,
                item_req.quantity,
            )
        locked_inventories[item_req.item_id] = inv

    # ── Phase 2: Fetch item prices ────────────────────────────────────────────
    item_ids = [r.item_id for r in items]
    items_result = await write_db.execute(select(Item).where(Item.id.in_(item_ids)))
    items_map: dict[int, Item] = {item.id: item for item in items_result.scalars().all()}

    # ── Phase 3: Compute total price ─────────────────────────────────────────
    total_price = 0
    for item_req in items:
        item = items_map.get(item_req.item_id)
        if item:
            total_price += item.unit_price_cents * item_req.quantity

    # ── Phase 4: Create order ─────────────────────────────────────────────────
    order = Order(
        customer_id=customer_id,
        dc_id=dc_id,
        status="CONFIRMED",
        total_price_cents=total_price,
    )
    write_db.add(order)
    await write_db.flush()  # Assign order.id without committing

    # ── Phase 5: Create order items + decrement inventory ────────────────────
    for item_req in items:
        item = items_map.get(item_req.item_id)
        write_db.add(
            OrderItem(
                order_id=order.id,
                item_id=item_req.item_id,
                quantity=item_req.quantity,
                unit_price_cents=item.unit_price_cents if item else 0,
            )
        )
        await write_db.execute(
            update(Inventory)
            .where(Inventory.dc_id == dc_id, Inventory.item_id == item_req.item_id)
            .values(quantity=Inventory.quantity - item_req.quantity)
        )

    await write_db.commit()
    await write_db.refresh(order)

    # ── Phase 6: Invalidate cache (best effort) ───────────────────────────────
    try:
        for item_req in items:
            await invalidate_dc_item(redis, dc_id, item_req.item_id)
    except Exception:
        # Order is already committed; cache will expire via TTL
        pass

    return order
