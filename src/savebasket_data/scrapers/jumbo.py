"""Jumbo scraper adapter for automated store imports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ._fixture_loader import default_fixture_path, load_fixture_records

STORE_SLUG = 'jumbo'
STORE_NAME = 'Jumbo'
BASE_URL = 'https://www.jumbo.com'
PRODUCTS_PAGE_URL = f'{BASE_URL}/producten/'
GRAPHQL_URL = f'{BASE_URL}/api/graphql'
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
)
PRODUCTS_QUERY = (
    """query SearchProducts($input: ProductSearchInput!, $shelfTextInput: ShelfTextInput!) {
  searchProducts(input: $input) {
    start
    count
    pageHeader {
      headerText
      count
      __typename
    }
    products {
      id: sku
      brand
      category: rootCategory
      subtitle: packSizeDisplay
      title
      image
      link
      prices: price {
        price
        promoPrice
        pricePerUnit {
          price
          unit
          __typename
        }
        __typename
      }
      promotions {
        tags {
          text
          inverse
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  getCategoryShelfText(input: $shelfTextInput) {
    shelfText
    __typename
  }
}"""
)
DISCOVERY_QUERY = (
    """query SearchProducts(
$input: ProductSearchInput!,
$shelfTextInput: ShelfTextInput!,
$withFacetChildren: Boolean!
) {
  searchProducts(input: $input) {
    pageHeader {
      headerText
      count
      __typename
    }
    facets {
      key
      displayName
      values {
        id
        count
        name
        friendlyUrl
        selected
        children @include(if: $withFacetChildren) {
          id
          count
          name
          friendlyUrl
          selected
          children {
            id
            count
            name
            friendlyUrl
            selected
            children {
              id
              count
              name
              friendlyUrl
              selected
              children {
                id
                count
                name
                friendlyUrl
                selected
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  getCategoryShelfText(input: $shelfTextInput) {
    shelfText
    __typename
  }
}"""
)
CATEGORIES_TREE_QUERY = (
    """query CategoriesTree(
$exclusions: [String!],
$depth: Int = 2,
$megaMenuEnabled: Boolean = true
) {
  categoriesTree(
    exclusions: $exclusions,
    depth: $depth,
    megaMenuEnabled: $megaMenuEnabled
  ) {
    title: name
    link: seoURL
    subpages: children {
      title: name
      link: seoURL
      __typename
    }
    __typename
  }
}"""
)


@dataclass(frozen=True, slots=True)
class JumboCategoryTarget:
    group_slug: str
    group_name: str
    category_slug: str
    category_name: str
    friendly_url: str
    depth: int


def get_default_fixture_path() -> Path:
    """Return the default Jumbo raw fixture path."""
    return default_fixture_path(STORE_SLUG)


def _category_page_path(friendly_url: str, offset: int) -> str:
    slug = friendly_url.strip('/')
    path = f'/producten/{slug}/'
    if offset > 0:
        return f'{path}?offSet={offset}'
    return path


def _friendly_url_with_offset(friendly_url: str, offset: int) -> str:
    slug = friendly_url.strip('/') + '/'
    if offset > 0:
        return f'{slug}?offSet={offset}'
    return slug


def _request_headers(friendly_url: str, offset: int) -> dict[str, str]:
    referer_url = (
        PRODUCTS_PAGE_URL
        if not friendly_url
        else f'{BASE_URL}{_category_page_path(friendly_url, offset)}'
    )
    return {
        'User-Agent': USER_AGENT,
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': BASE_URL,
        'Referer': referer_url,
        'x-source': 'JUMBO_WEB-search',
        'apollographql-client-name': 'JUMBO_WEB-search',
        'apollographql-client-version': 'master-v31.5.0-web',
    }


def _query_payload(
    friendly_url: str,
    offset: int,
    query: str,
    *,
    with_facet_children: bool = False,
) -> dict[str, Any]:
    friendly_url_with_offset = _friendly_url_with_offset(friendly_url, offset)
    payload = {
        'operationName': 'SearchProducts',
        'variables': {
            'input': {
                'searchType': 'category',
                'searchTerms': 'producten',
                'friendlyUrl': friendly_url_with_offset,
                'offSet': offset,
                'currentUrl': _category_page_path(friendly_url, offset),
                'previousUrl': '',
                'bloomreachCookieId': '',
            },
            'shelfTextInput': {
                'searchType': 'category',
                'friendlyUrl': friendly_url_with_offset,
            },
        },
        'query': query,
    }
    if with_facet_children:
        payload['variables']['withFacetChildren'] = True
    return payload


def _post_graphql(
    client: httpx.Client,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(GRAPHQL_URL, headers=headers, json=payload)
    response.raise_for_status()
    body = response.json()
    if 'errors' in body:
        raise RuntimeError(f'Jumbo GraphQL returned errors: {body["errors"]}')
    return body['data']


def _post_search_products(
    client: httpx.Client,
    friendly_url: str,
    offset: int,
    query: str,
    *,
    with_facet_children: bool = False,
) -> dict[str, Any]:
    data = _post_graphql(
        client,
        _request_headers(friendly_url, offset),
        _query_payload(
            friendly_url,
            offset,
            query,
            with_facet_children=with_facet_children,
        ),
    )
    search_products = data.get('searchProducts')
    if not isinstance(search_products, dict):
        raise RuntimeError('Jumbo GraphQL response is missing searchProducts data')
    return search_products


def _discover_root_category_urls(client: httpx.Client) -> list[tuple[str, str]]:
    payload = {
        'operationName': 'CategoriesTree',
        'variables': {'depth': 2, 'megaMenuEnabled': True},
        'query': CATEGORIES_TREE_QUERY,
    }
    data = _post_graphql(client, _request_headers('', 0), payload)
    categories_tree = data.get('categoriesTree') or []
    root_categories: list[tuple[str, str]] = []
    for item in categories_tree:
        if not isinstance(item, dict):
            continue
        title = item.get('title')
        link = item.get('link')
        if not isinstance(title, str) or not isinstance(link, str):
            continue
        if not link.startswith('/producten/'):
            continue
        friendly_url = link.removeprefix('/producten/')
        root_categories.append((title, friendly_url))
    return root_categories


def _last_slug_segment(friendly_url: str) -> str:
    return friendly_url.strip('/').split('/')[-1]


def _collect_targets_from_node(
    node: dict[str, Any],
    group_slug: str,
    group_name: str,
    *,
    depth: int,
) -> list[JumboCategoryTarget]:
    friendly_url = node.get('friendlyUrl')
    category_name = node.get('name')
    if not isinstance(friendly_url, str) or not isinstance(category_name, str):
        return []

    targets = [
        JumboCategoryTarget(
            group_slug=group_slug,
            group_name=group_name,
            category_slug=_last_slug_segment(friendly_url),
            category_name=category_name,
            friendly_url=friendly_url,
            depth=depth,
        )
    ]
    for child in node.get('children') or []:
        targets.extend(
            _collect_targets_from_node(
                child,
                group_slug,
                group_name,
                depth=depth + 1,
            )
        )
    return targets


def _discover_category_targets(
    client: httpx.Client,
    root_group_name: str,
    root_friendly_url: str,
) -> list[JumboCategoryTarget]:
    search_products = _post_search_products(
        client,
        root_friendly_url,
        0,
        DISCOVERY_QUERY,
        with_facet_children=True,
    )
    group_slug = _last_slug_segment(root_friendly_url)
    root_target = JumboCategoryTarget(
        group_slug=group_slug,
        group_name=root_group_name,
        category_slug=group_slug,
        category_name=root_group_name,
        friendly_url=root_friendly_url,
        depth=0,
    )

    facets = search_products.get('facets') or []
    category_facet = next(
        (facet for facet in facets if facet.get('key') == 'category'),
        None,
    )
    if not isinstance(category_facet, dict):
        return [root_target]

    root_node = next(
        (
            value
            for value in category_facet.get('values') or []
            if value.get('friendlyUrl') == root_friendly_url
        ),
        None,
    )
    if not isinstance(root_node, dict):
        return [root_target]

    targets: list[JumboCategoryTarget] = [root_target]
    for child in root_node.get('children') or []:
        targets.extend(
            _collect_targets_from_node(
                child,
                group_slug,
                root_group_name,
                depth=1,
            )
        )

    deduped: dict[str, JumboCategoryTarget] = {}
    for target in targets:
        deduped[target.friendly_url] = target
    return sorted(deduped.values(), key=lambda item: (item.depth, item.friendly_url))


def _build_raw_record(
    product: dict[str, Any],
    target: JumboCategoryTarget,
    captured_at: datetime,
) -> dict[str, Any]:
    price_block = product.get('prices') or {}
    promo_price = price_block.get('promoPrice') if isinstance(price_block, dict) else None
    base_price = price_block.get('price') if isinstance(price_block, dict) else None
    selected_price = promo_price if promo_price is not None else base_price

    product_link = product.get('link')
    if isinstance(product_link, str) and product_link.startswith('/'):
        product_link = f'{BASE_URL}{product_link}'

    return {
        'store': STORE_NAME,
        'source_id': product.get('id'),
        'original_name': product.get('title') or '',
        'price': (
            selected_price / 100
            if isinstance(selected_price, (int, float))
            else selected_price
        ),
        'captured_at': captured_at.isoformat(),
        'category_group': target.group_name,
        'category': target.category_name,
        'brand': product.get('brand'),
        'quantity_text': product.get('subtitle'),
        'product_url': product_link,
        'image_url': product.get('image'),
    }


def scrape_jumbo_products(fixture_path: Path | None = None) -> list[dict[str, Any]]:
    """Scrape the full Jumbo live catalog or load a provided fixture."""
    if fixture_path is not None:
        return load_fixture_records(STORE_SLUG, fixture_path)

    captured_at = datetime.now(timezone.utc)
    records_by_source_id: dict[str, tuple[int, dict[str, Any]]] = {}

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for root_group_name, root_friendly_url in _discover_root_category_urls(client):
            category_targets = _discover_category_targets(
                client,
                root_group_name,
                root_friendly_url,
            )
            if not category_targets:
                continue

            for target in category_targets:
                offset = 0
                total_count: int | None = None

                while True:
                    search_products = _post_search_products(
                        client,
                        target.friendly_url,
                        offset,
                        PRODUCTS_QUERY,
                    )
                    products = search_products.get('products') or []

                    if total_count is None and isinstance(search_products.get('count'), int):
                        total_count = search_products['count']

                    if not products:
                        break

                    for product in products:
                        raw_record = _build_raw_record(product, target, captured_at)
                        source_id = str(
                            raw_record.get('source_id')
                            or f'{target.friendly_url}{offset}:{len(records_by_source_id)}'
                        )
                        current = records_by_source_id.get(source_id)
                        if current is None or target.depth >= current[0]:
                            records_by_source_id[source_id] = (target.depth, raw_record)

                    offset += len(products)
                    if total_count is not None and offset >= total_count:
                        break

    return [record for _, record in records_by_source_id.values()]
