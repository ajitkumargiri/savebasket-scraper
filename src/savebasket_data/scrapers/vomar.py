"""Vomar scraper adapter for automated store imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._fixture_loader import default_fixture_path, load_fixture_records

STORE_SLUG = 'vomar'
STORE_NAME = 'Vomar'
LIVE_ACCESS_BLOCKED_MESSAGE = (
    'Vomar live scraping is currently blocked by 403 responses in this environment. '
    'Pass --fixture-path until a working saved HTML or API source is available.'
)


def get_default_fixture_path() -> Path:
    """Return the default Vomar raw fixture path."""
    return default_fixture_path(STORE_SLUG)


def scrape_vomar_products(fixture_path: Path | None = None) -> list[dict[str, Any]]:
    """Load Vomar data from a fixture or raise a clear live-access error."""
    if fixture_path is not None:
        return load_fixture_records(STORE_SLUG, fixture_path)
    raise RuntimeError(LIVE_ACCESS_BLOCKED_MESSAGE)
