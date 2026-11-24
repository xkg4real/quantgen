"""Official filing sources for DIDM (owner answer Q3, 2026-11-18): SEC EDGAR and OpenDART.

No network here. ``data.didm.edgar`` and ``data.didm.opendart`` fetch; these
functions turn their JSON into point-in-time store rows. Only filing metadata is
kept (form, accession / receipt number, times, company id, title); filing text is
not stored.

Timestamps:
* EDGAR ``acceptanceDateTime`` is the SEC acceptance time (UTC "Z" in the
  submissions JSON). That is the public-availability time, so it is ``published_at``.
  If a filing has none, ``published_at`` = filingDate 00:00 New York time and
  ``time_precision`` = "date" (same lag rule as OpenDART).
* Older filings (before the ~1,000 in ``filings.recent``) sit in ``filings.files``
  (D6, 2026-11-24): ``edgar_history_files`` picks the files for a date range and
  ``edgar_history_rows`` reads one, checking its filing count against the index.
* OpenDART ``rcept_dt`` is a date only (YYYYMMDD). ``published_at`` = that date at
  00:00 Asia/Seoul and ``time_precision`` = "date"; PREREG_V0 section 5 then applies
  the conservative +1 trading day lag for historical use.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Mapping

SOURCE_EDGAR = "sec-edgar"
SOURCE_OPENDART = "opendart"
KST = timezone(timedelta(hours=9))
_CIK = re.compile(r"^\d{1,10}$")
_HISTORY_NAME = re.compile(r"^CIK(\d{10})-submissions-\d{3}\.json$")
NEW_YORK = ZoneInfo("America/New_York")
DEFAULT_FORMS = ("8-K", "6-K", "10-Q", "10-K")


class FilingError(ValueError):
    pass


def _aware(received_at: datetime) -> None:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise FilingError("received_at must be timezone-aware")


def _edgar_published(accepted: Any, filing_date: Any, accession: str) -> tuple[datetime, str]:
    """acceptanceDateTime (second precision) or, when it is missing, filingDate at 00:00 New York time
    with time_precision "date" (PREREG_V0 section 5 then applies the +1 trading day lag)."""
    if accepted not in (None, ""):
        try:
            published = datetime.fromisoformat(str(accepted).replace("Z", "+00:00"))
        except ValueError:
            raise FilingError(f"{accession}: bad acceptanceDateTime {accepted!r}") from None
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        return published, "second"
    try:
        day = date.fromisoformat(str(filing_date))
    except ValueError:
        raise FilingError(f"{accession}: no acceptanceDateTime and bad filingDate {filing_date!r}") from None
    return datetime(day.year, day.month, day.day, tzinfo=NEW_YORK), "date"


def _edgar_column_rows(cols: Mapping[str, Any], submissions: Mapping[str, Any], received_at: datetime,
                       forms: tuple[str, ...] | None, where: str) -> list[dict]:
    cik = str(submissions.get("cik", "")).lstrip("0") or "0"
    if not _CIK.match(cik):
        raise FilingError(f"bad CIK {submissions.get('cik')!r}")
    acc = cols.get("accessionNumber") or []
    for col in ("form", "filingDate", "acceptanceDateTime"):
        if len(cols.get(col) or []) != len(acc):
            raise FilingError(f"{where}.{col} length differs from accessionNumber")
    items = cols.get("items") or []
    docs = cols.get("primaryDocument") or []
    out = []
    for i, accession in enumerate(acc):
        form = cols["form"][i]
        if forms is not None and form not in forms:
            continue
        published, precision = _edgar_published(cols["acceptanceDateTime"][i], cols["filingDate"][i], accession)
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
                "filing_date": cols["filingDate"][i],
                "items": items[i] if i < len(items) else "",
                "primary_document": docs[i] if i < len(docs) else "",
                "time_precision": precision,
            },
        })
    return out


def edgar_rows(submissions: Mapping[str, Any], received_at: datetime,
               forms: tuple[str, ...] | None = DEFAULT_FORMS) -> list[dict]:
    """data.sec.gov submissions JSON (``filings.recent`` column arrays) -> store rows."""
    _aware(received_at)
    recent = (submissions.get("filings") or {}).get("recent")
    if not isinstance(recent, Mapping):
        raise FilingError("submissions JSON has no filings.recent")
    return _edgar_column_rows(recent, submissions, received_at, forms, "filings.recent")


def edgar_history_files(submissions: Mapping[str, Any], start: date | None = None,
                        end: date | None = None) -> list[dict]:
    """The older submissions files (``filings.files``) whose filingFrom..filingTo overlaps start..end.

    Each entry: {"name", "filing_count", "filing_from", "filing_to"}. Names are checked against the
    CIK so only data.sec.gov submissions files of this company can be requested.
    """
    cik = str(submissions.get("cik", "")).lstrip("0") or "0"
    if not _CIK.match(cik):
        raise FilingError(f"bad CIK {submissions.get('cik')!r}")
    files = (submissions.get("filings") or {}).get("files") or []
    if not isinstance(files, list):
        raise FilingError("filings.files is not a list")
    out = []
    for f in files:
        name = str((f or {}).get("name") or "")
        m = _HISTORY_NAME.match(name)
        if not m or int(m.group(1)) != int(cik):
            raise FilingError(f"unexpected submissions file name {name!r}")
        try:
            lo, hi = date.fromisoformat(f["filingFrom"]), date.fromisoformat(f["filingTo"])
            count = int(f["filingCount"])
        except (KeyError, TypeError, ValueError):
            raise FilingError(f"{name}: bad filingFrom/filingTo/filingCount") from None
        if hi < lo or count < 0:
            raise FilingError(f"{name}: inconsistent range or count")
        if (end is not None and lo > end) or (start is not None and hi < start):
            continue
        out.append({"name": name, "filing_count": count, "filing_from": lo.isoformat(), "filing_to": hi.isoformat()})
    return out


def edgar_history_rows(submissions: Mapping[str, Any], file_entry: Mapping[str, Any],
                       payload: Mapping[str, Any], received_at: datetime,
                       forms: tuple[str, ...] | None = DEFAULT_FORMS) -> list[dict]:
    """One older submissions file (column arrays at the top level) -> store rows.

    The file must hold exactly ``filing_count`` filings; company name and tickers come from the
    main submissions JSON (the older files do not repeat them).
    """
    _aware(received_at)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("accessionNumber"), list):
        raise FilingError(f"{file_entry.get('name')}: no accessionNumber column")
    if len(payload["accessionNumber"]) != int(file_entry["filing_count"]):
        raise FilingError(f"{file_entry.get('name')}: {len(payload['accessionNumber'])} filings, "
                          f"index says {file_entry['filing_count']}")
    return _edgar_column_rows(payload, submissions, received_at, forms, str(file_entry.get("name")))


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
