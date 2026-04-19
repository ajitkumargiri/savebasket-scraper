"""Clock and identifier helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def iso_timestamp(value: datetime | None = None) -> str:
    """Serialize a datetime as an ISO-8601 string."""
    current = value or utc_now()
    return current.isoformat()


def date_stamp(value: datetime | None = None) -> str:
    """Return a YYYY-MM-DD date stamp."""
    current = value or utc_now()
    return current.strftime("%Y-%m-%d")


def run_id(prefix: str, value: datetime | None = None) -> str:
    """Build a deterministic run identifier prefix-timestamp."""
    current = value or utc_now()
    return f"{prefix}-{current.strftime('%Y%m%dT%H%M%SZ')}"
