from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from savebasket_data.contracts.offer_import import OfferImportPayload, OfferRecord


def test_offer_import_payload_validates() -> None:
    payload = OfferImportPayload(
        import_id="offer-import-1",
        imported_at=datetime.now(timezone.utc),
        valid_on=date(2026, 4, 19),
        source_artifact_path="data/raw/2026-04-19/offers.json",
        offers=[
            OfferRecord(
                store="Jumbo",
                title="1+1 gratis",
                offer_type="multi_buy",
                description="Buy one get one free",
                valid_from=date(2026, 4, 19),
                valid_to=date(2026, 4, 25),
                normalized_name="optimel yoghurt aardbei 1 l",
                buy_quantity=2,
                pay_quantity=1,
            )
        ],
    )

    assert payload.offers[0].offer_type == "multi_buy"


def test_offer_record_rejects_incomplete_shape() -> None:
    with pytest.raises(ValidationError):
        OfferRecord(
            store="Jumbo",
            title="50% korting",
            offer_type="percentage_discount",
            description="Discount offer",
            valid_from=date(2026, 4, 19),
            valid_to=date(2026, 4, 25),
        )
