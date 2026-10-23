"""The owner's approval of a paper's scope (spec 5.1): the deterministic refusal behind `/quantgen-paper write`.

    python -m tools.paper.approval approve papers/<paper_id> --words "I approve this scope as written"
    python -m tools.paper.approval check papers/<paper_id>     # exit 1 when the scope changed after approval

scope/approval.json records the sha256 of every file under scope/ except itself, the owner's words and the UTC
time. `check` compares the scope as it is now with that record, so no agent's judgment stands in for it.
A bare paper id is read as papers/<paper_id>.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = "scope/approval.json"


def scope_digest(paper_dir: Path) -> dict[str, str]:
    """{'scope/<file>': sha256} for every file under scope/, approval.json excluded."""
    paper_dir = Path(paper_dir)
    out = {}
    for path in sorted(p for p in (paper_dir / "scope").rglob("*") if p.is_file()):
        rel = path.relative_to(paper_dir).as_posix()
        if rel != RECORD:
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def approve(paper_dir: Path, owner_words: str, now_utc: str) -> Path:
    files = scope_digest(paper_dir)
    if not owner_words.strip():
        raise ValueError("approval: the owner's words are required")
    if not files:
        raise ValueError(f"approval: {Path(paper_dir) / 'scope'} has no files to approve")
    out = Path(paper_dir) / RECORD
    record = {"files": files, "owner_words": owner_words.strip(), "approved_utc": now_utc}
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return out


def check(paper_dir: Path) -> list[str]:
    path = Path(paper_dir) / RECORD
    if not path.is_file():
        return [f"{RECORD} missing: the owner has not approved this scope"]
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{RECORD} unreadable: {exc}"]
    if not isinstance(record, dict) or not isinstance(record.get("files"), dict) or not record["files"]:
        return [f"{RECORD} approves no files"]
    then, now = record["files"], scope_digest(paper_dir)
    problems = [f"{f} changed after approval" for f in sorted(then.keys() & now.keys()) if then[f] != now[f]]
    problems += [f"{f} removed after approval" for f in sorted(then.keys() - now.keys())]
    problems += [f"{f} added after approval" for f in sorted(now.keys() - then.keys())]
    if not str(record.get("owner_words", "")).strip():
        problems.append(f"{RECORD} has no owner words")
    return problems


def _paper_dir(arg: str) -> Path:
    path = Path(arg)
    return path if path.is_dir() else ROOT / "papers" / arg


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Record or check the owner's approval of a paper's scope.")
    parser.add_argument("action", choices=("approve", "check"))
    parser.add_argument("paper", help="papers/<paper_id> or a bare paper id")
    parser.add_argument("--words", help="the owner's words of approval (approve only)")
    args = parser.parse_args(argv)
    paper_dir = _paper_dir(args.paper)
    if args.action == "approve":
        if not args.words:
            parser.error("approve needs --words")
        print(approve(paper_dir, args.words, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        return 0
    problems = check(paper_dir)
    for problem in problems:
        print(problem)
    print(f"approval: {len(problems)} problem(s); the scope is not approved as it stands" if problems else "approval: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
