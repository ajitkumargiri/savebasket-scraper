"""Jumbo import job entrypoint for Sprint 2."""

from __future__ import annotations

from pathlib import Path

from ..config.settings import Settings
from ..scrapers.jumbo import STORE_NAME, STORE_SLUG, scrape_jumbo_products
from .store_import_runner import StoreImportRunResult, run_store_import


def run_jumbo_import(
    fixture_path: Path | None = None,
    settings: Settings | None = None,
) -> StoreImportRunResult:
    """Run the Jumbo automated import flow."""
    return run_store_import(
        store_slug=STORE_SLUG,
        store_name=STORE_NAME,
        job_name='run_jumbo_import',
        fetch_records=scrape_jumbo_products,
        fixture_path=fixture_path,
        settings=settings,
    )
