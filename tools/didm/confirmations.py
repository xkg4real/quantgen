"""Storage for DIDM market-confirmation side records (DS-8, main decision C, 2026-11-24).

The line format, its checks and the append/as-of rules belong to DIDM_DEV
(``core/didm/models/confirmation_log.py``: ``dumps`` / ``loads`` / ``append`` / ``as_of``); this module only
puts those lines into the point-in-time store and reads them back. It is the file-opening side that
core/didm stays out of.

* File: ``<data-dir>/didm_derived.sqlite``, a second PointInTimeStore next to the collected-data store
  ``didm_store.sqlite`` (derived values can be rebuilt; collection_status counts only collected data).
* Row: ``source_id`` "didm-confirmation-v0", ``kind`` "market_confirmation",
  ``item_id`` = ``record_id@rule_version``, ``published_at`` = ``known_at``, ``valid_at`` = the scored record's
  ``published_at``, payload ``{"line": dumps(entry)}``. ``received_at`` = the time the wrapper wrote the row;
  in operation that is known_at (rule 1), and it is kept separate so the read rule below can be checked.
* Rule 1: known_at is when the verdict was actually written. A live store refuses a known_at more than
  ``MAX_SKEW`` away from the write time, so a verdict is never written into the past. A replay of past
  periods (research re-computation) goes to a separate store object with ``replay=True``: source_id
  "didm-confirmation-v0-replay", any known_at, never read by the live store.
* Rule 2: for one (record_id, rule_version, known_at) a second, different line is refused; the same line
  again is a no-op. DIDM_DEV's ``append`` rules (order of knowledge, one judgement per record, no change of
  a final verdict under one rule version) are applied to the record's stored history before writing.
* Read rule (DIDM_DEV advice): ``as_of(when)`` uses only rows whose later of known_at and the store's
  received_at is at or before ``when``, then ``confirmation_log.as_of`` picks the verdict.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable

from core.didm.models import confirmation_log as cl
from core.didm.store import PointInTimeStore

DERIVED_FILE = "didm_derived.sqlite"
SOURCE_ID = cl.SCHEMA                      # "didm-confirmation-v0"
REPLAY_SOURCE_ID = cl.SCHEMA + "-replay"
KIND = "market_confirmation"
MAX_SKEW = timedelta(minutes=5)
FAR_FUTURE = "9999-12-31T00:00:00+00:00"


class ConfirmationStoreError(ValueError):
    pass


def _utc(t: datetime) -> datetime:
    return t.astimezone(timezone.utc)


class ConfirmationStore:
    def __init__(self, store: PointInTimeStore, *, replay: bool = False,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.store, self.replay, self.clock = store, replay, clock
        self.source_id = REPLAY_SOURCE_ID if replay else SOURCE_ID

    @classmethod
    def open(cls, data_dir: str | Path, **kwargs) -> "ConfirmationStore":
        return cls(PointInTimeStore(Path(data_dir) / DERIVED_FILE), **kwargs)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "ConfirmationStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- reading -------------------------------------------------------------------------------------------
    def _rows(self, record_id: str | None = None) -> list[tuple[datetime, cl.Entry]]:
        """(received_at, entry) for every stored version, in write order."""
        items = {i.item_id for i in self.store.as_of(FAR_FUTURE, source_id=self.source_id)}
        if record_id is not None:
            items = {i for i in items if i.rsplit("@", 1)[0] == record_id}
        out = []
        for item_id in sorted(items):
            for row in self.store.history(self.source_id, item_id):
                out.append((datetime.fromisoformat(row.received_at), cl.loads(row.payload["line"])))
        out.sort(key=lambda pair: pair[0])
        return out

    def entries(self, record_id: str | None = None) -> list[cl.Entry]:
        return [entry for _, entry in self._rows(record_id)]

    def visible(self, when: datetime, record_id: str | None = None) -> list[cl.Entry]:
        """Entries whose later of known_at and stored received_at is at or before ``when``."""
        if not isinstance(when, datetime) or when.tzinfo is None:
            raise ConfirmationStoreError("when must be a timezone-aware datetime")
        return [e for received, e in self._rows(record_id) if max(_utc(e.known_at), received) <= _utc(when)]

    def as_of(self, record_id: str, when: datetime, *, rule: str | None = None) -> cl.Entry | None:
        return cl.as_of(self.visible(when, record_id), record_id, when, rule=rule)

    def status_as_of(self, record_id: str, when: datetime, *, rule: str | None = None):
        return cl.status_as_of(self.visible(when, record_id), record_id, when, rule=rule)

    # -- writing -------------------------------------------------------------------------------------------
    def append(self, entry: cl.Entry, *, record_published_at: datetime) -> bool:
        """Write one verdict. True if written, False if the identical line was already there."""
        if not isinstance(entry, cl.Entry):
            raise ConfirmationStoreError("only entries built by core.didm.models.confirmation_log")
        line = cl.dumps(entry)
        item_id = f"{entry.record_id}@{entry.rule_version}"
        with self.store.write_transaction():
            now = _utc(self.clock())
            if not self.replay and abs(_utc(entry.known_at) - now) > MAX_SKEW:
                raise ConfirmationStoreError("known_at must be the time of writing (use replay=True for re-computation)")
            for row in self.store.history(self.source_id, item_id):
                old = cl.loads(row.payload["line"])
                if old.known_at == entry.known_at:
                    if row.payload["line"] == line:
                        return False
                    raise ConfirmationStoreError("a different line for the same record, rule version and known_at")
            cl.append(self.entries(entry.record_id), entry)       # DIDM_DEV's rules on the stored history
            return self.store.append(source_id=self.source_id, item_id=item_id, kind=KIND,
                                     published_at=entry.known_at, received_at=now, valid_at=record_published_at,
                                     payload={"line": line})


def append_many(target: ConfirmationStore, pairs: Iterable[tuple[cl.Entry, datetime]]) -> int:
    return sum(1 for entry, published in pairs if target.append(entry, record_published_at=published))
