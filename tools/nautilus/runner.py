"""The parent of the NautilusTrader bridge (spec 2026-10-26 section 5.3), run in the global interpreter.

    python -B -m tools.nautilus.runner --table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp> [--child-cmd <json>]
    python -B -m tools.nautilus.runner --table <t> --of-record [--rerun-of <id> --reason <text>]
    python -B -m tools.nautilus.runner --check-env | --egress-record | --fixtures [--record-baseline | --write-goldens]
    python -B -m tools.nautilus.runner --fingerprint --table <t> | --timing | --handoff-report

A run registers every variant in its family ledger before any child starts, computes QUANTGEN's reference matrices
with `simulate`, starts one child per (column, cost level) through the launch contract of launch.py, rebuilds each
child's daily returns from its fills (5.3.3) and checks every child (section 7). Steps 16 and 17 (parity, gate and
card) sit behind `parity_and_gate`, in tools/nautilus/parity.py. Exit codes: 0 card written, a clean rehearsal or a
mode's success; 1 WITHHELD; 2 refused before registration; 3 refused at registration; 4 ERROR; 5 ABORTED. The last
console line of every mode is `STATUS <status> exit=<n> record=<path or ->`. The runner never imports the engine
(spec 5.6 rule C2); it reads the venv's own files through launch.py.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import types
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path, PurePath
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from core.quant import gate_ledger, validate
from core.quant import strategies as S
from tools.nautilus import launch
from tools.nautilus.launch import BridgeRefusal, ChildInvalid

for _stream in (sys.stdout, sys.stderr):              # spec 3.7: the house locale is cp949
    with contextlib.suppress(Exception):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = launch.REPO_ROOT
STUDY_FILE = Path("docs") / "asset_expansion_study.py"
DGS3MO_FILE = "docs/asset_expansion/cache/fred_DGS3MO.csv"
SCRIPT = "tools/nautilus/runner.py"
STATUSES = ("IN_PROGRESS", "CARD_WRITTEN", "WITHHELD", "REFUSED_REGISTRATION", "ERROR", "ABORTED")
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}
TABLE_SCHEMA, INPUT_SCHEMA, RUN_SCHEMA = "nautilus-bridge-table/1", "nautilus-bridge-input/2", "nautilus-bridge-run/2"
GOLDEN_SCHEMA, CENSUS_SCHEMA = "nautilus-bridge-golden/1", "nautilus-bridge-census/1"
EGRESS_SCHEMA = "nautilus-bridge-egress/1"
FRESH_S = 600                                       # R-16: a ledger written less than 600 s ago
PRICE_DECIMALS = 9                                  # 5.3.2 step 5: closes = np.round(raw, 9), the one rounding
PINNED_REAL_MD5 = {"SPY": "d2164597d576e1b2fcadde063065811d", "BTC-USD": "bc76f530ff24ab445367fe826150bc10"}
LAYER = "QUANTGEN-nautilus-block-out" if os.name == "nt" else "unshare -rn"
GOLDEN_FIXTURES = ("F1", "F2", "N1")
DENIED_CENSUS = ("nautilus_trader.adapters", "nautilus_trader.network")      # 5.2.7 (C-08)
CRYPTO_DEFAULTS = {"lookbacks": [7, 14, 21, 28], "mas": [10, 20, 50, 100, 200]}
FN = {"trend_switch": S.trend_switch, "crypto_trend": S.crypto_trend}
SHAPES = {"trend_switch": {"family_id": "E1", "instrument": "SPY", "keys": ({"rule", "lookback", "step"},)},
          "crypto_trend": {"family_id": "C3", "instrument": "BTC/USD",
                           "keys": ({"hysteresis"}, {"hysteresis", "lookbacks", "mas"})}}
PILOTS = {"E1-SPY": {"strategy": "trend_switch", "family_id": "E1", "rule": "E1", "market": "US", "symbol": "SPY",
                     "instrument": "SPY", "size_precision": 0},
          "C3-BTCUSD": {"strategy": "crypto_trend", "family_id": "C3", "rule": "C3", "market": "CRYPTO",
                        "symbol": "BTC-USD", "instrument": "BTC/USD", "size_precision": 8}}
PILOT_VALUES = {"capital_usd": "1000000", "price_precision": 9, "volume": "1000000000", "fill_seed": 42}
TABLE_TYPES = {                                     # spec 6.6: field -> (types, null allowed)
    "schema": ((str,), False), "pilot": ((str,), False), "family_id": ((str,), False), "rule": ((str,), False),
    "market": ((str,), False), "strategy": ((str,), False), "symbol": ((str,), False), "instrument": ((str,), False),
    "prices_file": ((str,), False), "prices_md5": ((str,), False), "start": ((str,), False), "end": ((str,), False),
    "rf_file": ((str,), True), "rf_md5": ((str,), True), "axes": ((dict,), False), "grid": ((list,), False),
    "cost_bps": ((int, float), False), "embargo": ((int,), False), "capital_usd": ((str,), False),
    "price_precision": ((int,), False), "size_precision": ((int,), False), "volume": ((str,), False),
    "fill_seed": ((int,), False), "domain": ((dict,), True), "hypothesis": ((str,), False),
    "claim_label": ((str,), False), "card_id": ((str,), False), "study_configs": ((list,), False),
    "reference_card": ((str,), True), "reference_card_md5": ((str,), True)}
OWNER_FIELDS = ("owner_confirmed", "host_fingerprint")
FILLS_HEADER = ("ts_event", "order_side", "last_qty", "last_px", "commission", "commission_ccy", "trade_id",
                "venue_order_id")
DECISIONS_HEADER = ("i", "ts_event", "decision", "margin", "action")
EQUITY_HEADER = ("i", "ts_event", "close", "cash", "qty", "equity_pre")
REMEDY = {                                          # section 7's Remedy column, printed after the message
    "R-01": "commit or remove the printed paths",
    "R-02": 'packed ref: git commit --allow-empty -m "nautilus: re-anchor", then git push; worktree: use the main clone',
    "R-03": launch.VENV_FIX,
    "R-04": "restore the pinned bytes; new bytes need an owner ruling",
    "R-05": "as R-04: restore the pinned bytes; new bytes need an owner ruling",
    "R-06": "as R-04: restore the pinned bytes; new bytes need an owner ruling",
    "R-07": "a table cost at or above the printed floor",
    "R-08": "restore GATE (git diff core/quant/validate.py)",
    "R-09": "stop; an owner ruling",
    "R-10": "temp dirs; synthetic data only",
    "R-11": "fix the printed field; after a change, --fingerprint and a new owner_confirmed (7A.3); pilot 1 first "
            "(Step 8)",
    "R-12": "read the traceback; the rows stay; re-run under R-17",
    "R-13": "stop; an owner ruling",
    "R-14": ("Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Get-NetFirewallApplicationFilter and "
             "Get-NetFirewallProfile | Select Name, Enabled (a third-party firewall can disable these rules); if the "
             "filter's Program is not <printed path>\\py313\\python.exe, or the rule is disabled or not -Profile Any, "
             "the two elevated firewall lines of 7A.2 again, the first removing the rule by name and the second "
             "creating it; then --egress-record" if os.name == "nt" else "a Linux host with user namespaces"),
    "R-15": "the owner rules how the ledger starts (O11); --fingerprint on this host",
    "R-16": "wait the printed seconds, or end the runner holding the printed lock",
    "R-17": '--rerun-of <id> --reason "<text>"'}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_HEX = {32: re.compile(r"[0-9a-f]{32}"), 64: re.compile(r"[0-9a-f]{64}")}
_MISSING = object()
_TEMP_ROOTS: tuple[str, str] | None = None


def refuse(rid: str, message: str) -> BridgeRefusal:
    """A section-7 refusal with its remedy: `raise refuse("R-05", "...")`."""
    return BridgeRefusal(rid, message, REMEDY[rid])


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _under(path: str, root: str) -> bool:
    return path.startswith(root.rstrip(os.sep) + os.sep)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _json_text(obj) -> str:
    """C1: every JSON file the bridge writes, except input.json and the card."""
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def _int_text(x, lo: int, hi: float) -> bool:
    return isinstance(x, str) and x.isascii() and x.isdigit() and x == str(int(x)) and lo <= int(x) <= hi


def _is_int(x, lo: int, hi: int) -> bool:
    return type(x) is int and lo <= x <= hi


# --------------------------------------------------------------------------- #
# Temp root, digests, run id (spec 3.9, 6.6, 5.3.5)
# --------------------------------------------------------------------------- #
def temp_roots() -> tuple[str, str]:
    """The temp root in its two forms, computed once per process (3.9; OPS-R4-4)."""
    global _TEMP_ROOTS
    if _TEMP_ROOTS is None:
        d = tempfile.mkdtemp(prefix="qgnb_root_")
        os.rmdir(d)
        _TEMP_ROOTS = (_norm(tempfile.gettempdir()), _norm(os.path.dirname(d)))
    return _TEMP_ROOTS


def inside_temp_root(path) -> bool:
    """True for an absolute path under either form of the temp root and not under the repository (3.9)."""
    if not os.path.isabs(str(path)):
        return False
    p = _norm(path)
    return any(_under(p, root) for root in temp_roots()) and not _under(p, _norm(REPO_ROOT)) and p != _norm(REPO_ROOT)


def table_sha256(table: dict) -> str:
    """6.6: the SHA-256 of the table's sorted, compact JSON without owner_confirmed and host_fingerprint."""
    t = {k: v for k, v in table.items() if k not in OWNER_FIELDS}
    return hashlib.sha256(json.dumps(t, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def code_paths(repo_root: Path) -> list[Path]:
    """6.6: tools/nautilus/**/*.py, tools/nautilus/golden/*.json, requirements-nautilus.txt, the harness sources,
    docs/asset_expansion_study.py and config.py, sorted."""
    from core.quant.gate_package import HARNESS_SOURCES
    root = Path(repo_root)
    found = set((root / "tools" / "nautilus").rglob("*.py")) | set((root / "tools" / "nautilus" / "golden").glob("*.json"))
    found |= {root / p for p in ("requirements-nautilus.txt", *HARNESS_SOURCES, STUDY_FILE.as_posix(), "config.py")}
    return sorted(found)


def code_digest(repo_root: PurePath, paths: Sequence[PurePath], read: Callable[[PurePath], bytes]) -> str:
    """6.6: the SHA-256 of the sorted lines "<path relative to the root, as posix>,<sha256 of its bytes>"."""
    lines = sorted(f"{p.relative_to(repo_root).as_posix()},{hashlib.sha256(read(p)).hexdigest()}" for p in paths)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def code_sha256(repo_root: Path) -> str:
    return code_digest(Path(repo_root), code_paths(repo_root), lambda p: Path(p).read_bytes())


def host_fingerprint(hostname: str, ledger: gate_ledger.FamilyLedger) -> str | None:
    """6.6: sha256(hostname + "\\n" + the family ledger's first row_md5); None when the ledger holds no row."""
    rows = ledger.rows()
    if not rows:
        return None
    return hashlib.sha256((hostname + "\n" + rows[0]["row_md5"]).encode("utf-8")).hexdigest()


def bridge_run_id(now: datetime, table_sha256: str) -> str:
    """5.3.5: NB-<UTC %Y%m%dT%H%M%S%fZ>-<first 8 hex of table_sha256>; outside every result hash."""
    return f"NB-{now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{table_sha256[:8]}"


# --------------------------------------------------------------------------- #
# Step 0: lock, freshness, earlier runs (5.3.5; R-16, R-17)
# --------------------------------------------------------------------------- #
class TableLock:
    """A non-blocking OS lock on <out root>/.locks/<16 hex>.lock, held for the whole run."""

    def __init__(self, path: Path, fh) -> None:
        self.path, self._fh = path, fh

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fh, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self._fh.close()
            self._fh = None


def _earlier_runs(out_root: Path, table_sha: str) -> tuple[list[dict], list[str]]:
    """Every earlier run record of this table, best effort, and the ones the re-run policy does not pass."""
    earlier, blocking = [], []
    for path in sorted(out_root.glob(f"NB-*-{table_sha[:8]}/run.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            if rec["table"]["table_sha256"] != table_sha:
                continue
            entry = {"bridge_run_id": rec["bridge_run_id"], "status": rec["status"]}
            reasons = rec.get("withheld_reasons") or []
            ok = rec["status"] in ("IN_PROGRESS", "ABORTED", "ERROR") or (
                rec["status"] == "WITHHELD" and bool(reasons) and all(str(r).startswith("C-06") for r in reasons))
        except (OSError, ValueError, KeyError, TypeError):
            entry, ok = {"bridge_run_id": path.parent.name, "status": "UNREADABLE"}, False
        earlier.append(entry)
        if not ok:
            blocking.append(f"{entry['bridge_run_id']} {entry['status']}")
    return earlier, blocking


def take_lock(out_root: Path, table_sha256: str, ledger_paths: Sequence[Path], rerun_of: str | None
              ) -> tuple[TableLock, list[dict]]:
    """Step 0: the table lock (R-16 when held), the freshness of C3.jsonl and the family ledger (R-16 under 600 s),
    the earlier records of this table and the re-run policy (R-17). Returns the lock and earlier_runs."""
    locks = Path(out_root) / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    path = locks / f"{table_sha256[:16]}.lock"
    fh = open(path, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise refuse("R-16", f"another runner is active: it holds {path}")
    lock = TableLock(path, fh)
    try:
        now = time.time()
        for ledger in ledger_paths:
            if Path(ledger).exists() and now - Path(ledger).stat().st_mtime < FRESH_S:
                wait = FRESH_S - (now - Path(ledger).stat().st_mtime)
                raise refuse("R-16", f"{ledger} was modified less than {FRESH_S} s ago; wait {wait:.0f} s")
        earlier, blocking = _earlier_runs(Path(out_root), table_sha256)
        if blocking and rerun_of is None:
            raise refuse("R-17", f"earlier runs of this table: {', '.join(blocking)}")
        if rerun_of is not None and rerun_of not in {e["bridge_run_id"] for e in earlier}:
            raise refuse("R-17", f"--rerun-of {rerun_of} names no earlier run of this table")
        return lock, earlier
    except BaseException:
        lock.release()
        raise


# --------------------------------------------------------------------------- #
# Step 1: the registration table (6.6; R-10, R-11, R-15, R-09)
# --------------------------------------------------------------------------- #
def load_table(path: Path) -> tuple[dict, bytes]:
    """The table as one JSON object, read with utf-8-sig (3.7), and its raw bytes; R-11 otherwise."""
    try:
        raw = Path(path).read_bytes()
        table = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise refuse("R-11", f"the table {path} is not readable JSON: {exc}") from exc
    if not isinstance(table, dict):
        raise refuse("R-11", f"the table {path} is not a JSON object")
    return table, raw


def _check_place(t: dict, mode: str, repo_root: Path) -> None:
    """R-10 (rehearsal) and R-11 (of-record) by place alone, before any data file is opened (QA-R4-2)."""
    named = {k: t.get(k) for k in ("prices_file", "rf_file", "reference_card") if t.get(k) is not None}
    if any(not isinstance(v, str) for v in named.values()):
        raise refuse("R-11", f"file fields must be strings: {named}")
    if mode == "rehearsal":
        bad = [k for k in ("prices_file", "reference_card") if k in named and not inside_temp_root(named[k])]
        rf = named.get("rf_file")
        if rf is not None and not inside_temp_root(rf) and _norm(Path(repo_root) / rf) != _norm(Path(repo_root) / DGS3MO_FILE):
            bad.append("rf_file")
        if bad:
            raise refuse("R-10", f"rehearsal files outside the temp root {temp_roots()}: "
                                 + ", ".join(f"{k}={named[k]!r}" for k in bad))
        return
    root = _norm(repo_root)
    bad = [k for k, v in named.items() if os.path.isabs(v) or not _under(_norm(Path(repo_root) / v), root)]
    if bad:
        raise refuse("R-11", "of-record files must be repo-relative paths inside the repository: "
                             + ", ".join(f"{k}={named[k]!r}" for k in bad))


def _check_fields(t: dict, mode: str) -> None:
    """R-11: exactly 6.6's fields, each of its type; the owner fields are required in of-record mode only."""
    unknown = sorted(set(t) - set(TABLE_TYPES) - set(OWNER_FIELDS))
    required = list(TABLE_TYPES) + (list(OWNER_FIELDS) if mode == "of-record" else [])
    missing = [k for k in required if k not in t]
    if unknown or missing:
        raise refuse("R-11", f"table fields: unknown {unknown}, missing {missing}")
    types_ = dict(TABLE_TYPES, **{k: ((str,), False) for k in OWNER_FIELDS})
    wrong = [k for k, (allowed, null) in types_.items() if k in t and not (
        (t[k] is None and null) or (isinstance(t[k], allowed) and not isinstance(t[k], bool)))]
    if wrong:
        raise refuse("R-11", "wrong types: " + ", ".join(f"{k}={t[k]!r}" for k in wrong))


def _check_column(strategy: str, theta) -> bool:
    """One grid column has exactly the strategy's keys, each in the child's range (6.1)."""
    if not isinstance(theta, dict) or set(theta) not in SHAPES[strategy]["keys"]:
        return False
    if strategy == "trend_switch":
        return theta["rule"] in ("sma", "tsmom") and _is_int(theta["lookback"], 1, 5000) and _is_int(theta["step"], 1, 5000)
    lists = [theta.get(k, CRYPTO_DEFAULTS[k]) for k in ("lookbacks", "mas")]
    return (type(theta["hysteresis"]) is float and 0.0 <= theta["hysteresis"] < 1.0
            and all(isinstance(v, list) and 1 <= len(v) <= 16 and all(_is_int(x, 1, 5000) for x in v) for v in lists))


def _check_values(t: dict, mode: str) -> None:
    """R-11: schema, pilot shape and values, dates, digests' form, child ranges and grid == grid_from(**axes)."""
    bad = []
    if t["schema"] != TABLE_SCHEMA:
        bad.append(f"schema {t['schema']!r}")
    if (mode == "of-record") != (t["pilot"] in PILOTS) or (mode == "rehearsal" and t["pilot"] != "rehearsal"):
        bad.append(f"pilot {t['pilot']!r} in {mode} mode")
    shape = SHAPES.get(t["strategy"])
    if shape is None or t["family_id"] != shape["family_id"] or t["rule"] != t["family_id"] or t["instrument"] != shape["instrument"]:
        bad.append(f"strategy {t['strategy']!r}, family_id {t['family_id']!r}, rule {t['rule']!r}, "
                   f"instrument {t['instrument']!r} do not form a pilot shape")
    if mode == "of-record" and t["pilot"] in PILOTS:
        bad += [f"{k} {t.get(k)!r} (pilot value {v!r})" for k, v in {**PILOTS[t["pilot"]], **PILOT_VALUES}.items()
                if t.get(k) != v]
    if not (_DATE.fullmatch(t["start"]) and _DATE.fullmatch(t["end"]) and t["start"] <= t["end"]):
        bad.append(f"start {t['start']!r} and end {t['end']!r}")
    if not _HEX[32].fullmatch(t["prices_md5"]) or (t["rf_file"] is None) != (t["rf_md5"] is None) or (
            t["rf_md5"] is not None and not _HEX[32].fullmatch(t["rf_md5"])):
        bad.append("prices_md5, rf_file or rf_md5")
    if (t["reference_card"] is None) != (t["reference_card_md5"] is None):
        bad.append("reference_card and reference_card_md5 go together")
    if not re.fullmatch(r"[A-Za-z0-9.^=-]+", t["symbol"]):
        bad.append(f"symbol {t['symbol']!r}")
    if not (0.0 <= float(t["cost_bps"]) <= 1000.0) or t["embargo"] < 0:
        bad.append(f"cost_bps {t['cost_bps']!r} or embargo {t['embargo']!r}")
    if not (_int_text(t["capital_usd"], 1, 9223372036) and t["price_precision"] == PRICE_DECIMALS
            and _is_int(t["size_precision"], 0, 9) and _int_text(t["volume"], 1, 18446744073)
            and _is_int(t["fill_seed"], 0, 2**32 - 1)):
        bad.append("capital_usd, price_precision (9), size_precision, volume or fill_seed outside spec 6.1 and 3.6")
    if not all(isinstance(v, list) for v in t["axes"].values()) or t["grid"] != S.grid_from(**t["axes"]):
        bad.append("grid differs from grid_from(**axes), whose order follows the axes keys (keep the study's call order)")
    elif shape is not None and not (t["grid"] and all(_check_column(t["strategy"], g) for g in t["grid"])):
        bad.append("a grid column has the wrong keys or a value outside spec 6.1")
    if not all(isinstance(c, dict) and set(c) == {"source", "symbols", "cost_bps", "params"} for c in t["study_configs"]):
        bad.append("study_configs entries are {source, symbols, cost_bps, params}")
    if bad:
        raise refuse("R-11", "; ".join(bad))


def _check_reference(t: dict, repo_root: Path) -> None:
    """R-11: the reference card's bytes match reference_card_md5 (QUANT-R3-3)."""
    if t["reference_card"] is None:
        return
    path = Path(t["reference_card"]) if os.path.isabs(t["reference_card"]) else Path(repo_root) / t["reference_card"]
    try:
        found = hashlib.md5(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise refuse("R-11", f"reference_card {t['reference_card']!r} cannot be read: {exc}") from exc
    if found != t["reference_card_md5"]:
        raise refuse("R-11", f"reference_card md5 {found} differs from reference_card_md5 {t['reference_card_md5']}")


def e1_parity_passed(repo_root: Path, code: str) -> bool:
    """GOVERNANCE-R4-4: an of-record E1-SPY record under <repo>/docs/nautilus_bridge/runs/ with parity.hard_pass
    true, 12 registered columns and this code_sha256."""
    for path in sorted((Path(repo_root) / "docs" / "nautilus_bridge" / "runs").glob("*/run.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            if (rec["mode"], rec["pilot"], rec["table"]["code_sha256"]) == ("of-record", "E1-SPY", code) and (
                    rec["parity"]["hard_pass"] is True and len(rec["registration"]["rows"]) == 12):
                return True
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return False


def _check_of_record(t: dict, ledger_dir: Path, hostname: str, repo_root: Path) -> None:
    """R-11 (owner_confirmed, the pilot-2 preconditions), R-15 and R-09 (the family ledger), R-15 (the host)."""
    tsha, code = table_sha256(t), code_sha256(repo_root)
    m = re.fullmatch(r"(.+), (\d{4}-\d{2}-\d{2}), table ([0-9a-f]{16}), code ([0-9a-f]{16})", t["owner_confirmed"])
    if not m or (m[3], m[4]) != (tsha[:16], code[:16]):
        raise refuse("R-11", f"owner_confirmed {t['owner_confirmed']!r} does not quote this table and tree: "
                             f"table {tsha[:16]}, code {code[:16]}")
    if t["pilot"] == "C3-BTCUSD" and t["reference_card"] is None:
        raise refuse("R-11", "of-record C3-BTCUSD needs a reference_card (QUANT-R4-2)")
    if t["pilot"] == "C3-BTCUSD" and not e1_parity_passed(repo_root, code):
        raise refuse("R-11", f"of-record C3-BTCUSD needs an of-record E1-SPY record whose parity passed for all 12 "
                             f"columns at both cost levels under code {code[:16]} (GOVERNANCE-R4-4)")
    ledger = gate_ledger.family_ledger(t["family_id"], ledger_dir)
    if not ledger.path.is_file():
        raise refuse("R-15", f"the family ledger {ledger.path} does not exist")
    check = ledger.verify_chain()
    if not check:
        raise refuse("R-09", f"{ledger.path}: chain broken at line {check.first_bad_line}: {check.reason}")
    if check.n_rows == 0:
        raise refuse("R-15", f"the family ledger {ledger.path} holds no row")
    found = host_fingerprint(hostname, ledger)
    if t["host_fingerprint"] != found:
        raise refuse("R-15", f"host_fingerprint {t['host_fingerprint']!r} is not this host's {found}")


def check_table(table: Path, mode: str, ledger_dir: Path, hostname: str, repo_root: Path) -> dict:
    """Step 1 (5.3.2): the validated table. In rehearsal the place rule of 3.9 is judged first, before any file the
    table names is opened (R-10); then 6.6's fields and values (R-11), the reference card's md5 (R-11) and, in
    of-record mode, owner_confirmed, the pilot-2 preconditions (R-11), the family ledger (R-15, R-09) and the host
    fingerprint (R-15)."""
    t, _ = load_table(table)
    _check_place(t, mode, repo_root)
    _check_fields(t, mode)
    _check_values(t, mode)
    _check_reference(t, repo_root)
    if mode == "of-record":
        _check_of_record(t, Path(ledger_dir), hostname, repo_root)
    return t


# --------------------------------------------------------------------------- #
# Step 2: git (R-01, R-02)
# --------------------------------------------------------------------------- #
def _git(git_exe: str, repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([git_exe, "-C", str(repo_root), *args], stdin=subprocess.DEVNULL, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=120)


def check_tree(repo_root: Path, anchor_fn: Callable[[Path], str], git_exe: str | None) -> dict:
    """Step 2's findings: HEAD, the ledger anchor, the porcelain entries (untracked under docs/nautilus_bridge/runs/
    exempt) and what is wrong with the anchor. Judged by tree_refusal."""
    found = {"head": None, "anchor": anchor_fn(repo_root), "clean": False, "porcelain": [], "porcelain_exempt": [],
             "offending": [], "anchor_problem": None}
    if git_exe is None:
        found["anchor_problem"] = "git is not on PATH"
        return found
    head = _git(git_exe, repo_root, "rev-parse", "HEAD")
    found["head"] = head.stdout.strip() if head.returncode == 0 else None
    status = _git(git_exe, repo_root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = status.stdout.split("\0") if status.returncode == 0 else [f"!! git status failed: {status.stderr.strip()}"]
    skip = False
    for entry in entries:
        if skip or not entry:
            skip = False
            continue
        skip = entry[0] in "RC"                         # a rename or copy: the source path follows
        found["porcelain"].append(entry)
        exempt = entry.startswith("?? docs/nautilus_bridge/runs/")
        found["porcelain_exempt" if exempt else "offending"].append(entry)
    found["clean"] = not found["offending"]
    git_path = Path(repo_root) / ".git"
    if found["head"] is None:
        found["anchor_problem"] = "git rev-parse HEAD failed"
    elif found["anchor"] == gate_ledger.UNVERSIONED and git_path.is_file():
        found["anchor_problem"] = f"the anchor is UNVERSIONED: {git_path} is a file, so this is a worktree; use the main clone"
    elif found["anchor"] == gate_ledger.UNVERSIONED and git_path.is_dir():
        found["anchor_problem"] = ('the anchor is UNVERSIONED: the branch ref is packed: run '
                                   '`git commit --allow-empty -m "nautilus: re-anchor"`, then `git push`')
    elif found["anchor"] != f"git:{found['head']}":
        found["anchor_problem"] = f"the anchor {found['anchor']} differs from HEAD {found['head']}"
    return found


def tree_refusal(findings: dict, mode: str) -> str | None:
    """R-02 (git missing, HEAD unreadable, anchor problem), R-01 (an offending entry); None in rehearsal."""
    if mode != "of-record":
        return None
    if findings["head"] is None:
        return "R-02"
    if findings["offending"]:
        return "R-01"
    return "R-02" if findings["anchor_problem"] else None


# --------------------------------------------------------------------------- #
# Steps 3 and 4: venv self-checks and egress (R-03, R-14)
# --------------------------------------------------------------------------- #
def venv_python_from_key() -> Path:
    """The venv python named by QUANTGEN_NAUTILUS_PYTHON (6.7); R-03 when the key is blank."""
    value = launch.venv_key()
    if not value:
        raise refuse("R-03", "QUANTGEN_NAUTILUS_PYTHON is not set")
    return launch.resolve_venv_python(value)


def launch_once(mode_args: list[str], *, python: Path | None, child_cmd: list[str] | None, unshare: str | None,
                timeout: float, script: Path = launch.SANDBOX) -> tuple[launch.ChildResult, dict | None]:
    """One short child in a fresh temp dir; returns its result and its last stdout line as JSON (or None)."""
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch(mode_args, tempdir=tmp, venv_python=python, unshare=unshare, child_cmd=child_cmd,
                                    script=script)
        res = launch.run_child(child, timeout=timeout)
    finally:
        launch.cleanup_tempdir(tmp)
    try:
        out = json.loads(res.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        out = None
    return res, out if isinstance(out, dict) else None


def check_venv(*, child_cmd: list[str] | None, unshare: str | None, timeout: float) -> dict:
    """Step 3: no nautilus-trader in the parent; the venv's reads match the pins (skipped with a stub child); the
    child's --check-env reports Python 3.13.x and BACKTEST; --guard-selftest exits 0 with 5.2.1's five outcomes.
    R-03 otherwise. Returns {"python", "reads", "check_env", "guard_selftest"}."""
    if launch.parent_nautilus() is not None:
        raise BridgeRefusal("R-03", f"nautilus-trader {launch.parent_nautilus()} is installed in the global "
                                    "interpreter", launch.PARENT_NAUTILUS_REMEDY)
    python = reads = None
    if child_cmd is None:
        python = venv_python_from_key()
        reads = launch.read_venv(python)
        bad = launch.venv_mismatches(reads)
        if bad:
            raise refuse("R-03", "the venv is off its pins: " + "; ".join(b.removeprefix("R-03: ") for b in bad))
    res, env = launch_once(["--check-env"], python=python, child_cmd=child_cmd, unshare=unshare, timeout=timeout)
    if res.returncode != 0 or env is None or env.get("schema") != "nautilus-bridge-check-env/1" or not str(
            env.get("python", "")).startswith("3.13.") or env.get("environment") != "BACKTEST" or set(
            env.get("precision") or {}) != {"HIGH_PRECISION", "FIXED_PRECISION", "QUANTITY_MAX", "PRICE_MAX"}:
        raise refuse("R-03", f"--check-env: exit {res.returncode}, output {res.stdout_tail[-300:]!r}, "
                             f"stderr {res.stderr_tail[-300:]!r}")
    res, sel = launch_once(["--guard-selftest"], python=python, child_cmd=child_cmd, unshare=unshare, timeout=timeout)
    if res.returncode != 0 or sel != SELFTEST:
        raise refuse("R-03", f"--guard-selftest misbehaved (QA-R2-10): exit {res.returncode}, outcomes {sel}")
    return {"python": python, "reads": reads, "check_env": env, "guard_selftest": sel}


def run_probe(*, python: Path | None, probe_cmd: list[str] | None, unshare: str | None) -> dict:
    """Step 4: the egress probe through the launch contract (probe_cmd replaces its argv); R-14 unless blocked."""
    if probe_cmd is None and python is None:
        python = venv_python_from_key()
    res, out = launch_once([], python=None if probe_cmd else python, child_cmd=probe_cmd, unshare=unshare,
                           timeout=60, script=launch.EGRESS_PROBE)
    if res.returncode != 0 or out is None or out.get("blocked") is not True:
        raise refuse("R-14", f"the egress probe was not blocked: exit {res.returncode}, output "
                             f"{res.stdout.strip()[-300:]!r}")
    return out


def check_egress_record(record_dir: Path, run_facts: dict) -> None:
    """Of-record step 4: the Step 7A record <record_dir>/<host tag>.json exists, proves the rule (probe blocked, the
    control connect ok) and names this run's venv python, base python and layer, paths compared as 4.3 says. R-14."""
    path = Path(record_dir) / f"{launch.host_tag()}.json"
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
        proved = rec["probe"]["blocked"] is True and rec["control_connect"]["ok"] is True
        named = {k: rec[k] for k in ("venv_python", "base_python", "layer")}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise refuse("R-14", f"no readable Step 7A egress record at {path}: {exc}") from exc
    if not proved:
        raise refuse("R-14", f"{path} does not prove the rule: probe {rec['probe']}, control {rec['control_connect']}")
    off = [k for k in ("venv_python", "base_python") if _norm(str(named[k] or "")) != _norm(str(run_facts[k] or ""))]
    off += ["layer"] if named["layer"] != run_facts["layer"] else []
    if off:
        raise refuse("R-14", f"{path} differs from this run in " + ", ".join(
            f"{k} (record {named[k]!r}, run {run_facts[k]!r})" for k in off))


def control_connect(host: str = "1.1.1.1", port: int = 443, timeout: float = 3) -> dict:
    """The parent's own connect for the egress record (4.4): it must succeed, so the record proves the rule."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "error": ""}
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------- #
# Steps 5 to 9: data, cash rate, P0a, cost, gate (R-04 to R-08, R-10, R-13)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Prices:
    md5: str
    kept: bytes                                     # the header and the kept lines, as read (P0a's trimmed cache)
    dates: tuple[str, ...]
    raw: np.ndarray
    closes: np.ndarray                              # np.round(raw, 9)
    ts: list[int]
    rounding_changed: bool


def bar_timestamps(dates: Sequence[str], instrument: str) -> list[int]:
    """5.2.4: SPY at 21:00 UTC on the date; BTC/USD at 00:00 UTC on the next calendar day (ns)."""
    epoch, day = date(1970, 1, 1), 86_400
    if instrument == "BTC/USD":
        return [((date.fromisoformat(d) - epoch).days + 1) * day * 10**9 for d in dates]
    return [((date.fromisoformat(d) - epoch).days * day + 21 * 3_600) * 10**9 for d in dates]


def check_round_trip(closes: np.ndarray, p: int = PRICE_DECIMALS) -> None:
    """5.2.4: float(f"{y:.{p}f}") == y for every close, so bars.csv carries the parent's floats exactly; R-05."""
    bad = [i for i, y in enumerate(np.asarray(closes, dtype=float)) if float(f"{y:.{p}f}") != y]
    if bad:
        raise refuse("R-05", f"{len(bad)} close(s) fail the {p}-decimal round trip, first at row {bad[0]}")


def load_prices(path: Path, *, md5: str, start: str, end: str, instrument: str, mode: str) -> Prices:
    """Step 5: the md5 (R-04; in rehearsal a pinned real md5 is R-10), the [start, end] filter on each line's date
    text before any value is parsed, the study's read (first column as index, dropna, values above zero), at least
    300 strictly increasing unique dates (R-05), the one rounding and its round trip (R-05)."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise refuse("R-04", f"the prices file is missing or unreadable: {exc}") from exc
    found = hashlib.md5(data).hexdigest()
    if mode == "rehearsal" and found in PINNED_REAL_MD5.values():
        raise refuse("R-10", f"{path} is a byte copy of a pinned real series (md5 {found}); rehearsals use "
                             "synthetic data only")
    if found != md5:
        raise refuse("R-04", f"{path}: md5 {found} differs from the table's {md5}")
    try:
        lines = data.decode("utf-8").splitlines(keepends=True)
        kept = "".join([lines[0]] + [x for x in lines[1:] if _DATE.fullmatch(x[:10]) and start <= x[:10] <= end])
        s = pd.read_csv(io.StringIO(kept), index_col=0, parse_dates=True).iloc[:, 0].dropna()
        s.index = pd.to_datetime(s.index)
        s = s[s > 0]
        raw = s.to_numpy(dtype=float)
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        raise refuse("R-04", f"{path} cannot be read as the study reads it: {exc}") from exc
    if len(s) < 300:
        raise refuse("R-05", f"{len(s)} sessions in [{start}, {end}]; the study needs 300")
    if not (s.index.is_monotonic_increasing and s.index.is_unique):
        raise refuse("R-05", "the dates are not strictly increasing and unique (a duplicated or swapped date)")
    closes = np.round(raw, PRICE_DECIMALS)
    check_round_trip(closes)
    dates = tuple(d.strftime("%Y-%m-%d") for d in s.index)
    return Prices(found, kept.encode("utf-8"), dates, raw, closes, bar_timestamps(dates, instrument),
                  bool(np.any(closes != raw)))


def load_rf(path: Path, *, md5: str, dates: Sequence[str]) -> tuple[np.ndarray, bytes]:
    """Step 6 (K8): DGS3MO read as study.fred reads it, dropna, forward-filled onto the panel dates, / 100 / 252;
    R-06 for a missing, unreadable or off-md5 file and for a NaN left after the fill. No 3 % fallback."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise refuse("R-06", f"the cash-rate file is missing or unreadable: {exc}") from exc
    if hashlib.md5(data).hexdigest() != md5:
        raise refuse("R-06", f"{path}: md5 {hashlib.md5(data).hexdigest()} differs from the table's {md5}")
    try:
        s = pd.read_csv(io.BytesIO(data), index_col=0, parse_dates=True).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        rf = (s.dropna().reindex(pd.to_datetime(list(dates)), method="ffill") / 100.0 / 252.0).to_numpy(dtype=float)
    except (ValueError, TypeError, IndexError, KeyError) as exc:
        raise refuse("R-06", f"{path} cannot be read as study.fred reads it: {exc}") from exc
    if np.isnan(rf).any():
        raise refuse("R-06", f"no DGS3MO observation on or before {dates[int(np.argmax(np.isnan(rf)))]}")
    return rf, data


def load_study(repo_root: Path) -> types.ModuleType:
    """docs/asset_expansion_study.py loaded by path (5.3.2 step 7); its import creates no file and reads no data."""
    spec = importlib.util.spec_from_file_location("qgnb_asset_expansion_study", Path(repo_root) / STUDY_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Blocked(types.ModuleType):
    """A raising stand-in for a download module (QA-R4-1): an attribute read records the attempt and raises."""

    def __getattr__(self, attr: str):
        if attr.startswith("__"):
            raise AttributeError(attr)
        self.log.append(f"{self.__name__}.{attr}")
        raise RuntimeError(f"download blocked: {self.__name__}.{attr}")


def check_p0a(study_module: types.ModuleType, cache_dir: Path, arrays: dict) -> Any:
    """Step 7, P0a (QUANT-1): with study.CACHE at cache_dir and raising stand-ins for yfinance and pandas_datareader
    in sys.modules (restored in finally), the study's own loaders must give byte-equal dates, 9-decimal closes and
    (when arrays["rf"] is not None) rf. arrays: symbol, start, dates, closes, rf. Returns study.panel's Panel; R-13."""
    if getattr(study_module, "REFRESH", None) is not False:
        raise refuse("R-13", "study.REFRESH is not False")
    study_module.CACHE = Path(cache_dir)
    log: list[str] = []
    names = ("yfinance", "pandas_datareader", "pandas_datareader.data")
    saved = {n: sys.modules.get(n, _MISSING) for n in names}
    for n in names:
        sys.modules[n] = stand = _Blocked(n)
        stand.log = log
    try:
        pn = study_module.panel({arrays["symbol"]: study_module.yf(arrays["symbol"])}, start=arrays["start"])
        rf = None if arrays["rf"] is None else np.asarray(study_module.rf_daily(pd.to_datetime(pn.dates)), dtype=float)
    except Exception as exc:                        # noqa: BLE001 - any loader failure is R-13
        raise refuse("R-13", f"the study's loaders raised {type(exc).__name__}: {exc}; blocked downloads {log}") from exc
    finally:
        for n, m in saved.items():
            if m is _MISSING:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
    diff = [] if tuple(pn.dates) == tuple(arrays["dates"]) else ["dates"]
    if np.round(np.asarray(pn.prices, dtype=float)[:, 0], 9).tobytes() != np.asarray(arrays["closes"], float).tobytes():
        diff.append("closes")
    if rf is not None and rf.tobytes() != np.asarray(arrays["rf"], dtype=float).tobytes():
        diff.append("rf")
    if diff:
        raise refuse("R-13", f"{', '.join(diff)} differ from the study's loaders; blocked downloads {log}")
    return pn


def check_cost(symbol: str, cost_bps: float) -> tuple[float, dict]:
    """Step 8 (K15): validate.cost_floor_bp; R-07 for an uncosted symbol or a table cost below the floor."""
    floor, classes = validate.cost_floor_bp([symbol])
    if floor is None:
        raise refuse("R-07", f"QUANTGEN has no cost row for {symbol} (classes {classes})")
    if cost_bps < floor:
        raise refuse("R-07", f"cost_bps {cost_bps:g} is below the floor {floor:g} bp for {symbol}")
    return floor, classes


def check_gate() -> dict:
    """Step 9: a deep copy of validate.GATE; R-08 unless bootstrap_B is 2000."""
    snapshot = copy.deepcopy(validate.GATE)
    if snapshot["bootstrap_B"] != 2000:
        raise refuse("R-08", f"GATE['bootstrap_B'] is {snapshot['bootstrap_B']}, not 2000")
    return snapshot


# --------------------------------------------------------------------------- #
# Step 11: the ledger row (6.4)
# --------------------------------------------------------------------------- #
def ledger_row(table: dict, theta: dict, *, span: Sequence[str], run_utc: str, anchor: str, bridge_run_id: str) -> dict:
    """6.4: the Lab's params expression (ui/strategy_lab_page.py:75-76) with cost_bps a float, so config_id equals
    the Lab's (K9); the engine tag sits in source, outside the key."""
    nt = launch.expected_versions()["nautilus-trader"]
    params = json.loads(json.dumps(dict(theta, symbols=sorted([table["symbol"]]), cost_bps=float(table["cost_bps"])),
                                   default=str))
    return {"rule": table["rule"], "params": params, "timing_class": "COMPLIANT", "span": [span[0], span[-1]],
            "market": table["market"], "run_utc": run_utc, "phase": "research", "script": SCRIPT,
            "run_kind": "variant", "run_utc_anchor": anchor,
            "source": f"nautilus-bridge {table['pilot']}; engines quantgen.simulate + nautilus_trader {nt}; "
                      f"run {bridge_run_id}"}


def registration_entry(col: int, result: gate_ledger.RegisterResult) -> dict:
    """The run record's row: result.row["row_md5"], never RegisterResult's third element (A-1)."""
    return {"col": col, "config_id": result.row["config_id"], "row_md5": result.row["row_md5"],
            "appended": result.appended}


# --------------------------------------------------------------------------- #
# The import census (5.2.7; C-08)
# --------------------------------------------------------------------------- #
def census_class(name: str, stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> str:
    """NT (nautilus_trader), STD (the parent's stdlib, site customisation, _sysconfigdata*) or TP."""
    top = name.split(".")[0]
    if top == "nautilus_trader":
        return "NT"
    if top in stdlib or top in ("sitecustomize", "usercustomize") or top.startswith("_sysconfigdata"):
        return "STD"
    return "TP"


def judge_census(census: Sequence[str], baseline: Sequence[str], *,
                 stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> list[str]:
    """C-08 reasons: a module at or under nautilus_trader.adapters or .network; an NT or TP set that differs from the
    baseline's, in either direction. STD names may differ (QA-11)."""
    out = []
    denied = sorted(n for n in census if any(n == p or n.startswith(p + ".") for p in DENIED_CENSUS))
    if denied:
        out.append(f"C-08: denied modules imported: {', '.join(denied)}")
    for cls in ("NT", "TP"):
        mine = {n for n in census if census_class(n, stdlib) == cls}
        base = {n for n in baseline if census_class(n, stdlib) == cls}
        if mine - base:
            out.append(f"C-08: {cls} names added: {', '.join(sorted(mine - base))}")
        if base - mine:
            out.append(f"C-08: {cls} names missing: {', '.join(sorted(base - mine))}")
    return out


def census_diff(old: Sequence[str], new: Sequence[str]) -> list[str]:
    """"+ <class> <name>" and "- <class> <name>" lines, sorted."""
    a, b = set(old), set(new)
    return [f"+ {census_class(n)} {n}" for n in sorted(b - a)] + [f"- {census_class(n)} {n}" for n in sorted(a - b)]


def load_baseline(tag: str, golden_dir: Path = launch.GOLDEN_DIR) -> list[str] | None:
    path = Path(golden_dir) / f"modules_{tag}.json"
    return json.loads(path.read_text(encoding="utf-8"))["census"] if path.is_file() else None


def record_baseline(golden_dir: Path, tag: str, census: Sequence[str], *, tracked: bool,
                    python: str | None = None) -> tuple[int, list[str]]:
    """5.2.7 (OPS-R3-2, OPS-R4-2, OPS-R5-3): a tracked equal baseline gives (0, ["unchanged"]); a tracked different
    one writes nothing and gives (2, its diff and the removal line); an untracked one, or a tracked path with no
    file, is written and gives (0, its diff and "written <name>")."""
    path = Path(golden_dir) / f"modules_{tag}.json"
    new = sorted(set(census))
    old = None
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))["census"]
        except (OSError, ValueError, KeyError, TypeError):
            old = []
    diff = census_diff(old or [], new)
    if old is not None and tracked:
        if old == new:
            return 0, ["unchanged"]
        removal = (f"Remove-Item tools\\nautilus\\golden\\{path.name}" if os.name == "nt"
                   else f"rm tools/nautilus/golden/{path.name}")
        return 2, diff + [f"{path.name} is tracked and differs; review the diff above, then remove it with:", removal]
    obj = {"schema": CENSUS_SCHEMA, "platform_tag": tag, "python": python or platform.python_version(),
           "recorded_from": ["F1", "F2"], "census": new}
    path.write_text(_json_text(obj), encoding="utf-8", newline="\n")
    return 0, diff + [f"written {path.name}"]


# --------------------------------------------------------------------------- #
# The run record (5.3.5; OPS-R2-3)
# --------------------------------------------------------------------------- #
def write_record(path: Path, obj: dict, *, replace=os.replace, sleep=time.sleep) -> None:
    """mkstemp in the same folder, fsync, replace; up to 10 attempts 0.5 s apart on PermissionError; then raises."""
    data = _json_text(obj)
    last: PermissionError | None = None
    for attempt in range(10):
        if attempt:
            sleep(0.5)
        fd, tmp = tempfile.mkstemp(prefix=".run.", suffix=".tmp", dir=Path(path).parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            replace(tmp, path)
            return
        except PermissionError as exc:
            last = exc
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
    raise last


# --------------------------------------------------------------------------- #
# Child outputs, return reconstruction and reconciliation (5.2.6, 5.3.3; C-09)
# --------------------------------------------------------------------------- #
def _rows(path: Path, header: tuple[str, ...]) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != header:
            raise ValueError(f"{Path(path).name}: header {reader.fieldnames}, expected {list(header)}")
        return list(reader)


def parse_fills(path: Path) -> list[dict]:
    return [{"ts_event": int(r["ts_event"]), "order_side": r["order_side"], "last_qty": Decimal(r["last_qty"]),
             "last_px": Decimal(r["last_px"]), "commission": Decimal(r["commission"]),
             "commission_ccy": r["commission_ccy"], "trade_id": r["trade_id"], "venue_order_id": r["venue_order_id"]}
            for r in _rows(path, FILLS_HEADER)]


def parse_decisions(path: Path) -> list[dict]:
    return [{"i": int(r["i"]), "ts_event": int(r["ts_event"]), "decision": int(r["decision"]),
             "margin": float(r["margin"]), "action": r["action"]} for r in _rows(path, DECISIONS_HEADER)]


def parse_equity(path: Path) -> list[dict]:
    return [{"i": int(r["i"]), "ts_event": int(r["ts_event"]), "close": Decimal(r["close"]), "cash": Decimal(r["cash"]),
             "qty": Decimal(r["qty"]), "equity_pre": Decimal(r["equity_pre"])} for r in _rows(path, EQUITY_HEADER)]


@dataclass(frozen=True)
class Rebuilt:                                      # 5.3.3
    R: np.ndarray
    TV: np.ndarray
    E_minus: np.ndarray
    cash: list[Decimal]
    q: list[Decimal]
    fill_bars: list[int]
    final_cash: Decimal


def _px(closes) -> list[Decimal]:
    return [Decimal(f"{c:.{PRICE_DECIMALS}f}") for c in np.asarray(closes, dtype=float)]


def rebuild_returns(fills: list[dict], closes: np.ndarray, ts: Sequence[int], rf: np.ndarray,
                    capital: Decimal) -> Rebuilt:
    """5.3.3: cash and position after each bar's fills, in Decimal, from cash(-1) = capital and q(-1) = 0;
    E-(t) = cash(t-1) + q(t-1) P(t); R(t) = E-(t+1) / E-(t) - 1 + (cash(t) / E-(t)) rf(t) and
    TV(t) = sum of qty x px at bar t / E-(t), for t = 0 .. T-2. C-09 for a fill off every bar timestamp."""
    bar = {t: i for i, t in enumerate(ts)}
    per_bar: list[list[dict]] = [[] for _ in ts]
    fill_bars = []
    for f in fills:
        if f["ts_event"] not in bar or f["order_side"] not in ("BUY", "SELL"):
            raise ChildInvalid("C-09", f"fill at ts_event {f['ts_event']} side {f['order_side']} is not on a bar")
        per_bar[bar[f["ts_event"]]].append(f)
        fill_bars.append(bar[f["ts_event"]])
    P, cash, q = _px(closes), Decimal(capital), Decimal(0)
    e_minus, cash_l, q_l, traded = [], [], [], []
    for t in range(len(ts)):
        e_minus.append(cash + q * P[t])
        value = Decimal(0)
        for f in per_bar[t]:
            notional = f["last_qty"] * f["last_px"]
            value += notional
            if f["order_side"] == "BUY":
                cash, q = cash - notional - f["commission"], q + f["last_qty"]
            else:
                cash, q = cash + notional - f["commission"], q - f["last_qty"]
        traded.append(value)
        cash_l.append(cash)
        q_l.append(q)
    T = len(ts)
    R = np.array([float(e_minus[t + 1] / e_minus[t]) - 1.0 + float(cash_l[t] / e_minus[t]) * float(rf[t])
                  for t in range(T - 1)])
    TV = np.array([float(traded[t] / e_minus[t]) for t in range(T - 1)])
    return Rebuilt(R=R, TV=TV, E_minus=np.array([float(e) for e in e_minus]), cash=cash_l, q=q_l,
                   fill_bars=fill_bars, final_cash=cash)


def reconcile(rebuilt: Rebuilt, equity: list[dict], closes: np.ndarray, ts: Sequence[int], capital: Decimal,
              balance: str) -> list[str]:
    """5.3.3's cross-checks (C-09): onbar_equity.csv has n_bars rows on the bar timestamps; the rebuilt E-(t) equals
    its equity_pre within $0.01 per fill so far; the final cash equals the manifest's balance within $0.01 per fill."""
    if len(equity) != len(ts):
        return [f"C-09: onbar_equity.csv has {len(equity)} rows; n_bars is {len(ts)}"]
    P, done, out = _px(closes), Counter(rebuilt.fill_bars), []
    so_far = 0
    for t, row in enumerate(equity):
        exact = (Decimal(capital) if t == 0 else rebuilt.cash[t - 1]) + (Decimal(0) if t == 0 else rebuilt.q[t - 1]) * P[t]
        if (row["i"], row["ts_event"]) != (t, ts[t]) or abs(exact - row["equity_pre"]) > Decimal("0.01") * so_far:
            out.append(f"C-09: bar {t}: equity_pre {row['equity_pre']} against the rebuilt {exact}")
            break
        so_far += done[t]
    if abs(rebuilt.final_cash - Decimal(balance)) > Decimal("0.01") * len(rebuilt.fill_bars):
        out.append(f"C-09: final cash {rebuilt.final_cash} against the account's {balance}")
    return out


def manifest_reasons(m: dict, *, n_bars: int, first_ts: int, last_ts: int, bars_sha256: str, input_sha256: str,
                     ledger_hash: str, check_env: dict) -> list[str]:
    """The parent's re-derivation from manifest.json (5.2.7, QA-R3-2, QA-R4-3): C-01 to C-04, C-15, C-07, C-11 and
    C-14, whatever the manifest's own `valid` says. A field missing is C-06."""
    try:
        r, inp, out = m["result"], m["input"], []
        if r["force_stop"] is not False:
            out.append("C-01: forced stop (re-derived from the manifest)")
        if r["bars_seen"] < n_bars or r["backtest_end"] is None or r["backtest_end"] < last_ts:
            out.append(f"C-02: bars seen {r['bars_seen']} of {n_bars}, backtest_end {r['backtest_end']}")
        if r["orders_not_filled"]:
            out.append(f"C-03: orders not FILLED: {r['orders_not_filled']}")
        if r["denied"] or r["rejected"]:
            out.append(f"C-04: {r['denied']} denied, {r['rejected']} rejected")
        if m["strategy_started"] is not True or m["environment"] != "BACKTEST":
            out.append(f"C-15: environment {m['environment']}, strategy_started {m['strategy_started']}")
        if m["precision"] != check_env["precision"] or m["environment"] != check_env["environment"]:
            out.append(f"C-07: manifest precision {m['precision']} differs from --check-env's {check_env['precision']}")
        echo = {"bars_sha256": bars_sha256, "bars_fed": n_bars, "first_ts": first_ts, "last_ts": last_ts,
                "input_json_sha256": input_sha256}
        off = [k for k, v in echo.items() if inp[k] != v]
        if off:
            out.append(f"C-11: manifest echoes differ from the parent's: {off}")
        if inp["ledger_hash_after_registration"] != ledger_hash:
            out.append(f"C-14: ledger hash echo {inp['ledger_hash_after_registration']} is not {ledger_hash}")
    except (KeyError, TypeError) as exc:
        return [f"C-06: manifest.json lacks a field of spec 6.2: {exc!r}"]
    return out


# --------------------------------------------------------------------------- #
# The run context and the seam for steps 16 and 17
# --------------------------------------------------------------------------- #
@dataclass
class Leg:                                          # one child: column `col`, cost level `stress` (1 or 2)
    col: int
    stress: int
    child: dict
    manifest: dict | None
    fills: list[dict]
    decisions: list[dict]
    equity: list[dict]
    rebuilt: Rebuilt | None
    invalid: list[str]


@dataclass
class RunContext:                                   # built by step 12; filled through step 15; read by Task 5
    mode: str
    repo_root: Path
    table: dict
    table_sha256: str
    code_sha256: str
    bridge_run_id: str
    run_dir: Path
    record: dict
    dates: tuple[str, ...]
    ts: list[int]
    closes: np.ndarray
    rf: np.ndarray
    study: types.ModuleType
    study_pn: Any
    grid: list[dict]
    fn: Callable
    weights: np.ndarray
    pnl_qg: np.ndarray
    pnl_stress_qg: np.ndarray
    turnover_qg: np.ndarray
    pnl_nt: np.ndarray
    pnl_stress_nt: np.ndarray
    turnover_nt: np.ndarray
    legs: dict[tuple[int, int], Leg]
    gate_snapshot: dict
    ledger: gate_ledger.FamilyLedger
    hash_after_registration: str
    score_fn: Callable
    hooks: dict
    stub_child: bool


@dataclass(frozen=True)
class Outcome:
    status: str                                     # "CARD_WRITTEN" | "WITHHELD" | "ERROR"
    exit_code: int                                  # 0 | 1 | 4
    withheld_reasons: list[str]


def parity_and_gate(ctx: RunContext) -> Outcome:
    """Steps 16 and 17 (spec 5.4, 5.5): tools/nautilus/parity.py."""
    from tools.nautilus import parity
    return parity.hand_off(ctx)


# --------------------------------------------------------------------------- #
# Child inputs (6.1) and one leg (steps 14 and 15)
# --------------------------------------------------------------------------- #
def child_params(table: dict, theta: dict) -> dict:
    """6.1's params: the grid column, with the study's crypto defaults filled in when it names only hysteresis."""
    if table["strategy"] == "crypto_trend":
        return {"hysteresis": float(theta["hysteresis"]), "lookbacks": list(theta.get("lookbacks", CRYPTO_DEFAULTS["lookbacks"])),
                "mas": list(theta.get("mas", CRYPTO_DEFAULTS["mas"]))}
    return {"rule": theta["rule"], "lookback": int(theta["lookback"]), "step": int(theta["step"])}


def cost_text(cost_bps) -> str:
    """The table's float cost as 6.1's decimal string: 50.0 -> "50", 12.5 -> "12.5"."""
    return format(Decimal(repr(float(cost_bps))).normalize(), "f")


def bars_bytes(closes: np.ndarray, ts: Sequence[int]) -> bytes:
    """bars.csv (C3): header i,ts_ns,close, LF, closes at 9 decimals."""
    rows = ["i,ts_ns,close"] + [f"{i},{t},{c:.{PRICE_DECIMALS}f}" for i, (t, c) in enumerate(zip(ts, closes))]
    return ("\n".join(rows) + "\n").encode("utf-8")


def input_bytes(table: dict, theta: dict, stress: int, bars: bytes, n_bars: int, ledger_hash: str) -> bytes:
    """input.json (C5): exactly 6.1's 14 keys, C1's compact sorted JSON, no trailing newline."""
    obj = {"schema": INPUT_SCHEMA, "strategy": table["strategy"], "params": child_params(table, theta),
           "instrument": table["instrument"], "capital_usd": table["capital_usd"], "cost_bps": cost_text(table["cost_bps"]),
           "stress": str(stress), "fill_seed": table["fill_seed"], "price_precision": PRICE_DECIMALS,
           "size_precision": table["size_precision"], "volume": table["volume"], "n_bars": n_bars,
           "bars_sha256": hashlib.sha256(bars).hexdigest(), "ledger_hash_after_registration": ledger_hash}
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _judge_leg(st: "_State", leg: Leg, res: launch.ChildResult, tmp: Path, raw: bytes, bars: bytes) -> None:
    """Step 15 for one child: C-06 (exit, timeout, missing or unparsable output), the manifest's own reasons, the
    parent's re-derivation, the census (C-08; skipped with a stub child) and the rebuild and reconciliation (C-09)."""
    c, bad, ctx = leg.child, leg.invalid, st.ctx
    c.update(returncode=res.returncode, ntstatus=res.ntstatus, timed_out=res.timed_out, seconds=res.seconds,
             stdout_tail=res.stdout_tail, stderr_tail=res.stderr_tail,
             census_sha256=hashlib.sha256("\n".join(res.census).encode("utf-8")).hexdigest())
    if res.timed_out:
        bad.append(f"C-06: timed out after {st.timeout:g} s; the process tree was killed")
    elif res.returncode not in (0, 10):
        bad.append(f"C-06: exit {res.returncode}" + (f" ({res.ntstatus})" if res.ntstatus else ""))
    try:
        m = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(m, dict):
            raise ValueError("not a JSON object")
        leg.manifest = c["manifest"] = m
    except (OSError, ValueError) as exc:
        bad.append(f"C-06: manifest.json missing or not a JSON object: {type(exc).__name__}")
    parsed = False
    try:
        c["fills"] = _rows(tmp / "fills.csv", FILLS_HEADER)
        leg.fills, leg.decisions = parse_fills(tmp / "fills.csv"), parse_decisions(tmp / "decisions.csv")
        leg.equity, parsed = parse_equity(tmp / "onbar_equity.csv"), True
    except (OSError, ValueError, ArithmeticError) as exc:
        bad.append(f"C-06: an output CSV is missing or unreadable: {type(exc).__name__}: {exc}")
    m = leg.manifest
    if m is None:
        return
    bad += [r for r in m.get("invalid_reasons") or [] if r not in bad]
    if res.returncode in (0, 10) and (res.returncode == 0) != (m.get("valid") is True):
        bad.append(f"C-06: exit {res.returncode} with valid {m.get('valid')!r}")
    bad += manifest_reasons(m, n_bars=len(ctx.ts), first_ts=ctx.ts[0], last_ts=ctx.ts[-1],
                            bars_sha256=hashlib.sha256(bars).hexdigest(), input_sha256=hashlib.sha256(raw).hexdigest(),
                            ledger_hash=ctx.hash_after_registration, check_env=st.check_env_out)
    if not ctx.stub_child:
        tag = st.reads["wheel"]["platform_tag"]
        bad += (judge_census(res.census, st.baseline) if st.baseline is not None
                else [f"C-08: no census baseline modules_{tag}.json"])
    if parsed and not any(r.startswith("C-06") for r in bad):
        try:
            leg.rebuilt = rebuild_returns(leg.fills, ctx.closes, ctx.ts, ctx.rf, Decimal(ctx.table["capital_usd"]))
            bad += reconcile(leg.rebuilt, leg.equity, ctx.closes, ctx.ts, Decimal(ctx.table["capital_usd"]),
                             m["result"]["account_balance_usd"])
        except ChildInvalid as exc:
            bad.append(str(exc))
        except (ArithmeticError, KeyError, TypeError) as exc:
            bad.append(f"C-09: the rebuild failed: {type(exc).__name__}: {exc}")
    if not bad and not ctx.stub_child:
        st.record["census"].setdefault(st.reads["wheel"]["platform_tag"], res.census)


def _run_leg(st: "_State", col: int, stress: int) -> Leg:
    """Step 14 for one (column, cost level): a fresh temp dir with input.json and bars.csv, the launch contract,
    the child_started hook after Popen, then _judge_leg; the temp dir is removed whatever happens (OPS-R2-4)."""
    ctx = st.ctx
    bars = bars_bytes(ctx.closes, ctx.ts)
    raw = input_bytes(ctx.table, ctx.grid[col], stress, bars, len(ctx.ts), ctx.hash_after_registration)
    child = {"col": col, "stress": stress, "returncode": None, "ntstatus": None, "timed_out": False, "seconds": None,
             "manifest": None, "census_sha256": None, "fills": [], "stdout_tail": "", "stderr_tail": "", "invalid": []}
    leg = Leg(col, stress, child, None, [], [], [], None, child["invalid"])
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        try:
            lc = launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=st.python,
                                     unshare=st.unshare, child_cmd=st.child_cmd)
        except ChildInvalid as exc:                 # C-10: nothing launched
            leg.invalid.append(str(exc))
            return leg
        hook = st.hooks.get("child_started")
        st.record["times"]["first_child_utc"] = st.record["times"]["first_child_utc"] or _utc_now()
        res = launch.run_child(lc, timeout=st.timeout, on_started=(lambda: hook(lc)) if hook else None)
        _judge_leg(st, leg, res, tmp, raw, bars)
    finally:
        st.record["cleanup_leftovers"].extend(launch.cleanup_tempdir(tmp))
    return leg


# --------------------------------------------------------------------------- #
# The run lifecycle (5.3.2, 5.3.5)
# --------------------------------------------------------------------------- #
@dataclass
class _State:
    table_path: Path
    mode: str
    ledger_dir: Path | None
    out_dir: Path | None
    child_cmd: list[str] | None
    probe_cmd: list[str] | None
    hooks: dict
    hooks_given: bool
    timeout: float
    register_fn: Callable
    score_fn: Callable
    rerun_of: str | None
    reason: str | None
    repo_root: Path = REPO_ROOT
    out_root: Path | None = None
    record: dict = field(default_factory=dict)
    table: dict | None = None
    table_sha: str = ""
    run_id: str = ""
    lock: TableLock | None = None
    run_dir: Path | None = None
    python: Path | None = None
    reads: dict | None = None
    unshare: str | None = None
    check_env_out: dict | None = None
    prices: Prices | None = None
    rf: np.ndarray | None = None
    rf_bytes: bytes | None = None
    pn: Any = None
    study: Any = None
    p0a_dir: Path | None = None
    gate: dict | None = None
    ledger: Any = None
    baseline: list[str] | None = None
    ctx: RunContext | None = None
    awake: bool = False


def _new_record(st: _State) -> dict:
    return {"schema": RUN_SCHEMA, "read_only": True, "bridge_run_id": None, "mode": st.mode, "pilot": None,
            "stub_child": st.child_cmd is not None, "status": None, "withheld_reasons": [], "earlier_runs": [],
            "supersedes": st.rerun_of, "rerun_reason": st.reason,
            "times": {"started_utc": _utc_now(), "registered_utc": None, "first_child_utc": None, "finished_utc": None},
            "git": None, "table": None, "data": None, "provenance": None, "costs": None, "venv": None, "egress": None,
            "engine": None, "registration": None, "children": [], "census": {}, "parity": None, "gate": None,
            "card": None, "cleanup_leftovers": [], "record_write_failures": [], "error": None}


def _check_arguments(st: _State) -> None:
    """Argument validation, before step 0 writes anything: R-11 (mode, re-run pair, a seam or a directory in
    of-record mode, a malformed child_cmd), R-10 (rehearsal directories outside the temp root)."""
    if st.mode not in ("rehearsal", "of-record"):
        raise refuse("R-11", f"mode must be rehearsal or of-record, not {st.mode!r}")
    if (st.rerun_of is None) != (st.reason is None) or (st.reason is not None and not st.reason.strip()):
        raise refuse("R-11", "--rerun-of and a non-empty --reason go together")
    if st.mode == "of-record":
        seams = [n for n, used in (("child_cmd", st.child_cmd is not None), ("probe_cmd", st.probe_cmd is not None),
                                   ("hooks", st.hooks_given), ("timeout", st.timeout != launch.TIMEOUT_S),
                                   ("register_fn", st.register_fn is not gate_ledger.register_trial),
                                   ("score_fn", st.score_fn is not validate.score_strategy),
                                   ("ledger_dir", st.ledger_dir is not None), ("out_dir", st.out_dir is not None))
                 if used]
        if seams:
            raise refuse("R-11", f"of-record mode takes no test seam and no directory: {seams}")
        import config
        st.ledger_dir, st.out_root = config.macro_dir() / "ledgers", st.repo_root / "docs" / "nautilus_bridge" / "runs"
        return
    outside = [f"{n}={p!r}" for n, p in (("ledger_dir", st.ledger_dir), ("out_dir", st.out_dir))
               if p is None or not inside_temp_root(p)]
    if outside:
        raise refuse("R-10", f"rehearsal needs --ledger-dir and --out-dir inside the temp root {temp_roots()}: "
                             f"{', '.join(outside)}")
    for cmd in (st.child_cmd, st.probe_cmd):
        if cmd is not None and not (isinstance(cmd, list) and cmd and all(isinstance(c, str) for c in cmd)):
            raise refuse("R-11", f"a child or probe command must be a non-empty list of strings: {cmd!r}")
    st.ledger_dir, st.out_root = Path(st.ledger_dir), Path(st.out_dir)


def _hook(st: _State, n: int) -> None:
    fn = st.hooks.get(f"after_step{n}")
    if fn is not None:
        fn(st.ctx if n >= 12 else None)


def _step0(st: _State) -> None:
    """Lock, freshness and earlier runs (5.3.5): the table is parsed only for table_sha256 (R-11 when not JSON)."""
    table, _ = load_table(st.table_path)
    st.table_sha = table_sha256(table)
    st.run_id = bridge_run_id(datetime.now(timezone.utc), st.table_sha)
    fid = table.get("family_id")
    family = [st.ledger_dir / f"{fid}.jsonl"] if isinstance(fid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", fid) else []
    st.lock, earlier = take_lock(st.out_root, st.table_sha, [st.ledger_dir / "C3.jsonl", *family], st.rerun_of)
    st.record.update(bridge_run_id=st.run_id, earlier_runs=earlier)
    for e in earlier:
        if e["status"] in ("IN_PROGRESS", "ABORTED"):
            print(f"earlier run {e['bridge_run_id']} ended {e['status']}")
    if os.name == "nt":                             # OPS-R3-8: keep the machine awake while the run lasts
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
        st.awake = True


def _step1(st: _State) -> None:
    st.table = check_table(st.table_path, st.mode, st.ledger_dir, socket.gethostname(), st.repo_root)
    raw = st.table_path.read_bytes()
    st.record.update(pilot=st.table["pilot"], table={
        "path": str(st.table_path), "raw_sha256": hashlib.sha256(raw).hexdigest(), "table_sha256": st.table_sha,
        "code_sha256": code_sha256(st.repo_root), "table": st.table})


def _step2(st: _State) -> None:
    found = check_tree(st.repo_root, gate_ledger.repo_anchor, shutil.which("git"))
    rid = tree_refusal(found, st.mode)
    if rid is not None:
        raise refuse(rid, "; ".join(found["offending"]) if rid == "R-01" else str(found["anchor_problem"]))
    st.record["git"] = found


def _step3(st: _State) -> None:
    st.unshare = launch.resolve_unshare()
    v = check_venv(child_cmd=st.child_cmd, unshare=st.unshare, timeout=st.timeout)
    st.python, st.reads, st.check_env_out = v["python"], v["reads"], v["check_env"]
    st.record["venv"] = {"reads": v["reads"], "parent_pyarrow": launch.parent_pyarrow(), "sys_executable": sys.executable,
                         "sys_base_executable": sys._base_executable, "sys_version": sys.version}
    st.record["engine"] = {"check_env": v["check_env"], "guard_selftest": v["guard_selftest"]}


def _step4(st: _State) -> None:
    probe = run_probe(python=st.python, probe_cmd=st.probe_cmd, unshare=st.unshare)
    egress = {"probe": probe, "layer": LAYER, "unshare": st.unshare, "record_path": None, "record_path_norm": None}
    if st.mode == "of-record":
        record_dir = st.repo_root / "docs" / "nautilus_bridge" / "egress"
        check_egress_record(record_dir, {"venv_python": str(st.python), "layer": LAYER,
                                         "base_python": st.reads["pyvenv"]["executable"]})
        egress["record_path"] = str(record_dir / f"{launch.host_tag()}.json")
        egress["record_path_norm"] = _norm(egress["record_path"])
    st.record["egress"] = egress


def _step5_6(st: _State, step: int) -> None:
    t = st.table
    if step == 5:
        path = Path(t["prices_file"]) if st.mode == "rehearsal" else st.repo_root / t["prices_file"]
        st.prices = load_prices(path, md5=t["prices_md5"], start=t["start"], end=t["end"], instrument=t["instrument"],
                                mode=st.mode)
        st.record["data"] = {"prices_file": t["prices_file"], "prices_md5": st.prices.md5, "rf_file": t["rf_file"],
                             "rf_md5": None, "start": t["start"], "end": t["end"], "sessions": len(st.prices.dates),
                             "rounding_changed": st.prices.rounding_changed}
    elif t["rf_file"] is None:
        st.rf = np.zeros(len(st.prices.dates))      # pilot 2: rf = 0.0, no overlay (QUANT-R3-2)
    else:
        path = Path(t["rf_file"]) if os.path.isabs(t["rf_file"]) else st.repo_root / t["rf_file"]
        st.rf, st.rf_bytes = load_rf(path, md5=t["rf_md5"], dates=st.prices.dates)
        st.record["data"]["rf_md5"] = hashlib.md5(st.rf_bytes).hexdigest()


def _step7(st: _State) -> None:
    """P0a: the trimmed cache in the run's temp dir, the study loaded by path, check_p0a (R-13)."""
    t = st.table
    st.p0a_dir = Path(tempfile.mkdtemp(prefix="qgnb_p0a_"))
    name = "yf_" + re.sub(r"[=^:/]", "_", t["symbol"]) + ".csv"          # the name study._cached builds
    (st.p0a_dir / name).write_bytes(st.prices.kept)
    names = [name]
    if st.rf_bytes is not None:
        (st.p0a_dir / "fred_DGS3MO.csv").write_bytes(st.rf_bytes)
        names.append("fred_DGS3MO.csv")
    missing = [n for n in names if not (st.p0a_dir / n).is_file()]
    if missing:
        raise refuse("R-13", f"the trimmed cache lacks {missing}")
    st.study = load_study(st.repo_root)
    arrays = {"symbol": t["symbol"], "start": t["start"], "dates": st.prices.dates, "closes": st.prices.closes,
              "rf": None if t["rf_file"] is None else st.rf}
    st.pn = check_p0a(st.study, st.p0a_dir, arrays)
    st.record["provenance"] = {"p0a": {"passed": True, "cache_files": names}, "p0b": None}


def _step8_10(st: _State, step: int) -> None:
    t = st.table
    if step == 8:
        floor, classes = check_cost(t["symbol"], float(t["cost_bps"]))
        st.record["costs"] = {"cost_bps": float(t["cost_bps"]), "floor_bp": floor, "classes": classes, "stress": 2.0,
                              "source": "validate.cost_floor_bp"}
    elif step == 9:
        st.gate = check_gate()
    else:
        st.ledger = gate_ledger.family_ledger(t["family_id"], st.ledger_dir)
        check = st.ledger.verify_chain()
        if not check:
            raise refuse("R-09", f"{st.ledger.path}: chain broken at line {check.first_bad_line}: {check.reason}")
        st.record["registration"] = {"family_id": t["family_id"], "ledger_path": str(st.ledger.path),
                                     "hash_before": st.ledger.hash(), "n_raw_before": check.n_rows, "hash_after": None,
                                     "n_raw_after": None, "market_n_raw": None, "rows": []}


def _before_registration(st: _State) -> None:
    """Steps 0 to 10, each followed by its after_step<n> hook (called with None)."""
    steps = [_step0, _step1, _step2, _step3, _step4, lambda s: _step5_6(s, 5), lambda s: _step5_6(s, 6), _step7,
             lambda s: _step8_10(s, 8), lambda s: _step8_10(s, 9), lambda s: _step8_10(s, 10)]
    for n, step in enumerate(steps):
        step(st)
        _hook(st, n)


def _step11(st: _State) -> None:
    """Register every column in grid order (6.4); the run folder exists from here on (R-12's record)."""
    run_dir = st.out_root / st.run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    st.run_dir = run_dir
    t, rows = st.table, st.record["registration"]["rows"]
    run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    anchor = gate_ledger.repo_anchor(st.repo_root)
    for col, theta in enumerate(t["grid"]):
        row = ledger_row(t, theta, span=(st.prices.dates[0], st.prices.dates[-1]), run_utc=run_utc, anchor=anchor,
                         bridge_run_id=st.run_id)
        rows.append(registration_entry(col, st.register_fn(st.ledger, row, script=SCRIPT)))


def _step12(st: _State) -> None:
    """The post-registration snapshot, the RunContext and the IN_PROGRESS record."""
    reg, rows = st.record["registration"], st.ledger.rows()
    reg.update(hash_after=st.ledger.hash(rows), n_raw_after=len(rows),
               market_n_raw=sum(r.get("market") == st.table["market"] for r in rows))
    st.record["times"]["registered_utc"] = _utc_now()
    st.record["status"] = "IN_PROGRESS"
    T, G = len(st.prices.dates), len(st.table["grid"])
    nan = np.full((T - 1, G), np.nan)
    st.ctx = RunContext(
        mode=st.mode, repo_root=st.repo_root, table=st.table, table_sha256=st.table_sha,
        code_sha256=st.record["table"]["code_sha256"], bridge_run_id=st.run_id, run_dir=st.run_dir, record=st.record,
        dates=st.prices.dates, ts=st.prices.ts, closes=st.prices.closes, rf=st.rf, study=st.study, study_pn=st.pn,
        grid=st.table["grid"], fn=FN[st.table["strategy"]], weights=np.zeros((T, G)), pnl_qg=nan.copy(),
        pnl_stress_qg=nan.copy(), turnover_qg=nan.copy(), pnl_nt=nan.copy(), pnl_stress_nt=nan.copy(),
        turnover_nt=nan.copy(), legs={}, gate_snapshot=st.gate, ledger=st.ledger,
        hash_after_registration=reg["hash_after"], score_fn=st.score_fn, hooks=st.hooks,
        stub_child=st.child_cmd is not None)
    _write_best_effort(st, "IN_PROGRESS")


def _step13_15(st: _State, step: int) -> None:
    ctx, cost = st.ctx, float(st.table["cost_bps"])
    if step == 13:                                  # QUANTGEN's reference: pnl_matrix column by column
        for g, theta in enumerate(ctx.grid):
            W = np.asarray(ctx.fn(ctx.closes, **theta), dtype=float).reshape(len(ctx.closes), -1)
            ctx.weights[:, g] = W[:, 0]
            ctx.pnl_qg[:, g], ctx.turnover_qg[:, g] = S.simulate(ctx.closes, W, cost_bps=cost, cash_daily=ctx.rf)
            ctx.pnl_stress_qg[:, g] = S.simulate(ctx.closes, W, cost_bps=cost * 2.0, cash_daily=ctx.rf)[0]
    elif step == 14:                                # one child per (column, cost level), sequentially
        st.baseline = None if ctx.stub_child else load_baseline(st.reads["wheel"]["platform_tag"])
        for col in range(len(ctx.grid)):
            for stress in (1, 2):
                leg = ctx.legs[(col, stress)] = _run_leg(st, col, stress)
                st.record["children"].append(leg.child)
                _write_best_effort(st, f"child {col} x{stress}")
    else:                                           # the Nautilus matrices from the valid legs (5.3.4)
        for (col, stress), leg in ctx.legs.items():
            if leg.invalid or leg.rebuilt is None:
                continue
            if stress == 1:
                ctx.pnl_nt[:, col], ctx.turnover_nt[:, col] = leg.rebuilt.R, leg.rebuilt.TV
            else:
                ctx.pnl_stress_nt[:, col] = leg.rebuilt.R


def _write_best_effort(st: _State, what: str) -> None:
    """An intermediate record write: a failure is listed and never changes the status (5.3.5)."""
    try:
        write_record(st.run_dir / "run.json", st.record)
    except Exception as exc:                        # noqa: BLE001
        st.record["record_write_failures"].append(f"{what}: {type(exc).__name__}: {exc}")


def _finish(st: _State, status: str, code: int, message: str | None, tb: str | None) -> int:
    """The final record, in a try that catches BaseException; run.final.<pid>.json when it still fails."""
    st.record["status"] = status
    if message:
        print(message)
        st.record["error"] = {"message": message, "traceback": (tb or "")[-launch.TAIL_CHARS:]}
    st.record["times"]["finished_utc"] = _utc_now()
    if st.run_dir is None:                          # the run folder could not be made: nothing to write
        print(f"STATUS {status} exit={code} record=-")
        return code
    path = st.run_dir / "run.json"
    try:
        write_record(path, st.record)
    except BaseException as exc:                    # noqa: BLE001 - G-07 included
        st.record["record_write_failures"].append(f"final: {type(exc).__name__}: {exc}")
        path = st.run_dir / f"run.final.{os.getpid()}.json"
        try:
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(_json_text(st.record))
        except BaseException as exc2:               # noqa: BLE001
            print(f"the run record could not be written: {type(exc2).__name__}: {exc2}")
            path = "-"
    print(f"STATUS {status} exit={code} record={path}")
    return code


def _after_registration(st: _State) -> int:
    """Steps 11 to 17: R-12 (exit 3), G-06 (ERROR, 4), G-07 (ABORTED, 5), else the Outcome of steps 16 and 17."""
    try:
        _step11(st)
    except Exception as exc:                        # noqa: BLE001
        return _finish(st, "REFUSED_REGISTRATION", 3, f"R-12: register_trial raised {type(exc).__name__}: {exc}",
                       traceback.format_exc())
    except BaseException as exc:                    # noqa: BLE001
        return _finish(st, "ABORTED", 5, f"G-07: {type(exc).__name__} during registration", traceback.format_exc())
    try:
        _hook(st, 11)
        _step12(st)
        _hook(st, 12)
        for step in (13, 14, 15):
            _step13_15(st, step)
            _hook(st, step)
        outcome = parity_and_gate(st.ctx)
    except Exception as exc:                        # noqa: BLE001
        return _finish(st, "ERROR", 4, f"G-06: {type(exc).__name__}: {exc}", traceback.format_exc())
    except BaseException as exc:                    # noqa: BLE001
        return _finish(st, "ABORTED", 5, f"G-07: {type(exc).__name__} after registration", traceback.format_exc())
    st.record["withheld_reasons"] = list(outcome.withheld_reasons)
    return _finish(st, outcome.status, outcome.exit_code, None, None)


def _print_refusal(exc: BridgeRefusal) -> int:
    print(str(exc))
    if exc.remedy:
        print(f"remedy: {exc.remedy}")
    print("STATUS REFUSED exit=2 record=-")
    return 2


def run(table_path: Path, *, mode: str, ledger_dir: Path | None = None, out_dir: Path | None = None,
        child_cmd: list[str] | None = None, probe_cmd: list[str] | None = None,
        hooks: dict[str, Callable[..., None]] | None = None, timeout: float = launch.TIMEOUT_S,
        register_fn=gate_ledger.register_trial, score_fn=validate.score_strategy,
        rerun_of: str | None = None, reason: str | None = None) -> int:
    """One run of a registration table (5.3.1, 5.3.2, 5.3.5); returns the exit code and never re-raises (QA-R3-6).
    Before registration a refusal or an unexpected exception prints its reason, writes nothing and returns 2."""
    st = _State(Path(table_path), mode, ledger_dir, out_dir, child_cmd, probe_cmd, dict(hooks or {}), hooks is not None,
                timeout, register_fn, score_fn, rerun_of, reason)
    st.record = _new_record(st)
    try:
        try:
            _check_arguments(st)
            _before_registration(st)
        except BridgeRefusal as exc:
            return _print_refusal(exc)
        except BaseException:                       # noqa: BLE001 - OPS-R2-6
            print(traceback.format_exc()[-2000:])
            print("STATUS REFUSED exit=2 record=-")
            return 2
        return _after_registration(st)
    finally:
        if st.lock is not None:
            st.lock.release()
        if st.p0a_dir is not None:
            launch.cleanup_tempdir(st.p0a_dir)
        if st.awake:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


# --------------------------------------------------------------------------- #
# Modes: --fixtures, --check-env, --egress-record (5.3.1)
# --------------------------------------------------------------------------- #
def utc_date(ts_ns: int) -> str:
    return (date(1970, 1, 1) + timedelta(days=ts_ns // (86_400 * 10**9))).isoformat()


def golden_of(name: str, exit_code: int | None, manifest: dict | None, fills: list[dict]) -> dict:
    """6.8's golden shape from one fixture run: fills as their CSV text, money as the manifest's strings."""
    m = manifest or {}
    r = m.get("result") or {}
    return {"schema": GOLDEN_SCHEMA, "fixture": name,
            "status": "valid" if exit_code == 0 and m.get("valid") is True else "invalid", "exit_code": exit_code,
            "bars_fed": (m.get("input") or {}).get("bars_fed"), "bars_seen": r.get("bars_seen"),
            "force_stop": r.get("force_stop"),
            "fills": [{"date": utc_date(int(f["ts_event"])), "side": f["order_side"], "qty": f["last_qty"],
                       "price": f["last_px"], "commission": f["commission"]} for f in fills],
            "final_cash": r.get("account_balance_usd"), "final_qty": r.get("final_qty"),
            "invalid_reasons": list(m.get("invalid_reasons") or [])}


def _money_close(a, b) -> bool:
    try:
        return abs(Decimal(str(a)) - Decimal(str(b))) <= Decimal("0.005")
    except ArithmeticError:
        return False


def compare_golden(got: dict, want: dict) -> list[str]:
    """6.8: integers and strings exactly, the price as its string, money within 0.005, reasons by leading id."""
    out = [f"{k}: {got.get(k)!r} != {want.get(k)!r}" for k in ("schema", "fixture", "status", "exit_code", "bars_fed",
                                                               "bars_seen", "force_stop", "final_qty")
           if got.get(k) != want.get(k)]
    if not _money_close(got.get("final_cash"), want.get("final_cash")):
        out.append(f"final_cash: {got.get('final_cash')!r} != {want.get('final_cash')!r}")
    gf, wf = got.get("fills") or [], want.get("fills") or []
    if len(gf) != len(wf):
        out.append(f"fills: {len(gf)} rows != {len(wf)}")
    for n, (a, b) in enumerate(zip(gf, wf)):
        out += [f"fill {n} {k}: {a.get(k)!r} != {b.get(k)!r}" for k in ("date", "side", "qty", "price")
                if a.get(k) != b.get(k)]
        if not _money_close(a.get("commission"), b.get("commission")):
            out.append(f"fill {n} commission: {a.get('commission')!r} != {b.get('commission')!r}")
    ids = [[str(r).split(":")[0] for r in d.get("invalid_reasons") or []] for d in (got, want)]
    if ids[0] != ids[1]:
        out.append(f"invalid_reasons ids: {ids[0]} != {ids[1]}")
    return out


def run_fixture(name: str, python: Path, unshare: str | None, *, timeout: float = launch.TIMEOUT_S) -> dict:
    """One fixture of spec 8.2 through the exact launch contract: {"golden", "census", "manifest", "result"}."""
    raw, bars = launch.fixture_inputs(name)
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        res = launch.run_child(launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=python,
                                                   unshare=unshare), timeout=timeout)
        try:
            manifest = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = None
        try:
            fills = _rows(tmp / "fills.csv", FILLS_HEADER)
        except (OSError, ValueError):
            fills = []
    finally:
        launch.cleanup_tempdir(tmp)
    return {"golden": golden_of(name, res.returncode, manifest, fills), "census": res.census, "manifest": manifest,
            "result": res}


def _venv_for_mode() -> tuple[Path, dict, str | None]:
    python = venv_python_from_key()
    reads = launch.read_venv(python)
    bad = launch.venv_mismatches(reads)
    if bad:
        raise refuse("R-03", "the venv is off its pins: " + "; ".join(b.removeprefix("R-03: ") for b in bad))
    return python, reads, launch.resolve_unshare()


def fixtures_mode(*, record: bool = False, write: bool = False, golden_dir: Path = launch.GOLDEN_DIR,
                  repo_root: Path = REPO_ROOT) -> int:
    """--fixtures: F1, F2 and N1 against their goldens (6.8); --write-goldens writes missing goldens on Linux, never
    over a file (QA-R2-6); --record-baseline writes the census baseline only when all three match (OPS-R2-1)."""
    try:
        python, reads, unshare = _venv_for_mode()
        env = launch_once(["--check-env"], python=python, child_cmd=None, unshare=unshare, timeout=launch.TIMEOUT_S)[1]
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    tag, runs, ok = reads["wheel"]["platform_tag"], {}, True
    for name in GOLDEN_FIXTURES:
        runs[name] = run_fixture(name, python, unshare)
        path = Path(golden_dir) / f"{name}.json"
        want = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        diff = ["no golden file"] if want is None else compare_golden(runs[name]["golden"], want)
        print(f"{name}: exit {runs[name]['result'].returncode}, census {len(runs[name]['census'])} names, "
              + ("matches its golden" if not diff else "differs: " + "; ".join(diff)))
        ok = ok and not diff
    if write:
        if not tag.startswith("manylinux"):
            return _print_refusal(BridgeRefusal("R-11", f"--write-goldens runs on Linux only, not {tag}"))
        for name in GOLDEN_FIXTURES:
            path = Path(golden_dir) / f"{name}.json"
            if path.exists():
                print(f"{path.name} exists; never overwritten")
                continue
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(_json_text(runs[name]["golden"]))
            print(f"written {path.name}")
        print("STATUS OK exit=0 record=-")
        return 0
    baseline = load_baseline(tag, golden_dir)
    for name in ("F1", "F2"):
        if baseline is not None:
            print(f"{name} census against modules_{tag}.json: {judge_census(runs[name]['census'], baseline) or 'equal'}")
    if record:
        if not ok:
            print("--record-baseline writes nothing: a fixture differs from its golden (OPS-R2-1)")
            print("STATUS REFUSED exit=2 record=-")
            return 2
        union = sorted(set(runs["F1"]["census"]) | set(runs["F2"]["census"]))
        rel = f"tools/nautilus/golden/modules_{tag}.json"
        git = shutil.which("git")
        tracked = git is not None and _git(git, repo_root, "ls-files", "--error-unmatch", rel).returncode == 0
        code, lines = record_baseline(golden_dir, tag, union, tracked=tracked, python=(env or {}).get("python"))
        for other in sorted(Path(golden_dir).glob("modules_*.json")):
            if other.name != f"modules_{tag}.json":
                print(f"against {other.name}: {census_diff(load_baseline(other.stem[8:], golden_dir), union) or 'equal'}")
        print("\n".join(lines))
        print(f"STATUS {'OK' if code == 0 else 'REFUSED'} exit={code} record={Path(golden_dir) / f'modules_{tag}.json'}")
        return code
    print(f"STATUS {'OK' if ok else 'REFUSED'} exit={0 if ok else 2} record=-")
    return 0 if ok else 2


def check_env_mode() -> int:
    """--check-env: the venv checks of 6.7, --check-env and --guard-selftest; exit 0 on a match, 2 otherwise."""
    try:
        v = check_venv(child_cmd=None, unshare=launch.resolve_unshare(), timeout=launch.TIMEOUT_S)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    print(json.dumps(v["check_env"], sort_keys=True))
    print(json.dumps(v["guard_selftest"], sort_keys=True))
    print(json.dumps({"python": str(v["python"]), "python_minor": v["reads"]["python_minor"],
                      "versions": v["reads"]["versions"], "wheel": v["reads"]["wheel"]}, sort_keys=True))
    print("STATUS OK exit=0 record=-")
    return 0


def egress_record_mode(repo_root: Path = REPO_ROOT) -> int:
    """--egress-record (4.4): writes docs/nautilus_bridge/egress/<host tag>.json, then exits 2 (R-14) unless the
    probe is blocked and the parent's control connect succeeded; a failed control connect is printed first."""
    try:
        python, reads, unshare = _venv_for_mode()
        res, probe = launch_once([], python=python, child_cmd=None, unshare=unshare, timeout=60,
                                 script=launch.EGRESS_PROBE)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    control = control_connect()
    rec = {"schema": EGRESS_SCHEMA, "platform_tag": launch.host_tag(), "venv_python": str(python),
           "base_python": reads["pyvenv"]["executable"], "layer": LAYER,
           "probe": probe or {"blocked": False, "errno": None, "error": f"exit {res.returncode}: {res.stdout_tail[-200:]}"},
           "recorded_utc": _utc_now(), "control_connect": control}
    path = Path(repo_root) / "docs" / "nautilus_bridge" / "egress" / f"{launch.host_tag()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_text(rec), encoding="utf-8", newline="\n")
    print(json.dumps(rec, sort_keys=True))
    if rec["probe"].get("blocked") is True and control["ok"]:
        print(f"STATUS OK exit=0 record={path}")
        return 0
    if not control["ok"]:
        print(f"control connect failed: {control['error']}")
        print("this network does not reach 1.1.1.1:443, so the record cannot prove the rule; run Step 7A on a "
              "network that does, or ask Claude")
    exc = refuse("R-14", f"the record does not prove the rule: probe blocked {rec['probe'].get('blocked')}, "
                         f"control connect ok {control['ok']}")
    print(str(exc))
    print(f"remedy: {exc.remedy}")
    print(f"STATUS REFUSED exit=2 record={path}")
    return 2


# --------------------------------------------------------------------------- #
# Modes added by plan Task 5: --fingerprint, --timing, --handoff-report (5.3.1)
# --------------------------------------------------------------------------- #
HANDOFF_SCHEMA = "nautilus-bridge-handoff/1"
BRANCH = "claude/amazing-gauss-tdiguu"
TIMING_BARS, TIMING_ENGINE = 5600, "nautilus_trader.backtest.engine"
TIMING_GRID = {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]}      # pilot 1's 12 columns
FIREWALL_COMMANDS = (                               # 5.3.1 (OPS-R4-3): Format-List output is English and ASCII
    "Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Format-List DisplayName, Enabled, Direction, "
    "Action, Profile",
    "Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Get-NetFirewallApplicationFilter | Format-List "
    "Program",
    "Get-NetFirewallProfile | Format-List Name, Enabled")


def fingerprint_mode(table_path: Path, repo_root: Path = REPO_ROOT) -> int:
    """--fingerprint (GOVERNANCE-R4-1): prints table_sha256 and code_sha256 once the table parses, then validates it
    against 6.6 with both owner fields optional (R-11, exit 2), opens no prices_file, rf_file or reference_card, and
    prints host_fingerprint, or null with the reason, from the production family ledger; exit 0."""
    try:
        t, _ = load_table(table_path)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    tsha, code = table_sha256(t), code_sha256(repo_root)
    print(f"table_sha256 {tsha}")
    print(f"code_sha256 {code}")
    try:
        _check_place(t, "of-record", repo_root)
        _check_fields(t, "fingerprint")
        _check_values(t, "of-record")
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    import config
    ledger = gate_ledger.family_ledger(t["family_id"], config.macro_dir() / "ledgers")
    try:
        found = host_fingerprint(socket.gethostname(), ledger) if ledger.path.is_file() else None
        why = (f"the family ledger {ledger.path} does not exist" if not ledger.path.is_file()
               else f"the family ledger {ledger.path} holds no row")
    except gate_ledger.LedgerRefused as exc:
        found, why = None, f"the family ledger {ledger.path} does not verify: {exc}"
    print(f"host_fingerprint {found}" if found else f"host_fingerprint null ({why}; R-15, O11)")
    print(f"owner_confirmed form: <name>, <YYYY-MM-DD>, table {tsha[:16]}, code {code[:16]}")
    print("STATUS OK exit=0 record=-")
    return 0


def timing_inputs(n_bars: int = TIMING_BARS) -> list[tuple[bytes, bytes]]:
    """(input.json, bars.csv) of the 12 synthetic --timing runs: pilot 1's grid at 50 bp on 5,600 business days of
    spec 8.2's generator (seed 2026, 80 to 650), 9 decimals, the fixtures' empty-ledger hash (6.1)."""
    rng = np.random.default_rng(2026)
    lr = rng.normal(0.0, np.where(np.arange(n_bars) // 250 % 2 == 0, 0.008, 0.02))
    lr += (np.log(650.0 / 80.0) - lr.sum()) / n_bars
    closes = np.round(80.0 * np.exp(np.cumsum(lr)), PRICE_DECIMALS)
    dates = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2001-01-02", periods=n_bars)]
    bars = bars_bytes(closes, bar_timestamps(dates, "SPY"))
    table = {"strategy": "trend_switch", "instrument": "SPY", "capital_usd": "1000000", "cost_bps": 50.0,
             "fill_seed": 42, "size_precision": 0, "volume": "1000000000"}
    return [(input_bytes(table, theta, 1, bars, n_bars, gate_ledger.ledger_hash([])), bars)
            for theta in S.grid_from(**TIMING_GRID)]


def import_micros(stderr: str, module: str = TIMING_ENGINE) -> int | None:
    """The cumulative -X importtime figure, in microseconds, of `module` in a child's stderr; None if absent."""
    for line in stderr.splitlines():
        fields = line.split("|")
        if line.startswith("import time:") and len(fields) == 3 and fields[2].strip() == module:
            return int(fields[1])
    return None


def run_timing(python: Path, unshare: str | None) -> dict:
    """--timing's numbers: 12 sandbox runs of 5,600 bars through the exact launch contract, wall time each, and the
    BacktestEngine import time read from the first run's -X importtime lines."""
    seconds, codes, micros = [], [], None
    for raw, bars in timing_inputs():
        tmp = launch.make_tempdir()
        try:
            (tmp / "input.json").write_bytes(raw)
            (tmp / "bars.csv").write_bytes(bars)
            started = time.perf_counter()
            res = launch.run_child(launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=python,
                                                       unshare=unshare))
            seconds.append(round(time.perf_counter() - started, 3))
            codes.append(res.returncode)
            micros = micros if micros is not None else import_micros(res.stderr)
        finally:
            launch.cleanup_tempdir(tmp)
    return {"bars": TIMING_BARS, "runs": len(seconds), "exit_codes": codes, "seconds": seconds,
            "total_s": round(sum(seconds), 3), "timed_module": TIMING_ENGINE, "import_us": micros}


def timing_mode() -> int:
    """--timing (5.3.1): prints run_timing's JSON; exit 0 when all 12 runs exit 0 and the import line was found."""
    try:
        python, _reads, unshare = _venv_for_mode()
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    out = run_timing(python, unshare)
    print(json.dumps(out, sort_keys=True))
    ok = out["import_us"] is not None and out["exit_codes"] == [0] * len(out["exit_codes"]) and out["runs"] == 12
    print(f"STATUS {'OK' if ok else 'REFUSED'} exit={0 if ok else 2} record=-")
    return 0 if ok else 2


def _part(report: dict, name: str, fn: Callable[[], Any]) -> Any:
    """One part of the hand-off report: its value, or its own error, never a stop (5.3.1)."""
    try:
        report[name] = fn()
    except Exception as exc:                        # noqa: BLE001 - each part records its own error
        report[name] = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-2000:]}
    return report[name]


def _git_lines(repo_root: Path, *args: str) -> dict:
    git = shutil.which("git")
    if git is None:
        return {"error": "git is not on PATH"}
    res = _git(git, repo_root, *args)
    return {"exit": res.returncode, "stdout": res.stdout.splitlines(), "stderr": res.stderr.strip()[-500:]}


def _powershell(command: str) -> dict:
    res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], stdin=subprocess.DEVNULL,
                         capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    return {"command": command, "exit": res.returncode, "stdout": res.stdout.splitlines(), "stderr": res.stderr[-500:]}


def _fixture_part(python: Path, unshare: str | None, golden_dir: Path) -> dict:
    out = {}
    for name in GOLDEN_FIXTURES:
        run_ = run_fixture(name, python, unshare)
        path = Path(golden_dir) / f"{name}.json"
        want = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        res = run_["result"]
        out[name] = {"golden": run_["golden"], "diff": ["no golden file"] if want is None else compare_golden(
            run_["golden"], want), "returncode": res.returncode, "ntstatus": res.ntstatus, "census": res.census,
            "stdout_tail": res.stdout_tail, "stderr_tail": res.stderr_tail}
    return out


def _suite_rows(repo_root: Path) -> dict:
    path = Path(repo_root) / "qa" / "acceptance_results.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return {"path": str(path), "mtime_utc": mtime, "rows": [r for r in rows if r.get("status") == "FAIL"
                                                            or str(r.get("test", "")).startswith("nautilus/")]}


def _need(python: Path | None) -> Path:
    if python is None:
        raise RuntimeError("no venv python: see the venv part")
    return python


def _venv_part() -> dict:
    python = venv_python_from_key()
    return {"python": str(python), "reads": launch.read_venv(python)}


def _child_json(mode_args: list[str], python: Path, unshare: str | None) -> dict:
    res, out = launch_once(mode_args, python=python, child_cmd=None, unshare=unshare, timeout=launch.TIMEOUT_S)
    return {"returncode": res.returncode, "json": out, "stdout_tail": res.stdout_tail, "stderr_tail": res.stderr_tail}


def _stub_part() -> dict:
    from tests.nautilus_acceptance import stub_python          # the interpreter the suite's stub children use (8.1)
    return {"python": stub_python(), "sys_executable": sys.executable}


def _egress_part(python: Path, venv: dict, unshare: str | None) -> dict:
    probe = launch_once([], python=python, child_cmd=None, unshare=unshare, timeout=60, script=launch.EGRESS_PROBE)[1]
    return {"schema": EGRESS_SCHEMA, "platform_tag": launch.host_tag(), "venv_python": str(python),
            "base_python": venv["reads"]["pyvenv"]["executable"], "layer": LAYER, "probe": probe,
            "recorded_utc": _utc_now(), "control_connect": control_connect()}


def _firewall_part():
    if os.name != "nt":
        return {"skipped": f"not Windows ({launch.host_tag()})"}
    return [_powershell(c) for c in FIREWALL_COMMANDS]


def _census_part(fixtures: dict, golden_dir: Path) -> dict:
    union = sorted(set(fixtures["F1"]["census"]) | set(fixtures["F2"]["census"]))
    linux = load_baseline("manylinux_2_35_x86_64", golden_dir)
    return {"against": "modules_manylinux_2_35_x86_64.json", "union_F1_F2": len(union),
            "diff": census_diff(linux or [], union), "judgement": judge_census(union, linux or [])}


def handoff_report(repo_root: Path = REPO_ROOT, golden_dir: Path = launch.GOLDEN_DIR) -> dict:
    """The Step 7A hand-off report (5.3.1; OPS-8): every part in order, each recording its own error, never a stop."""
    rep: dict = {"schema": HANDOFF_SCHEMA, "host_tag": launch.host_tag(), "recorded_utc": _utc_now()}
    _part(rep, "parent", lambda: {"sys_executable": sys.executable, "sys_base_executable": sys._base_executable,
                                  "sys_version": sys.version, "nautilus_trader": launch.parent_nautilus(),
                                  "pyarrow": launch.parent_pyarrow()})
    _part(rep, "git", lambda: {"head": _git_lines(repo_root, "rev-parse", "HEAD"),
                               "origin_branch": _git_lines(repo_root, "rev-parse", f"origin/{BRANCH}"),
                               "status": _git_lines(repo_root, "status", "--porcelain=v1")})
    venv = _part(rep, "venv", _venv_part)
    python = Path(venv["python"]) if "python" in venv else None
    unshare = _part(rep, "unshare", launch.resolve_unshare)
    unshare = unshare if isinstance(unshare, str) else None
    _part(rep, "venv_mismatches", lambda: launch.venv_mismatches(venv["reads"]))
    _part(rep, "check_env", lambda: _child_json(["--check-env"], _need(python), unshare))
    _part(rep, "guard_selftest", lambda: _child_json(["--guard-selftest"], _need(python), unshare))
    _part(rep, "stub_interpreter", _stub_part)
    _part(rep, "egress", lambda: _egress_part(_need(python), venv, unshare))
    _part(rep, "firewall", _firewall_part)
    fixtures = _part(rep, "fixtures", lambda: _fixture_part(_need(python), unshare, golden_dir))
    _part(rep, "census", lambda: _census_part(fixtures, golden_dir))
    _part(rep, "timing", lambda: run_timing(_need(python), unshare))
    _part(rep, "suite", lambda: _suite_rows(repo_root))
    return rep


def handoff_mode(repo_root: Path = REPO_ROOT) -> int:
    """--handoff-report: writes docs/nautilus_bridge/handoff/<host tag>.json (overwritten; git keeps the history)."""
    from tools.nautilus import parity
    report = handoff_report(repo_root)
    path = Path(repo_root) / "docs" / "nautilus_bridge" / "handoff" / f"{launch.host_tag()}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_record(path, parity.plain(report))
    except Exception as exc:                        # noqa: BLE001
        print(f"the hand-off report could not be written: {type(exc).__name__}: {exc}")
        print("STATUS ERROR exit=4 record=-")
        return 4
    failed = sorted(k for k, v in report.items() if isinstance(v, dict) and "error" in v)
    print(f"parts with an error: {', '.join(failed) or 'none'}")
    print(f"STATUS OK exit=0 record={path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -B -m tools.nautilus.runner")
    ap.add_argument("--table")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--of-record", action="store_true")
    ap.add_argument("--ledger-dir")
    ap.add_argument("--out-dir")
    ap.add_argument("--child-cmd", help="rehearsal only: a JSON list replacing <venv python> ... <sandbox.py>")
    ap.add_argument("--rerun-of")
    ap.add_argument("--reason")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--egress-record", action="store_true")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--write-goldens", action="store_true")
    ap.add_argument("--fingerprint", action="store_true", help="with --table: table_sha256, code_sha256, host_fingerprint")
    ap.add_argument("--timing", action="store_true")
    ap.add_argument("--handoff-report", action="store_true")
    a = ap.parse_args(argv)
    run_mode = bool(a.table) and not a.fingerprint
    modes = [run_mode, a.fingerprint, a.check_env, a.egress_record, a.fixtures, a.timing, a.handoff_report]
    if sum(modes) != 1 or (run_mode and a.rehearsal == a.of_record) or (a.fingerprint and (
            not a.table or a.rehearsal or a.of_record)) or (
            (a.record_baseline or a.write_goldens) and not a.fixtures) or (a.record_baseline and a.write_goldens):
        ap.print_usage()
        print("STATUS REFUSED exit=2 record=-")
        return 2
    if a.fingerprint:
        return fingerprint_mode(Path(a.table))
    if a.timing:
        return timing_mode()
    if a.handoff_report:
        return handoff_mode()
    if a.check_env:
        return check_env_mode()
    if a.egress_record:
        return egress_record_mode()
    if a.fixtures:
        return fixtures_mode(record=a.record_baseline, write=a.write_goldens)
    child_cmd = None
    if a.child_cmd is not None:
        try:
            child_cmd = json.loads(a.child_cmd)
        except ValueError:
            return _print_refusal(refuse("R-11", f"--child-cmd is not a JSON list: {a.child_cmd!r}"))
    return run(Path(a.table), mode="rehearsal" if a.rehearsal else "of-record",
               ledger_dir=Path(a.ledger_dir) if a.ledger_dir else None, out_dir=Path(a.out_dir) if a.out_dir else None,
               child_cmd=child_cmd, rerun_of=a.rerun_of, reason=a.reason)


if __name__ == "__main__":
    raise SystemExit(main())
