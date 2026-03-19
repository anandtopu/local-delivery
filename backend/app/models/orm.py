import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DistributionCenter(Base):
    __tablename__ = "distribution_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Double, nullable=False, index=True)
    lng: Mapped[float] = mapped_column(Double, nullable=False, index=True)
    zipcode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    region_id: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )

    inventories: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="dc")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="dc")

    __table_args__ = (
        Index("ix_dc_region_active", "region_id", "is_active"),
        Index("ix_dc_lat_lng", "lat", "lng"),
    )


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_grams: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )

    inventories: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="item")


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    dc_id: Mapped[int] = mapped_column(ForeignKey("distribution_centers.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa_func.now(),
        onupdate=sa_func.now(),
    )

    dc: Mapped["DistributionCenter"] = relationship(
        "DistributionCenter", back_populates="inventories"
    )
    item: Mapped["Item"] = relationship("Item", back_populates="inventories")

    __table_args__ = (
        UniqueConstraint("dc_id", "item_id", name="uq_inventory_dc_item"),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonneg"),
        Index("ix_inventory_dc_item_qty", "dc_id", "item_id", "quantity"),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dc_id: Mapped[int] = mapped_column(ForeignKey("distribution_centers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED", server_default="CONFIRMED")
    total_price_cents: Mapped[int] = mapped_column(Integer, default=0)
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    dc: Mapped["DistributionCenter"] = relationship("DistributionCenter", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_dc_placed", "dc_id", "placed_at"),
        Index("ix_orders_customer_placed", "customer_id", "placed_at"),
        Index("ix_orders_placed", "placed_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE")
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    item: Mapped["Item"] = relationship("Item")

    __table_args__ = (Index("ix_order_items_order_item", "order_id", "item_id"),)
