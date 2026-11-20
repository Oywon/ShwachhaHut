from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ProductionCost(Base):
    __tablename__ = "production_costs"
    __table_args__ = (
        CheckConstraint("cost_per_kg > 0", name="ck_production_cost_positive"),
        CheckConstraint("margin_rate >= 0 AND margin_rate <= 1", name="ck_margin_rate_range"),
        CheckConstraint("range_rate >= 0 AND range_rate <= 1", name="ck_range_rate_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    crop: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80), index=True)
    upazila: Mapped[str] = mapped_column(String(80), index=True)
    cost_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    margin_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    range_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    source_label: Mapped[str] = mapped_column(String(160))
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketObservation(Base):
    __tablename__ = "market_observations"
    __table_args__ = (CheckConstraint("price_per_kg > 0", name="ck_market_price_positive"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    crop: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80), index=True)
    upazila: Mapped[str] = mapped_column(String(80), index=True)
    market: Mapped[str] = mapped_column(String(120))
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    source_label: Mapped[str] = mapped_column(String(160))
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class SaleTransaction(Base):
    __tablename__ = "sales_transactions"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="ck_transaction_quantity_positive"),
        CheckConstraint("price_per_kg > 0", name="ck_transaction_price_positive"),
        Index("ix_transaction_farmer_created", "farmer_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    crop: Mapped[str] = mapped_column(String(80))
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    district: Mapped[str] = mapped_column(String(80))
    upazila: Mapped[str] = mapped_column(String(80))
    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InventoryLot(Base):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        CheckConstraint("original_quantity_kg > 0", name="ck_lot_original_positive"),
        CheckConstraint("remaining_quantity_kg >= 0", name="ck_lot_remaining_nonnegative"),
        CheckConstraint("remaining_quantity_kg <= original_quantity_kg", name="ck_lot_remaining_max"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("sales_transactions.id"), unique=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    crop: Mapped[str] = mapped_column(String(80))
    original_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    remaining_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    purpose: Mapped[str | None] = mapped_column(String(40), nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    expected_release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="ck_movement_quantity_positive"),
        Index("ix_movement_lot_created", "lot_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lot_id: Mapped[str] = mapped_column(ForeignKey("inventory_lots.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    movement_type: Mapped[str] = mapped_column(String(20))
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_entity_time", "entity_type", "entity_id", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(36))
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80))
    occurred_at: Mapped[str] = mapped_column(String(40))
    payload_json: Mapped[str] = mapped_column(Text)
    previous_hash: Mapped[str] = mapped_column(String(64), default="")
    event_hash: Mapped[str] = mapped_column(String(64), unique=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

