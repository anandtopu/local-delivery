"""
Tests for the availability cache-aside service.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.availability import check_availability


def _make_dc(dc_id: int, lat: float = 34.0522, lng: float = -118.2437):
    dc = MagicMock()
    dc.id = dc_id
    dc.name = f"DC-{dc_id}"
    dc.region_id = "900"
    dc.lat = lat
    dc.lng = lng
    return dc


def _make_item(item_id: int, name: str = "Chips", category: str = "snacks"):
    item = MagicMock()
    item.id = item_id
    item.name = name
    item.is_active = True
    return item


def _make_entry(dc, dist_km: float = 2.0, travel_min: float = 3.0):
    return {
        "dc": dc,
        "distance_km": dist_km,
        "travel_minutes": travel_min,
        "can_deliver": travel_min <= 60,
    }


class TestCheckAvailabilityCacheHit:
    @pytest.mark.asyncio
    async def test_full_cache_hit_returns_hit_status(self):
        dc = _make_dc(1)
        item = _make_item(1)

        read_db = MagicMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]
        read_db.execute = AsyncMock(return_value=items_result)

        redis = MagicMock()

        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc)]),
            ),
            patch(
                "app.services.availability.get_cached_quantity",
                AsyncMock(return_value=(50, True)),  # cache HIT
            ),
        ):
            results, status = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=15.0,
                read_db=read_db,
                redis=redis,
            )

        assert status == "HIT"
        assert len(results) == 1
        assert results[0].quantity == 50
        assert results[0].dc_id == 1

    @pytest.mark.asyncio
    async def test_full_cache_miss_queries_db_and_populates_cache(self):
        dc = _make_dc(1)
        item = _make_item(1)

        inv_result = MagicMock()
        inv_result.scalar_one_or_none.return_value = 100

        read_db = MagicMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]
        read_db.execute = AsyncMock(side_effect=[items_result, inv_result])

        set_cache = AsyncMock()
        redis = MagicMock()

        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc)]),
            ),
            patch(
                "app.services.availability.get_cached_quantity",
                AsyncMock(return_value=(None, False)),  # cache MISS
            ),
            patch("app.services.availability.set_cached_quantity", set_cache),
        ):
            results, status = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=15.0,
                read_db=read_db,
                redis=redis,
            )

        assert status == "MISS"
        assert len(results) == 1
        assert results[0].quantity == 100
        # Ensure cache was populated
        set_cache.assert_awaited_once_with(redis, 1, 1, 100)

    @pytest.mark.asyncio
    async def test_partial_cache_returns_partial_status(self):
        dc1 = _make_dc(1)
        dc2 = _make_dc(2)
        item = _make_item(1)

        inv_result = MagicMock()
        inv_result.scalar_one_or_none.return_value = 20

        read_db = MagicMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]
        read_db.execute = AsyncMock(side_effect=[items_result, inv_result])

        redis = MagicMock()
        hit_calls = [True, False]  # dc1 hits, dc2 misses

        call_count = 0

        async def mock_get_cached(r, dc_id, item_id):
            nonlocal call_count
            hit = hit_calls[call_count % len(hit_calls)]
            call_count += 1
            return (30, True) if hit else (None, False)

        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc1, 1.0, 1.5), _make_entry(dc2, 5.0, 7.5)]),
            ),
            patch("app.services.availability.get_cached_quantity", mock_get_cached),
            patch("app.services.availability.set_cached_quantity", AsyncMock()),
        ):
            results, status = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=15.0,
                read_db=read_db,
                redis=redis,
            )

        assert status == "PARTIAL"

    @pytest.mark.asyncio
    async def test_no_nearby_dcs_returns_empty(self):
        read_db = MagicMock()
        redis = MagicMock()

        with patch(
            "app.services.availability.find_nearby_dcs",
            AsyncMock(return_value=[]),
        ):
            results, status = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=15.0,
                read_db=read_db,
                redis=redis,
            )

        assert results == []
        assert status == "MISS"

    @pytest.mark.asyncio
    async def test_zero_quantity_items_excluded_from_results(self):
        dc = _make_dc(1)
        item = _make_item(1)

        read_db = MagicMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]
        read_db.execute = AsyncMock(return_value=items_result)

        redis = MagicMock()

        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc)]),
            ),
            patch(
                "app.services.availability.get_cached_quantity",
                AsyncMock(return_value=(0, True)),  # qty = 0
            ),
        ):
            results, status = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=15.0,
                read_db=read_db,
                redis=redis,
            )

        assert results == []

    @pytest.mark.asyncio
    async def test_can_deliver_in_1h_flag(self):
        dc = _make_dc(1)
        item = _make_item(1)

        read_db = MagicMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [item]
        read_db.execute = AsyncMock(return_value=items_result)

        redis = MagicMock()

        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc, dist_km=40.0, travel_min=60.0)]),
            ),
            patch(
                "app.services.availability.get_cached_quantity",
                AsyncMock(return_value=(10, True)),
            ),
        ):
            results, _ = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=50.0,
                read_db=read_db,
                redis=redis,
            )

        assert results[0].can_deliver_in_1h is True

        # Now test just over the boundary
        with (
            patch(
                "app.services.availability.find_nearby_dcs",
                AsyncMock(return_value=[_make_entry(dc, dist_km=41.0, travel_min=61.5)]),
            ),
            patch(
                "app.services.availability.get_cached_quantity",
                AsyncMock(return_value=(10, True)),
            ),
        ):
            results, _ = await check_availability(
                lat=34.0522,
                lng=-118.2437,
                item_ids=[1],
                radius_km=50.0,
                read_db=read_db,
                redis=redis,
            )

        assert results[0].can_deliver_in_1h is False
