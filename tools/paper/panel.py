"""Run the CLI referees of tools.debate on one review round of a paper and record each result
(spec 2026-10-23 section 5.3 steps 10-11).

Every run builds its own disposable, secret-free bundle (tools.paper.bundle.make_bundle) and writes REVIEW_BRIEF.md
into it, so the command-line prompt stays short. Every selected referee gets a record, review/round<k>_<name>.json
(review/fidelity_<name>.json for the Korean fidelity review), whatever happened: a quota, a missing CLI, a timeout, a
crash, an empty reply, a reply without both `## Major` and `## Minor` headings, or a REJECT / NOT FAITHFUL verdict
with an empty `## Major` is recorded as such, and tools.paper.index.review_gate reads it as REVIEW_INCOMPLETE, never as
"no objections". From round 2 on the bundle also holds every report of the previous round and the authors' response.
The Claude referee runs as an agent on a --bundle-only bundle (which first files a pending Claude record, so a stale
one never counts) and files its report with --record, which applies the same checks and takes only the name claude.

CLI, from the repository root:
  python -m tools.paper.panel <paper_dir> <round_k> [--only NAME,...] [--fidelity] [--allow-private]
  python -m tools.paper.panel <paper_dir> <round_k> --bundle-only [--fidelity] [--allow-private]
  python -m tools.paper.panel <paper_dir> <round_k> --record NAME REPORT_MD [--fidelity]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from tools import debate
from tools.paper import bundle

PROMPT = ("Read REVIEW_BRIEF.md in the current directory and follow it exactly. Reply with the Markdown report only. "
          + debate.NO_SHELL)

REFEREE_BRIEF = """# Referee brief (round <K>)

<NO_SHELL>

You are an anonymous referee for a refereed quantitative-finance journal. This folder is a read-only copy of one
manuscript and its evidence: en/paper_en.tex (the manuscript; ko/ holds the Korean edition when it exists),
common/*.tex (shared equations and tables), study/numbers.json (every number the text prints, with its source), the
study code (study/*.py), the repository modules it calls (code/), the pre-registration (scope/prereg.json), the run
MANIFEST.json and results.json, refs.yaml and refs.bib, and claims.yaml (what each citation is claimed to support,
and where). Do not modify any file.

Check the correctness of derivations and estimators; the validity of the inference (dependence, multiplicity, power,
leakage); that every number traces to numbers.json and the study code; that each cited source supports its claim
(claims.yaml); that each claim is labelled honestly as exploratory, pre-specified on historical data or confirmatory,
as scope/prereg.json registered it; and that the AI-assistance statement and the limits of the study are stated.
<ROUND2>
Severity: an issue is Major when fixing it would change a result, a conclusion or the provenance of a number.
Everything else is Minor.

Reply in Markdown, in exactly this shape, and leave a heading empty when it has no issues:

# Verdict: ACCEPT | ACCEPT WITH CHANGES | REJECT

## Major

- M1: <the issue, with the file and the paragraph id or line>

## Minor

- m1: <the issue>
"""

ROUND2 = """
This is round <K>. review/round<P>_<referee>.md holds each referee's round <P> report, and review/response_round<P>.md
the authors' response to them. For each Major issue in those reports, decide whether the response and the revised
manuscript resolve it. Repeat every unresolved one under Major with its original id; do not repeat resolved ones.
"""

FIDELITY_BRIEF = """# Fidelity brief (Korean edition)

<NO_SHELL>

This folder holds the English edition en/paper_en.tex and the Korean edition ko/paper_ko.tex of one paper. Their
paragraphs are aligned by the "% id: <section>-<n>" comment on the line before each paragraph. Do not modify any file.

For every aligned pair, check that the Korean says what the English says: signs and directions, negations,
qualifiers and hedges, units and scales, claims of significance, and the claim labels (exploratory, pre-specified,
confirmatory). Numbers appear only as \\qnum{key} macros in both editions, so compare the keys.

Then read claims.yaml: for each row, the Korean paragraph with that paragraph_id must make the claim that the row's
support passage backs, no stronger and no weaker, and cite the same source_key.

Severity: Major when the Korean states something the English does not, drops a qualifier that changes a claim, or
claims more than claims.yaml supports. Minor for style and terminology.

Reply in Markdown, in exactly this shape, and leave a heading empty when it has no issues:

# Verdict: FAITHFUL | FAITHFUL WITH CHANGES | NOT FAITHFUL

## Major

- M1: <paragraph id: the discrepancy>

## Minor

- m1: <paragraph id: the issue>
"""


_REJECTED = re.compile(r"(?im)^#{1,6}\s*Verdict\b[:\s*]*(REJECT|NOT FAITHFUL)\b")


def _stem(round_k: int, name: str, fidelity: bool) -> str:
    return f"fidelity_{name}" if fidelity else f"round{round_k}_{name}"


def record(paper_dir: Path, round_k: int, name: str, status: str, report_md: str, *, fidelity: bool = False,
           reset_at: str | None = None, version: str | None = None, raw: Path | None = None,
           note: str = "") -> Path:
    """Write review/<stem>.md and review/<stem>.json for one reviewer (`note`: why a CLI referee failed, filed in the
    json and, when the report is empty, in the .md). An "ok" with an empty report is "empty"; one without both
    `## Major` and `## Minor` headings, or whose verdict is REJECT / NOT FAITHFUL while `## Major` is empty, is
    "error": none of them is ever read as no objections."""
    if status == "ok" and not report_md.strip():
        status = "empty"
    elif status == "ok" and not debate.has_report_headings(report_md):
        status = "error"
    parsed = debate.parse_report(report_md) if status == "ok" else {"major": [], "minor": []}
    if status == "ok" and not parsed["major"] and _REJECTED.search(report_md):
        status = "error"                              # the objections sit somewhere the parser does not read
    review = paper_dir / "review"
    review.mkdir(parents=True, exist_ok=True)
    stem = _stem(round_k, name, fidelity)
    shown = report_md if report_md.strip() or not note else note + "\n"      # an empty report still says why
    (review / f"{stem}.md").write_text(shown, encoding="utf-8", newline="\n")
    out = review / f"{stem}.json"
    out.write_text(json.dumps({"name": name, "status": status, "reset_at": reset_at, "version": version,
                               "raw": str(raw) if raw else None, "note": note, "major": parsed["major"],
                               "minor": parsed["minor"]},
                              indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return out


def make_round_bundle(paper_dir: Path, round_k: int, *, fidelity: bool = False, allow_private: bool = False,
                      for_cli: bool = True) -> Path:
    """A fresh bundle with REVIEW_BRIEF.md and, from round 2 on, every report of the previous round and the authors'
    response to it. The brief of a CLI referee opens with debate.NO_SHELL; the Claude agent's (for_cli=False) does
    not, because that agent runs shell commands to get the bundle and to file its report."""
    prev = paper_dir / "review" / f"response_round{round_k - 1}.md"
    if not fidelity and round_k > 1 and not prev.is_file():
        raise ValueError(f"{prev} is missing: round {round_k} needs the authors' response to round {round_k - 1}")
    where = bundle.make_bundle(paper_dir, round_k, allow_private=allow_private)
    if fidelity:
        brief = FIDELITY_BRIEF
    else:
        brief = REFEREE_BRIEF.replace("<ROUND2>", ROUND2 if round_k > 1 else "")
        brief = brief.replace("<K>", str(round_k)).replace("<P>", str(round_k - 1))
        if round_k > 1:
            (where / "review").mkdir(exist_ok=True)
            for src in [prev, *sorted((paper_dir / "review").glob(f"round{round_k - 1}_*.md"))]:
                shutil.copy2(src, where / "review" / src.name)
    brief = brief.replace("<NO_SHELL>\n\n", debate.NO_SHELL + "\n\n" if for_cli else "")
    (where / "REVIEW_BRIEF.md").write_text(brief, encoding="utf-8", newline="\n")
    return where


def run_panel(paper_dir: Path, round_k: int, *, only: list[str] | None = None, fidelity: bool = False,
              allow_private: bool = False) -> dict[str, str]:
    """Run the selected CLI referees one after another (all of DEFAULT_REFEREES, or only the agy ones for the
    fidelity review); returns {name: recorded status}."""
    refs = [r for r in debate.DEFAULT_REFEREES if (not fidelity or r.kind == "agy") and (not only or r.name in only)]
    if only and len(refs) != len(set(only)):
        known = [r.name for r in debate.DEFAULT_REFEREES if not fidelity or r.kind == "agy"]
        raise ValueError(f"unknown referee in {only}; known here: {known}")
    where = make_round_bundle(paper_dir, round_k, fidelity=fidelity, allow_private=allow_private)
    out_dir = paper_dir / "review" / "raw" / ("fidelity" if fidelity else f"round{round_k}")
    out_dir.mkdir(parents=True, exist_ok=True)
    statuses = {}
    for ref in refs:
        try:
            res = debate.run_referee(ref, where, PROMPT, out_dir)
            path = record(paper_dir, round_k, ref.name, res.status, res.report_md, fidelity=fidelity,
                          reset_at=res.reset_at, version=res.version, raw=res.raw_path, note=res.note)
        except Exception as exc:                      # a crashed runner still leaves a record, never silence
            path = record(paper_dir, round_k, ref.name, "error", f"runner error: {type(exc).__name__}: {exc}\n",
                          fidelity=fidelity)
        statuses[ref.name] = json.loads(path.read_text(encoding="utf-8"))["status"]
    return statuses


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(prog="python -m tools.paper.panel", description=__doc__.split("\n\n")[0])
    parser.add_argument("paper_dir", type=Path)
    parser.add_argument("round_k", type=int)
    parser.add_argument("--only", default="", help="comma-separated referee names")
    parser.add_argument("--fidelity", action="store_true", help="the Korean fidelity review")
    parser.add_argument("--allow-private", action="store_true", help="only when the owner allowed it for this paper")
    parser.add_argument("--bundle-only", action="store_true", help="print a fresh bundle path and stop")
    parser.add_argument("--record", nargs=2, metavar=("NAME", "REPORT_MD"), help="file an agent referee's report")
    args = parser.parse_args(argv)
    try:
        if args.bundle_only:
            # Until --record claude overwrites it, the gate reads this round's Claude review as REVIEW_INCOMPLETE.
            record(args.paper_dir, args.round_k, "claude", "error",
                   "pending: the Claude referee has not filed its report\n", fidelity=args.fidelity)
            print(make_round_bundle(args.paper_dir, args.round_k, fidelity=args.fidelity,
                                    allow_private=args.allow_private, for_cli=False))
        elif args.record:
            name, report = args.record
            if name != "claude":
                raise ValueError(f"--record files only the Claude referee's report; {name} is recorded by run_panel")
            path = record(args.paper_dir, args.round_k, name, "ok", Path(report).read_text(encoding="utf-8"),
                          fidelity=args.fidelity)
            print(path, json.loads(path.read_text(encoding="utf-8"))["status"])
        else:
            only = [n for n in args.only.split(",") if n] or None
            print(json.dumps(run_panel(args.paper_dir, args.round_k, only=only, fidelity=args.fidelity,
                                       allow_private=args.allow_private)))
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
