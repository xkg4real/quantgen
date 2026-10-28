"""Publish a handoff document as CURRENT.md on the code-free `handoff` branch.

The working tree and the checked-out branch are never touched: the commit is built with git plumbing on a
temporary index, so this is safe to run from a hook while an agent is mid-edit. Rules the branch's README.md
states and this script enforces:

- A document whose remote copy says `status: taken` by another agent is a lock; it is not overwritten
  without `--force`.
- When the new document names a different `task` than the remote one (and the remote one is not idle), the
  remote one is moved to `archive/<updated_at>-<task>.md` in the same commit.
- A rejected push (someone else wrote first) is retried from a fresh fetch, so the lock check sees their
  write.

Exit codes: 0 published, 2 bad input, 3 locked by another agent, 4 git or network failure.

    python3 tools/handoff/push_handoff.py path/to/handoff.md
    python3 tools/handoff/push_handoff.py --show            # print the remote CURRENT.md front matter
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REQUIRED = ("status", "task", "from", "updated_at")
STATUSES = {"idle", "checkpoint", "handoff", "taken", "returned"}


class GitError(RuntimeError):
    pass


def git(*args: str, env: dict | None = None, input_bytes: bytes | None = None, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, input=input_bytes,
                          env={**os.environ, **(env or {})})
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout.decode(errors="replace").strip()


def front_matter(text: str) -> dict[str, str]:
    """Flat `key: value  # comment` lines between the leading `---` fences."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*(?:#.*)?$", line)
        if m:
            fields[m.group(1)] = m.group(2)
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


def remote_current(parent: str) -> str:
    return git("show", f"{parent}:CURRENT.md", check=False)


def archive_name(fields: dict[str, str]) -> str:
    stamp = re.sub(r"[^0-9T]", "", fields.get("updated_at", ""))[:13] or "undated"
    task = re.sub(r"[^a-z0-9._-]+", "-", fields.get("task", "task").lower()).strip("-") or "task"
    return f"archive/{stamp}-{task}.md"


def build_commit(parent: str, new_text: str, new: dict[str, str], message: str) -> str:
    old_text = remote_current(parent)
    old = front_matter(old_text)
    fd, index = tempfile.mkstemp(prefix="handoff-index-")
    os.close(fd)
    env = {"GIT_INDEX_FILE": index}
    try:
        git("read-tree", parent, env=env)
        if old and old.get("status") != "idle" and old.get("task") not in (None, "", "none") \
                and old.get("task") != new["task"]:
            blob = git("hash-object", "-w", "--stdin", input_bytes=old_text.encode())
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{archive_name(old)}", env=env)
        blob = git("hash-object", "-w", "--stdin", input_bytes=new_text.encode())
        git("update-index", "--add", "--cacheinfo", f"100644,{blob},CURRENT.md", env=env)
        tree = git("write-tree", env=env)
    finally:
        os.unlink(index)
    if tree == git("rev-parse", f"{parent}^{{tree}}"):
        return parent
    return git("commit-tree", tree, "-p", parent, "-m", message)


def publish(path: Path, remote: str, branch: str, force: bool, message: str | None) -> int:
    new_text = path.read_text(encoding="utf-8")
    new = front_matter(new_text)
    missing = [k for k in REQUIRED if not new.get(k)]
    if missing:
        print(f"push_handoff: {path} front matter lacks {', '.join(missing)}", file=sys.stderr)
        return 2
    if new["status"] not in STATUSES:
        print(f"push_handoff: status '{new['status']}' is not one of {sorted(STATUSES)}", file=sys.stderr)
        return 2
    msg = message or f"handoff: {new['status']} {new['task']}"

    for _ in range(3):
        parent = fetch(remote, branch)
        old = front_matter(remote_current(parent))
        if old.get("status") == "taken" and old.get("from") != new["from"] and not force:
            print(f"push_handoff: locked — {old.get('from')} took '{old.get('task')}' at {old.get('updated_at')}. "
                  "Wait for status: returned, or pass --force with the owner's say-so.", file=sys.stderr)
            return 3
        commit = build_commit(parent, new_text, new, msg)
        if commit == parent:
            print(f"push_handoff: remote already holds this document ({parent[:7]})")
            return 0
        push = subprocess.run(["git", "push", "-q", remote, f"{commit}:refs/heads/{branch}"],
                              capture_output=True, text=True)
        if push.returncode == 0:
            print(f"push_handoff: {branch} -> {commit[:7]} ({new['status']} {new['task']})")
            return 0
        if "rejected" not in push.stderr and "non-fast-forward" not in push.stderr:
            with_retries(lambda: git("push", "-q", remote, f"{commit}:refs/heads/{branch}"))
            print(f"push_handoff: {branch} -> {commit[:7]} ({new['status']} {new['task']})")
            return 0
    print("push_handoff: the remote kept moving; gave up after 3 attempts", file=sys.stderr)
    return 4


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", type=Path, help="handoff document to publish as CURRENT.md")
    ap.add_argument("--show", action="store_true", help="print the remote CURRENT.md front matter and exit")
    ap.add_argument("--force", action="store_true", help="overwrite a 'taken' lock held by another agent")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="handoff")
    ap.add_argument("-m", "--message")
    args = ap.parse_args(argv)
    try:
        if args.show:
            for k, v in front_matter(remote_current(fetch(args.remote, args.branch))).items():
                print(f"{k}: {v}")
            return 0
        if not args.file:
            ap.error("give a handoff document, or --show")
        return publish(args.file, args.remote, args.branch, args.force, args.message)
    except GitError as e:
        print(f"push_handoff: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
