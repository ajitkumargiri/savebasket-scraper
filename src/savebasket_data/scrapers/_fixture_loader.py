"""Fixture-backed raw record loading for store scrapers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config.settings import get_settings


def default_fixture_path(store_slug: str) -> Path:
    """Return the default raw fixture path for a store."""
    return get_settings().project_root / 'tests' / 'fixtures' / 'raw' / store_slug / 'products.json'


def load_fixture_records(
    store_slug: str,
    fixture_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load a JSON-array fixture for one store."""
    resolved_path = fixture_path or default_fixture_path(store_slug)
    if not resolved_path.exists():
        raise FileNotFoundError(f'Fixture file not found: {resolved_path}')

    payload = json.loads(resolved_path.read_text(encoding='utf-8'))
    if not isinstance(payload, list):
        raise ValueError('Fixture payload must be a JSON array')

    records: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f'Fixture record {index} must be a JSON object')
        records.append(item)

    return records
