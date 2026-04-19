"""CLI entrypoints for SaveBasket data jobs."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import typer

from .config.settings import get_settings
from .contracts.ah_import import AhImportPayload, AhProductRecord
from .contracts.offer_import import OfferImportPayload, OfferRecord
from .contracts.store_price_import import StorePriceImportPayload, StorePriceRecord

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
                category="dairy",
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
                category="dairy",
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


def main() -> None:
    """Run the Typer app."""
    app()


if __name__ == "__main__":
    main()
