"""ALDI import job entrypoint for Sprint 2."""

from __future__ import annotations

from pathlib import Path

from ..config.settings import Settings
from ..scrapers.aldi import STORE_NAME, STORE_SLUG, scrape_aldi_products
from .store_import_runner import StoreImportRunResult, run_store_import


def run_aldi_import(
    fixture_path: Path | None = None,
    settings: Settings | None = None,
) -> StoreImportRunResult:
    """Run the ALDI automated import flow."""
    return run_store_import(
        store_slug=STORE_SLUG,
        store_name=STORE_NAME,
        job_name='run_aldi_import',
        fetch_records=scrape_aldi_products,
        fixture_path=fixture_path,
        settings=settings,
    )
