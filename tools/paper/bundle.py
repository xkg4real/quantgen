"""Review bundle for one referee round (spec 5.3 step 10).

A fresh, disposable temp folder holding the manuscript (en/, ko/, common/), study/numbers.json, the latest
run's MANIFEST.json and results.json, the study code (study/*.py), scope/prereg.json with every repository
file it pins or adds (pinned_code, new_code) under code/<path>, and refs.yaml, refs.bib and claims.yaml.
Referees run with it as cwd, never the repo. Raw data, the other scope files and review files stay out. A claim
backed by the owner's private notes (refs class `local_note`) refuses the bundle unless the owner allows it.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import yaml


def _private_claims(paper_dir: Path) -> list[str]:
    claims, refs = paper_dir / "claims.yaml", paper_dir / "refs.yaml"
    if not claims.is_file() or not refs.is_file():
        return []
    private = {r.get("key") for r in yaml.safe_load(refs.read_text(encoding="utf-8")) or []
               if r.get("class") == "local_note"}
    rows = yaml.safe_load(claims.read_text(encoding="utf-8")) or []
    return sorted({str(r.get("source_key")) for r in rows if r.get("source_key") in private})


def _study_code(paper_dir: Path) -> list[tuple[Path, str]]:
    """(source, bundle path): scope/prereg.json and each repository file it pins or adds, as code/<path>."""
    prereg = paper_dir / "scope" / "prereg.json"
    if not prereg.is_file():
        return []
    data = json.loads(prereg.read_text(encoding="utf-8"))
    root = paper_dir.resolve().parents[1]                  # papers/<paper_id> -> the repository root
    out = [(prereg, "scope/prereg.json")]
    for rel in [*(data.get("pinned_code") or {}), *(data.get("new_code") or [])]:
        src = (root / rel).resolve()
        if root in src.parents and src.is_file():
            out.append((src, f"code/{src.relative_to(root).as_posix()}"))
    return out


def make_bundle(paper_dir: Path, round_k: int, *, allow_private: bool = False,
                dest_root: Path | None = None) -> Path:
    paper_dir = Path(paper_dir)
    if not (paper_dir / "en" / "paper_en.tex").is_file():
        raise ValueError(f"{paper_dir}: en/paper_en.tex is missing; nothing to review")
    private = [] if allow_private else _private_claims(paper_dir)
    if private:
        raise ValueError(f"claims.yaml cites private local_note sources {private}; "
                         "pass allow_private=True only with the owner's consent")
    if dest_root is not None:
        Path(dest_root).mkdir(parents=True, exist_ok=True)
    bundle = Path(tempfile.mkdtemp(prefix=f"qg_{paper_dir.name}_r{round_k}_", dir=dest_root))
    for name in ("en", "ko", "common"):
        if (paper_dir / name).is_dir():
            shutil.copytree(paper_dir / name, bundle / name, ignore=shutil.ignore_patterns("__pycache__"))
    study = paper_dir / "study"
    picks = [study / "numbers.json", paper_dir / "refs.yaml", paper_dir / "refs.bib", paper_dir / "claims.yaml",
             *sorted(study.glob("*.py"))]
    runs = sorted(p for p in (study / "runs").glob("*") if p.is_dir())   # run ids sort by time
    if runs:
        picks += [runs[-1] / "MANIFEST.json", runs[-1] / "results.json"]
    copies = [(src, src.relative_to(paper_dir).as_posix()) for src in picks] + _study_code(paper_dir)
    for src, rel in copies:
        if src.is_file():
            dst = bundle / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return bundle
