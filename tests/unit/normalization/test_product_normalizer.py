from datetime import datetime, timezone

import pytest

from savebasket_data.contracts.store_price_import import StorePriceImportPayload, StorePriceRecord
from savebasket_data.normalization.product_normalizer import (
    RawStoreProduct,
    build_store_price_import_payload,
    normalize_store_product,
)


def test_raw_store_product_from_mapping_parses_timestamp() -> None:
    product = RawStoreProduct.from_mapping(
        {
            'store': 'ah',
            'original_name': 'Campina Halfvolle Melk 1L',
            'price': '€1,89',
            'captured_at': '2026-04-19T12:00:00Z',
            'category_group': 'Zuivel, boter en eieren',
            'category': 'Verse zuivel',
            'quantity': '1 l',
        }
    )

    assert product.store == 'ah'
    assert product.category_group == 'Zuivel, boter en eieren'
    assert product.category == 'Verse zuivel'
    assert product.quantity_text == '1 l'
    assert product.captured_at.tzinfo is not None


def test_normalize_store_product_builds_store_price_record() -> None:
    captured_at = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)

    product = RawStoreProduct(
        store='ah',
        source_id='ah-1',
        original_name='Campina Halfvolle Melk 1L',
        price='€1,89',
        captured_at=captured_at,
        category_group='Zuivel, boter en eieren',
        category='Verse zuivel',
        brand=' Campina ',
        product_url='https://www.ah.nl/producten/product/wi123',
    )

    normalized = normalize_store_product(product)

    assert isinstance(normalized, StorePriceRecord)
    assert normalized.store == 'Albert Heijn'
    assert normalized.normalized_name == 'campina halfvolle melk 1 l'
    assert normalized.price_amount == 1.89
    assert normalized.quantity_value == 1
    assert normalized.quantity_unit == 'l'
    assert normalized.category_group == 'zuivel-boter-en-eieren'
    assert normalized.category == 'verse-zuivel'
    assert normalized.captured_at == captured_at


def test_normalize_store_product_prefers_explicit_quantity_text() -> None:
    captured_at = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)

    product = RawStoreProduct(
        store='Jumbo',
        original_name='Jumbo Volkorenbrood',
        price='2.49',
        captured_at=captured_at,
        category_group='Brood en gebak',
        category='Volkoren brood',
        quantity_text='800 g',
    )

    normalized = normalize_store_product(product)

    assert normalized is not None
    assert normalized.quantity_value == 800
    assert normalized.quantity_unit == 'g'
    assert normalized.category_group == 'brood-en-gebak'
    assert normalized.category == 'volkoren-brood'


def test_normalize_store_product_returns_none_for_invalid_price() -> None:
    captured_at = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)

    product = RawStoreProduct(
        store='ALDI',
        original_name='Campina Halfvolle Melk 1L',
        price='n/a',
        captured_at=captured_at,
    )

    assert normalize_store_product(product) is None


def test_build_store_price_import_payload_builds_valid_contract() -> None:
    captured_at = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    products = [
        RawStoreProduct(
            store='Jumbo',
            original_name='Coca-Cola Zero 1,5L',
            price='2.39',
            captured_at=captured_at,
            category_group='Frisdrank en sappen',
            category='Cola',
        ),
        RawStoreProduct(
            store='Jumbo',
            original_name='Croissant 4 stuks',
            price='1.99',
            captured_at=captured_at,
            category_group='Brood en gebak',
            category='Croissants',
        ),
    ]

    payload = build_store_price_import_payload(
        products,
        import_id='demo-jumbo',
        source_artifact_path='tests/fixtures/raw/normalization_demo.json',
    )

    assert isinstance(payload, StorePriceImportPayload)
    assert payload.store == 'Jumbo'
    assert len(payload.records) == 2
    assert payload.records[0].category_group == 'frisdrank-en-sappen'
    assert payload.records[0].category == 'cola'


def test_build_store_price_import_payload_rejects_mixed_store_records() -> None:
    captured_at = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    products = [
        RawStoreProduct(
            store='ALDI',
            original_name='Campina Halfvolle Melk 1L',
            price='1.89',
            captured_at=captured_at,
        ),
        RawStoreProduct(
            store='Jumbo',
            original_name='Coca-Cola Zero 1,5L',
            price='2.39',
            captured_at=captured_at,
        ),
    ]

    with pytest.raises(ValueError):
        build_store_price_import_payload(
            products,
            import_id='demo-mixed',
            source_artifact_path='tests/fixtures/raw/normalization_demo.json',
        )
