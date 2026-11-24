"""What the owner's DIDM point-in-time store holds, per source: counts, date spans, days without receipts,
and how much of the Stage 2 sample window (2015-2024, DIDM_DEV) is covered. Read only.

    python -m tools.didm.collection_status --data-dir "%LOCALAPPDATA%\\QUANTGEN\\didm"
    python -m tools.didm.collection_status --data-dir <folder> --since 2026-11-17 --json

Opens <data-dir>/didm_store.sqlite in SQLite read-only mode (never creates or changes it). Prints only
source names, kinds, counts and dates: no payload values, titles, URLs or keys.

* items = distinct (source_id, item_id); versions = stored rows (corrections and re-fetches included).
* valid span = earliest/latest ``valid_at`` (article time or observation date).
* received span = earliest/latest ``received_at`` (when the collector ran).
* missing receive days = UTC days between --since (default: first receipt of that source) and the last
  receipt overall on which that source got nothing. Sources fetched on demand (ALFRED, ECOS, history
  back-fills) are expected to have gaps; GDELT/Kalshi daily runs should not.
* sample years = for each year of --sample (default 2015-2024), items whose valid_at falls in it.

``--by-entity`` (D13, 2026-11-24) adds, per source/kind, how items spread over entities: the company or
series identifier each source already stores (``ENTITY_FIELDS``: CIK, OpenDART corp_code, news symbols,
Kalshi ticker, ALFRED series, ECOS stat code). Identifiers only, never titles or values. Each item counts
once per entity it is tagged with (a news article on two tickers counts for both). GDELT and other sources
without an entity field are left out. Use: compare items per entity-year between large and small companies
(SAMPLE_EXPANSION_FEASIBILITY section 4).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from core.didm.ingest import terms

STORE_FILE = "didm_store.sqlite"
SAMPLE = (2015, 2024)
MAX_LISTED_GAPS = 10
ENTITY_FIELDS = {          # source_id -> payload field holding the entity identifier (str or list of str)
    "sec-edgar": "cik", "opendart": "corp_code", "alpaca-news": "symbols", "massive-news": "tickers",
    "kalshi": "ticker", "alfred": "series_id", "ecos": "stat_code",
}
LISTED_ENTITIES = 5


class StatusError(RuntimeError):
    pass


def open_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise StatusError(f"no store at {path} (run tools.didm.collect_daily first)")
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def _day(iso: str) -> date:
    return date.fromisoformat(iso[:10])


def _gaps(days: set[date], first: date, last: date) -> list[date]:
    out, d = [], first
    while d <= last:
        if d not in days:
            out.append(d)
        d += timedelta(days=1)
    return out


def summarize(db: sqlite3.Connection, *, since: date | None = None,
              sample: tuple[int, int] = SAMPLE) -> dict:
    """Per (source_id, kind) summary. Pure read of the items table."""
    rows = db.execute(
        "SELECT source_id, kind, COUNT(DISTINCT item_id), COUNT(*), MIN(valid_at), MAX(valid_at),"
        " MIN(received_at), MAX(received_at) FROM items GROUP BY source_id, kind ORDER BY source_id, kind"
    ).fetchall()
    overall_last = db.execute("SELECT MAX(received_at) FROM items").fetchone()[0]
    sources = []
    for source_id, kind, items, versions, vmin, vmax, rmin, rmax in rows:
        days = {_day(r[0]) for r in db.execute(
            "SELECT DISTINCT substr(received_at, 1, 10) FROM items WHERE source_id = ? AND kind = ?",
            (source_id, kind))}
        first = max(since, _day(rmin)) if since else _day(rmin)
        gaps = _gaps(days, first, _day(overall_last)) if first <= _day(overall_last) else []
        years = dict(db.execute(
            "SELECT substr(valid_at, 1, 4) AS y, COUNT(DISTINCT item_id) FROM items"
            " WHERE source_id = ? AND kind = ? AND y BETWEEN ? AND ? GROUP BY y",
            (source_id, kind, f"{sample[0]:04d}", f"{sample[1]:04d}")).fetchall())
        sources.append({
            "source_id": source_id, "kind": kind, "items": items, "versions": versions,
            "valid_from": vmin[:10], "valid_to": vmax[:10],
            "received_from": rmin[:10], "received_to": rmax[:10],
            "receive_days": len(days),
            "missing_receive_days": len(gaps),
            "missing_examples": [d.isoformat() for d in gaps[:MAX_LISTED_GAPS]],
            "sample_years": {str(y): years.get(f"{y:04d}", 0) for y in range(sample[0], sample[1] + 1)},
            "research_excluded": terms.is_research_excluded(source_id),
        })
    return {"store_last_received": overall_last[:10] if overall_last else None,
            "sample": list(sample), "sources": sources}


def _entities(source_id: str, payload: dict) -> list[str]:
    raw = payload.get(ENTITY_FIELDS[source_id])
    values = raw if isinstance(raw, list) else [raw]
    return sorted({str(v)[:40] for v in values if isinstance(v, (str, int)) and str(v).strip()})


def _median(values: list[int]) -> float:
    v = sorted(values)
    mid = len(v) // 2
    return float(v[mid]) if len(v) % 2 else (v[mid - 1] + v[mid]) / 2


def by_entity(db: sqlite3.Connection) -> list[dict]:
    """Per (source_id, kind): entity count and items per entity, from the latest version of each item."""
    marks = ",".join("?" for _ in ENTITY_FIELDS)
    rows = db.execute(
        f"SELECT i.source_id, i.kind, i.valid_at, i.payload FROM items i WHERE i.source_id IN ({marks})"
        " AND i.seq = (SELECT MAX(j.seq) FROM items j WHERE j.source_id = i.source_id AND j.item_id = i.item_id)",
        tuple(ENTITY_FIELDS)).fetchall()
    groups: dict[tuple[str, str], dict[str, dict]] = {}
    untagged: dict[tuple[str, str], int] = {}
    for source_id, kind, valid_at, body in rows:
        try:
            payload = json.loads(body)
        except ValueError:
            payload = {}
        ents = _entities(source_id, payload) if isinstance(payload, dict) else []
        if not ents:
            untagged[(source_id, kind)] = untagged.get((source_id, kind), 0) + 1
        g = groups.setdefault((source_id, kind), {})
        day = valid_at[:10]
        for e in ents:
            st = g.setdefault(e, {"entity": e, "items": 0, "first": day, "last": day})
            st["items"] += 1
            st["first"], st["last"] = min(st["first"], day), max(st["last"], day)
    out = []
    for (source_id, kind) in sorted(set(groups) | set(untagged)):
        ents = sorted(groups.get((source_id, kind), {}).values(), key=lambda x: (-x["items"], x["entity"]))
        for e in ents:
            years = (date.fromisoformat(e["last"]) - date.fromisoformat(e["first"])).days / 365.25
            e["items_per_year"] = round(e["items"] / max(years, 1.0), 3)
        counts = [e["items"] for e in ents]
        out.append({
            "source_id": source_id, "kind": kind, "entities": len(ents),
            "research_excluded": terms.is_research_excluded(source_id),
            "untagged_items": untagged.get((source_id, kind), 0),
            "items_per_entity": ({"min": min(counts), "median": _median(counts), "max": max(counts)}
                                 if counts else None),
            "per_entity": ents,
        })
    return out


def entity_lines(groups: list[dict]) -> list[str]:
    if not groups:
        return ["by entity: no source with an entity field"]
    out = []
    for g in groups:
        spread = g["items_per_entity"]
        head = (f"by entity {g['source_id']} / {g['kind']}: entities {g['entities']}, untagged items "
                f"{g['untagged_items']}")
        if g["research_excluded"]:
            head += " [EXCLUDED from research]"
        if spread:
            head += f", items per entity min {spread['min']} median {spread['median']:g} max {spread['max']}"
        out.append(head)
        ents = g["per_entity"]
        shown = ents if len(ents) <= 2 * LISTED_ENTITIES else ents[:LISTED_ENTITIES] + ents[-LISTED_ENTITIES:]
        for e in shown:
            out.append(f"  {e['entity']}: items {e['items']}, {e['first']}..{e['last']}, per year {e['items_per_year']:g}")
        if len(shown) < len(ents):
            out.append(f"  ({len(ents) - len(shown)} more in --json)")
    return out


def lines(summary: dict) -> list[str]:
    if not summary["sources"]:
        return ["store is empty"]
    lo, hi = summary["sample"]
    out = [f"store last receipt {summary['store_last_received']}; sample years {lo}-{hi}"]
    for s in summary["sources"]:
        covered = sum(1 for n in s["sample_years"].values() if n)
        out.append(
            f"{s['source_id']} / {s['kind']}: items {s['items']} (versions {s['versions']}), "
            f"valid {s['valid_from']}..{s['valid_to']}, received {s['received_from']}..{s['received_to']} "
            f"on {s['receive_days']} days, missing {s['missing_receive_days']} days"
            + (f" (e.g. {', '.join(s['missing_examples'][:3])})" if s["missing_examples"] else "")
            + f", sample years with data {covered}/{hi - lo + 1}"
            + (f" [EXCLUDED from research: {terms.NOTICE}]" if s["research_excluded"] else ""))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DIDM store summary (read only, counts and dates only)")
    ap.add_argument("--data-dir", required=True, help="the folder given to tools.didm.collect_daily")
    ap.add_argument("--since", metavar="YYYY-MM-DD", help="count missing receive days from this day")
    ap.add_argument("--sample", nargs=2, type=int, default=list(SAMPLE), metavar=("FROM", "TO"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--by-entity", action="store_true",
                    help="also items per company/series identifier (D13; identifiers only, no titles or values)")
    args = ap.parse_args(argv)
    since = date.fromisoformat(args.since) if args.since else None
    if args.sample[0] > args.sample[1]:
        ap.error("--sample FROM must not be after TO")
    try:
        db = open_read_only(Path(args.data_dir).expanduser() / STORE_FILE)
    except StatusError as exc:
        print(exc, file=sys.stderr)
        return 1
    try:
        summary = summarize(db, since=since, sample=tuple(args.sample))
        if args.by_entity:
            summary["by_entity"] = by_entity(db)
    finally:
        db.close()
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
    else:
        text = lines(summary)
        if args.by_entity:
            text += entity_lines(summary["by_entity"])
        print("\n".join(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
