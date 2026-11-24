"""Rule-based entity linking, first version: a point-in-time alias dictionary matched against the
headline, the first paragraph and the body. No model, no network, no clock.

Precision comes first (PREREG_V0 3, Stage 1: linking precision >= 0.95, recall >= 0.80; "a false link
trades the wrong security, a missed link only loses signal"):

* an alias is used only inside its validity dates (a renamed company, a recycled ticker);
* an alias that points at two entities on that date links to neither;
* a Latin-script alias must stand alone as a word; a short or all-capitals alias (a ticker) must also
  match case exactly;
* a Korean alias must not continue a longer Korean or alphanumeric word on its left (particles on the
  right are fine: "삼성전자는").

The dictionary itself is supplied by the caller (built from filings and exchange lists by the data
side). The mention position gives the registered pre-calibration relevance value (PREREG_V0 4: headline
100, first paragraph 80, body 40, tag only 20), which is a feature of the relevance model and not the
relevance score.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from core.didm.llm.schema import TargetKind

# PREREG_V0 4, "관련성 보정 전 대체 규칙" (registered)
MENTION_SCORE = {"title": 100, "lead": 80, "body": 40, "tag": 20}
SHORT_ALIAS = 4                    # Latin aliases this short, or all capitals, match case exactly


class LinkError(ValueError):
    pass


@dataclass(frozen=True)
class Alias:
    alias: str
    entity_id: str
    target_kind: TargetKind
    valid_from: date
    valid_to: date | None = None           # None = still valid; the end day is included

    def __post_init__(self) -> None:
        if not isinstance(self.alias, str) or len(unicodedata.normalize("NFKC", self.alias).strip()) < 2:
            raise LinkError("an alias needs at least two characters")
        if self.target_kind not in (TargetKind.FIRM, TargetKind.MACRO):
            raise LinkError("an alias points at a firm or a macro target")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise LinkError("valid_to is before valid_from")

    def valid_on(self, day: date) -> bool:
        return self.valid_from <= day and (self.valid_to is None or day <= self.valid_to)


@dataclass(frozen=True)
class Link:
    article_id: str
    entity_id: str
    target_kind: TargetKind
    where: str                    # best position found: title > lead > body > tag
    mention_score: int
    mentions: int


def _clean(text: str | None) -> str:
    return unicodedata.normalize("NFKC", text or "")


def _is_hangul(ch: str) -> bool:
    return "가" <= ch <= "힣"


def _pattern(alias: str) -> re.Pattern:
    text = unicodedata.normalize("NFKC", alias).strip()
    body = re.escape(text)
    if any(_is_hangul(ch) for ch in text):
        # not the tail of a longer Korean or alphanumeric word; anything may follow (particles)
        return re.compile(rf"(?<![0-9A-Za-z가-힣]){body}")
    exact_case = len(text) <= SHORT_ALIAS or (text.isupper() and text.isalpha())
    flags = 0 if exact_case else re.IGNORECASE
    return re.compile(rf"(?<![0-9A-Za-z_]){body}(?![0-9A-Za-z_])", flags)


class Linker:
    def __init__(self, aliases: Iterable[Alias]):
        self._aliases = tuple(aliases)
        for a in self._aliases:
            if not isinstance(a, Alias):
                raise LinkError("the dictionary must hold Alias entries")
        self._patterns = [(a, _pattern(a.alias)) for a in self._aliases]

    def _active(self, day: date) -> list[tuple[Alias, re.Pattern]]:
        live = [(a, p) for a, p in self._patterns if a.valid_on(day)]
        owners: dict[str, set[str]] = {}
        for a, _ in live:
            owners.setdefault(unicodedata.normalize("NFKC", a.alias).strip().casefold(), set()).add(a.entity_id)
        # an alias claimed by two entities on this day is ambiguous: use it for neither
        return [(a, p) for a, p in live
                if len(owners[unicodedata.normalize("NFKC", a.alias).strip().casefold()]) == 1]

    def link(self, *, article_id: str, as_of: date, title: str, lead: str | None = None, body: str | None = None,
             tags: Iterable[str] = ()) -> list[Link]:
        """Links for one article, using the dictionary as it stood on ``as_of`` (the article's day)."""
        if not isinstance(as_of, date):
            raise LinkError("as_of must be a date")
        parts = (("title", _clean(title)), ("lead", _clean(lead)), ("body", _clean(body)),
                 ("tag", " | ".join(_clean(t) for t in tags)))
        found: dict[str, dict] = {}
        for alias, pattern in self._active(as_of):
            for where, text in parts:
                n = len(pattern.findall(text)) if text else 0
                if not n:
                    continue
                slot = found.setdefault(alias.entity_id, {"kind": alias.target_kind, "where": where, "n": 0})
                slot["n"] += n
                if MENTION_SCORE[where] > MENTION_SCORE[slot["where"]]:
                    slot["where"] = where
        return [Link(article_id, entity, slot["kind"], slot["where"], MENTION_SCORE[slot["where"]], slot["n"])
                for entity, slot in sorted(found.items())]


def link_pairs(links: Iterable[Link]) -> set[tuple[str, str]]:
    """(article_id, entity_id) pairs, the shape core/didm/eval/metrics.linking_scores compares."""
    return {(link.article_id, link.entity_id) for link in links}
