"""Publish a handoff document as CURRENT.md on the code-free `handoff` branch.

The working tree and the checked-out branch are never touched: the commit is built with git plumbing on a
temporary index, so this is safe to run from a hook while an agent is mid-edit. Rules the branch's README.md
states and this script enforces:

- A document whose remote copy says `status: taken` by another agent is a lock; it is not overwritten
  without `--force`. A remote CURRENT.md whose front matter cannot be read counts as locked too.
- A `status: handoff` that nobody has taken yet is not archived away by a document for another task, and
  neither is another session's live `checkpoint` (one updated within its stale_after_hours).
- When the new document names a different `task` than the remote one (and the remote one is not idle), the
  remote one is moved, byte for byte, to `archive/<updated_at>-<task>.md` in the same commit.
- A rejected push (someone else wrote first) is retried from a fresh fetch, so the lock check sees their
  write.
- `--key` adds a `handoff-key:` trailer to the commit (an empty commit when the document is already there),
  which marks a usage window as handed off while CURRENT.md stays `handoff`, `taken` or `returned`.
- LEDGER.md is the append-only record of finished work, one row per roadmap ID
  (docs/nautilus_bridge/REMAINING_WORK_*.md). Each `--done "id | what | files | commit | check"` appends a row,
  stamped with the time, the usage cycle and the writer, in the same commit as CURRENT.md. IDs are compared
  normalised (NFKC, one kind of hyphen, no Markdown marks), and the ledger's whole history counts: a row removed
  by hand, or a deleted LEDGER.md, is put back on the next publish. An ID already recorded by another writer or
  commit is refused, so finished work is not done twice; the same row again is skipped, so a publish can be
  re-run. A `next_ids` entry that is already done, a `done_ids` entry with no row, an ID that does not read as
  one, and a row whose commit is not on the remote are input errors.
- After the push, the commit is read back from the remote: its CURRENT.md must be the bytes that were sent
  and its LEDGER.md must hold the new rows.

Exit codes: 0 published and verified, 2 bad input (fix it and publish again), 3 refused (locked, unreadable, an
untaken handoff or a live checkpoint of another task, or an ID another writer already recorded), 4 git or
network failure, or a read-back that did not match (the push may have landed: run --show and --ledger). Every
publish, and a re-publish of the same document, prints `push_handoff: <branch> at <sha> (<status> <task>)`.

    python3 tools/handoff/push_handoff.py path/to/handoff.md [--key seven_day@<resets_at>] [--done "..."]...
    python3 tools/handoff/push_handoff.py --show            # the remote CURRENT.md front matter and the ledger tip
    python3 tools/handoff/push_handoff.py --ledger          # the whole ledger
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

REQUIRED = ("status", "task", "from", "updated_at")
STATUSES = {"idle", "checkpoint", "handoff", "taken", "returned"}
KST = timezone(timedelta(hours=9))
# The owner's weekly usage limit refills on Tuesdays at 17:00 KST; a cycle is named by the Tuesday it began.
REFILL_WEEKDAY, REFILL_HOUR = 1, 17
LEDGER = "LEDGER.md"
_DASHES = re.compile(r"[\u2010-\u2015\u2212\ufe58\ufe63\uff0d]")
ID_SEPARATORS = re.compile(r"[\s,\uff0c\u3001;\uff1b\u25b6\u2192>\[\]]+")
ID_SHAPE = re.compile(r"^[0-9a-z][0-9a-z.\-/]*$")
LEDGER_SKELETON = ("# 완료 기록 (LEDGER)\n\n"
                   "| id | 완료 시각 (KST) | 주기 | 누가 | 한 일 | 바뀐 파일 | 커밋 | 확인 방법과 결과 |\n"
                   "|---|---|---|---|---|---|---|---|\n")


class GitError(RuntimeError):
    pass


def git_bytes(*args: str, env: dict | None = None, input_bytes: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(["git", *args], capture_output=True, input=input_bytes,
                          env={**os.environ, **(env or {})})
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git(*args: str, env: dict | None = None, input_bytes: bytes | None = None, check: bool = True) -> str:
    return git_bytes(*args, env=env, input_bytes=input_bytes, check=check).decode(errors="replace").strip()


def front_matter(text: str) -> dict[str, str]:
    """Flat `key: value  # comment` lines between the leading `---` fences; keys lower-cased, quotes dropped."""
    lines = text.lstrip("﻿").lstrip().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*(?:#.*)?$", line)
        if m:
            fields[m.group(1).lower()] = m.group(2).strip("\"'")
    return {}


def with_retries(fn, attempts: int = 4):
    """Network calls: retry with 2, 4, 8, 16 s back-off."""
    for i in range(attempts + 1):
        try:
            return fn()
        except GitError:
            if i == attempts:
                raise
            time.sleep(2 ** (i + 1))


def fetch(remote: str, branch: str) -> str:
    with_retries(lambda: git("fetch", "-q", remote, f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}"))
    return git("rev-parse", f"refs/remotes/{remote}/{branch}")


def remote_current(parent: str) -> bytes:
    return git_bytes("show", f"{parent}:CURRENT.md", check=False)


def remote_fields(parent: str) -> tuple[bytes, dict[str, str]]:
    raw = remote_current(parent)
    return raw, front_matter(raw.decode(errors="replace"))


def is_unreadable(raw: bytes, fields: dict[str, str]) -> bool:
    return bool(raw.strip()) and fields.get("status", "").lower() not in STATUSES


def key_recorded(ref: str, key: str) -> bool:
    return bool(git("log", ref, "-1", "--format=%H", "--fixed-strings", f"--grep=handoff-key: {key}", check=False))


def handed_off(ref: str, key: str) -> bool:
    """Whether this usage window was handed off: keyed on the branch, and CURRENT.md still that handoff, GPT's lock
    on it, or GPT's return of it (until Claude publishes its own document again)."""
    _, fields = remote_fields(ref)
    return fields.get("status", "").lower() in ("handoff", "taken", "returned") and key_recorded(ref, key)


def is_stale(fields: dict[str, str]) -> bool:
    """Whether the document has gone without an update for longer than its stale_after_hours (3 if unset)."""
    try:
        updated = datetime.fromisoformat(fields.get("updated_at", ""))
        hours = float(fields.get("stale_after_hours") or 3)
    except ValueError:
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=KST)
    return datetime.now(KST) - updated > timedelta(hours=hours)


def same_writer(old: dict[str, str], new: dict[str, str]) -> bool:
    """Whether two documents come from the same session or the same work branch."""
    for k in ("session", "work_branch"):
        a, b = old.get(k, "").strip(), new.get(k, "").strip()
        if a and a == b and a.lower() not in ("none", "unknown") and not a.startswith("<"):
            return True
    return False


def cycle_of(t: datetime) -> str:
    """The usage cycle `t` falls in, named by the date of the Tuesday 17:00 KST refill that opened it."""
    t = t.astimezone(KST)
    start = (t - timedelta(days=(t.weekday() - REFILL_WEEKDAY) % 7)).replace(
        hour=REFILL_HOUR, minute=0, second=0, microsecond=0)
    if start > t:
        start -= timedelta(days=7)
    return start.date().isoformat()


def norm_id(s: str) -> str:
    """The form IDs are compared in: NFKC (`③` reads as `3`, full-width as ASCII), one hyphen, no Markdown marks."""
    s = _DASHES.sub("-", unicodedata.normalize("NFKC", s))
    return re.sub(r"[\s`*_]", "", s).casefold()


def id_tokens(value: str | None) -> list[str]:
    """The IDs of a done_ids / next_ids value as written, whatever separates them (commas, spaces, arrows)."""
    return [x.strip() for x in ID_SEPARATORS.split(value or "") if x.strip() and x.strip().lower() != "none"]



def cells_of(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def ledger_rows(text: str) -> dict[str, str]:
    """Normalised id -> row, for every row below LEDGER.md's table header (the first row of an id wins)."""
    rows: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        cells = cells_of(line)
        if not in_table:
            in_table = len(cells) >= 8 and all(c and set(c) <= set("-: ") for c in cells)
            continue
        if len(cells) >= 8 and cells[0]:
            rows.setdefault(norm_id(cells[0]), line.strip())
    return rows


def ledger_history(ref: str) -> tuple[dict[str, str], str]:
    """Every row any committed LEDGER.md on `ref` has held, oldest first, and the newest text the file had."""
    seen: dict[str, str] = {}
    last = ""
    for sha in reversed(git("log", "--format=%H", ref, "--", LEDGER, check=False).split()):
        text = git("show", f"{sha}:{LEDGER}", check=False)
        last = text or last
        for rid, row in ledger_rows(text).items():
            seen.setdefault(rid, row)
    return seen, last


def done_rows(specs: list[str], by: str, when: datetime) -> list[tuple[str, str, list[str]]]:
    """(id, ledger row, commits) for each --done 'id | what | files | commit[,commit] | check'."""
    out = []
    for spec in specs:
        cells = [c.strip() for c in spec.split("|")]
        if len(cells) != 5 or not all(cells):
            raise ValueError(f"--done needs five non-empty fields 'id | what | files | commit | check': {spec!r}")
        rid, what, files, commits, check = cells
        row = "| " + " | ".join([rid, when.isoformat(), cycle_of(when), by, what, files, commits, check]) + " |"
        out.append((norm_id(rid), row, [c.strip() for c in commits.split(",") if c.strip()]))
    return out


def on_remote(sha: str) -> bool:
    if subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode != 0:
        return False
    return bool(git("branch", "-r", "--contains", sha, check=False))


def ledger_problem(known: dict[str, str], rows: list[tuple[str, str, list[str]]],
                   new: dict[str, str]) -> tuple[list[tuple[str, str, list[str]]], tuple[int, str] | None]:
    """The --done rows still to append, and (exit code, why) when the document or a row disagrees with the ledger.

    A row the same writer already recorded with the same commit is a repeat of this command and is skipped, so a
    publish can be re-run safely; any other row for a recorded ID is refused."""
    fresh = []
    ids = [rid for rid, _, _ in rows]
    if len(set(ids)) != len(ids):
        return [], (2, "the same ID is given twice in --done")
    for rid, row, commits in rows:
        if rid not in known:
            fresh.append((rid, row, commits))
            continue
        old, mine = cells_of(known[rid]), cells_of(row)
        if len(old) >= 8 and old[3].lower() == mine[3].lower() and old[6].replace(" ", "") == mine[6].replace(" ", ""):
            continue
        return [], (3, f"{mine[0]} is already in LEDGER.md: {known[rid]}. Finished work is not done again; if "
                       f"the owner asked for more on it, record it under a new ID such as {mine[0]}/2")
    written = [cells_of(row)[0] for _, row, _ in rows] + id_tokens(new.get("next_ids")) + id_tokens(new.get("done_ids"))
    odd = [t for t in written if not ID_SHAPE.match(norm_id(t))]
    if odd:
        return [], (2, f"{', '.join(odd)} does not read as a roadmap ID; write IDs as in REMAINING_WORK, "
                       "separated by commas")
    done = set(known) | set(ids)
    done_again = [t for t in id_tokens(new.get("next_ids")) if norm_id(t) in done]
    if done_again:
        return [], (2, f"next_ids lists finished work ({', '.join(done_again)}); take it out of the document and "
                       "publish again")
    unrecorded = [t for t in id_tokens(new.get("done_ids")) if norm_id(t) not in done]
    if unrecorded:
        return [], (2, f"done_ids lists {', '.join(unrecorded)} with no LEDGER.md row; pass a --done for each")
    return fresh, None


def archive_name(parent: str, fields: dict[str, str]) -> str:
    stamp = re.sub(r"[^0-9T]", "", fields.get("updated_at", ""))[:13] or "undated"
    task = re.sub(r"[^a-z0-9._-]+", "-", fields.get("task", "task").lower()).strip("-") or "task"
    name, n = f"archive/{stamp}-{task}.md", 1
    while subprocess.run(["git", "cat-file", "-e", f"{parent}:{name}"], capture_output=True).returncode == 0:
        n += 1
        name = f"archive/{stamp}-{task}-{n}.md"
    return name


def commit_files(parent: str, files: dict[str, bytes | None], message: str) -> str:
    """A commit on `parent` with `files` written (None removes the path); `parent` itself when nothing changes."""
    fd, index = tempfile.mkstemp(prefix="handoff-index-")
    os.close(fd)
    env = {"GIT_INDEX_FILE": index}
    try:
        git("read-tree", parent, env=env)
        for path, data in files.items():
            if data is None:
                git("update-index", "--force-remove", path, env=env)
            else:
                blob = git("hash-object", "-w", "--stdin", input_bytes=data)
                git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git("write-tree", env=env)
    finally:
        os.unlink(index)
    if tree == git("rev-parse", f"{parent}^{{tree}}"):
        return parent
    return make_commit(tree, parent, message)


def make_commit(tree: str, parent: str, message: str) -> str:
    # commit-tree ignores commit.gpgSign, so carry the setting over by hand
    sign = ["-S"] if git("config", "--bool", "commit.gpgSign", check=False) == "true" else []
    return git("commit-tree", *sign, tree, "-p", parent, "-m", message)


def push_commit(remote: str, branch: str, commit: str) -> bool:
    """True once pushed; False when the remote moved on (re-fetch and rebuild); GitError on other failures."""
    push = subprocess.run(["git", "push", "-q", remote, f"{commit}:refs/heads/{branch}"],
                          capture_output=True, text=True)
    if push.returncode == 0:
        return True
    if "rejected" in push.stderr or "non-fast-forward" in push.stderr:
        return False
    with_retries(lambda: git("push", "-q", remote, f"{commit}:refs/heads/{branch}"))
    return True


def build_commit(parent: str, new_raw: bytes, new: dict[str, str], message: str, ledger: bytes | None = None) -> str:
    old_raw, old = remote_fields(parent)
    files: dict[str, bytes | None] = {} if ledger is None else {LEDGER: ledger}
    if old and old.get("status", "").lower() != "idle" and old.get("task") not in (None, "", "none") \
            and old.get("task") != new["task"]:
        files[archive_name(parent, old)] = old_raw
    files["CURRENT.md"] = new_raw
    return commit_files(parent, files, message)


def refusal(old_raw: bytes, old: dict[str, str], new: dict[str, str]) -> str | None:
    """Why the remote document must not be replaced by `new`, or None."""
    status = old.get("status", "").lower()
    if is_unreadable(old_raw, old):
        return ("the remote CURRENT.md has no readable front matter; read it with "
                "`git show origin/handoff:CURRENT.md` and fix it, or pass --force with the owner's say-so")
    if status == "taken" and old.get("from", "").lower() != new["from"].lower():
        return (f"locked: {old.get('from')} took '{old.get('task')}' at {old.get('updated_at')}. "
                "Wait for status: returned, or pass --force with the owner's say-so")
    other_task = old.get("task") not in (None, "", "none") and old.get("task") != new["task"]
    if status == "handoff" and other_task:
        return (f"'{old.get('task')}' was handed off at {old.get('updated_at')} and nobody has taken it; publishing "
                f"'{new['task']}' would archive it out of the next agent's sight. Resume that task, wait for "
                "status: taken, or pass --force with the owner's say-so")
    if status == "checkpoint" and other_task and not is_stale(old) and not same_writer(old, new):
        return (f"'{old.get('task')}' is another session's live checkpoint (updated {old.get('updated_at')}, "
                f"{old.get('work_branch')}); publishing '{new['task']}' would archive it. Ask the owner, or pass "
                "--force with the owner's say-so")
    return None


def read_back(remote: str, branch: str, commit: str, new_raw: bytes, ids: list[str]) -> bool:
    """Whether the remote branch holds `commit`, with these CURRENT.md bytes and these ledger rows."""
    tip = fetch(remote, branch)
    if subprocess.run(["git", "merge-base", "--is-ancestor", commit, tip], capture_output=True).returncode != 0:
        return False
    if git_bytes("show", f"{commit}:CURRENT.md", check=False) != new_raw:
        return False
    ledger = ledger_rows(git("show", f"{commit}:{LEDGER}", check=False))
    return all(rid in ledger for rid in ids)


def publish(path: Path, remote: str, branch: str, force: bool, message: str | None, key: str | None,
            done: list[str]) -> int:
    new_raw = path.read_bytes()
    new = front_matter(new_raw.decode("utf-8-sig", errors="replace"))
    missing = [k for k in REQUIRED if not new.get(k)]
    if missing:
        print(f"push_handoff: {path} front matter lacks {', '.join(missing)}", file=sys.stderr)
        return 2
    if new["status"].lower() not in STATUSES:
        print(f"push_handoff: status '{new['status']}' is not one of {sorted(STATUSES)}", file=sys.stderr)
        return 2
    try:
        rows = done_rows(done, new["from"].lower(), datetime.now(KST).replace(microsecond=0))
    except ValueError as e:
        print(f"push_handoff: {e}", file=sys.stderr)
        return 2
    if rows:
        with_retries(lambda: git("fetch", "-q", remote))
        unpushed = [c for _, _, commits in rows for c in commits if not on_remote(c)]
        if unpushed:
            print(f"push_handoff: commit {', '.join(unpushed)} is not on {remote}; push the work branch first",
                  file=sys.stderr)
            return 2
    msg = message or f"handoff: {new['status']} {new['task']}"
    if rows:
        msg += "\n\ndone: " + ", ".join(rid for rid, _, _ in rows)
    if key:
        msg += f"\n\nhandoff-key: {key}\n"

    for _ in range(3):
        parent = fetch(remote, branch)
        old_raw, old = remote_fields(parent)
        why = None if force else refusal(old_raw, old, new)
        if why:
            print(f"push_handoff: {why}.", file=sys.stderr)
            return 3
        # A ledger row is never lost: a deleted LEDGER.md comes back as its last version, and rows removed by
        # hand are put back from history.
        ledger_text = git("show", f"{parent}:{LEDGER}", check=False)
        history, last_text = ledger_history(parent)
        current = ledger_text or last_text
        current_rows = ledger_rows(current)
        lost = [row for rid, row in history.items() if rid not in current_rows]
        fresh, problem = ledger_problem({**history, **current_rows}, rows, new)
        if problem:
            print(f"push_handoff: {problem[1]}.", file=sys.stderr)
            return problem[0]
        ledger = None
        if fresh or lost or current != ledger_text:
            if current != ledger_text:
                print("push_handoff: LEDGER.md was deleted on the branch; restored from its last version",
                      file=sys.stderr)
            if lost:
                print(f"push_handoff: LEDGER.md had lost {len(lost)} row(s) an earlier version held; put back: "
                      + "; ".join(lost), file=sys.stderr)
            base = current + "\n" if current else LEDGER_SKELETON
            ledger = (base + "".join(r + "\n" for r in lost) + "".join(row + "\n" for _, row, _ in fresh)).encode()
        commit = build_commit(parent, new_raw, new, msg, ledger)
        if commit == parent and key and not key_recorded(parent, key):
            commit = make_commit(git("rev-parse", f"{parent}^{{tree}}"), parent, msg)
        if commit == parent or push_commit(remote, branch, commit):
            try:
                verified = read_back(remote, branch, commit, new_raw, [rid for rid, _, _ in rows])
            except GitError as e:
                print(f"push_handoff: pushed {commit[:7]} but could not read it back ({e}); run --show and --ledger "
                      "before publishing again (re-running the same --done is safe)", file=sys.stderr)
                return 4
            if not verified:
                print(f"push_handoff: {remote}/{branch} does not hold what was sent ({commit[:7]}); "
                      "run --show and --ledger, then publish again", file=sys.stderr)
                return 4
            skipped = len(rows) - len(fresh)
            print(f"push_handoff: {branch} at {commit[:7]} ({new['status'].lower()} {new['task']}), "
                  f"verified on {remote}" + (f"; ledger +{len(fresh)}" if rows else "")
                  + (f" ({skipped} already recorded)" if skipped else ""))
            return 0
    print("push_handoff: the remote kept moving; gave up after 3 attempts", file=sys.stderr)
    return 4


def show(remote: str, branch: str) -> int:
    raw, fields = remote_fields(fetch(remote, branch))
    if is_unreadable(raw, fields):
        print("status: unreadable (CURRENT.md front matter could not be parsed; treat it as taken)")
        return 3
    for k, v in fields.items():
        print(f"{k}: {v}")
    print_ledger_tip(remote, branch)
    return 0


def print_ledger_tip(remote: str, branch: str) -> None:
    ref = f"refs/remotes/{remote}/{branch}"
    tip = ledger_rows(git("show", f"{ref}:{LEDGER}", check=False))
    rows = list(tip.values())
    print(f"# cycle now: {cycle_of(datetime.now(KST))}; ledger: {len(rows)} rows" +
          (f", last: {rows[-1]}" if rows else ""))
    lost = [row for rid, row in ledger_history(ref)[0].items() if rid not in tip]
    if lost:
        print(f"# WARNING: LEDGER.md lost {len(lost)} row(s) an earlier version held (the next publish puts them "
              "back): " + "; ".join(lost))


def show_ledger(remote: str, branch: str) -> int:
    fetch(remote, branch)
    print(git("show", f"refs/remotes/{remote}/{branch}:{LEDGER}", check=False) or LEDGER_SKELETON)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", type=Path, help="handoff document to publish as CURRENT.md")
    ap.add_argument("--show", action="store_true", help="print the remote CURRENT.md front matter and exit")
    ap.add_argument("--force", action="store_true", help="publish over a lock or an untaken handoff (owner's say-so)")
    ap.add_argument("--key", help="usage-window key, written as a 'handoff-key:' commit trailer")
    ap.add_argument("--done", action="append", default=[], metavar="'ID | WHAT | FILES | COMMIT | CHECK'",
                    help="append a finished roadmap item to LEDGER.md (repeatable)")
    ap.add_argument("--ledger", action="store_true", help="print the remote LEDGER.md and exit")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="handoff")
    ap.add_argument("-m", "--message")
    args = ap.parse_args(argv)
    try:
        if args.show:
            return show(args.remote, args.branch)
        if args.ledger:
            return show_ledger(args.remote, args.branch)
        if not args.file:
            ap.error("give a handoff document, or --show / --ledger")
        return publish(args.file, args.remote, args.branch, args.force, args.message, args.key, args.done)
    except GitError as e:
        print(f"push_handoff: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
