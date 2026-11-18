"""Official filing sources for DIDM (owner answer Q3, 2026-11-18): SEC EDGAR and OpenDART.

No network here. ``data.didm.edgar`` and ``data.didm.opendart`` fetch; these
functions turn their JSON into point-in-time store rows. Only filing metadata is
kept (form, accession / receipt number, times, company id, title); filing text is
not stored.

Timestamps:
* EDGAR ``acceptanceDateTime`` is the SEC acceptance time (UTC "Z" in the
  submissions JSON). That is the public-availability time, so it is ``published_at``.
* OpenDART ``rcept_dt`` is a date only (YYYYMMDD). ``published_at`` = that date at
  00:00 Asia/Seoul and ``time_precision`` = "date"; PREREG_V0 section 5 then applies
  the conservative +1 trading day lag for historical use.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

SOURCE_EDGAR = "sec-edgar"
SOURCE_OPENDART = "opendart"
KST = timezone(timedelta(hours=9))
_CIK = re.compile(r"^\d{1,10}$")


class FilingError(ValueError):
    pass


def _aware(received_at: datetime) -> None:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise FilingError("received_at must be timezone-aware")


def edgar_rows(submissions: Mapping[str, Any], received_at: datetime,
               forms: tuple[str, ...] | None = ("8-K", "6-K", "10-Q", "10-K")) -> list[dict]:
    """data.sec.gov submissions JSON (``filings.recent`` column arrays) -> store rows."""
    _aware(received_at)
    cik = str(submissions.get("cik", "")).lstrip("0") or "0"
    if not _CIK.match(cik):
        raise FilingError(f"bad CIK {submissions.get('cik')!r}")
    recent = (submissions.get("filings") or {}).get("recent")
    if not isinstance(recent, Mapping):
        raise FilingError("submissions JSON has no filings.recent")
    acc = recent.get("accessionNumber") or []
    columns = ("form", "filingDate", "acceptanceDateTime", "primaryDocument", "items")
    for col in columns[:3]:
        if len(recent.get(col) or []) != len(acc):
            raise FilingError(f"filings.recent.{col} length differs from accessionNumber")
    out = []
    for i, accession in enumerate(acc):
        form = recent["form"][i]
        if forms is not None and form not in forms:
            continue
        accepted = recent["acceptanceDateTime"][i]
        try:
            published = datetime.fromisoformat(str(accepted).replace("Z", "+00:00"))
        except ValueError:
            raise FilingError(f"{accession}: bad acceptanceDateTime {accepted!r}") from None
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        items = recent.get("items") or []
        docs = recent.get("primaryDocument") or []
        out.append({
            "source_id": SOURCE_EDGAR,
            "item_id": accession,
            "kind": "filing",
            "published_at": published,
            "received_at": received_at,
            "valid_at": published,
            "payload": {
                "cik": cik,
                "company": submissions.get("name"),
                "tickers": list(submissions.get("tickers") or []),
                "form": form,
                "filing_date": recent["filingDate"][i],
                "items": items[i] if i < len(items) else "",
                "primary_document": docs[i] if i < len(docs) else "",
                "time_precision": "second",
            },
        })
    return out


def opendart_rows(listing: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """OpenDART list.json payload -> store rows."""
    _aware(received_at)
    rows = listing.get("list")
    if rows is None:
        return []  # status 013: no data
    if not isinstance(rows, list):
        raise FilingError("list.json payload 'list' is not a list")
    out = []
    for raw in rows:
        receipt = str(raw.get("rcept_no") or "")
        day = str(raw.get("rcept_dt") or "")
        if not (receipt.isdigit() and len(day) == 8 and day.isdigit()):
            raise FilingError(f"bad receipt {receipt!r} / date {day!r}")
        published = datetime.strptime(day, "%Y%m%d").replace(tzinfo=KST)
        out.append({
            "source_id": SOURCE_OPENDART,
            "item_id": receipt,
            "kind": "filing",
            "published_at": published,
            "received_at": received_at,
            "valid_at": published,
            "payload": {
                "corp_code": str(raw.get("corp_code") or ""),
                "corp_name": str(raw.get("corp_name") or "").strip(),
                "stock_code": str(raw.get("stock_code") or "").strip(),
                "corp_cls": str(raw.get("corp_cls") or ""),
                "report_nm": str(raw.get("report_nm") or "").strip(),
                "filer": str(raw.get("flr_nm") or "").strip(),
                "remark": str(raw.get("rm") or ""),
                "time_precision": "date",
            },
        })
    return out
