"""Contract for validated manual offer imports."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

OfferType = Literal["fixed_price", "percentage_discount", "multi_buy"]
StoreName = Literal["ALDI", "Jumbo", "Vomar", "Albert Heijn"]


class OfferRecord(BaseModel):
    """One validated offer record from a manual JSON import."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    store: StoreName
    title: str = Field(min_length=1)
    offer_type: OfferType
    description: str = Field(min_length=1)
    valid_from: date
    valid_to: date
    normalized_name: str | None = None
    category: str | None = None
    fixed_price_amount: float | None = Field(default=None, ge=0)
    percentage_off: int | None = Field(default=None, gt=0, le=100)
    buy_quantity: int | None = Field(default=None, gt=0)
    pay_quantity: int | None = Field(default=None, gt=0)
    source_reference: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "OfferRecord":
        if self.valid_to < self.valid_from:
            raise ValueError("valid_to must be on or after valid_from")

        if self.offer_type == "fixed_price" and self.fixed_price_amount is None:
            raise ValueError("fixed_price_amount is required for fixed_price offers")
        if self.offer_type == "percentage_discount" and self.percentage_off is None:
            raise ValueError("percentage_off is required for percentage_discount offers")
        if self.offer_type == "multi_buy":
            if self.buy_quantity is None or self.pay_quantity is None:
                raise ValueError("buy_quantity and pay_quantity are required for multi_buy offers")
            if self.pay_quantity > self.buy_quantity:
                raise ValueError("pay_quantity cannot be greater than buy_quantity")

        return self


class OfferImportPayload(BaseModel):
    """Batch payload for validated manual offer imports."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    import_id: str = Field(min_length=1)
    imported_at: datetime
    valid_on: date
    source_artifact_path: str = Field(min_length=1)
    offers: list[OfferRecord] = Field(min_length=1)
