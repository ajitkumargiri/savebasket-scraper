from datetime import datetime, timezone

from savebasket_data.contracts.store_price_import import StorePriceImportPayload, StorePriceRecord


def test_store_price_import_payload_validates() -> None:
    now = datetime.now(timezone.utc)

    payload = StorePriceImportPayload(
        import_id="aldi-import-1",
        store="ALDI",
        imported_at=now,
        source_artifact_path="data/raw/2026-04-19/aldi.json",
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

    assert payload.store == "ALDI"
    assert payload.records[0].normalized_name == "campina halfvolle melk 1 l"
