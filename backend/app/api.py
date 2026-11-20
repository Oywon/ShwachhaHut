from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    InventoryLot,
    MarketObservation,
    Notification,
    ProductionCost,
    SaleTransaction,
    StockMovement,
    User,
    new_id,
)
from app.schemas import (
    AuthResponse,
    BuyerOption,
    ConfirmationRequest,
    DeclarationCreate,
    LoginRequest,
    MovementCreate,
    PriceRangeResponse,
    RegisterRequest,
    SaleCreate,
    SaleResponse,
    UserResponse,
)
from app.security import create_access_token, current_user, hash_password, require_roles, verify_password
from app.services.audit import record_event, verify_entity_chain


router = APIRouter()


def _notify(db: Session, user_id: str, title: str, message: str) -> None:
    db.add(Notification(user_id=user_id, title=title, message=message))


def _expire_pending(db: Session, user: User) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    query = select(SaleTransaction).where(
        SaleTransaction.status == "pending",
        SaleTransaction.created_at <= cutoff,
    )
    if user.role == "farmer":
        query = query.where(SaleTransaction.farmer_id == user.id)
    elif user.role == "buyer":
        query = query.where(SaleTransaction.buyer_id == user.id)
    else:
        return
    for transaction in db.scalars(query).all():
        transaction.status = "unconfirmed"
        record_event(
            db,
            entity_type="transaction",
            entity_id=transaction.id,
            actor_id=None,
            event_type="expired_unconfirmed",
            payload={"status": "unconfirmed", "reason": "No buyer response within 48 hours"},
        )
        _notify(db, transaction.farmer_id, "Transaction unconfirmed", f"Sale {transaction.id} was not confirmed within 48 hours.")
        _notify(db, transaction.buyer_id, "Transaction response overdue", f"Sale {transaction.id} is now marked unconfirmed.")
    if db.dirty or db.new:
        db.commit()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.phone == payload.phone)):
        raise HTTPException(status_code=409, detail="A user with this phone number already exists")
    user = User(name=payload.name.strip(), phone=payload.phone.strip(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    record_event(
        db,
        entity_type="user",
        entity_id=user.id,
        actor_id=user.id,
        event_type="registered",
        payload={"role": user.role},
    )
    db.commit()
    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.phone == payload.phone.strip()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Phone number or password is incorrect")
    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


@router.get("/users/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@router.get("/buyers", response_model=list[BuyerOption])
def buyers(db: Session = Depends(get_db), _user: User = Depends(current_user)):
    return db.scalars(select(User).where(User.role == "buyer").order_by(User.name)).all()


@router.get("/prices/fair-range", response_model=PriceRangeResponse)
def fair_range(
    district: str = Query(min_length=2, max_length=80),
    upazila: str = Query(min_length=2, max_length=80),
    crop: str = Query(default="onion", min_length=2, max_length=80),
    db: Session = Depends(get_db),
):
    config = db.scalar(
        select(ProductionCost).where(
            ProductionCost.crop == crop,
            ProductionCost.district == district,
            ProductionCost.upazila == upazila,
        )
    )
    if config is None:
        raise HTTPException(status_code=404, detail="No price calculation inputs are available for this location")
    base = config.cost_per_kg * (Decimal("1") + config.margin_rate)
    minimum = (base * (Decimal("1") - config.range_rate)).quantize(Decimal("0.01"))
    maximum = (base * (Decimal("1") + config.range_rate)).quantize(Decimal("0.01"))
    observations = db.scalars(
        select(MarketObservation)
        .where(
            MarketObservation.crop == crop,
            MarketObservation.district == district,
            MarketObservation.upazila == upazila,
        )
        .order_by(MarketObservation.observed_at.desc())
        .limit(10)
    ).all()
    return PriceRangeResponse(
        crop=crop,
        district=district,
        upazila=upazila,
        minimum=minimum,
        maximum=maximum,
        production_cost_per_kg=config.cost_per_kg,
        methodology="Production cost × (1 + configured margin), with a configured symmetric range. This is guidance, not a validated or mandatory price.",
        market_observations=[
            {
                "market": item.market,
                "price_per_kg": item.price_per_kg,
                "source": item.source_label,
                "observed_at": item.observed_at,
                "simulated": item.simulated,
            }
            for item in observations
        ],
        source_label=config.source_label,
        simulated=config.simulated or any(item.simulated for item in observations),
        updated_at=config.updated_at,
    )


@router.post("/transactions", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("farmer")),
):
    buyer = db.get(User, payload.buyer_id)
    if buyer is None or buyer.role != "buyer":
        raise HTTPException(status_code=404, detail="Buyer account not found")
    transaction = SaleTransaction(
        farmer_id=user.id,
        buyer_id=buyer.id,
        crop=payload.crop.strip(),
        quantity_kg=payload.quantity_kg,
        price_per_kg=payload.price_per_kg,
        district=payload.district.strip(),
        upazila=payload.upazila.strip(),
        sale_date=datetime.combine(payload.sale_date, time.min, tzinfo=timezone.utc),
        notes=payload.notes,
        status="pending",
    )
    db.add(transaction)
    db.flush()
    record_event(
        db,
        entity_type="transaction",
        entity_id=transaction.id,
        actor_id=user.id,
        event_type="submitted",
        payload={
            "buyer_id": buyer.id,
            "crop": transaction.crop,
            "quantity_kg": str(transaction.quantity_kg),
            "price_per_kg": str(transaction.price_per_kg),
        },
    )
    _notify(db, buyer.id, "Sale confirmation requested", f"Farmer {user.name} submitted sale {transaction.id} for your review.")
    db.commit()
    return transaction


@router.get("/transactions", response_model=list[SaleResponse])
def list_transactions(db: Session = Depends(get_db), user: User = Depends(current_user)):
    _expire_pending(db, user)
    query = select(SaleTransaction)
    if user.role == "farmer":
        query = query.where(SaleTransaction.farmer_id == user.id)
    elif user.role == "buyer":
        query = query.where(SaleTransaction.buyer_id == user.id)
    elif user.role not in {"moderator", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return db.scalars(query.order_by(SaleTransaction.created_at.desc())).all()


@router.post("/transactions/{transaction_id}/confirm", response_model=SaleResponse)
def confirm_transaction(
    transaction_id: str,
    payload: ConfirmationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("buyer")),
):
    transaction = db.scalar(
        select(SaleTransaction).where(SaleTransaction.id == transaction_id).with_for_update()
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="This transaction belongs to another buyer")
    if transaction.status != "pending":
        raise HTTPException(status_code=409, detail=f"Transaction is already {transaction.status}")
    event_type = "buyer_confirmed" if payload.confirm else "buyer_disputed"
    transaction.status = "confirmed" if payload.confirm else "disputed"
    record_event(
        db,
        entity_type="transaction",
        entity_id=transaction.id,
        actor_id=user.id,
        event_type=event_type,
        payload={"reason": payload.reason, "status": transaction.status},
    )
    _notify(db, transaction.farmer_id, "Buyer response received", f"Buyer {user.name} {('confirmed' if payload.confirm else 'disputed')} sale {transaction.id}.")
    if payload.confirm:
        lot = InventoryLot(
            transaction_id=transaction.id,
            buyer_id=user.id,
            crop=transaction.crop,
            original_quantity_kg=transaction.quantity_kg,
            remaining_quantity_kg=transaction.quantity_kg,
        )
        db.add(lot)
        db.flush()
        record_event(
            db,
            entity_type="lot",
            entity_id=lot.id,
            actor_id=user.id,
            event_type="verified_lot_created",
            payload={"transaction_id": transaction.id, "quantity_kg": str(lot.original_quantity_kg)},
        )
    db.commit()
    return transaction


@router.get("/inventory/lots")
def list_lots(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(InventoryLot)
    if user.role == "buyer":
        query = query.where(InventoryLot.buyer_id == user.id)
    elif user.role not in {"moderator", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return db.scalars(query.order_by(InventoryLot.created_at.desc())).all()


@router.post("/inventory/lots/{lot_id}/declaration")
def declare_lot(
    lot_id: str,
    payload: DeclarationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("buyer")),
):
    lot = db.scalar(select(InventoryLot).where(InventoryLot.id == lot_id).with_for_update())
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="This lot belongs to another buyer")
    if lot.purpose is not None:
        raise HTTPException(status_code=409, detail="A declaration already exists; corrections must be recorded as new audit events")
    if payload.expected_release_date < date.today():
        raise HTTPException(status_code=422, detail="Expected release date cannot be in the past")
    lot.purpose = payload.purpose
    lot.storage_location = payload.storage_location.strip()
    lot.expected_release_date = datetime.combine(payload.expected_release_date, time.min, tzinfo=timezone.utc)
    record_event(
        db,
        entity_type="lot",
        entity_id=lot.id,
        actor_id=user.id,
        event_type="inventory_declared",
        payload={
            "purpose": lot.purpose,
            "storage_location": lot.storage_location,
            "expected_release_date": payload.expected_release_date.isoformat(),
        },
    )
    db.commit()
    return lot


@router.post("/inventory/lots/{lot_id}/movements")
def create_movement(
    lot_id: str,
    payload: MovementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("buyer")),
):
    lot = db.scalar(select(InventoryLot).where(InventoryLot.id == lot_id).with_for_update())
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="This lot belongs to another buyer")
    if lot.purpose is None:
        raise HTTPException(status_code=409, detail="Declare the lot before recording movements")
    if payload.quantity_kg > lot.remaining_quantity_kg:
        raise HTTPException(status_code=422, detail="Movement quantity exceeds remaining inventory")
    result = db.execute(
        update(InventoryLot)
        .where(
            InventoryLot.id == lot.id,
            InventoryLot.buyer_id == user.id,
            InventoryLot.purpose.is_not(None),
            InventoryLot.remaining_quantity_kg >= payload.quantity_kg,
        )
        .values(remaining_quantity_kg=InventoryLot.remaining_quantity_kg - payload.quantity_kg)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Inventory changed or is insufficient; reload and try again")
    db.refresh(lot)
    movement = StockMovement(
        lot_id=lot.id,
        actor_id=user.id,
        movement_type=payload.movement_type,
        quantity_kg=payload.quantity_kg,
        note=payload.note,
    )
    db.add(movement)
    db.flush()
    record_event(
        db,
        entity_type="lot",
        entity_id=lot.id,
        actor_id=user.id,
        event_type=f"stock_{payload.movement_type}",
        payload={"quantity_kg": str(payload.quantity_kg), "remaining_quantity_kg": str(lot.remaining_quantity_kg)},
    )
    db.commit()
    return {"movement": movement, "remaining_quantity_kg": lot.remaining_quantity_kg}


@router.get("/inventory/lots/{lot_id}/history")
def lot_history(
    lot_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    lot = db.get(InventoryLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if user.role == "buyer" and lot.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="This lot belongs to another buyer")
    if user.role not in {"buyer", "moderator", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    from app.models import AuditEvent

    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.entity_type == "lot", AuditEvent.entity_id == lot.id)
        .order_by(AuditEvent.occurred_at, AuditEvent.id)
    ).all()
    return {
        "events": events,
        "chain_valid": verify_entity_chain(db, "lot", lot.id),
    }


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)
    ).all()

