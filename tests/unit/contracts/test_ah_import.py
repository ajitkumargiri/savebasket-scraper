from datetime import datetime, timezone

from savebasket_data.contracts.ah_import import AhImportPayload, AhProductRecord


def test_ah_import_payload_validates() -> None:
    now = datetime.now(timezone.utc)

    payload = AhImportPayload(
        import_id="ah-import-1",
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

    assert payload.records[0].price_amount == 1.49
