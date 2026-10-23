"""Study runs for a paper (spec 5.3 step 7), used by papers/<paper_id>/study/run.py.

start_run() refuses unless scope/prereg.json is committed at HEAD and unmodified, carries
"pinned_code" ({repo-relative posix path: sha256}, the key the research workflow writes), and every
pinned file still matches. A prespecified or confirmatory run also refuses a dirty working tree,
because the anchor is HEAD and would otherwise vouch for uncommitted code. Each run gets a fresh
study/runs/<run_id>/ that is never overwritten, raw inputs are frozen into study/data/ with their
sha256, NEXTGEN_FICC_CACHE points at the git-ignored study/cache/, and finish() writes results.json
and MANIFEST.json exactly once. compare_runs() checks an offline rerun from the frozen data. Trials
go to the paper-local ledger family PAPER-<paper_id> under paper_ledger_dir()
(core.quant.gate_ledger.family_ledger).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from importlib import metadata
from pathlib import Path

KINDS = ("exploratory", "prespecified", "confirmatory")
QUALIFICATIONS = ("qualified", "insufficient_data", "smoke_only", "not_run")
PACKAGES = ("numpy", "scipy", "pandas")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class StudyRefused(Exception):
    """A run that must not start, or a write that would change a frozen input or a finished run."""


@dataclass
class RunContext:
    paper_dir: Path
    run_id: str
    run_dir: Path
    kind: str
    seed: int
    inputs: dict[str, str]
    command: str = ""
    commit: str = ""
    clean: bool = False
    started_utc: str = ""
    prereg_sha256: str = ""
    vintages: dict[str, str] = field(default_factory=dict)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise StudyRefused("git is not on PATH") from exc


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "absent"


def start_run(paper_dir: Path, *, kind: str, seed: int, command: str, now_utc: str) -> RunContext:
    if kind not in KINDS:
        raise StudyRefused(f"kind {kind!r} not in {KINDS}")
    started = datetime.strptime(now_utc, "%Y-%m-%dT%H:%M:%SZ")      # ValueError on any other shape
    paper_dir = Path(paper_dir).resolve()
    top = _git(paper_dir, "rev-parse", "--show-toplevel")
    if top.returncode:
        raise StudyRefused(f"{paper_dir} is not inside a git work tree")
    root = Path(top.stdout.strip())
    prereg_rel = _git(paper_dir, "rev-parse", "--show-prefix").stdout.strip() + "scope/prereg.json"
    if _git(root, "cat-file", "-e", f"HEAD:{prereg_rel}").returncode:
        raise StudyRefused(f"{prereg_rel} is not committed at HEAD")
    if _git(root, "status", "--porcelain", "--", prereg_rel).stdout.strip():
        raise StudyRefused(f"{prereg_rel} differs from HEAD")
    prereg_bytes = (root / prereg_rel).read_bytes()
    try:
        prereg = json.loads(prereg_bytes.decode("utf-8"))
    except ValueError as exc:
        raise StudyRefused(f"{prereg_rel} is not JSON: {exc}") from exc
    pinned = prereg.get("pinned_code") if isinstance(prereg, dict) else None
    if not isinstance(pinned, dict):
        raise StudyRefused(f"{prereg_rel} lacks pinned_code {{repository-relative path: sha256}}")
    for rel, want in pinned.items():
        path = root / rel
        got = _sha(path.read_bytes()) if path.is_file() else "absent"
        if got != want:
            raise StudyRefused(f"pinned {rel}: sha256 {got} != prereg {want}")
    clean = not _git(root, "status", "--porcelain").stdout.strip()
    if kind != "exploratory" and not clean:
        raise StudyRefused(f"{kind} run refused: the working tree is dirty; commit first")
    commit = _git(root, "rev-parse", "HEAD").stdout.strip()
    run_id = f"{started:%Y%m%dT%H%M%SZ}-{commit[:7]}"
    run_dir = paper_dir / "study" / "runs" / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise StudyRefused(f"{run_dir} exists; runs are never overwritten") from exc
    cache = paper_dir / "study" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / ".gitignore").write_text("*\n", encoding="utf-8", newline="\n")     # ignores the cache and itself
    os.environ["NEXTGEN_FICC_CACHE"] = str(cache)
    return RunContext(paper_dir, run_id, run_dir, kind, int(seed), {}, command=command, commit=commit,
                      clean=clean, started_utc=now_utc, prereg_sha256=_sha(prereg_bytes))


def freeze_input(ctx: RunContext, name: str, data: bytes, *, vintage: str = "") -> Path:
    """Write study/data/<name> once; the same bytes again are a no-op, other bytes are refused."""
    if not NAME_RE.match(name):
        raise StudyRefused(f"input name {name!r} must be a plain file name")
    path = ctx.paper_dir / "study" / "data" / name
    if path.exists() and path.read_bytes() != data:
        raise StudyRefused(f"study/data/{name} is already frozen with other bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    ctx.inputs[name] = _sha(data)
    if vintage:
        ctx.vintages[name] = vintage
    return path


def finish(ctx: RunContext, results: dict, *, qualification: str, config: dict | None = None) -> Path:
    """Write run_dir/results.json and run_dir/MANIFEST.json (each exactly once); returns the manifest."""
    if qualification not in QUALIFICATIONS:
        raise StudyRefused(f"qualification {qualification!r} not in {QUALIFICATIONS}")
    body = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    study = ctx.paper_dir / "study"
    manifest = {
        "run_id": ctx.run_id, "kind": ctx.kind, "seed": ctx.seed, "command": ctx.command,
        "started_utc": ctx.started_utc, "qualification": qualification,
        "inputs": dict(sorted(ctx.inputs.items())), "vintages": dict(sorted(ctx.vintages.items())),
        "git": {"commit": ctx.commit, "clean": ctx.clean}, "prereg_sha256": ctx.prereg_sha256,
        "study_code": {p.name: _sha(p.read_bytes()) for p in sorted(study.glob("*.py"))},
        "python": sys.version, "packages": {n: _version(n) for n in PACKAGES},
        "timezone": {"tzname": list(time.tzname), "utc_offset_s": -time.timezone},
        "config": config or {}, "ficc_cache": str(study / "cache"), "results_sha256": _sha(body),
    }
    # serialised before any file exists, so a config that is not JSON raises with nothing written
    mbody = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    try:
        for name, data in (("results.json", body), ("MANIFEST.json", mbody)):
            with open(ctx.run_dir / name, "xb") as fh:
                fh.write(data)
    except FileExistsError as exc:
        raise StudyRefused(f"{ctx.run_dir} is already finished") from exc
    return ctx.run_dir / "MANIFEST.json"


def paper_ledger_dir(paper_dir: Path) -> Path:
    return Path(paper_dir) / "study" / "ledgers"


def compare_runs(a: Path, b: Path, *, rtol: float = 1e-9) -> list[str]:
    """Differences between two finished runs: frozen inputs, then every results.json leaf."""
    out = []
    ma, mb = (json.loads((Path(d) / "MANIFEST.json").read_text(encoding="utf-8")) for d in (a, b))
    if ma.get("inputs") != mb.get("inputs"):
        out.append("inputs differ: the runs did not read the same frozen data")
    ra, rb = (json.loads((Path(d) / "results.json").read_text(encoding="utf-8")) for d in (a, b))
    _diff(ra, rb, "results", rtol, out)
    return out


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _diff(x, y, where: str, rtol: float, out: list[str]) -> None:
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y:
                out.append(f"{where}.{k}: present in one run only")
            else:
                _diff(x[k], y[k], f"{where}.{k}", rtol, out)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            out.append(f"{where}: length {len(x)} != {len(y)}")
        for i, (u, v) in enumerate(zip(x, y)):
            _diff(u, v, f"{where}[{i}]", rtol, out)
    elif _num(x) and _num(y):
        if not (math.isclose(x, y, rel_tol=rtol, abs_tol=0.0) or (math.isnan(x) and math.isnan(y))):
            out.append(f"{where}: {x!r} != {y!r} (rtol {rtol})")
    elif x != y:
        out.append(f"{where}: {x!r} != {y!r}")
