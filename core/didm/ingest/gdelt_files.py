"""DS-10: read GDELT 2.0 files the owner downloaded, and pick rows for event windows. No network here.

Input is the file name and its bytes (a ``YYYYMMDDHHMMSS.export.CSV[.zip]`` events file or a
``YYYYMMDDHHMMSS.gkg.csv[.zip]`` GKG file, as GDELT names them); tools/didm/collect_daily ``--gdelt-file``
reads the bytes from disk. Rows come from ``core.didm.ingest.gdelt.parse_events`` / ``parse_gkg`` (the same
columns the 15-minute collector keeps: identifiers, times, URL, title, codes, tone, tags -- no article text),
plus three payload fields: ``citation`` (GDELT's terms require a citation and link on any use;
www.gdeltproject.org/about.html, read 2026-11-24), ``file_stamp`` and ``md5_verified``.

Column positions follow the existing parser (events 61 columns, GKG 27). The GDELT codebooks that define
them are PDFs on data.gdeltproject.org, which is not reachable from this environment: **column definitions
not re-checked against the codebooks** (see docs/didm/GDELT_FILES_V0.md).

``available_at`` = the file's 15-minute stamp (PREREG_V0 5.1: a GDELT file is public at its stamp).
``select`` keeps rows in a time window and, for GKG, tags the entities whose aliases appear in the row's
organizations or page title (a minimal exact match; the linking rule itself is DIDM_DEV's).
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

from core.didm.ingest import gdelt

CITATION = "GDELT Project, https://www.gdeltproject.org/"
_NAME = re.compile(r"^(\d{14})\.(export\.csv|gkg\.csv)(\.zip)?$", re.IGNORECASE)
MIN_ALIAS = 3


def kind_and_stamp(name: str) -> tuple[str, str]:
    m = _NAME.fullmatch(name or "")
    if not m:
        raise gdelt.GdeltError("not a GDELT 2.0 events or GKG file name (YYYYMMDDHHMMSS.export.CSV / .gkg.csv)")
    gdelt.gdelt_time(m.group(1))
    return ("events" if m.group(2).lower() == "export.csv" else "gkg"), m.group(1)


def _text(name: str, data: bytes, md5: str | None) -> str:
    if md5 is not None and hashlib.md5(data).hexdigest() != md5.lower():  # noqa: S324 - GDELT's own check
        raise gdelt.GdeltError(f"{name}: md5 mismatch")
    if name.lower().endswith(".zip"):
        return gdelt.unzip_crc_checked(data, name)
    return data.decode("utf-8", errors="replace")


def read_file(name: str, data: bytes, received_at: datetime, *, md5: str | None = None) -> list[dict]:
    """One downloaded file -> store rows. ``md5`` from GDELT's file list, if the owner has it."""
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise gdelt.GdeltError("received_at must be timezone-aware")
    kind, stamp = kind_and_stamp(name)
    text = _text(name, data, md5)
    rows = gdelt.parse_events(text, received_at) if kind == "events" else gdelt.parse_gkg(text, received_at)
    for r in rows:
        r["payload"].update(citation=CITATION, file_stamp=stamp, md5_verified=md5 is not None)
    return rows


def available_at(row: Mapping) -> datetime:
    """When the row was public: its file's stamp (falls back to published_at for rows without one)."""
    stamp = (row.get("payload") or {}).get("file_stamp")
    return gdelt.gdelt_time(stamp) if stamp else row["published_at"]


@dataclass(frozen=True)
class Selected:
    row: dict
    entity_ids: tuple[str, ...]      # GKG: entities whose alias matched; events: ()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def select(rows: Iterable[dict], start: datetime, end: datetime, *, aliases: Mapping[str, str] | None = None,
           countries: Iterable[str] | None = None, require_entity: bool = False) -> list[Selected]:
    """Rows whose available_at is within [start, end].

    ``aliases`` (alias -> entity_id, aliases of at least MIN_ALIAS characters): a GKG row is tagged with every
    entity whose alias equals one of its organizations or appears as whole words in its page title (case and
    spacing ignored). ``require_entity`` drops GKG rows with no tag. ``countries`` keeps events whose actor or
    action country is in the set (events carry no organization names).
    """
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise gdelt.GdeltError("start and end must be timezone-aware with start <= end")
    table = {}
    for alias, entity in (aliases or {}).items():
        a = _norm(alias)
        if len(a) < MIN_ALIAS:
            raise gdelt.GdeltError("aliases must have at least 3 characters")
        table[a] = entity
    patterns = {a: re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)") for a in table}
    wanted = {c.upper() for c in countries} if countries is not None else None
    out = []
    for row in rows:
        if not start <= available_at(row) <= end:
            continue
        p = row["payload"]
        if row["source_id"] == gdelt.SOURCE_GKG:
            orgs = {_norm(o) for o in p.get("organizations") or []}
            title = _norm(p.get("page_title") or "")
            ents = sorted({table[a] for a in table if a in orgs or patterns[a].search(title)})
            if require_entity and not ents:
                continue
            out.append(Selected(row, tuple(ents)))
        elif row["source_id"] == gdelt.SOURCE_EVENTS:
            if wanted is not None and not ({p.get("actor1_country"), p.get("actor2_country"),
                                             p.get("action_geo_country")} & wanted):
                continue
            out.append(Selected(row, ()))
    return out
