"""
Tests for the order placement service.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.models.schemas import OrderItemRequest
from app.services.orders import InsufficientInventoryError, place_order


def _make_inventory(dc_id: int, item_id: int, quantity: int):
    inv = MagicMock()
    inv.dc_id = dc_id
    inv.item_id = item_id
    inv.quantity = quantity
    return inv


def _make_item(item_id: int, price_cents: int = 500):
    item = MagicMock()
    item.id = item_id
    item.unit_price_cents = price_cents
    return item


def _make_order(dc_id: int, customer_id: str, total: int):
    order = MagicMock()
    order.id = uuid.uuid4()
    order.customer_id = customer_id
    order.dc_id = dc_id
    order.status = "CONFIRMED"
    order.total_price_cents = total
    order.order_items = []
    return order


class TestPlaceOrder:
    @pytest.mark.asyncio
    async def test_successful_order(self):
        inv = _make_inventory(dc_id=1, item_id=10, quantity=50)
        item = _make_item(item_id=10, price_cents=299)
        order = _make_order(dc_id=1, customer_id="cust-1", total=299 * 2)

        write_db = MagicMock()
        write_db.execute = AsyncMock()
        write_db.add = MagicMock()
        write_db.flush = AsyncMock()
        write_db.commit = AsyncMock()
        write_db.refresh = AsyncMock()

        # execute calls: SET TRANSACTION, SELECT FOR UPDATE, SELECT items, UPDATE inventory
        inv_result = MagicMock()
        inv_result.scalar_one_or_none.return_value = inv

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]

        execute_results = [
            MagicMock(),   # SET TRANSACTION ISOLATION LEVEL
            inv_result,    # SELECT FOR UPDATE
            items_result,  # SELECT items
            MagicMock(),   # UPDATE inventory
        ]
        write_db.execute = AsyncMock(side_effect=execute_results)

        redis = MagicMock()
        redis.delete = AsyncMock()

        with patch("app.services.orders.invalidate_dc_item", AsyncMock()):
            result = await place_order(
                write_db=write_db,
                redis=redis,
                customer_id="cust-1",
                dc_id=1,
                items=[OrderItemRequest(item_id=10, quantity=2)],
            )

        write_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_insufficient_inventory_raises_error(self):
        inv = _make_inventory(dc_id=1, item_id=10, quantity=1)  # only 1 available

        write_db = MagicMock()
        execute_results = [
            MagicMock(),   # SET TRANSACTION
            MagicMock(scalar_one_or_none=MagicMock(return_value=inv)),  # SELECT FOR UPDATE
        ]
        write_db.execute = AsyncMock(side_effect=execute_results)
        write_db.add = MagicMock()
        write_db.flush = AsyncMock()
        write_db.commit = AsyncMock()

        redis = MagicMock()

        with pytest.raises(InsufficientInventoryError) as exc_info:
            await place_order(
                write_db=write_db,
                redis=redis,
                customer_id="cust-1",
                dc_id=1,
                items=[OrderItemRequest(item_id=10, quantity=5)],  # requesting 5, have 1
            )

        err = exc_info.value
        assert err.item_id == 10
        assert err.available == 1
        assert err.requested == 5
        # No commit should have happened
        write_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_inventory_row_raises_error(self):
        """If inventory row doesn't exist at all, should raise InsufficientInventoryError."""
        write_db = MagicMock()
        execute_results = [
            MagicMock(),  # SET TRANSACTION
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # no row
        ]
        write_db.execute = AsyncMock(side_effect=execute_results)
        write_db.commit = AsyncMock()

        redis = MagicMock()

        with pytest.raises(InsufficientInventoryError) as exc_info:
            await place_order(
                write_db=write_db,
                redis=redis,
                customer_id="cust-1",
                dc_id=1,
                items=[OrderItemRequest(item_id=99, quantity=1)],
            )

        assert exc_info.value.available == 0
        write_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_invalidation_called_after_commit(self):
        inv = _make_inventory(dc_id=1, item_id=10, quantity=100)
        item = _make_item(item_id=10, price_cents=100)

        write_db = MagicMock()
        execute_results = [
            MagicMock(),
            MagicMock(scalar_one_or_none=MagicMock(return_value=inv)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[item])))),
            MagicMock(),
        ]
        write_db.execute = AsyncMock(side_effect=execute_results)
        write_db.add = MagicMock()
        write_db.flush = AsyncMock()
        write_db.commit = AsyncMock()
        write_db.refresh = AsyncMock()

        redis = MagicMock()
        invalidate_mock = AsyncMock()

        with patch("app.services.orders.invalidate_dc_item", invalidate_mock):
            await place_order(
                write_db=write_db,
                redis=redis,
                customer_id="cust-1",
                dc_id=1,
                items=[OrderItemRequest(item_id=10, quantity=1)],
            )

        invalidate_mock.assert_awaited_once_with(redis, 1, 10)

    @pytest.mark.asyncio
    async def test_cache_invalidation_failure_does_not_fail_order(self):
        """
        Even if Redis is down after commit, the order should succeed.
        """
        inv = _make_inventory(dc_id=1, item_id=10, quantity=100)
        item = _make_item(item_id=10, price_cents=100)

        write_db = MagicMock()
        execute_results = [
            MagicMock(),
            MagicMock(scalar_one_or_none=MagicMock(return_value=inv)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[item])))),
            MagicMock(),
        ]
        write_db.execute = AsyncMock(side_effect=execute_results)
        write_db.add = MagicMock()
        write_db.flush = AsyncMock()
        write_db.commit = AsyncMock()
        write_db.refresh = AsyncMock()

        redis = MagicMock()

        async def failing_invalidate(*args, **kwargs):
            raise ConnectionError("Redis unavailable")

        with patch("app.services.orders.invalidate_dc_item", failing_invalidate):
            # Should NOT raise despite cache failure
            await place_order(
                write_db=write_db,
                redis=redis,
                customer_id="cust-1",
                dc_id=1,
                items=[OrderItemRequest(item_id=10, quantity=1)],
            )

        write_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_insufficient_inventory_error_message(self):
        err = InsufficientInventoryError(item_id=42, available=3, requested=10)
        assert "42" in str(err)
        assert "3" in str(err)
        assert "10" in str(err)
        assert err.item_id == 42
        assert err.available == 3
        assert err.requested == 10
