from datetime import datetime, timezone

from savebasket_data.utils.clock import date_stamp, iso_timestamp, run_id


def test_clock_helpers_are_stable() -> None:
    value = datetime(2026, 4, 19, 12, 30, tzinfo=timezone.utc)

    assert date_stamp(value) == "2026-04-19"
    assert iso_timestamp(value) == "2026-04-19T12:30:00+00:00"
    assert run_id("aldi", value) == "aldi-20260419T123000Z"
