"""Offline overseas-stock name search for the chart (owner request UI-16).

The bundled list (`core/market/data/overseas_symbols.json`) is a curated subset with
KIS exchange codes; it is not a market master. Search is local: no request leaves
the computer until the user chooses a result and the chart loads it.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

from core.search_text import best_score, normal

DATA = Path(__file__).parent / "data" / "overseas_symbols.json"
EXCHANGE_NAMES = {"NAS": "NASDAQ", "NYS": "NYSE", "AMS": "NYSE Arca/American", "HKS": "HKEX", "TSE": "TSE"}


@dataclass(frozen=True)
class SymbolEntry:
    code: str
    exchange: str
    name_en: str
    name_ko: str

    def label(self, language="ko"):
        name = self.name_ko if language == "ko" else self.name_en
        return f"{name} · {self.code} · {EXCHANGE_NAMES.get(self.exchange, self.exchange)}"


@lru_cache(maxsize=1)
def entries() -> tuple[SymbolEntry, ...]:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    return tuple(SymbolEntry(row["code"], row["exchange"], row["name_en"], row["name_ko"])
                 for row in payload["symbols"])


def search(query, limit=8) -> tuple[SymbolEntry, ...]:
    """Best matches first: exact code, then name/code prefixes, then substrings."""
    wanted = normal(query)
    if not wanted:
        return ()
    scored = []
    for order, entry in enumerate(entries()):
        code_score = best_score(wanted, (entry.code,))
        name = best_score(wanted, (entry.name_en, entry.name_ko, *entry.name_ko.split()))
        scores = [s for s in (code_score, name) if s is not None]
        if scores:
            # An exact or prefix code hit outranks a name substring.
            scored.append((min(scores), 0 if code_score is not None and code_score <= 1 else 1, order, entry))
    return tuple(entry for *_, entry in sorted(scored, key=lambda row: row[:3])[:max(0, int(limit))])


def lookup(code, exchange=""):
    code = str(code).strip().upper()
    for entry in entries():
        if entry.code == code and (not exchange or entry.exchange == exchange):
            return entry
    return None
