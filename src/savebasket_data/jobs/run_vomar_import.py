"""Vomar import job entrypoint for Sprint 2."""

from __future__ import annotations

from pathlib import Path

from ..config.settings import Settings
from ..scrapers.vomar import STORE_NAME, STORE_SLUG, scrape_vomar_products
from .store_import_runner import StoreImportRunResult, run_store_import


def run_vomar_import(
    fixture_path: Path | None = None,
    settings: Settings | None = None,
) -> StoreImportRunResult:
    """Run the Vomar automated import flow."""
    return run_store_import(
        store_slug=STORE_SLUG,
        store_name=STORE_NAME,
        job_name='run_vomar_import',
        fetch_records=scrape_vomar_products,
        fixture_path=fixture_path,
        settings=settings,
    )
