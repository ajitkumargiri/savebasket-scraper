"""Contract for Albert Heijn saved HTML imports."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AhProductRecord(BaseModel):
    """One normalized product extracted from a saved AH HTML file."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_id: str | None = None
    category: str | None = None
    original_name: str = Field(min_length=1)
    normalized_name: str = Field(min_length=1)
    price_amount: float | None = Field(default=None, ge=0)
    quantity_value: float | None = Field(default=None, gt=0)
    quantity_unit: str | None = None
    product_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    captured_at: datetime


class AhImportPayload(BaseModel):
    """Batch payload for AH imports derived from saved HTML."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    import_id: str = Field(min_length=1)
    imported_at: datetime
    source_html_path: str = Field(min_length=1)
    html_captured_at: datetime
    records: list[AhProductRecord] = Field(min_length=1)
