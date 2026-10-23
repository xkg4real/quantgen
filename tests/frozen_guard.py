"""Frozen-study guard (spec 2026-10-23 section 3.1 point 4; D9).

The GROKTEAM-BOOK and paper_live H2 readouts run only from a local git clone checked out at the annotated tag TAG on the baseline
commit, so the main line is free to change. This module imports nothing from paper_live or grokteam (importing
paper_live.engine silences warnings): it reads git through subprocess and hashes with hashlib. It fails when

  (a) TAG is missing, is not an annotated tag, or no longer peels to TAG_COMMIT;
  (b) in the tagged tree, a PREREG-pinned file's sha256 differs from PREREG, or paper_live/engine.py or config.py
      differs from either out*/frozen_rule copy;
  (c) before LOOK_OPENS, grokteam/out/book/FORWARD_LOOK.json exists on main (an early look);
  (d) the interpreter's numpy, scipy or pandas differ from the PREREG pins while a readout is still pending.

Expiry: (a) and (b) stay forever as provenance; (c) and (d) retire once both readouts are committed. NotRun when
git is not on PATH. Clause (d) has no warn-only branch (spec 3.1 point 4 (d)): a dedicated pinned venv is set up, and
this clause rewritten, only if the global interpreter must move before the looks.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from tests.notrun import NotRun

ROOT = Path(__file__).resolve().parents[1]
TAG = "studies-of-record-2026-10-23"
TAG_COMMIT = "eacd57d2b0821ad796ab9b66d2d2c96a3d71081f"
PREREG = "grokteam/out/PREREG_book.json"
H2_FILES = ("engine.py", "config.py")
H2_PROFILES = ("paper_live/out", "paper_live/out_krx")
LOOK = "grokteam/out/book/FORWARD_LOOK.json"
LOOK_OPENS = datetime(2027, 2, 1, 1, 0, tzinfo=timezone.utc)
H2_FINAL = ("confirmed", "not confirmed")
LIBS = ("numpy", "scipy", "pandas")


def _git(*args: str) -> bytes:
    if shutil.which("git") is None:
        raise NotRun("OWNER: git is not on PATH; frozen_guard reads the tagged snapshot through git")
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    if r.returncode:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def _tagged(path: str) -> bytes:
    return _git("show", f"{TAG}:{path}")


def pending_readouts(root: Path = ROOT) -> list[str]:
    """Readouts not yet committed on main: the GROKTEAM look, and each H2 profile without a final verdict."""
    out = [] if (root / LOOK).exists() else ["GROKTEAM-BOOK forward look"]
    for d in H2_PROFILES:
        v = root / d / "verdict.json"
        status = json.loads(v.read_text(encoding="utf-8")).get("H2", {}).get("status") if v.exists() else None
        if status not in H2_FINAL:
            out.append(f"H2 {d}")
    return out


def test_a_tag_is_annotated_and_peels_to_the_baseline():
    kind = _git("cat-file", "-t", TAG).decode().strip()
    peeled = _git("rev-parse", "--verify", f"{TAG}^{{commit}}").decode().strip()
    assert kind == "tag" and peeled == TAG_COMMIT, f"{TAG} is a {kind} on {peeled}; want an annotated tag on {TAG_COMMIT}"


def test_b_tagged_pins_match_prereg_and_frozen_rule():
    pins = json.loads(_tagged(PREREG))["code"]
    bad = [p for p, h in sorted(pins.items()) if hashlib.sha256(_tagged(p)).hexdigest() != h]
    bad += [f"{d}/frozen_rule/{f}" for d in H2_PROFILES for f in H2_FILES
            if _tagged(f"paper_live/{f}") != _tagged(f"{d}/frozen_rule/{f}")]
    assert len(pins) == 10 and not bad, f"{TAG}: {len(pins)} pins; differs from its freeze: {bad}"


def test_c_no_forward_look_before_it_opens():
    early = datetime.now(timezone.utc) < LOOK_OPENS and (ROOT / LOOK).exists()
    assert not early, f"{LOOK} exists before {LOOK_OPENS.isoformat()}: the one GROKTEAM look was taken early"


def test_d_library_versions_match_the_pins_while_a_readout_is_pending():
    pending = pending_readouts()
    if not pending:
        return                                                    # both readouts committed: clause (d) retired
    pins = json.loads(_tagged(PREREG))["versions"]
    drift = [f"{lib} {version(lib)} != {pins[lib]}" for lib in LIBS if version(lib) != pins[lib]]
    assert not drift, f"{drift} while pending: {pending}; read out from a venv pinned to {pins}"


def test_d_pending_readouts_retire_only_when_all_three_are_in():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert pending_readouts(root) == ["GROKTEAM-BOOK forward look", "H2 paper_live/out", "H2 paper_live/out_krx"]
        (root / LOOK).parent.mkdir(parents=True)
        (root / LOOK).write_text("{}", encoding="utf-8")
        for d, status in zip(H2_PROFILES, ("not confirmed", "pending")):
            (root / d).mkdir(parents=True)
            (root / d / "verdict.json").write_text(json.dumps({"H2": {"status": status}}), encoding="utf-8")
        assert pending_readouts(root) == ["H2 paper_live/out_krx"]
        (root / H2_PROFILES[1] / "verdict.json").write_text(json.dumps({"H2": {"status": "confirmed"}}), encoding="utf-8")
        assert pending_readouts(root) == []


def tests():
    return sorted((n, v) for n, v in globals().items() if n.startswith("test_") and callable(v))
