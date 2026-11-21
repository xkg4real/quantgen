"""DIDM point-in-time (bitemporal) store, V0 (DIDM 10.3).

* Append-only. A correction is a new row for the same (source_id, item_id) with a
  later received_at; nothing is overwritten or deleted.
* Two times per row: ``valid_at`` (what the fact is about: article published_at, or
  an observation date) and ``received_at`` (when *we* received it; transaction time).
  ``published_at`` is required; ``received_at`` is required and must carry a timezone.
* ``as_of(t)`` returns, for every item, the latest version with received_at <= t,
  ordered deterministically. Rows received after t can never change the answer,
  so the same "as of" query returns the same records every time.

Stdlib only (sqlite3). The database lives outside the repository, in a folder the
caller passes in (the owner's user-data folder). No network, no clock reads: the
caller supplies received_at.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    published_at TEXT NOT NULL,
    valid_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    UNIQUE (source_id, item_id, received_at, payload_sha256)
);
CREATE INDEX IF NOT EXISTS items_received ON items (received_at);
CREATE INDEX IF NOT EXISTS items_key ON items (source_id, item_id, received_at);
"""


class StoreError(ValueError):
    pass


@dataclass(frozen=True)
class StoredItem:
    source_id: str
    item_id: str
    kind: str
    published_at: str
    valid_at: str
    received_at: str
    payload: dict
    payload_sha256: str


def utc_iso(value: str | datetime, name: str) -> str:
    """Normalise a timezone-aware time to 'YYYY-MM-DDTHH:MM:SS.ffffff+00:00'."""
    if value is None:
        raise StoreError(f"{name} is required")
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise StoreError(f"{name} is not ISO 8601") from None
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise StoreError(f"{name} must be a timezone-aware time")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class PointInTimeStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._db = sqlite3.connect(str(self.path))
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "PointInTimeStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def append(self, *, source_id: str, item_id: str, kind: str, published_at,
               received_at, payload: Mapping[str, Any], valid_at=None) -> bool:
        """Append one version; False only for an identical normalized record already stored.

        A matching version key with different kind/publication/validity metadata is an
        input conflict, not a duplicate. Refuse it without changing history. A correction
        can be supplied with its later received_at; no receipt time is invented here.
        """
        for name, val in (("source_id", source_id), ("item_id", item_id), ("kind", kind)):
            if not isinstance(val, str) or not val:
                raise StoreError(f"{name} must be a non-empty string")
        pub = utc_iso(published_at, "published_at")
        rec = utc_iso(received_at, "received_at")
        valid = utc_iso(valid_at, "valid_at") if valid_at is not None else pub
        if not isinstance(payload, Mapping):
            raise StoreError("payload must be a mapping")
        body = canonical_json(payload)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        cur = self._db.execute(
            "INSERT OR IGNORE INTO items (source_id, item_id, kind, published_at, valid_at,"
            " received_at, payload, payload_sha256) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, item_id, kind, pub, valid, rec, body, digest),
        )
        if cur.rowcount == 0:
            existing = self._db.execute(
                "SELECT kind, published_at, valid_at, payload FROM items"
                " WHERE source_id = ? AND item_id = ? AND received_at = ? AND payload_sha256 = ?",
                (source_id, item_id, rec, digest),
            ).fetchone()
            if existing != (kind, pub, valid, body):
                self._db.rollback()
                raise StoreError("conflicting metadata for an already stored version")
        self._db.commit()
        return cur.rowcount == 1

    def append_many(self, rows: Iterable[Mapping[str, Any]]) -> int:
        return sum(1 for row in rows if self.append(**row))

    def as_of(self, when, *, source_id: str | None = None, kind: str | None = None,
              valid_from=None, valid_to=None) -> list[StoredItem]:
        """Latest version of each item with received_at <= when, in a fixed order."""
        t = utc_iso(when, "as_of")
        sql = (
            "SELECT i.source_id, i.item_id, i.kind, i.published_at, i.valid_at, i.received_at,"
            " i.payload, i.payload_sha256 FROM items i"
            " WHERE i.received_at <= ? AND i.seq = ("
            "   SELECT j.seq FROM items j WHERE j.source_id = i.source_id AND j.item_id = i.item_id"
            "   AND j.received_at <= ? ORDER BY j.received_at DESC, j.payload_sha256 DESC LIMIT 1)"
        )
        args: list[Any] = [t, t]
        if source_id is not None:
            sql += " AND i.source_id = ?"
            args.append(source_id)
        if kind is not None:
            sql += " AND i.kind = ?"
            args.append(kind)
        if valid_from is not None:
            sql += " AND i.valid_at >= ?"
            args.append(utc_iso(valid_from, "valid_from"))
        if valid_to is not None:
            sql += " AND i.valid_at <= ?"
            args.append(utc_iso(valid_to, "valid_to"))
        sql += " ORDER BY i.valid_at, i.source_id, i.item_id"
        return [
            StoredItem(r[0], r[1], r[2], r[3], r[4], r[5], json.loads(r[6]), r[7])
            for r in self._db.execute(sql, args)
        ]

    def history(self, source_id: str, item_id: str) -> list[StoredItem]:
        rows = self._db.execute(
            "SELECT source_id, item_id, kind, published_at, valid_at, received_at, payload,"
            " payload_sha256 FROM items WHERE source_id = ? AND item_id = ?"
            " ORDER BY received_at, payload_sha256", (source_id, item_id))
        return [StoredItem(r[0], r[1], r[2], r[3], r[4], r[5], json.loads(r[6]), r[7]) for r in rows]
