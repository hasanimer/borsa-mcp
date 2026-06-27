from __future__ import annotations

import re


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_number(value: str | int | float | None) -> float | None:
    if value is None or isinstance(value, (int, float)):
        return None if value is None else float(value)
    text = clean_text(value).replace("%", "")
    if not text or text in {"-", "—"}:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(re.sub(r"[^0-9.\-]", "", text))
    except ValueError:
        return None
