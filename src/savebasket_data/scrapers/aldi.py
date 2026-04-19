"""ALDI scraper adapter for automated store imports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ._fixture_loader import default_fixture_path, load_fixture_records

STORE_SLUG = 'aldi'
STORE_NAME = 'ALDI'
BASE_URL = 'https://www.aldi.nl'
PRODUCTS_PAGE_URL = f'{BASE_URL}/producten.html'
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
)
ALGOLIA_INDEX = 'an_prd_nl_nl_products2'


def get_default_fixture_path() -> Path:
    """Return the default ALDI raw fixture path."""
    return default_fixture_path(STORE_SLUG)


def _fetch_page_props(client: httpx.Client, url: str) -> dict[str, Any]:
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    next_data = soup.select_one('script#__NEXT_DATA__')
    if next_data is None:
        raise ValueError(f'ALDI page is missing __NEXT_DATA__: {url}')

    payload = json.loads(next_data.get_text())
    return payload['props']['pageProps']


def _normalize_category_path(path: str) -> str:
    normalized = path.removeprefix('/netherlands').strip()
    if not normalized.startswith('/'):
        normalized = f'/{normalized}'
    if not normalized.endswith('.html'):
        normalized = f'{normalized}.html'
    return normalized


def _extract_category_items(page_props: dict[str, Any]) -> list[dict[str, Any]]:
    api_data_raw = page_props.get('apiData')
    if not isinstance(api_data_raw, str):
        return []

    items: list[dict[str, Any]] = []
    for operation_name, payload in json.loads(api_data_raw):
        if operation_name != 'PRODUCT_MGNL_CATEGORY_CHILDREN_GET':
            continue
        if not isinstance(payload, dict):
            continue
        for item in payload.get('res') or []:
            if isinstance(item, dict):
                items.append(item)
    return items


def _category_url_from_item(item: dict[str, Any]) -> str | None:
    path = item.get('path')
    if not isinstance(path, str) or not path:
        return None
    return f'{BASE_URL}{_normalize_category_path(path)}'


def _extract_subcategory_urls(page_props: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for item in _extract_category_items(page_props):
        category_url = _category_url_from_item(item)
        if category_url is not None:
            urls.append(category_url)
    return urls


def _discover_root_category_urls(client: httpx.Client) -> list[str]:
    page_props = _fetch_page_props(client, PRODUCTS_PAGE_URL)
    urls: list[str] = []
    for item in _extract_category_items(page_props):
        category_url = _category_url_from_item(item)
        if category_url is not None:
            urls.append(category_url)
    return urls


def _extract_hits(page_props: dict[str, Any]) -> list[dict[str, Any]]:
    algolia_state = page_props.get('algoliaState')
    if not isinstance(algolia_state, dict):
        return []

    initial_results = algolia_state.get('initialResults')
    if not isinstance(initial_results, dict):
        return []

    search_state = initial_results.get(ALGOLIA_INDEX, {})
    results = search_state.get('results') or []
    if not results:
        return []

    first_result = results[0]
    if not isinstance(first_result, dict):
        return []
    hits = first_result.get('hits') or []
    return [hit for hit in hits if isinstance(hit, dict)]


def _category_title_from_hit(hit: dict[str, Any]) -> str | None:
    hierarchical_categories = hit.get('hierarchicalCategories') or {}
    level_one = hierarchical_categories.get('lvl1')

    if isinstance(level_one, list) and level_one:
        return str(level_one[0]).split(' > ')[-1].strip()
    if isinstance(level_one, str) and level_one:
        return level_one.split(' > ')[-1].strip()

    main_category = hit.get('mainCategoryID')
    if isinstance(main_category, str) and main_category:
        return main_category.replace('-', ' ')
    return None


def _category_group_from_hit(hit: dict[str, Any]) -> str | None:
    hierarchical_categories = hit.get('hierarchicalCategories') or {}
    level_zero = hierarchical_categories.get('lvl0')

    if isinstance(level_zero, list) and level_zero:
        return str(level_zero[0]).strip()
    if isinstance(level_zero, str) and level_zero:
        return level_zero.strip()
    return None


def _build_original_name(hit: dict[str, Any]) -> str:
    name = str(hit.get('name') or '').strip()
    brand = str(hit.get('brandName') or '').strip()

    if brand and name and brand.casefold() not in name.casefold():
        return f'{brand} {name}'
    return name


def _extract_image_url(hit: dict[str, Any]) -> str | None:
    assets = hit.get('assets') or []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        image_url = asset.get('url')
        if isinstance(image_url, str) and image_url:
            return image_url
    return None


def _url_depth(url: str) -> int:
    path = url.removeprefix(BASE_URL).strip('/')
    return len([segment for segment in path.split('/') if segment])


def _build_raw_record(hit: dict[str, Any], captured_at: datetime) -> dict[str, Any]:
    current_price = hit.get('currentPrice') or {}
    price_value = current_price.get('priceValue') if isinstance(current_price, dict) else None

    return {
        'store': STORE_NAME,
        'source_id': hit.get('objectID') or hit.get('productSlug'),
        'original_name': _build_original_name(hit),
        'price': price_value,
        'captured_at': captured_at.isoformat(),
        'category_group': _category_group_from_hit(hit),
        'category': _category_title_from_hit(hit),
        'brand': hit.get('brandName'),
        'quantity_text': hit.get('salesUnit') or hit.get('shortDescription'),
        'product_url': None,
        'image_url': _extract_image_url(hit),
    }


def scrape_aldi_products(fixture_path: Path | None = None) -> list[dict[str, Any]]:
    """Scrape the full ALDI live catalog or load a provided fixture."""
    if fixture_path is not None:
        return load_fixture_records(STORE_SLUG, fixture_path)

    captured_at = datetime.now(timezone.utc)
    records_by_source_id: dict[str, tuple[int, dict[str, Any]]] = {}
    seen_urls: set[str] = set()

    with httpx.Client(
        headers={'User-Agent': USER_AGENT},
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        pending_urls = list(_discover_root_category_urls(client))

        while pending_urls:
            category_url = pending_urls.pop(0)
            if category_url in seen_urls:
                continue
            seen_urls.add(category_url)

            try:
                page_props = _fetch_page_props(client, category_url)
            except Exception:
                continue

            for subcategory_url in _extract_subcategory_urls(page_props):
                if subcategory_url not in seen_urls:
                    pending_urls.append(subcategory_url)

            page_depth = _url_depth(category_url)
            for hit in _extract_hits(page_props):
                raw_record = _build_raw_record(hit, captured_at)
                source_id = str(
                    raw_record.get('source_id')
                    or f'{category_url}::{len(records_by_source_id)}'
                )
                current = records_by_source_id.get(source_id)
                if current is None or page_depth >= current[0]:
                    records_by_source_id[source_id] = (page_depth, raw_record)

    return [record for _, record in records_by_source_id.values()]
