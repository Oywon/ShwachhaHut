from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.models import MarketObservation, ProductionCost, User
from app.security import hash_password


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        demo_accounts = [
            ("Farmer Demo", "+8801700000001", "farmer"),
            ("Buyer Demo", "+8801700000002", "buyer"),
            ("Moderator Demo", "+8801700000003", "moderator"),
            ("Authority Demo", "+8801700000004", "authority"),
            ("Admin Demo", "+8801700000005", "admin"),
        ]
        users: dict[str, User] = {}
        for name, phone, role in demo_accounts:
            user = db.scalar(select(User).where(User.phone == phone))
            if user is None:
                user = User(name=name, phone=phone, role=role, password_hash=hash_password("DemoOnly!234"))
                db.add(user)
                db.flush()
            users[role] = user

        config = db.scalar(
            select(ProductionCost).where(
                ProductionCost.crop == "onion",
                ProductionCost.district == "Faridpur",
                ProductionCost.upazila == "Faridpur Sadar",
            )
        )
        if config is None:
            db.add(
                ProductionCost(
                    crop="onion",
                    district="Faridpur",
                    upazila="Faridpur Sadar",
                    cost_per_kg=Decimal("35.00"),
                    margin_rate=Decimal("0.15"),
                    range_rate=Decimal("0.05"),
                    source_label="Simulated development example; not verified market or government data",
                    simulated=True,
                )
            )
            db.add_all(
                [
                    MarketObservation(
                        crop="onion",
                        district="Faridpur",
                        upazila="Faridpur Sadar",
                        market=market,
                        price_per_kg=Decimal(price),
                        source_label="Simulated development example",
                        simulated=True,
                        observed_at=datetime.now(timezone.utc),
                    )
                    for market, price in (("Faridpur Demo Market", "44.00"), ("Sadar Demo Market", "46.00"))
                ]
            )
        db.commit()


if __name__ == "__main__":
    seed()

