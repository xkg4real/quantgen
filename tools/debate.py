"""Referee runner for the paper pipeline (spec 5.3 step 10, D6).

`run_referee` runs one referee CLI (Codex or Antigravity `agy`) headless, with a disposable review bundle as
cwd, and classifies the outcome. Any status but `ok` makes the round REVIEW_INCOMPLETE; it is never read as
"no objections". `parse_report` splits a Markdown report into its `## Major` and `## Minor` issues, and
`has_report_headings` (both headings present) is the test every report must pass before it counts as `ok`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Referee:
    name: str
    kind: str                 # "codex" | "agy"
    model: str | None
    exe: str


@dataclass
class RefereeResult:
    name: str
    status: str               # "ok" | "missing_cli" | "auth_failed" | "quota" | "timeout" | "error"
    report_md: str
    raw_path: Path | None
    reset_at: str | None      # quota only: machine-local "YYYY-MM-DDTHH:MM" parsed from Codex's message
    version: str | None
    note: str = ""            # why a non-ok run failed, when the runner can tell (panel.record files it)


# Sent to every CLI referee, in the prompt and in each REVIEW_BRIEF.md (tools.paper.panel). Headless agy auto-denies a
# shell command and then replies empty (status SUCCESS, response ""), so it is told up front.
NO_SHELL = ("Do not run any shell command: commands are blocked in this sandbox. Read the files with your "
            "file-reading and search tools only. Your final message must be the full Markdown report itself.")


DEFAULT_REFEREES = [
    Referee("gpt_codex", "codex", None, "codex"),
    Referee("gemini_agy", "agy", "gemini-4-argon-high",
            os.environ.get("QUANTGEN_AGY", r"C:\Users\whydi\AppData\Local\agy\bin\agy.exe")),
]

_MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
_QUOTA_RE = re.compile(r"usage limit", re.I)
_RESET_RE = re.compile(r"try again at (\w{3})\w* (\d{1,2})(?:st|nd|rd|th)?, (\d{4}) (\d{1,2}):(\d{2}) ([AP]M)")
_AUTH_RE = re.compile(r"not logged in|log ?in required|please (?:log|sign) ?in|unauthori[sz]ed|\b401\b", re.I)
_HEADING_RE = re.compile(r"^##\s+(major|minor)\b", re.I | re.M)
_ID_RE = re.compile(r"\**\s*((?i:major|minor)-\d+|[Mm]-?\d+)\b")


def has_report_headings(md: str) -> bool:
    """True when the report has both a `## Major` and a `## Minor` heading. Anything else (one of them, `# Major`,
    `**Major**`, `## Main issues`) is malformed, never "no objections": parse_report drops text under other headings."""
    return {h.lower() for h in _HEADING_RE.findall(md or "")} == {"major", "minor"}


def _run(argv, *, input=None, cwd=None, timeout=None):
    """subprocess.run with UTF-8 pipes whose timeout kills the whole process tree before draining the pipes.

    subprocess.run's own timeout kills only the child and then waits on pipes that grandchildren
    (codex.cmd -> node -> codex.exe) still hold open, so it can hang for the whole referee run.
    """
    with subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace") as proc:
        try:
            out, err = proc.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            out, err = proc.communicate()
            raise subprocess.TimeoutExpired(argv, timeout, out, err) from None
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def _text(value) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else (value or "")


def _version(exe: str, runner) -> str | None:
    try:
        proc = runner([exe, "--version"], input=None, cwd=None, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return _text(proc.stdout).strip() or None


def _reset_at(text: str) -> str | None:
    m = _RESET_RE.search(text)
    if not m or m[1] not in _MONTHS:
        return None
    hour = int(m[4]) % 12 + (12 if m[6] == "PM" else 0)
    return f"{m[3]}-{_MONTHS.index(m[1]) + 1:02d}-{int(m[2]):02d}T{hour:02d}:{m[5]}"


def _save_raw(out_dir: Path, ref: Referee, argv, version, returncode, stdout: str, stderr: str) -> Path:
    path = out_dir / f"{ref.name}_raw.json"
    path.write_text(json.dumps({"argv": list(argv), "version": version, "returncode": returncode,
                                "stdout": stdout, "stderr": stderr}, indent=2, ensure_ascii=False),
                    encoding="utf-8", newline="\n")
    return path


def run_referee(ref: Referee, bundle: Path, prompt: str, out_dir: Path, *, timeout_s: int = 1500,
                runner=None) -> RefereeResult:
    """Run one referee in `bundle` (its cwd) and classify the outcome.

    `runner(argv, *, input, cwd, timeout)` returns an object with `returncode`, `stdout`, `stderr` (str) and
    may raise FileNotFoundError or subprocess.TimeoutExpired; it defaults to `_run`. Codex reads the prompt
    from stdin (`-`), which keeps it away from cmd.exe quoting in the npm `codex.cmd` shim.
    """
    runner = runner or _run
    # Absolute: the child runs with the bundle as cwd, so a relative --output-last-message would land under it.
    bundle, out_dir = Path(bundle).resolve(), Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = shutil.which(ref.exe)
    if exe is None:
        return RefereeResult(ref.name, "missing_cli", "", None, None, None)
    model = ["--model", ref.model] if ref.model else []
    last = out_dir / f"{ref.name}_last_message.md"
    if ref.kind == "codex":
        last.unlink(missing_ok=True)       # a stale report from an earlier run must never count
        argv = [exe, "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-C", str(bundle),
                "--output-last-message", str(last), *model, "-"]
        stdin = prompt
    elif ref.kind == "agy":
        argv = [exe, "-p", prompt, *model, "--sandbox", "--disable-slash-commands", "--output-format", "json",
                "--print-timeout", f"{timeout_s}s"]
        stdin = None
    else:
        raise ValueError(f"unknown referee kind {ref.kind!r}")
    version = _version(exe, runner)
    try:
        # One minute over the budget, so agy's own --print-timeout gets to stop it cleanly first.
        proc = runner(argv, input=stdin, cwd=str(bundle), timeout=timeout_s + 60)
    except FileNotFoundError:
        return RefereeResult(ref.name, "missing_cli", "", None, None, version)
    except subprocess.TimeoutExpired as exc:
        raw = _save_raw(out_dir, ref, argv, version, None, _text(exc.stdout), _text(exc.stderr))
        return RefereeResult(ref.name, "timeout", "", raw, None, version)
    out, err = _text(proc.stdout), _text(proc.stderr)
    raw = _save_raw(out_dir, ref, argv, version, proc.returncode, out, err)
    report, note = "", ""
    if ref.kind == "codex":
        report = last.read_text(encoding="utf-8").strip() if last.is_file() else ""
    else:
        try:
            envelope = json.loads(out)
        except json.JSONDecodeError:
            envelope = None
        if isinstance(envelope, dict) and envelope.get("status") == "SUCCESS":
            report = str(envelope.get("response") or "").strip()
            denied = envelope.get("denied_actions")
            if not report and isinstance(denied, list) and denied:
                kinds = sorted({str(d.get("action")) for d in denied if isinstance(d, dict)})
                what = "a shell command" if kinds == ["command"] else "action(s) " + ", ".join(kinds)
                note = (f"agy denied {what} and replied empty: headless mode cannot approve tools, "
                        "so the referee left no report")
    if proc.returncode == 0 and has_report_headings(report):
        return RefereeResult(ref.name, "ok", report, raw, None, version)
    text = out + "\n" + err
    if _QUOTA_RE.search(text):
        return RefereeResult(ref.name, "quota", report, raw, _reset_at(text), version, note)
    status = "auth_failed" if _AUTH_RE.search(text) else "error"
    return RefereeResult(ref.name, status, report, raw, None, version, note)


_STARTS = [re.compile(p) for p in (
    r"###+\s+",                                          # a `###` heading per issue
    r"(?:[-*]|\d+[.)])\s+",                              # a top-level bullet or numbered line
    r"(?=\*\*\s*(?i:major-|minor-|m-?)\d+\b)")]            # a bold-led paragraph: **M1. Title.** text
_RULE_RE = re.compile(r"\s*(?:[-_*]\s*){3,}")             # a horizontal rule, never an issue
_NONE_RE = re.compile(r"(?:none|n/a|nil|no (?:(?:major|minor) )?(?:issues?|concerns?|objections?|problems?))"
                      r"(?: (?:identified|found|noted|raised))?")


def _items(lines: list[str], prefix: str) -> list[dict]:
    lines = [l for l in lines if not _RULE_RE.fullmatch(l)]
    start = next((p for p in _STARTS if any(p.match(l) for l in lines)), None)
    chunks: list[list[str]] = []
    for line in lines:
        m = start and start.match(line)
        if m:
            chunks.append([line[m.end():].strip()])
        elif chunks and line.strip():
            chunks[-1].append(line.strip())
    if not chunks:
        # No item shape matched (plain prose, a table, an indented list). Text there is still an objection, so
        # keep the body as one item; only an explicit "none" / "n/a" means the section is empty.
        body = [l.strip() for l in lines if l.strip()]
        if body and not _NONE_RE.fullmatch(re.sub(r"[\s*_.!:()\-]+", " ", " ".join(body)).strip().lower()):
            chunks = [body]
    out, seen = [], set()
    for n, chunk in enumerate(chunks, 1):
        text = "\n".join(chunk)
        m = _ID_RE.match(text)
        base = m[1] if m else f"{prefix}{n}"
        ident, k = base, 1
        while ident.lower() in seen:                      # an explicit M2 and a positional M2 must not collide
            k += 1
            ident = f"{base}-{k}"
        seen.add(ident.lower())
        out.append({"id": ident, "text": text})
    return out


def parse_report(md: str) -> dict:
    """{"major": [...], "minor": [...]}, each a list of {"id", "text"}.

    Sections are `## Major...` / `## Minor...` headings (any case); any other `##` heading ends one. An issue is
    a `###` heading when the section has any, else a top-level `-`, `*` or `1.` line, else a bold-led `**M1.`
    paragraph; the lines below it belong to it. A section with text but none of those shapes (prose, a table) is
    one item holding the whole body; only none / n/a / "no issues" leaves it empty, so a report is never read
    as "no objections" by accident. A leading id (M1, m2, MAJOR-3) is kept, otherwise M<n> / m<n> is generated
    by position; a repeated id gets a `-2`, `-3` suffix so ids are unique within a section.
    """
    bodies: dict[str, list[str]] = {"major": [], "minor": []}
    kind = None
    for line in md.splitlines():
        if re.match(r"##(?!#)", line):
            m = _HEADING_RE.match(line)
            kind = m[1].lower() if m else None
        elif kind:
            bodies[kind].append(line)
    return {"major": _items(bodies["major"], "M"), "minor": _items(bodies["minor"], "m")}
