from __future__ import annotations

from datetime import datetime, timezone

from savebasket_data.scrapers.jumbo import (
    JumboCategoryTarget,
    _build_raw_record,
    _category_page_path,
    _collect_targets_from_node,
    _discover_category_targets,
)


def test_category_page_path_adds_offset_query() -> None:
    assert _category_page_path('zuivel,-boter-en-eieren/', 0) == (
        '/producten/zuivel,-boter-en-eieren/'
    )
    assert _category_page_path('zuivel,-boter-en-eieren/', 24) == (
        '/producten/zuivel,-boter-en-eieren/?offSet=24'
    )


def test_collect_targets_from_node_flattens_descendants() -> None:
    node = {
        'name': 'Verse melk',
        'friendlyUrl': 'zuivel,-boter-en-eieren/verse-melk/',
        'children': [
            {
                'name': 'Halfvolle melk',
                'friendlyUrl': 'zuivel,-boter-en-eieren/verse-melk/halfvolle-melk/',
                'children': [],
            }
        ],
    }

    targets = _collect_targets_from_node(
        node,
        'zuivel-boter-en-eieren',
        'Zuivel, boter en eieren',
        depth=1,
    )

    assert [target.category_slug for target in targets] == ['verse-melk', 'halfvolle-melk']
    assert [target.depth for target in targets] == [1, 2]


def test_discover_category_targets_includes_root_and_children(monkeypatch) -> None:
    monkeypatch.setattr(
        'savebasket_data.scrapers.jumbo._post_search_products',
        lambda client, friendly_url, offset, query, with_facet_children=False: {
            'facets': [
                {
                    'key': 'category',
                    'values': [
                        {
                            'friendlyUrl': 'zuivel,-boter-en-eieren/',
                            'children': [
                                {
                                    'name': 'Verse melk',
                                    'friendlyUrl': 'zuivel,-boter-en-eieren/verse-melk/',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    targets = _discover_category_targets(
        object(),
        'Zuivel, boter en eieren',
        'zuivel,-boter-en-eieren/',
    )

    assert [target.category_name for target in targets] == [
        'Zuivel, boter en eieren',
        'Verse melk',
    ]
    assert [target.depth for target in targets] == [0, 1]


def test_build_raw_record_uses_group_category_and_absolute_url() -> None:
    product = {
        'id': '736180PAK',
        'brand': 'Optimel',
        'title': 'Optimel Vezels Drinkyoghurt Mango Ananas 0% Vet 1L',
        'subtitle': '1000 ml',
        'link': '/producten/optimel-736180PAK',
        'image': 'https://cdn.example/jumbo.png',
        'category': 'Zuivel, boter en eieren',
        'prices': {
            'price': 229,
            'promoPrice': 199,
        },
    }
    target = JumboCategoryTarget(
        group_slug='zuivel-boter-en-eieren',
        group_name='Zuivel, boter en eieren',
        category_slug='verse-melk',
        category_name='Verse melk',
        friendly_url='zuivel,-boter-en-eieren/verse-melk/',
        depth=1,
    )

    record = _build_raw_record(
        product,
        target,
        datetime(2026, 4, 19, tzinfo=timezone.utc),
    )

    assert record['store'] == 'Jumbo'
    assert record['source_id'] == '736180PAK'
    assert record['category_group'] == 'Zuivel, boter en eieren'
    assert record['category'] == 'Verse melk'
    assert record['price'] == 1.99
    assert record['quantity_text'] == '1000 ml'
    assert record['product_url'] == 'https://www.jumbo.com/producten/optimel-736180PAK'
    assert record['image_url'] == 'https://cdn.example/jumbo.png'
