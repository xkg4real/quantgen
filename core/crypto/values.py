"""Provider numbers: a missing value stays missing (§10 NEW-M6-14, NEW-M6-22; the Upbit daily part of D12-03).

Shared by the provider parsers (data/crypto) and the analytics (core/crypto), so both
layers agree on what counts as missing.
"""
from __future__ import annotations

import math
from typing import Optional


def number_or_none(value) -> Optional[float]:
    """A finite number of any sign, or None when it is missing, blank or not a number."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def price_or_none(value) -> Optional[float]:
    """A price: finite and positive, else None. A missing price must never become 0.0."""
    x = number_or_none(value)
    return x if x is not None and x > 0 else None
