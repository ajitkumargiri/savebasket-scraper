"""CLI entrypoints for SaveBasket data jobs."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated

import typer

from .config.settings import get_settings
from .contracts.ah_import import AhImportPayload, AhProductRecord
from .contracts.offer_import import OfferImportPayload, OfferRecord
from .contracts.store_price_import import StorePriceImportPayload, StorePriceRecord
from .jobs.run_aldi_import import run_aldi_import
from .jobs.run_jumbo_import import run_jumbo_import
from .jobs.run_vomar_import import run_vomar_import
from .jobs.store_import_runner import StoreImportRunResult
from .normalization.product_normalizer import (
    RawStoreProduct,
    build_store_price_import_payload,
    normalize_store_product,
)

app = typer.Typer(help="SaveBasket data ingestion commands.")


@app.command("settings")
def show_settings() -> None:
    """Print resolved settings for the current environment."""
    settings = get_settings()
    typer.echo(json.dumps(settings.to_public_dict(), indent=2))


@app.command("demo-contracts")
def demo_contracts() -> None:
    """Validate one representative payload for each contract."""
    now = datetime.now(timezone.utc)

    store_payload = StorePriceImportPayload(
        import_id="demo-store-import",
        store="ALDI",
        imported_at=now,
        source_artifact_path="data/raw/2026-04-19/aldi-demo.json",
        records=[
            StorePriceRecord(
                source_id="aldi-1",
                store="ALDI",
                category_group="zuivel-boter-en-eieren",
                category="verse-zuivel",
                brand="Campina",
                original_name="Campina Halfvolle Melk 1L",
                normalized_name="campina halfvolle melk 1 l",
                price_amount=1.89,
                quantity_value=1,
                quantity_unit="l",
                product_url="https://www.aldi.nl/product/halfvolle-melk",
                captured_at=now,
            )
        ],
    )

    ah_payload = AhImportPayload(
        import_id="demo-ah-import",
        imported_at=now,
        source_html_path="ah_page_source.html",
        html_captured_at=now,
        records=[
            AhProductRecord(
                source_id="ah-1",
                category_group="zuivel-boter-en-eieren",
                category="yoghurt",
                original_name="AH Magere Yoghurt 1L",
                normalized_name="ah magere yoghurt 1 l",
                price_amount=1.49,
                quantity_value=1,
                quantity_unit="l",
                product_url="https://www.ah.nl/producten/product/wi123",
                captured_at=now,
            )
        ],
    )

    offer_payload = OfferImportPayload(
        import_id="demo-offer-import",
        imported_at=now,
        valid_on=date.today(),
        source_artifact_path="data/raw/2026-04-19/offers-demo.json",
        offers=[
            OfferRecord(
                store="Jumbo",
                title="2e halve prijs",
                offer_type="multi_buy",
                description="Second item at 50% discount",
                valid_from=date.today(),
                valid_to=date.today(),
                normalized_name="optimel yoghurt aardbei 1 l",
                buy_quantity=2,
                pay_quantity=1,
            )
        ],
    )

    typer.echo(
        json.dumps(
            {
                "store_price_import": store_payload.model_dump(mode="json"),
                "ah_import": ah_payload.model_dump(mode="json"),
                "offer_import": offer_payload.model_dump(mode="json"),
            },
            indent=2,
        )
    )


def _default_demo_fixture_path() -> Path:
    return get_settings().project_root / 'tests' / 'fixtures' / 'raw' / 'normalization_demo.json'


def _relative_to_project(path: Path) -> str:
    project_root = get_settings().project_root
    try:
        return str(path.resolve().relative_to(project_root))
    except ValueError:
        return str(path.resolve())


StoreFixtureOption = Annotated[
    Path | None,
    typer.Option(
        '--fixture-path',
        help='Path to a store-specific JSON fixture.',
        resolve_path=True,
    ),
]


def _echo_store_import_result(result: StoreImportRunResult) -> None:
    typer.echo(json.dumps(asdict(result), indent=2))
    if result.status != 'success':
        raise typer.Exit(code=1)


@app.command('demo-normalization')
def demo_normalization(
    fixture_path: Annotated[
        Path | None,
        typer.Option(
            '--fixture-path',
            help='Path to a JSON array of raw store products.',
            resolve_path=True,
        ),
    ] = None,
) -> None:
    """Normalize 10 mixed sample products and print before/after output."""
    resolved_path = fixture_path or _default_demo_fixture_path()
    if not resolved_path.exists():
        raise typer.BadParameter(f'Fixture file not found: {resolved_path}')

    raw_products = json.loads(resolved_path.read_text(encoding='utf-8'))
    if not isinstance(raw_products, list):
        raise typer.BadParameter('Demo fixture must be a JSON array')

    demo_records: list[dict[str, object]] = []
    payload_inputs_by_store: dict[str, list[RawStoreProduct]] = defaultdict(list)
    invalid_count = 0

    for item in raw_products:
        product = RawStoreProduct.from_mapping(item)
        normalized = normalize_store_product(product)
        if normalized is None:
            invalid_count += 1
        else:
            payload_inputs_by_store[normalized.store].append(product)

        demo_records.append(
            {
                'raw': product.to_dict(),
                'normalized': normalized.model_dump(mode='json') if normalized else None,
            }
        )

    payloads_by_store: dict[str, dict[str, object]] = {}
    for store_name, products in payload_inputs_by_store.items():
        payload = build_store_price_import_payload(
            products,
            import_id=f'demo-{store_name.lower().replace(" ", "-")}',
            source_artifact_path=_relative_to_project(resolved_path),
            source_type='scraper',
        )
        if payload is not None:
            payloads_by_store[store_name] = payload.model_dump(mode='json')

    typer.echo(
        json.dumps(
            {
                'fixture_path': _relative_to_project(resolved_path),
                'input_count': len(raw_products),
                'normalized_count': len(raw_products) - invalid_count,
                'invalid_count': invalid_count,
                'payload_count': len(payloads_by_store),
                'records': demo_records,
                'payloads_by_store': payloads_by_store,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


@app.command('run-aldi-import')
def run_aldi_import_command(fixture_path: StoreFixtureOption = None) -> None:
    """Run the ALDI store import using live data or a fixture override."""
    _echo_store_import_result(run_aldi_import(fixture_path=fixture_path))


@app.command('run-jumbo-import')
def run_jumbo_import_command(fixture_path: StoreFixtureOption = None) -> None:
    """Run the Jumbo store import using live data or a fixture override."""
    _echo_store_import_result(run_jumbo_import(fixture_path=fixture_path))


@app.command('run-vomar-import')
def run_vomar_import_command(fixture_path: StoreFixtureOption = None) -> None:
    """Run the Vomar store import from a fixture until live access is resolved."""
    _echo_store_import_result(run_vomar_import(fixture_path=fixture_path))


def main() -> None:
    """Run the Typer app."""
    app()


if __name__ == "__main__":
    main()
