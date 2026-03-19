"""
Tests for the Haversine geo-filtering logic.
"""
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.nearby import (
    EARTH_RADIUS_KM,
    find_nearby_dcs,
    haversine_km,
    mock_travel_minutes,
)


class TestHaversineKm:
    def test_same_point_returns_zero(self):
        assert haversine_km(34.0, -118.0, 34.0, -118.0) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_nyc_to_la(self):
        # NYC: 40.7128, -74.0060  |  LA: 34.0522, -118.2437
        # Expected ≈ 3940 km
        dist = haversine_km(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3900 < dist < 4000, f"Expected ~3940 km, got {dist}"

    def test_known_distance_london_to_paris(self):
        # London: 51.5074, -0.1278  |  Paris: 48.8566, 2.3522
        # Expected ≈ 341 km
        dist = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
        assert 330 < dist < 355, f"Expected ~341 km, got {dist}"

    def test_symmetry(self):
        d1 = haversine_km(10.0, 20.0, 30.0, 40.0)
        d2 = haversine_km(30.0, 40.0, 10.0, 20.0)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_north_pole_to_equator(self):
        # 90 degrees of arc ≈ π/2 * R ≈ 10_007 km
        dist = haversine_km(90.0, 0.0, 0.0, 0.0)
        expected = math.pi / 2 * EARTH_RADIUS_KM
        assert dist == pytest.approx(expected, rel=0.001)

    def test_short_distance_accuracy(self):
        # Two points ~1 km apart in NYC area
        dist = haversine_km(40.7128, -74.0060, 40.7218, -74.0060)
        assert 0.9 < dist < 1.1, f"Expected ~1 km, got {dist}"


class TestMockTravelMinutes:
    def test_zero_distance(self):
        assert mock_travel_minutes(0.0) == 0.0

    def test_40km_takes_60min(self):
        assert mock_travel_minutes(40.0) == 60.0

    def test_20km_takes_30min(self):
        assert mock_travel_minutes(20.0) == 30.0

    def test_10km_takes_15min(self):
        assert mock_travel_minutes(10.0) == pytest.approx(15.0)


class TestFindNearbyDCs:
    @pytest.mark.asyncio
    async def test_no_dcs_returns_empty(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await find_nearby_dcs(mock_db, lat=34.0, lng=-118.0, radius_km=15.0)
        assert result == []

    @pytest.mark.asyncio
    async def test_dc_within_radius_is_included(self):
        from app.models.orm import DistributionCenter

        dc = MagicMock(spec=DistributionCenter)
        dc.id = 1
        dc.lat = 34.0522  # ~0 km from query point
        dc.lng = -118.2437
        dc.is_active = True

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [dc]
        mock_db.execute = AsyncMock(return_value=mock_result)

        results = await find_nearby_dcs(mock_db, lat=34.0522, lng=-118.2437, radius_km=15.0)
        assert len(results) == 1
        assert results[0]["distance_km"] == pytest.approx(0.0, abs=0.1)
        assert results[0]["can_deliver"] is True

    @pytest.mark.asyncio
    async def test_dc_outside_radius_excluded(self):
        from app.models.orm import DistributionCenter

        # DC is in NYC, query is in LA — well beyond 15 km radius
        dc = MagicMock(spec=DistributionCenter)
        dc.id = 2
        dc.lat = 40.7128
        dc.lng = -74.0060
        dc.is_active = True

        mock_db = MagicMock()
        mock_result = MagicMock()
        # Bounding box filter would normally exclude this, but we simulate
        # it passing the bbox and then being excluded by haversine
        mock_result.scalars.return_value.all.return_value = [dc]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Query from the same NYC coords but tiny radius
        results = await find_nearby_dcs(mock_db, lat=40.7228, lng=-74.0060, radius_km=1.0)
        # DC at 40.7128 is ~1.12 km away — outside 1 km radius
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_results_sorted_by_distance(self):
        from app.models.orm import DistributionCenter

        dc_far = MagicMock(spec=DistributionCenter)
        dc_far.id = 1
        dc_far.lat = 34.0522 + 0.1  # ~11 km away
        dc_far.lng = -118.2437

        dc_near = MagicMock(spec=DistributionCenter)
        dc_near.id = 2
        dc_near.lat = 34.0522 + 0.01  # ~1.1 km away
        dc_near.lng = -118.2437

        mock_db = MagicMock()
        mock_result = MagicMock()
        # Return far DC first — results should be re-sorted
        mock_result.scalars.return_value.all.return_value = [dc_far, dc_near]
        mock_db.execute = AsyncMock(return_value=mock_result)

        results = await find_nearby_dcs(mock_db, lat=34.0522, lng=-118.2437, radius_km=15.0)
        assert len(results) == 2
        assert results[0]["dc"].id == dc_near.id
        assert results[1]["dc"].id == dc_far.id
