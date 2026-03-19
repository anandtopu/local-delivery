"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── distribution_centers ─────────────────────────────────────────────────
    op.create_table(
        "distribution_centers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("lat", sa.Double(), nullable=False),
        sa.Column("lng", sa.Double(), nullable=False),
        sa.Column("zipcode", sa.String(10), nullable=False),
        sa.Column("region_id", sa.String(3), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dc_lat_lng", "distribution_centers", ["lat", "lng"])
    op.create_index("ix_dc_region_active", "distribution_centers", ["region_id", "is_active"])
    op.create_index(
        op.f("ix_distribution_centers_lat"), "distribution_centers", ["lat"]
    )
    op.create_index(
        op.f("ix_distribution_centers_lng"), "distribution_centers", ["lng"]
    )
    op.create_index(
        op.f("ix_distribution_centers_region_id"), "distribution_centers", ["region_id"]
    )
    op.create_index(
        op.f("ix_distribution_centers_zipcode"), "distribution_centers", ["zipcode"]
    )

    # ── items ────────────────────────────────────────────────────────────────
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("weight_grams", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index(op.f("ix_items_category"), "items", ["category"])

    # ── inventory ────────────────────────────────────────────────────────────
    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dc_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reorder_threshold", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonneg"),
        sa.ForeignKeyConstraint(["dc_id"], ["distribution_centers.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dc_id", "item_id", name="uq_inventory_dc_item"),
    )
    op.create_index(
        "ix_inventory_dc_item_qty", "inventory", ["dc_id", "item_id", "quantity"]
    )

    # ── orders ───────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", sa.String(100), nullable=False),
        sa.Column("dc_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="CONFIRMED", nullable=False),
        sa.Column("total_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "placed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dc_id"], ["distribution_centers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_dc_placed", "orders", ["dc_id", "placed_at"])
    op.create_index("ix_orders_customer_placed", "orders", ["customer_id", "placed_at"])
    op.create_index("ix_orders_placed", "orders", ["placed_at"])
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"])

    # ── order_items ───────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_order_items_order_item", "order_items", ["order_id", "item_id"]
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("inventory")
    op.drop_table("items")
    op.drop_table("distribution_centers")
