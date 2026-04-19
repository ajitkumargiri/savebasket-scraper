"""Price parsing helpers."""

from __future__ import annotations

import re


def _normalize_numeric_string(text: str) -> str:
    separators = [index for index, char in enumerate(text) if char in ",."]
    if not separators:
        return text

    decimal_index = separators[-1]
    decimal_digits = len(text) - decimal_index - 1
    if decimal_digits not in {1, 2}:
        return text.replace(",", "").replace(".", "")

    integer_part = re.sub(r"[,.]", "", text[:decimal_index])
    decimal_part = re.sub(r"[,.]", "", text[decimal_index + 1 :])
    return f"{integer_part}.{decimal_part}"


def parse_price(value: str | int | float | None) -> float | None:
    """Parse a price value into a float, or return None when it is unusable."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        numeric_value = float(value)
        return round(numeric_value, 2) if numeric_value >= 0 else None

    text = str(value).strip()
    if not text:
        return None

    text = text.lower()
    text = text.replace("euro", "").replace("eur", "").replace("€", "")
    text = text.replace(",-", "")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\d,.-]", "", text)

    if not text or text in {"-", ".", ","}:
        return None

    normalized = _normalize_numeric_string(text)
    try:
        numeric_value = float(normalized)
    except ValueError:
        return None

    return round(numeric_value, 2) if numeric_value >= 0 else None
