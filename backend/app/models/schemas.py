import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Distribution Center ───────────────────────────────────────────────────────

class DCBase(BaseModel):
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    zipcode: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool = True


class DCCreate(DCBase):
    pass


class DCResponse(DCBase):
    id: int
    region_id: str
    created_at: datetime
    inventory_count: int = 0

    model_config = {"from_attributes": True}


# ── Item ──────────────────────────────────────────────────────────────────────

class ItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: str
    unit_price_cents: int = Field(..., ge=0)
    weight_grams: Optional[int] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Inventory ─────────────────────────────────────────────────────────────────

class InventoryResponse(BaseModel):
    id: int
    dc_id: int
    item_id: int
    quantity: int
    reorder_threshold: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemRequest(BaseModel):
    item_id: int
    quantity: int = Field(..., ge=1)


class PlaceOrderRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=100)
    dc_id: int
    items: list[OrderItemRequest] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    unit_price_cents: int

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    customer_id: str
    dc_id: int
    status: str
    total_price_cents: int
    placed_at: datetime
    delivered_at: Optional[datetime] = None
    order_items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


# ── Availability ──────────────────────────────────────────────────────────────

class AvailabilityResult(BaseModel):
    dc_id: int
    dc_name: str
    region_id: str
    item_id: int
    item_name: str
    quantity: int
    travel_minutes: float
    distance_km: float
    can_deliver_in_1h: bool


class AvailabilityResponse(BaseModel):
    results: list[AvailabilityResult]
    query_lat: float
    query_lng: float
    cache_status: str  # HIT | MISS | PARTIAL
    response_ms: float


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    postgres: str
    redis: str


# ── Admin / Stats ─────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_dcs: int
    total_items: int
    total_orders: int
    orders_today: int
    active_regions: int
