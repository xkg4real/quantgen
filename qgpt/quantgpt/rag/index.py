"""Evidence index: SQLite FTS5 over documents and research cards, with an as_of filter.

A document is evidence only from the moment it was available (``as_of``). A
search made as of a date never returns a document dated later, whatever the
query says; the filter is in the SQL, not in the caller.

Korean has no spaces between a word and its particle, and common terms are two
syllables long, so text is indexed as overlapping two-character pieces for
Hangul and CJK runs and as whole lowercase words for Latin letters and digits.
The same split is applied to a query; query text never reaches FTS5 syntax.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable, Mapping

from ..checks import schema as S
from ..checks.schema import SchemaError, parse_as_of

KINDS = ("doc", "card")
_RUN = re.compile(r"[A-Za-z0-9]+(?:[._][A-Za-z0-9]+)*|[가-힣぀-ヿ一-鿿]+")
_CJK = re.compile(r"[가-힣぀-ヿ一-鿿]")
_DOC = S.obj({
    "source_id": S.string(max_len=128, pattern=r"[A-Za-z0-9][A-Za-z0-9_.:\-/]*"),
    "as_of": S.iso_date(),
    "kind": S.string(enum=KINDS),
    "title": S.string(max_len=400),
    "text": S.string(max_len=200_000),
})


@dataclass(frozen=True)
class Hit:
    source_id: str
    as_of: str
    kind: str
    title: str
    text: str
    score: float

    def citation(self) -> dict:
        return {"source_id": self.source_id, "as_of": self.as_of}


def pieces(text: str) -> list[str]:
    """Index terms of a text: two-character pieces of Hangul/CJK runs, lowercase Latin words."""
    out = []
    for run in _RUN.findall(text or ""):
        if _CJK.match(run):
            out.extend([run] if len(run) == 1 else [run[i:i + 2] for i in range(len(run) - 1)])
        else:
            out.append(run.lower())
    return out


def _hex(term: str) -> str:
    """A term as an FTS5-safe token (letters only), so no query can carry FTS5 operators."""
    return "t" + term.encode("utf-8").hex()


def _as_of_stamp(as_of: str) -> str:
    return parse_as_of(as_of).strftime("%Y-%m-%dT%H:%M:%S")


class EvidenceIndex:
    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path)
        self._db.execute("create table if not exists docs (source_id text primary key, as_of text not null, "
                         "as_of_key text not null, kind text not null, title text not null, text text not null, "
                         "sha256 text not null)")
        self._db.execute("create virtual table if not exists terms using fts5(source_id unindexed, body)")

    def close(self) -> None:
        self._db.close()

    def add(self, doc: Mapping) -> None:
        """Add one document. A source_id is written once; changed evidence needs a new source_id."""
        doc = dict(doc)
        _DOC(doc, "$")
        digest = hashlib.sha256((doc["title"] + "\n" + doc["text"]).encode("utf-8")).hexdigest()
        row = self._db.execute("select as_of, sha256 from docs where source_id = ?", (doc["source_id"],)).fetchone()
        if row is not None:
            if row != (doc["as_of"], digest):
                raise SchemaError(f"$.source_id: {doc['source_id']} is already indexed with other content or date")
            return
        with self._db:
            self._db.execute("insert into docs values (?, ?, ?, ?, ?, ?, ?)",
                             (doc["source_id"], doc["as_of"], _as_of_stamp(doc["as_of"]), doc["kind"], doc["title"],
                              doc["text"], digest))
            body = " ".join(_hex(t) for t in pieces(doc["title"] + " " + doc["text"]))
            self._db.execute("insert into terms (source_id, body) values (?, ?)", (doc["source_id"], body))

    def add_all(self, docs: Iterable[Mapping]) -> int:
        n = 0
        for doc in docs:
            self.add(doc)
            n += 1
        return n

    def __len__(self) -> int:
        return self._db.execute("select count(*) from docs").fetchone()[0]

    def version(self) -> str:
        """Hash of what is indexed (ids, dates, content hashes), independent of insertion order."""
        rows = self._db.execute("select source_id, as_of, sha256 from docs order by source_id").fetchall()
        return hashlib.sha256(repr(rows).encode("utf-8")).hexdigest()

    def evidence_map(self, hits: Iterable[Hit]) -> dict[str, str]:
        """source_id -> as_of of the hits that were sent to a model, for the citation check."""
        return {h.source_id: h.as_of for h in hits}

    def search(self, query: str, *, as_of: str, k: int = 5, kind: str | None = None) -> list[Hit]:
        """Best matches among documents available at ``as_of``; ties broken by source_id."""
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 50:
            raise SchemaError("k must be 1..50")
        if kind is not None and kind not in KINDS:
            raise SchemaError(f"kind must be one of {list(KINDS)}")
        limit = _as_of_stamp(as_of)
        terms = sorted(set(pieces(query)))
        if not terms:
            return []
        match = " OR ".join(_hex(t) for t in terms[:200])
        sql = ("select d.source_id, d.as_of, d.kind, d.title, d.text, bm25(terms) from terms "
               "join docs d on d.source_id = terms.source_id where terms match ? and d.as_of_key <= ?")
        args: list = [match, limit]
        if kind is not None:
            sql += " and d.kind = ?"
            args.append(kind)
        sql += " order by bm25(terms), d.source_id limit ?"
        args.append(k)
        return [Hit(r[0], r[1], r[2], r[3], r[4], -float(r[5])) for r in self._db.execute(sql, args)]


def card_document(qss_doc: Mapping) -> dict:
    """The searchable text of a recorded QSS card: hypothesis, decision and the gate's lines."""
    decision = qss_doc["decision"]
    text = "\n".join([qss_doc["hypothesis"], f"{decision['verdict']}: {decision['reason']}",
                      *qss_doc["evidence"]["lines"]])
    return {"source_id": f"card:{qss_doc['card_id']}", "as_of": qss_doc["provenance"]["created"], "kind": "card",
            "title": f"{qss_doc['card_id']} ({qss_doc['kind']})", "text": text}
