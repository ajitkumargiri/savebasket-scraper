"""Quantity parsing helpers."""

from __future__ import annotations

import re

from .name_cleaner import clean_product_name

_UNIT_ALIASES: dict[str, tuple[str, float]] = {
    "g": ("g", 1),
    "gram": ("g", 1),
    "grams": ("g", 1),
    "gr": ("g", 1),
    "kg": ("kg", 1),
    "kilo": ("kg", 1),
    "kilos": ("kg", 1),
    "kilogram": ("kg", 1),
    "kilograms": ("kg", 1),
    "ml": ("ml", 1),
    "milliliter": ("ml", 1),
    "milliliters": ("ml", 1),
    "millilitre": ("ml", 1),
    "millilitres": ("ml", 1),
    "cl": ("ml", 10),
    "centiliter": ("ml", 10),
    "centiliters": ("ml", 10),
    "centilitre": ("ml", 10),
    "centilitres": ("ml", 10),
    "l": ("l", 1),
    "liter": ("l", 1),
    "liters": ("l", 1),
    "litre": ("l", 1),
    "litres": ("l", 1),
    "pc": ("pc", 1),
    "piece": ("pc", 1),
    "pieces": ("pc", 1),
    "pcs": ("pc", 1),
    "stuk": ("pc", 1),
    "stuks": ("pc", 1),
    "stukken": ("pc", 1),
    "st": ("pc", 1),
    "stk": ("pc", 1),
}

_MULTIPACK_PATTERN = re.compile(
    r"(?P<count>\d+)\s*[x×]\s*(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>[a-z]+)\b"
)
_SINGLE_PATTERN = re.compile(r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>[a-z]+)\b")


def _normalize_amount(amount: str) -> float:
    return float(amount.replace(",", "."))


def _normalize_unit(unit: str) -> tuple[str, float] | None:
    return _UNIT_ALIASES.get(unit.lower())


def _clean_number(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 3)


def parse_quantity(value: str | None) -> tuple[int | float | None, str | None]:
    """Extract a normalized quantity value and unit from free text."""
    cleaned = clean_product_name(value)
    if not cleaned:
        return None, None

    multipack_match = _MULTIPACK_PATTERN.search(cleaned)
    if multipack_match:
        normalized_unit = _normalize_unit(multipack_match.group("unit"))
        if normalized_unit is not None:
            unit, multiplier = normalized_unit
            total = int(multipack_match.group("count")) * _normalize_amount(
                multipack_match.group("amount")
            )
            return _clean_number(total * multiplier), unit

    for match in _SINGLE_PATTERN.finditer(cleaned):
        normalized_unit = _normalize_unit(match.group("unit"))
        if normalized_unit is None:
            continue

        unit, multiplier = normalized_unit
        amount = _normalize_amount(match.group("amount")) * multiplier
        return _clean_number(amount), unit

    return None, None
