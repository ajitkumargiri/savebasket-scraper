"""Product name normalization helpers."""

from __future__ import annotations

import re
import unicodedata

_UNIT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bkilograms?\b|\bkilogram\b|\bkilos?\b|\bkg\b", "kg"),
    (r"\bgrams?\b|\bgram\b|\bgr\b|\bg\b", "g"),
    (r"\bmillilit(?:er|re)s?\b|\bmilliliter\b|\bml\b", "ml"),
    (r"\bcentilit(?:er|re)s?\b|\bcentiliter\b|\bcl\b", "cl"),
    (r"\bliters?\b|\blitres?\b|\bliter\b|\blitre\b|\bl\b", "l"),
    (r"\bstuks?\b|\bstukken\b|\bstuk\b|\bstk\b|\bst\b|\bpcs?\b|\bpieces?\b", "pc"),
)


def clean_product_name(value: str | None) -> str:
    """Normalize a product name into a stable search and matching form."""
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", value).strip().lower()
    if not text:
        return ""

    text = text.replace("&", " and ")
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"[/_-]+", " ", text)
    text = re.sub(r"(?<=\d)\s*[x×]\s*(?=\d)", " x ", text)

    for pattern, replacement in _UNIT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"(\d+(?:\.\d+)?)\s*(kg|g|ml|cl|l|pc)\b", r"\1 \2", text)
    text = re.sub(r"[^\w\s.%]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
