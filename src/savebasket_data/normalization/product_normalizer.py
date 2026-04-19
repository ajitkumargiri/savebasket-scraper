"""Shared product normalization into the store import contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Mapping

from ..contracts.store_price_import import StorePriceImportPayload, StorePriceRecord
from .category_mapper import map_source_category, map_source_category_group
from .name_cleaner import clean_product_name
from .price_parser import parse_price
from .quantity_parser import parse_quantity

StoreSourceType = Literal["scraper", "saved_html"]

_STORE_ALIASES = {
    "aldi": "ALDI",
    "jumbo": "Jumbo",
    "vomar": "Vomar",
    "ah": "Albert Heijn",
    "albert heijn": "Albert Heijn",
}


@dataclass(slots=True)
class RawStoreProduct:
    """Minimal raw product input needed for normalization."""

    store: str
    original_name: str
    price: str | int | float | None
    captured_at: datetime
    source_id: str | None = None
    category_group: str | None = None
    category: str | None = None
    brand: str | None = None
    quantity_text: str | None = None
    product_url: str | None = None
    image_url: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> 'RawStoreProduct':
        """Build a raw product from JSON-compatible data."""
        captured_at = _parse_captured_at(payload.get('captured_at'))
        return cls(
            store=str(payload['store']),
            original_name=str(payload['original_name']),
            price=payload.get('price'),
            captured_at=captured_at,
            source_id=_optional_string(payload.get('source_id')),
            category_group=_optional_string(
                payload.get('category_group') or payload.get('group')
            ),
            category=_optional_string(payload.get('category')),
            brand=_optional_string(payload.get('brand')),
            quantity_text=_optional_string(payload.get('quantity_text') or payload.get('quantity')),
            product_url=_optional_string(payload.get('product_url')),
            image_url=_optional_string(payload.get('image_url')),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the raw product for debug and demo output."""
        return {
            'store': self.store,
            'source_id': self.source_id,
            'original_name': self.original_name,
            'price': self.price,
            'captured_at': self.captured_at.isoformat(),
            'category_group': self.category_group,
            'category': self.category,
            'brand': self.brand,
            'quantity_text': self.quantity_text,
            'product_url': self.product_url,
            'image_url': self.image_url,
        }


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _parse_captured_at(value: object) -> datetime:
    if isinstance(value, datetime):
        captured_at = value
    elif isinstance(value, str):
        captured_at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        raise ValueError('captured_at must be an ISO-8601 string or datetime')

    if captured_at.tzinfo is None:
        return captured_at.replace(tzinfo=timezone.utc)
    return captured_at


def normalize_store_name(value: str) -> str | None:
    """Normalize a store identifier into the contract store name."""
    return _STORE_ALIASES.get(value.strip().lower())


def normalize_store_product(product: RawStoreProduct) -> StorePriceRecord | None:
    """Normalize one raw store product into the shared contract shape."""
    store_name = normalize_store_name(product.store)
    normalized_name = clean_product_name(product.original_name)
    price_amount = parse_price(product.price)

    if store_name is None or not normalized_name or price_amount is None:
        return None

    quantity_value, quantity_unit = parse_quantity(product.quantity_text or product.original_name)
    return StorePriceRecord(
        source_id=product.source_id,
        store=store_name,
        category_group=map_source_category_group(
            store_name,
            product.category_group,
            product.category,
        ),
        category=map_source_category(store_name, product.category),
        brand=product.brand.strip() if product.brand else None,
        original_name=product.original_name.strip(),
        normalized_name=normalized_name,
        price_amount=price_amount,
        quantity_value=quantity_value,
        quantity_unit=quantity_unit,
        product_url=product.product_url,
        image_url=product.image_url,
        captured_at=product.captured_at,
    )


def normalize_store_products(products: Iterable[RawStoreProduct]) -> list[StorePriceRecord]:
    """Normalize many raw products, skipping records that cannot be validated."""
    normalized_records: list[StorePriceRecord] = []
    for product in products:
        normalized_record = normalize_store_product(product)
        if normalized_record is not None:
            normalized_records.append(normalized_record)
    return normalized_records


def build_store_price_import_payload(
    products: Iterable[RawStoreProduct],
    import_id: str,
    source_artifact_path: str,
    imported_at: datetime | None = None,
    source_type: StoreSourceType = 'scraper',
) -> StorePriceImportPayload | None:
    """Build a validated store payload from raw products for one store."""
    normalized_records = normalize_store_products(products)
    if not normalized_records:
        return None

    store_name = normalized_records[0].store
    if any(record.store != store_name for record in normalized_records[1:]):
        raise ValueError(
            'build_store_price_import_payload requires products from exactly one store'
        )

    return StorePriceImportPayload(
        import_id=import_id,
        store=store_name,
        imported_at=imported_at or datetime.now(timezone.utc),
        source_type=source_type,
        source_artifact_path=source_artifact_path,
        records=normalized_records,
    )
