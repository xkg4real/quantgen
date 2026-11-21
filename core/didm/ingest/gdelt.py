"""GDELT 2.0 ingest assembly (no network here; fetchers are injected).

GDELT 2.0 publishes three 15-minute files (2015-02 onward): events export,
mentions, and GKG 2.0. ``lastupdate.txt`` lists "<size> <md5> <url>" for the newest
set. This module parses that list, checks each file's MD5, unzips it and turns
events / GKG rows into store rows with ``published_at`` (GDELT's own timestamp) and
``received_at`` (supplied by the caller).

What is kept: identifiers, timestamps, the source URL, CAMEO event codes, tone,
counts, themes/organisations/persons. Not kept: article text (GDELT does not ship
it; publishers own it).

Terms (GDELT About page, 2026-11-17 search summary; not legal advice): free for
academic, commercial and government use, redistribution allowed, and any use must
cite the GDELT Project and link to https://www.gdeltproject.org/ -- see ATTRIBUTION.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable

SOURCE_EVENTS = "gdelt-events2"
SOURCE_GKG = "gdelt-gkg2"
ATTRIBUTION = (
    "Contains data from the GDELT Project (https://www.gdeltproject.org/). "
    "The GDELT Project is an open platform for research and analysis of global society."
)
COVERAGE_START = "2015-02-18"  # GDELT 2.0 15-minute files (GKG 2.0 from 2015-02)

csv.field_size_limit(10_000_000)
_TITLE = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)


class GdeltError(ValueError):
    pass


@dataclass(frozen=True)
class FileRef:
    size: int
    md5: str
    url: str

    @property
    def kind(self) -> str:
        name = self.url.rsplit("/", 1)[-1].lower()
        if ".export." in name:
            return "events"
        if ".gkg." in name:
            return "gkg"
        if ".mentions." in name:
            return "mentions"
        return "unknown"

    @property
    def stamp(self) -> str:
        return self.url.rsplit("/", 1)[-1].split(".", 1)[0]


def parse_lastupdate(text: str) -> list[FileRef]:
    refs = []
    for line in text.strip().splitlines():
        parts = line.split()
        if len(parts) != 3:
            raise GdeltError(f"lastupdate line not '<size> <md5> <url>': {line!r}")
        size, md5, url = parts
        if not size.isdigit() or len(md5) != 32 or not url.startswith("http"):
            raise GdeltError(f"lastupdate line malformed: {line!r}")
        refs.append(FileRef(int(size), md5.lower(), url))
    if not refs:
        raise GdeltError("lastupdate is empty")
    return refs


def unzip_checked(blob: bytes, ref: FileRef) -> str:
    """Verify size and MD5 against lastupdate, then return the single CSV member as text."""
    if len(blob) != ref.size:
        raise GdeltError(f"{ref.url}: size {len(blob)} != {ref.size}")
    if hashlib.md5(blob).hexdigest() != ref.md5:  # noqa: S324 - integrity check GDELT publishes
        raise GdeltError(f"{ref.url}: md5 mismatch")
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise GdeltError(f"{ref.url}: expected one member, got {len(names)}")
        return zf.read(names[0]).decode("utf-8", errors="replace")


def gdelt_time(stamp: str) -> datetime:
    """'YYYYMMDDHHMMSS' (UTC) -> aware datetime."""
    if len(stamp) != 14 or not stamp.isdigit():
        raise GdeltError(f"bad GDELT timestamp {stamp!r}")
    return datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def _rows(text: str, width: int, name: str):
    for n, row in enumerate(csv.reader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE), 1):
        if not row or row == [""]:
            continue
        if len(row) != width:
            raise GdeltError(f"{name} line {n}: {len(row)} columns, expected {width}")
        yield row


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _title(extras: str) -> str | None:
    m = _TITLE.search(extras or "")
    return html.unescape(m.group(1)).strip()[:300] if m else None


def parse_events(text: str, received_at: datetime) -> list[dict]:
    """GDELT 2.0 events export (61 columns) -> store rows."""
    out = []
    for r in _rows(text, 61, "events"):
        published = gdelt_time(r[59])  # DATEADDED
        out.append({
            "source_id": SOURCE_EVENTS,
            "item_id": r[0],  # GLOBALEVENTID
            "kind": "gdelt_event",
            "published_at": published,
            "received_at": received_at,
            "valid_at": published,
            "payload": {
                "event_date": r[1],
                "actor1_country": r[7], "actor2_country": r[17],
                "event_code": r[26], "event_base_code": r[27], "event_root_code": r[28],
                "quad_class": r[29],
                "goldstein": _float(r[30]),
                "num_mentions": int(r[31] or 0), "num_sources": int(r[32] or 0),
                "num_articles": int(r[33] or 0),
                "avg_tone": _float(r[34]),
                "action_geo_country": r[53],
                "source_url": r[60],
            },
        })
    return out


def parse_gkg(text: str, received_at: datetime) -> list[dict]:
    """GDELT GKG 2.0 (27 columns) -> store rows (no article text)."""
    out = []
    for r in _rows(text, 27, "gkg"):
        published = gdelt_time(r[1])  # DATE
        tone = r[15].split(",") if r[15] else []
        out.append({
            "source_id": SOURCE_GKG,
            "item_id": r[0],  # GKGRECORDID
            "kind": "gdelt_gkg",
            "published_at": published,
            "received_at": received_at,
            "valid_at": published,
            "payload": {
                "source_common_name": r[3],
                "document_identifier": r[4],
                "themes": [t for t in r[7].split(";") if t][:50],
                "persons": [p for p in r[11].split(";") if p][:50],
                "organizations": [o for o in r[13].split(";") if o][:50],
                "tone": _float(tone[0]) if tone else None,
                "positive": _float(tone[1]) if len(tone) > 1 else None,
                "negative": _float(tone[2]) if len(tone) > 2 else None,
                "word_count": int(tone[6]) if len(tone) > 6 and tone[6].isdigit() else None,
                "page_title": _title(r[26]),
            },
        })
    return out


def ingest_latest(fetch_text: Callable[[str], str], fetch_bytes: Callable[[str], bytes],
                  lastupdate_url: str, received_at: datetime,
                  kinds: tuple[str, ...] = ("events", "gkg")) -> tuple[list[dict], list[FileRef]]:
    """Fetch the newest 15-minute set through the injected functions and parse it."""
    if received_at.tzinfo is None:
        raise GdeltError("received_at must be timezone-aware")
    refs = [r for r in parse_lastupdate(fetch_text(lastupdate_url)) if r.kind in kinds]
    rows: list[dict] = []
    for ref in refs:
        text = unzip_checked(fetch_bytes(ref.url), ref)
        rows += parse_events(text, received_at) if ref.kind == "events" else parse_gkg(text, received_at)
    return rows, refs


BASE_URL = "http://data.gdeltproject.org/gdeltv2/"
FILE_SUFFIX = {"events": "export.CSV.zip", "gkg": "gkg.csv.zip"}


def stamps_for_day(day: date) -> list[str]:
    """The 96 fifteen-minute file stamps of one UTC day."""
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return [(start + timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S") for i in range(96)]


def previous_stamp(stamp: str) -> str:
    return (gdelt_time(stamp) - timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")


def file_url(stamp: str, kind: str) -> str:
    gdelt_time(stamp)
    return f"{BASE_URL}{stamp}.{FILE_SUFFIX[kind]}"


def unzip_crc_checked(blob: bytes, url: str) -> str:
    """For files not listed in lastupdate (no published MD5): check the zip's own CRCs."""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise GdeltError(f"{url}: CRC error in {bad}")
        names = zf.namelist()
        if len(names) != 1:
            raise GdeltError(f"{url}: expected one member, got {len(names)}")
        return zf.read(names[0]).decode("utf-8", errors="replace")


def ingest_stamps(fetch_optional: Callable[[str], bytes | None], stamps: list[str], received_at: datetime,
                  kinds: tuple[str, ...] = ("events",)) -> tuple[list[dict], list[str], list[str]]:
    """Fetch given 15-minute stamps; ``fetch_optional`` returns None for a file not (yet) published.

    Returns (rows, fetched file names, missing file names). Integrity = zip CRC
    (``md5_verified`` False in each row, since only lastupdate publishes MD5s).
    """
    if received_at.tzinfo is None:
        raise GdeltError("received_at must be timezone-aware")
    rows, fetched, missing = [], [], []
    for stamp in stamps:
        for kind in kinds:
            url = file_url(stamp, kind)
            blob = fetch_optional(url)
            name = url.rsplit("/", 1)[-1]
            if blob is None:
                missing.append(name)
                continue
            text = unzip_crc_checked(blob, url)
            got = parse_events(text, received_at) if kind == "events" else parse_gkg(text, received_at)
            for r in got:
                r["payload"]["md5_verified"] = False
            rows += got
            fetched.append(name)
    return rows, fetched, missing
