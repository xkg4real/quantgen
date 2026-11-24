"""Citation check: every cited source was among the evidence sent, with the same date, not later than as_of."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .schema import parse_as_of


@dataclass(frozen=True)
class CitationCheck:
    unknown: tuple        # source_ids that were not in the evidence sent
    wrong_date: tuple     # source_ids cited with a different as_of than the evidence carries
    late: tuple           # source_ids whose evidence is dated after the request's as_of
    missing: bool         # the task needs a citation and none was given

    @property
    def ok(self) -> bool:
        return not (self.unknown or self.wrong_date or self.late or self.missing)

    @property
    def reason_code(self) -> str | None:
        if self.late:
            return "after_as_of"
        if self.missing:
            return "no_evidence"
        if self.unknown or self.wrong_date:
            return "citation_unknown"
        return None


def check_citations(citations: Sequence[Mapping], evidence: Mapping[str, str], *, as_of: str | None = None,
                    required: bool = False) -> CitationCheck:
    """``evidence`` maps each source_id that was sent to the model onto its as_of date."""
    limit = parse_as_of(as_of) if as_of else None
    unknown, wrong_date, late = [], [], []
    for citation in citations:
        source_id = citation["source_id"]
        if source_id not in evidence:
            unknown.append(source_id)
            continue
        if parse_as_of(citation["as_of"]) != parse_as_of(evidence[source_id]):
            wrong_date.append(source_id)
        if limit is not None and parse_as_of(evidence[source_id]) > limit:
            late.append(source_id)
    return CitationCheck(tuple(unknown), tuple(wrong_date), tuple(late), required and not citations)
