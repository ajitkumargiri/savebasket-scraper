"""Contract for normalized store price imports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

StoreName = Literal["ALDI", "Jumbo", "Vomar", "Albert Heijn"]


class StorePriceRecord(BaseModel):
    """One normalized product price record from a store import."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_id: str | None = None
    store: StoreName
    category: str | None = None
    brand: str | None = None
    original_name: str = Field(min_length=1)
    normalized_name: str = Field(min_length=1)
    price_amount: float = Field(ge=0)
    quantity_value: float | None = Field(default=None, gt=0)
    quantity_unit: str | None = None
    product_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    captured_at: datetime


class StorePriceImportPayload(BaseModel):
    """Batch payload delivered from repo 1 to repo 2 for a store import."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    import_id: str = Field(min_length=1)
    store: StoreName
    imported_at: datetime
    source_type: Literal["scraper", "saved_html"] = "scraper"
    source_artifact_path: str = Field(min_length=1)
    records: list[StorePriceRecord] = Field(min_length=1)
