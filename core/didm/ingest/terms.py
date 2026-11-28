"""Sources whose terms keep their data out of DIDM research samples, training and the product (main decision A,
2026-11-24, after the owner-approved reading of the vendors' terms; SAMPLE_EXPANSION_FEASIBILITY section 9).

One place for the list. The collector prints NOTICE when it runs one of these, collection_status marks their
rows, and DIDM code that builds a sample filters with ``research_rows`` (no data.didm import; pure functions).
tests/didm_terms_guard_acceptance.py fails when this list and the documents' "연구 표본 제외" line differ.
Not legal advice: the reasons quote the terms as read on 2026-11-24.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# source_id -> why (short). Reserved ids for collectors that do not exist yet keep the rule when they arrive.
RESEARCH_EXCLUDED: Mapping[str, str] = {
    "alpaca-news": "Alpaca Terms: personal and non-commercial use; commercial use needs notice and written consent",
    "massive-news": "Massive individual and market data terms: personal non-commercial use; no AI/ML training (5(g))",
    "krx-listing-datagokr": "data.go.kr KRX listing: KOGL type 4, no commercial use, no redistribution (reserved id)",
    "krx-openapi": "KRX Open API terms: non-commercial use only, no third-party provision (reserved id)",
}
NOTICE = "개인·비상업 약관: 연결 확인용, 연구 표본·학습 불가"
DOC_LINE_PREFIX = "약관상 연구 표본 제외 (source_id):"


def excluded_sources() -> frozenset[str]:
    return frozenset(RESEARCH_EXCLUDED)


def is_research_excluded(source_id: str) -> bool:
    return isinstance(source_id, str) and source_id.strip().casefold() in RESEARCH_EXCLUDED


def _source(row: Any) -> str:
    if isinstance(row, Mapping):
        source_id = row.get("source_id")
    else:
        source_id = getattr(row, "source_id", None)
    return source_id.strip() if isinstance(source_id, str) else ""


def research_rows(rows: Iterable[Any]) -> list:
    """Rows (store dicts or StoredItem) a research sample may use: every row whose source_id is not excluded.
    A row without a source_id is kept out too (cannot be shown to be allowed)."""
    return [row for row in rows if (source_id := _source(row)) and not is_research_excluded(source_id)]


def doc_line() -> str:
    """The line the documents carry, in a fixed order, so a test can compare it with this list."""
    ids = ", ".join(f"`{s}`" for s in sorted(RESEARCH_EXCLUDED))
    return f"{DOC_LINE_PREFIX} {ids} — {NOTICE}"
