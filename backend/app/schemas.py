from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=32)
    password: str = Field(min_length=10, max_length=128)
    role: Literal["farmer", "buyer"]


class LoginRequest(BaseModel):
    phone: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class BuyerOption(BaseModel):
    id: str
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SaleCreate(BaseModel):
    buyer_id: str
    crop: str = Field(default="onion", min_length=2, max_length=80)
    quantity_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    price_per_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    district: str = Field(min_length=2, max_length=80)
    upazila: str = Field(min_length=2, max_length=80)
    sale_date: date
    notes: str | None = Field(default=None, max_length=2000)


class SaleResponse(BaseModel):
    id: str
    farmer_id: str
    buyer_id: str
    crop: str
    quantity_kg: Decimal
    price_per_kg: Decimal
    district: str
    upazila: str
    sale_date: datetime
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConfirmationRequest(BaseModel):
    confirm: bool
    reason: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def dispute_requires_reason(cls, value: str | None, info):
        if info.data.get("confirm") is False and not (value and value.strip()):
            raise ValueError("A reason is required when disputing a transaction")
        return value


class DeclarationCreate(BaseModel):
    purpose: Literal["storage", "resale", "wholesale", "processing", "other"]
    storage_location: str = Field(min_length=2, max_length=160)
    expected_release_date: date


class MovementCreate(BaseModel):
    movement_type: Literal["release", "loss"]
    quantity_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    note: str | None = Field(default=None, max_length=1000)


class PriceRangeResponse(BaseModel):
    crop: str
    district: str
    upazila: str
    minimum: Decimal
    maximum: Decimal
    currency: str = "BDT"
    unit: str = "kg"
    methodology: str
    production_cost_per_kg: Decimal
    market_observations: list[dict]
    source_label: str
    simulated: bool
    updated_at: datetime

