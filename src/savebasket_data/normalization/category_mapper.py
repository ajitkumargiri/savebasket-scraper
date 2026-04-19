"""Category and group normalization helpers."""

from __future__ import annotations

import re
import unicodedata

CanonicalSlug = str

_GROUP_KEYWORDS: dict[CanonicalSlug, tuple[str, ...]] = {
    'zuivel-boter-en-eieren': (
        'zuivel',
        'dairy',
        'melk',
        'yoghurt',
        'kaas',
        'boter',
        'eieren',
        'eggs',
    ),
    'aardappelen-groente-en-fruit': (
        'aardappel',
        'aardappelen',
        'groente',
        'groenten',
        'fruit',
        'produce',
        'vegetable',
        'vegetables',
        'salade',
    ),
    'brood-en-gebak': (
        'brood',
        'bakery',
        'bakkerij',
        'bakken',
        'gebak',
        'ontbijt',
        'breakfast',
        'granen',
        'cereal',
        'beschuit',
        'crackers',
    ),
    'frisdrank-en-sappen': (
        'drank',
        'drinks',
        'beverage',
        'beverages',
        'frisdrank',
        'sap',
        'sappen',
        'water',
        'koffie',
        'thee',
    ),
}


def _normalize_category_text(value: str | None) -> str:
    if value is None:
        return ''

    text = unicodedata.normalize('NFKC', value).lower().strip()
    text = re.sub(r'[^\w\s-]+', ' ', text)
    text = re.sub(r'[_\s]+', ' ', text)
    return text.strip()


def _slugify(value: str | None) -> str | None:
    normalized = _normalize_category_text(value)
    if not normalized:
        return None

    slug = normalized.replace(' ', '-')
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-') or None


def map_source_category(store: str | None, source_category: str | None) -> str | None:
    """Normalize a source leaf category to a canonical slug."""
    del store
    return _slugify(source_category)


def map_source_category_group(
    store: str | None,
    source_category_group: str | None,
    source_category: str | None,
) -> str | None:
    """Normalize a source category group to a canonical group slug."""
    del store
    candidates = [source_category_group, source_category]
    for candidate in candidates:
        normalized = _normalize_category_text(candidate)
        if not normalized:
            continue
        for group_slug, keywords in _GROUP_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return group_slug

    return _slugify(source_category_group)
