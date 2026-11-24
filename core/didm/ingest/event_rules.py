"""DS-9: filing -> DIDM event type hints (14 types + none), from EDGAR 8-K item codes and OpenDART report names.

Hints, not the scorer: a filing's subject is its filer, and the item code or report name says what kind of
event it is, but not whether the news is good or bad (STAGE2_EVENT_SAMPLE_PLAN_2026-11-24.md sections 4 and 7).
The tables below are the only copy in code; docs/didm/EVENT_RULES_V0.md carries the same tables and
tests/didm_event_rules_acceptance.py fails when they differ. No network, no data.didm import.

Rules (docs/didm/EVENT_RULES_V0.md section 1):
* One filing can carry several types (an 8-K with items 2.02 and 5.02 is earnings and management). They are
  returned without repeats in PRIORITY order; ``primary`` is the first. A filing with no mapped item or name
  is ``none``; ``none`` never sits next to a real type.
* 7.01 (Regulation FD), 8.01 (other events) and 9.01 (exhibits) are ``none``: the code alone does not say what
  happened (body text would be needed, which is not stored).
* An amendment (8-K/A, OpenDART report names with a correction marker) is a separate event with
  ``amendment`` True; linking it to the original filing is a DIDM_DEV rule.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from core.didm.llm.schema import EventType as E

# Highest first. Types a filing cannot carry (macro, geopolitics, crypto) are absent on purpose.
PRIORITY = (E.EARNINGS, E.MERGERS_ACQUISITIONS, E.MANAGEMENT, E.REGULATION_LITIGATION, E.SUPPLY_CHAIN)

# SEC Form 8-K item number -> type. Items not listed are none. (Item numbers: SEC Form 8-K; sec.gov not opened
# from this environment -- see the document.)
EDGAR_ITEMS: Mapping[str, E] = {
    "1.03": E.REGULATION_LITIGATION,   # bankruptcy or receivership
    "2.01": E.MERGERS_ACQUISITIONS,    # completion of acquisition or disposition of assets
    "2.02": E.EARNINGS,                # results of operations and financial condition
    "3.01": E.REGULATION_LITIGATION,   # notice of delisting or failure to satisfy a listing rule
    "4.01": E.REGULATION_LITIGATION,   # changes in registrant's certifying accountant
    "4.02": E.EARNINGS,                # non-reliance on previously issued financial statements (restatement)
    "5.02": E.MANAGEMENT,              # departure/election of directors or certain officers
}
EDGAR_NONE_ITEMS = ("1.01", "1.02", "1.04", "1.05", "5.07", "7.01", "8.01", "9.01")   # documented as none

# OpenDART report_nm substring (spaces removed before matching) -> type. Checked against the real list: none
# yet (unverified, the document marks each row).
OPENDART_NAMES: Mapping[str, E] = {
    "잠정실적": E.EARNINGS,
    "(잠정)실적": E.EARNINGS,           # "영업(잠정)실적": the parenthesis breaks "잠정실적"
    "매출액또는손익구조": E.EARNINGS,
    "합병": E.MERGERS_ACQUISITIONS,
    "회사분할": E.MERGERS_ACQUISITIONS,
    "주식교환": E.MERGERS_ACQUISITIONS,
    "영업양수": E.MERGERS_ACQUISITIONS,
    "타법인주식및출자증권취득": E.MERGERS_ACQUISITIONS,
    "대표이사변경": E.MANAGEMENT,
    "소송": E.REGULATION_LITIGATION,
    "횡령": E.REGULATION_LITIGATION,
    "배임": E.REGULATION_LITIGATION,
    "상장폐지": E.REGULATION_LITIGATION,
    "거래정지": E.REGULATION_LITIGATION,
    "단일판매ㆍ공급계약체결": E.SUPPLY_CHAIN,
}
# Correction markers OpenDART puts in front of a report name (unverified list).
OPENDART_AMENDMENT = ("[기재정정]", "[첨부정정]", "[정정명령부과]", "[정정제출요구]")

_ITEM = re.compile(r"^\d\.\d{2}$")


class EventRuleError(ValueError):
    pass


@dataclass(frozen=True)
class EventHint:
    types: tuple[E, ...]          # PRIORITY order, no repeats; (NONE,) when nothing maps
    amendment: bool
    matched: tuple[str, ...]      # the item codes or name parts that matched (identifiers, no free text)

    @property
    def primary(self) -> E:
        return self.types[0]


def _ordered(found: set[E]) -> tuple[E, ...]:
    return tuple(t for t in PRIORITY if t in found) or (E.NONE,)


def edgar_hint(form: str, items: str) -> EventHint:
    """8-K / 8-K/A ``form`` and the submissions ``items`` field ("2.02,9.01") -> hint. Other forms are none."""
    if not isinstance(form, str) or not isinstance(items, str):
        raise EventRuleError("form and items must be strings")
    base = form.strip().upper()
    amendment = base.endswith("/A")
    if base.removesuffix("/A") != "8-K":
        return EventHint((E.NONE,), amendment, ())
    codes = [c.strip() for c in items.split(",") if c.strip()]
    bad = [c for c in codes if not _ITEM.fullmatch(c)]
    if bad:
        raise EventRuleError("8-K items must look like 2.02")
    matched = tuple(c for c in codes if c in EDGAR_ITEMS)
    return EventHint(_ordered({EDGAR_ITEMS[c] for c in matched}), amendment, matched)


def opendart_hint(report_nm: str) -> EventHint:
    """OpenDART ``report_nm`` -> hint (spaces ignored; correction marker -> amendment)."""
    if not isinstance(report_nm, str):
        raise EventRuleError("report_nm must be a string")
    name = re.sub(r"\s+", "", report_nm)
    amendment = any(name.startswith(m) for m in OPENDART_AMENDMENT)
    matched = tuple(part for part in OPENDART_NAMES if part in name)
    return EventHint(_ordered({OPENDART_NAMES[p] for p in matched}), amendment, matched)


def hint_for_row(row: Mapping) -> EventHint | None:
    """A store row from core.didm.ingest.filings -> hint, or None for other sources."""
    payload = row.get("payload") or {}
    if row.get("source_id") == "sec-edgar":
        return edgar_hint(str(payload.get("form", "")), str(payload.get("items", "")))
    if row.get("source_id") == "opendart":
        return opendart_hint(str(payload.get("report_nm", "")))
    return None
