from __future__ import annotations

import json
from datetime import datetime, timezone

from savebasket_data.scrapers.aldi import (
    _build_raw_record,
    _discover_root_category_urls,
    _extract_subcategory_urls,
)


def test_extract_subcategory_urls_reads_next_data_children() -> None:
    page_props = {
        'apiData': json.dumps(
            [
                [
                    'PRODUCT_MGNL_CATEGORY_CHILDREN_GET',
                    {
                        'res': [
                            {'path': '/netherlands/producten/zuivel-eieren-boter/verse-zuivel'},
                            {'path': '/netherlands/producten/zuivel-eieren-boter/eieren'},
                        ]
                    },
                ]
            ]
        )
    }

    assert _extract_subcategory_urls(page_props) == [
        'https://www.aldi.nl/producten/zuivel-eieren-boter/verse-zuivel.html',
        'https://www.aldi.nl/producten/zuivel-eieren-boter/eieren.html',
    ]


def test_discover_root_category_urls_from_products_page(monkeypatch) -> None:
    fake_page_props = {
        'apiData': json.dumps(
            [
                [
                    'PRODUCT_MGNL_CATEGORY_CHILDREN_GET',
                    {
                        'res': [
                            {'path': '/netherlands/producten/zuivel-eieren-boter'},
                            {'path': '/netherlands/producten/diepvries'},
                        ]
                    },
                ]
            ]
        )
    }

    monkeypatch.setattr(
        'savebasket_data.scrapers.aldi._fetch_page_props',
        lambda client, url: fake_page_props,
    )

    assert _discover_root_category_urls(object()) == [
        'https://www.aldi.nl/producten/zuivel-eieren-boter.html',
        'https://www.aldi.nl/producten/diepvries.html',
    ]


def test_build_raw_record_uses_group_category_price_and_sales_unit() -> None:
    hit = {
        'objectID': '1237742',
        'brandName': 'MILSANI',
        'name': 'Yo to Go banaan',
        'currentPrice': {'priceValue': 0.99},
        'salesUnit': '200 g',
        'assets': [{'type': 'primary', 'url': 'https://cdn.example/aldi.png'}],
        'hierarchicalCategories': {
            'lvl0': ['Zuivel, eieren en boter'],
            'lvl1': ['Zuivel, eieren en boter > Verse zuivel'],
        },
    }

    record = _build_raw_record(hit, datetime(2026, 4, 19, tzinfo=timezone.utc))

    assert record['store'] == 'ALDI'
    assert record['source_id'] == '1237742'
    assert record['category_group'] == 'Zuivel, eieren en boter'
    assert record['category'] == 'Verse zuivel'
    assert record['original_name'] == 'MILSANI Yo to Go banaan'
    assert record['price'] == 0.99
    assert record['quantity_text'] == '200 g'
    assert record['image_url'] == 'https://cdn.example/aldi.png'
