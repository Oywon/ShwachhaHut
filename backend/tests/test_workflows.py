from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import Settings
from app.core.db import SessionLocal, normalize_database_url
from app.models import AuditEvent, InventoryLot, ProductionCost, SaleTransaction, User
from app.security import hash_password
from app.services.audit import verify_entity_chain


def register(client, name, phone, role):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "phone": phone, "password": "SecureDemo!123", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_farmer_buyer_confirmation_creates_declared_inventory(client):
    farmer = register(client, "Farmer A", "+8801700000101", "farmer")
    buyer = register(client, "Buyer A", "+8801700000102", "buyer")
    transaction = client.post(
        "/api/v1/transactions",
        headers=auth(farmer["access_token"]),
        json={
            "buyer_id": buyer["user"]["id"],
            "quantity_kg": "120.500",
            "price_per_kg": "45.00",
            "district": "Faridpur",
            "upazila": "Faridpur Sadar",
            "sale_date": date.today().isoformat(),
        },
    )
    assert transaction.status_code == 201, transaction.text
    transaction_id = transaction.json()["id"]

    confirmed = client.post(
        f"/api/v1/transactions/{transaction_id}/confirm",
        headers=auth(buyer["access_token"]),
        json={"confirm": True},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    lots = client.get("/api/v1/inventory/lots", headers=auth(buyer["access_token"]))
    assert len(lots.json()) == 1
    lot_id = lots.json()[0]["id"]
    declared = client.post(
        f"/api/v1/inventory/lots/{lot_id}/declaration",
        headers=auth(buyer["access_token"]),
        json={
            "purpose": "storage",
            "storage_location": "Demo warehouse",
            "expected_release_date": (date.today() + timedelta(days=14)).isoformat(),
        },
    )
    assert declared.status_code == 200

    movement = client.post(
        f"/api/v1/inventory/lots/{lot_id}/movements",
        headers=auth(buyer["access_token"]),
        json={"movement_type": "release", "quantity_kg": "20.500"},
    )
    assert movement.status_code == 200
    assert Decimal(movement.json()["remaining_quantity_kg"]) == Decimal("100.000")
    excessive_movement = client.post(
        f"/api/v1/inventory/lots/{lot_id}/movements",
        headers=auth(buyer["access_token"]),
        json={"movement_type": "release", "quantity_kg": "101"},
    )
    assert excessive_movement.status_code == 422

    history = client.get(f"/api/v1/inventory/lots/{lot_id}/history", headers=auth(buyer["access_token"]))
    assert history.status_code == 200
    assert history.json()["chain_valid"] is True


def test_only_assigned_buyer_can_confirm_and_unconfirmed_sale_never_creates_lot(client):
    farmer = register(client, "Farmer B", "+8801700000201", "farmer")
    buyer = register(client, "Buyer B", "+8801700000202", "buyer")
    other_buyer = register(client, "Buyer C", "+8801700000203", "buyer")
    transaction = client.post(
        "/api/v1/transactions",
        headers=auth(farmer["access_token"]),
        json={
            "buyer_id": buyer["user"]["id"],
            "quantity_kg": "50",
            "price_per_kg": "42",
            "district": "Faridpur",
            "upazila": "Boalmari",
            "sale_date": date.today().isoformat(),
        },
    ).json()
    denied = client.post(
        f"/api/v1/transactions/{transaction['id']}/confirm",
        headers=auth(other_buyer["access_token"]),
        json={"confirm": True},
    )
    assert denied.status_code == 403
    with SessionLocal() as db:
        assert db.scalar(select(InventoryLot)) is None
    buyer_options = client.get("/api/v1/buyers", headers=auth(farmer["access_token"]))
    assert buyer_options.status_code == 200
    assert all("phone" not in item for item in buyer_options.json())
    assert client.get("/api/v1/inventory/lots").status_code == 401


def test_dispute_requires_reason_and_does_not_create_lot(client):
    farmer = register(client, "Farmer D", "+8801700000301", "farmer")
    buyer = register(client, "Buyer D", "+8801700000302", "buyer")
    transaction = client.post(
        "/api/v1/transactions",
        headers=auth(farmer["access_token"]),
        json={
            "buyer_id": buyer["user"]["id"],
            "quantity_kg": "25",
            "price_per_kg": "41",
            "district": "Faridpur",
            "upazila": "Nagarkanda",
            "sale_date": date.today().isoformat(),
        },
    ).json()
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/confirm",
        headers=auth(buyer["access_token"]),
        json={"confirm": False, "reason": "Quantity differs"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "disputed"
    with SessionLocal() as db:
        assert db.scalar(select(InventoryLot)) is None


def test_price_range_labels_simulated_inputs(client):
    with SessionLocal() as db:
        db.add(
            ProductionCost(
                crop="onion",
                district="Faridpur",
                upazila="Sadar",
                cost_per_kg=Decimal("40.00"),
                margin_rate=Decimal("0.10"),
                range_rate=Decimal("0.05"),
                source_label="Simulated test inputs",
                simulated=True,
            )
        )
        db.commit()
    response = client.get("/api/v1/prices/fair-range?district=Faridpur&upazila=Sadar")
    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["minimum"]) == Decimal("41.80")
    assert Decimal(body["maximum"]) == Decimal("46.20")
    assert body["simulated"] is True


def test_audit_verification_detects_payload_tampering(client):
    user = register(client, "Farmer E", "+8801700000401", "farmer")
    with SessionLocal() as db:
        event = db.scalar(select(AuditEvent).where(AuditEvent.entity_type == "user", AuditEvent.entity_id == user["user"]["id"]))
        assert verify_entity_chain(db, "user", user["user"]["id"])
        event.payload_json = '{"role":"admin"}'
        db.commit()
        assert not verify_entity_chain(db, "user", user["user"]["id"])


def test_stale_pending_transaction_expires_without_creating_a_lot(client):
    farmer = register(client, "Farmer F", "+8801700000501", "farmer")
    buyer = register(client, "Buyer F", "+8801700000502", "buyer")
    transaction = client.post(
        "/api/v1/transactions",
        headers=auth(farmer["access_token"]),
        json={
            "buyer_id": buyer["user"]["id"],
            "quantity_kg": "30",
            "price_per_kg": "43",
            "district": "Faridpur",
            "upazila": "Sadar",
            "sale_date": date.today().isoformat(),
        },
    ).json()
    with SessionLocal() as db:
        stale = db.get(SaleTransaction, transaction["id"])
        stale.created_at = datetime.now(timezone.utc) - timedelta(hours=49)
        db.commit()

    response = client.get("/api/v1/transactions", headers=auth(farmer["access_token"]))
    assert response.status_code == 200
    assert response.json()[0]["status"] == "unconfirmed"
    with SessionLocal() as db:
        assert db.scalar(select(InventoryLot)) is None


def test_production_requires_an_explicit_signing_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(app_env="production", secret_key="")


def test_production_rejects_ephemeral_sqlite_database():
    with pytest.raises(ValidationError, match="persistent PostgreSQL"):
        Settings(
            app_env="production",
            secret_key="test-production-key-with-more-than-32-characters",
            database_url="sqlite:///./swachchhohat.db",
        )


def test_api_documentation_uses_public_api_prefix(client):
    docs = client.get("/api/docs")
    openapi = client.get("/api/openapi.json")
    assert docs.status_code == 200
    assert openapi.status_code == 200
    assert "/api/v1/health" in openapi.json()["paths"]


def test_postgres_urls_use_installed_psycopg_driver():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"

