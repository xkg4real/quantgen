"""The claims gate (spec 5.2 step 3): every citation in the literature, model and results sections
of the English edition is backed by a `supported` claims.yaml row for that paragraph, and the row's
source is a refs.yaml entry whose verified record is ok. `unread` and `unsupported` rows block
release, and so does a row whose paragraph id no longer exists.

claims.yaml: a list of rows {id, paragraph_id, source_key, locator, support, status}; locator and
support may stay empty only while the status is not `supported`.

The gate also reports every refs.yaml entry without an ok verified record that names a url, whether
or not a claims row uses it, so a reference added while drafting cannot reach release unverified.

A paragraph runs from its `% id: <section>-<n>` line to the next id line or \\section. A section is
a \\section and everything up to the next one, named by the first `\\label{sec:...}` anywhere in it
(as tools.paper.consistency does), so subsection labels do not move it. A \\section without such a
label is a problem, and so is each gated section (the labels in GATED) the paper lacks, because a
renamed one (sec:related, sec:methodology) would go unchecked. A cite in a gated section outside every id'd
paragraph is a problem too: no claims row can name it. An \\input of a file inside the paper folder
(for example tables/<name>) is read as part of the paragraph it sits in.

CLI: python -m tools.paper.claims <paper_dir>   (exit 1 on any problem)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from tools.paper.consistency import inline_inputs
from tools.paper.refs import load_refs, ref_problems

GATED = ("literature", "model", "results")
STATUSES = ("supported", "unread", "unsupported")
ROW_FIELDS = ("id", "paragraph_id", "source_key", "locator", "support", "status")
ID_RE = re.compile(r"^\s*%\s*id:\s*(\S+)\s*$")
SECTION_RE = re.compile(r"\\section\*?\s*[\[{]")
LABEL_RE = re.compile(r"\\label\{sec:([^}]+)\}")
COMMENT_RE = re.compile(r"(?<!\\)%.*")
CITE_RE = re.compile(r"\\[Cc]ite[a-zA-Z]*\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}")


def _scan(tex: str):
    r"""(paragraphs, loose, unlabelled). `loose` is (section, text) per section: its text outside every id'd
    paragraph, \section line included. `unlabelled` is the \section line of each section without a `sec:` label.
    The text before the first \section is section ""."""
    chunks = [[]]
    for line in tex.splitlines():
        code = None if ID_RE.match(line) else COMMENT_RE.sub("", line)      # None marks an id line
        if code is not None and SECTION_RE.search(code):
            chunks.append([])
        chunks[-1].append((line, code))
    out, loose, unlabelled = [], [], []
    for k, chunk in enumerate(chunks):
        labels = [m.group(1) for _, code in chunk if code is not None for m in LABEL_RE.finditer(code)]
        if k and not labels:
            unlabelled.append(chunk[0][1].strip())
        section, current, free = (labels or [""])[0], None, []
        for line, code in chunk:
            if code is None:
                current = (section, ID_RE.match(line).group(1), [])
                out.append(current)
            else:
                (free if current is None else current[2]).append(code)
        loose.append((section, "\n".join(free)))
    return [(s, pid, "\n".join(lines)) for s, pid, lines in out], loose, unlabelled


def paragraphs(tex: str) -> list[tuple[str, str, str]]:
    """(section label without `sec:`, paragraph id, text without comments) in document order."""
    return _scan(tex)[0]


def cite_keys(text: str) -> list[str]:
    """Keys of every \\cite, \\citet, \\Citep, ... in order (optional [..] arguments allowed)."""
    return [k.strip() for m in CITE_RE.finditer(text) for k in m.group(1).split(",") if k.strip()]


def check(paper_dir: Path) -> list[str]:
    paper_dir = Path(paper_dir)
    tex_path, claims_path, refs_path = (paper_dir / "en" / "paper_en.tex", paper_dir / "claims.yaml",
                                        paper_dir / "refs.yaml")
    missing = [p for p in (tex_path, claims_path, refs_path) if not p.is_file()]
    if missing:
        return [f"missing {p.relative_to(paper_dir).as_posix()}" for p in missing]
    try:
        entries = load_refs(refs_path)
    except ValueError as exc:
        return [str(exc)]
    refs = {e["key"]: e for e in entries}
    rows = yaml.safe_load(claims_path.read_text(encoding="utf-8")) or []
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        return ["claims.yaml must be a list of mappings"]
    lines = [ln if ID_RE.match(ln) else inline_inputs(COMMENT_RE.sub("", ln), tex_path.parent, paper_dir)
             for ln in tex_path.read_text(encoding="utf-8").splitlines()]
    paras, loose, unlabelled = _scan("\n".join(lines))
    pids = {pid for _, pid, _ in paras}
    problems, seen, supported = ref_problems(entries), set(), set()
    problems += [f"{head} has no \\label{{sec:...}}; the claims gate cannot tell which section it is"
                 for head in unlabelled]
    for r in rows:
        rid, status = r.get("id", "?"), r.get("status")
        absent = [f for f in ROW_FIELDS
                  if not r.get(f) and (status == "supported" or f not in ("locator", "support"))]
        if absent:
            problems.append(f"claim {rid}: missing {absent}")
        if rid in seen:
            problems.append(f"claim {rid}: duplicate id")
        seen.add(rid)
        if status not in STATUSES:
            problems.append(f"claim {rid}: status {status!r} not in {STATUSES}")
        elif status != "supported":
            problems.append(f"claim {rid}: status {status} blocks release")
        if r.get("paragraph_id") not in pids:
            problems.append(f"claim {rid}: paragraph {r.get('paragraph_id')!r} not in en/paper_en.tex")
        ref = refs.get(r.get("source_key"))
        if ref is None:
            problems.append(f"claim {rid}: source {r.get('source_key')!r} not in refs.yaml")
        elif (ref.get("verified") or {}).get("ok") is not True:
            problems.append(f"claim {rid}: source {ref['key']} is not verified ok")
        if status == "supported" and not absent:
            supported.add((r["paragraph_id"], r["source_key"]))
    present = {section for section, _ in loose}
    problems += [f"no \\label{{sec:{g}}} section; its citations are not gated" for g in GATED if g not in present]
    for section, pid, text in paras:
        if section in GATED:
            for key in cite_keys(text):
                if (pid, key) not in supported:
                    problems.append(f"{pid}: \\cite{{{key}}} has no supported claims.yaml row")
    for section, text in loose:
        if section in GATED:
            problems += [f"sec:{section}: \\cite{{{key}}} outside an id'd paragraph" for key in cite_keys(text)]
    return problems


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m tools.paper.claims <paper_dir>", file=sys.stderr)
        return 2
    problems = check(Path(argv[0]))
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
