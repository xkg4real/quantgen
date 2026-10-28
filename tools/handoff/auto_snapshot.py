"""Push a machine-made snapshot of this clone's git state to the `handoff` branch as AUTO_STATE.md.

No model is involved, so this still works when the usage limit has stopped the model. CURRENT.md (the
model-written handoff: intent, grounds, next steps) is never touched; AUTO_STATE.md beside it records what git
can tell: branch, HEAD, recent commits, unpushed commits, uncommitted changes, and the model's last message when
a hook passes it in. AUTO_STATE.patch holds, byte for byte, the diff of tracked files from `patch_base` (the
newest commit of this branch that the remote has) to the working tree, so it carries unpushed commits too;
untracked files are listed by name only, since their content may hold secrets.

AUTO_STATE.md belongs to the task CURRENT.md names. A clone on another branch than CURRENT.md's `work_branch`
leaves it alone while that task is `handoff`, `taken` or `checkpoint` (a --key run only a live checkpoint),
or while CURRENT.md is unreadable, so one session cannot overwrite the record of another. A throttled run that loses a
push race stops: what won is newer.

Callers:
- the handoff-usage-watch mod at the usage threshold (`--reason usage_limit_weekly --key ...`); exit 10 tells
  it that the handoff for that window is published and still outstanding (`push_handoff.py --key` wrote the
  `handoff-key: <key>` trailer, and CURRENT.md is `handoff` or `taken`); exit 11 that another task's handoff
  or lock holds the branch, so this session cannot hand off there;
- the same mod during work, throttled (`--reason periodic --min-interval 1800`): it pushes only when the git
  state changed and the interval has passed, so the branch holds a recent snapshot even when a session stops
  without warning;
- the same mod when a turn fails with a rate-limit error (`--reason rate_limit_error --hook-stdin`): a usage
  limit, or the service turning requests away under load, which the hook input does not tell apart, so
  CURRENT.md's status is left as it is.

Exit codes: 0 pushed or nothing to do, 10 window already handed off, 11 another task holds the branch
(--key runs only), 4 git or network failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from push_handoff import (GitError, commit_files, fetch, git, git_bytes, handed_off, is_stale, is_unreadable,
                          push_commit, remote_fields)

KST = timezone(timedelta(hours=9))
PATCH_LIMIT = 2 * 1024 * 1024
MESSAGE_LIMIT = 4000


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


# Plain diff output whatever the user's git config says (prefixes, colour, external tools, textconv).
PLAIN_DIFF = ("--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/", "--no-relative")


def patch_base(remote: str) -> str:
    """The newest commit of HEAD's history that the remote has: merge-base with the upstream, else the default branch."""
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    for ref in (upstream, f"refs/remotes/{remote}/HEAD", f"refs/remotes/{remote}/main"):
        base = git("merge-base", "HEAD", ref, check=False) if ref else ""
        if base:
            return base
    return ""


def state_file() -> Path:
    return Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")) / "handoff-auto.json"


def read_state() -> dict:
    try:
        return json.loads(state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def hook_input(enabled: bool) -> dict:
    if not enabled:
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def fence(text: str) -> str:
    return "```\n" + (text.strip() or "(없음)") + "\n```"


def snapshot(args: argparse.Namespace, hook: dict, parent: str) -> tuple[dict[str, bytes | None], str]:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    head = git("rev-parse", "--short=7", "HEAD")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    base = patch_base(args.remote)
    unpushed = git("log", "--oneline", f"{base}..HEAD", check=False) if base else "(원격에 있는 기준 커밋 없음)"
    status = git("status", "--porcelain")
    untracked = [line[3:] for line in status.splitlines() if line.startswith("??")]
    diff = git_bytes("diff", *PLAIN_DIFF, "--binary", base or "HEAD")
    _, current = remote_fields(parent)

    patch = diff if diff and len(diff) <= PATCH_LIMIT else None
    patch_note = ("AUTO_STATE.patch (`git apply AUTO_STATE.patch` on patch_base)" if patch and base
                  else "AUTO_STATE.patch (on source_head, which the remote does not have)" if patch
                  else "too large; see diff --stat" if diff else "none")

    message = (hook.get("last_assistant_message") or "").strip()
    if len(message) > MESSAGE_LIMIT:
        message = message[:MESSAGE_LIMIT] + "\n… (truncated)"

    fields = {
        "kind": "auto_snapshot",
        "reason": args.reason,
        "created_at": now_kst(),
        "source_branch": branch,
        "source_head": head,
        "upstream": upstream or "none",
        "patch_base": base[:7] if base else "none",
        "unpushed_commits": str(len(unpushed.splitlines())) if base else "unknown",
        "uncommitted_files": str(len(status.splitlines())),
        "patch": patch_note,
        "usage_pct": args.pct or "unknown",
        "usage_resets_at": args.resets_at or "unknown",
        "session": args.session or hook.get("session_id") or "unknown",
        "snapshot_key": args.key or "none",
        "current_md_updated_at": current.get("updated_at", "none"),
        "current_md_status": current.get("status", "none"),
    }
    body = [
        "---", *(f"{k}: {v}" for k, v in fields.items()), "---", "",
        "# 자동 스냅샷 (모델 없이 생성)", "",
        "스크립트가 git 상태만 보고 만든 파일입니다. 작업의 목표, 근거, 다음 할 일은 `CURRENT.md`에 있습니다.",
        "`CURRENT.md`의 `updated_at`이 이 파일의 `created_at`보다 오래됐다면, 그 사이에 바뀐 것은 아래 git 상태로",
        "확인하세요.", "",
        "## 최근 커밋", "", fence(git("log", "--oneline", "-15")), "",
        "## 푸시되지 않은 커밋", "", fence(unpushed), "",
        "## 커밋되지 않은 변경", "", fence(status), "",
        "`patch_base` 이후 바뀐 파일 (푸시 안 된 커밋 포함):", "", fence(git("diff", *PLAIN_DIFF, "--stat", base or "HEAD")), "",
        f"전체 diff: {patch_note}", "",
    ]
    if untracked:
        body += ["추적되지 않는 파일은 비밀 값이 있을 수 있어 이름만 적습니다:", "", fence("\n".join(untracked)), ""]
    if message:
        body += ["## Claude의 마지막 메시지", "", fence(message), ""]
    if hook.get("error"):
        body += [f"이 스냅샷은 턴이 `{hook['error']}` 오류로 끝나서 만들어졌습니다.", ""]

    files: dict[str, bytes | None] = {"AUTO_STATE.md": "\n".join(body).encode(), "AUTO_STATE.patch": patch}
    title = f"handoff: auto {args.reason} {branch}@{head}"
    return files, title + (f"\n\nsnapshot-key: {args.key}\n" if args.key else "\n")


def fingerprint() -> str:
    parts = (git_bytes("rev-parse", "HEAD"), git_bytes("status", "--porcelain"), git_bytes("diff", *PLAIN_DIFF, "--binary", "HEAD"))
    return hashlib.sha256(b"\0".join(parts)).hexdigest()


def run(args: argparse.Namespace) -> int:
    hook = hook_input(args.hook_stdin)
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch == args.branch:
        return 0
    state = read_state()
    mark = fingerprint()
    if args.min_interval:
        if state.get("fingerprint") == mark or time.time() - state.get("pushed_at", 0) < args.min_interval:
            return 0

    for attempt in range(3):
        if attempt and args.min_interval:
            return 0  # the branch moved under a throttled run: a fresher snapshot or handoff is on top
        parent = fetch(args.remote, args.branch)
        if args.key and handed_off(parent, args.key):
            print(f"auto_snapshot: the handoff for {args.key} is already on {args.branch}")
            return 10
        raw, current = remote_fields(parent)
        owner = current.get("work_branch", "none")
        status = current.get("status", "").lower()
        # A --key run may replace another branch's checkpoint only once that checkpoint has gone stale.
        guarded = ("handoff", "taken") + (("checkpoint",) if not args.key or not is_stale(current) else ())
        if is_unreadable(raw, current) or (status in guarded and owner not in ("", "none") and owner != branch):
            print(f"auto_snapshot: the branch belongs to {owner} ({current.get('task')}); skipped")
            return 11 if args.key else 0
        files, message = snapshot(args, hook, parent)
        commit = commit_files(parent, files, message)
        if commit == parent or push_commit(args.remote, args.branch, commit):
            state_file().write_text(json.dumps({"fingerprint": mark, "pushed_at": time.time()}), encoding="utf-8")
            print(f"auto_snapshot: {args.branch} -> {commit[:7]} ({args.reason})")
            return 0
    print("auto_snapshot: the remote kept moving; gave up after 3 attempts", file=sys.stderr)
    return 4


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reason", required=True,
                    choices=["usage_limit_weekly", "usage_limit_5h", "rate_limit_error", "periodic", "manual"])
    ap.add_argument("--key", help="once-per-window key: exit 10 when a handoff carrying it is already published")
    ap.add_argument("--pct", help="usage percent that triggered this")
    ap.add_argument("--resets-at", help="when that usage window resets")
    ap.add_argument("--session", help="session id or link")
    ap.add_argument("--hook-stdin", action="store_true", help="read a settings hook's JSON input from stdin")
    ap.add_argument("--min-interval", type=int, default=0,
                    help="seconds; push only if the git state changed and this long has passed since the last push")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="handoff")
    try:
        return run(ap.parse_args(argv))
    except GitError as e:
        print(f"auto_snapshot: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
