"""OpenDART market-wide filing list for DIDM (owner answer Q3, 2026-11-18).

Reuses the existing data.krx.opendart_client (same OPENDART_API_KEY, shared
retrying session, key kept out of errors). DIDM needs every company's filings for
a date range, so this calls list.json without corp_code and pages through it.
OpenDART limits such a range to three months. Parsing: core.didm.ingest.filings.
"""
from __future__ import annotations

from data.krx.opendart_client import OpenDARTClient

PAGE_COUNT = 100
MAX_PAGES = 200


def fetch_listing(bgn_de: str, end_de: str, *, client: OpenDARTClient | None = None) -> list[dict]:
    """All filings received between two dates (YYYYMMDD). Returns raw list.json payloads."""
    client = client or OpenDARTClient()
    pages = []
    for page in range(1, MAX_PAGES + 1):
        payload = client._get("list.json", {  # noqa: SLF001 - same module family, keeps key handling in one place
            "bgn_de": bgn_de, "end_de": end_de, "page_no": page, "page_count": PAGE_COUNT})
        pages.append(payload)
        if page >= int(payload.get("total_page") or 1):
            break
    return pages
