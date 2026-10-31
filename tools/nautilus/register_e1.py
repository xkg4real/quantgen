"""O11 A2: register pilot-1's twelve E1 configurations without reading prices.

This is not an of-record run, an owner_confirmed writer, or a review waiver.
Rehearsals accept only temporary directories; owner mode is Windows-only and
uses the existing production directory convention, with no path/test overrides.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
from datetime import datetime, timezone
import uuid

from core.quant import gate_ledger as G
from tools.nautilus import runner as R
from tools.nautilus.parity import trial_counts

SCRIPT = "tools/nautilus/register_e1.py"
SCHEMA = "nautilus-e1-registration/1"
SOURCE_PREFIX = "O11-A2 registration-only; table "
GRID = [{"rule": rule, "lookback": lookback, "step": step}
        for rule in ("sma", "tsmom") for lookback in (126, 210, 252) for step in (21, 42)]


def _write(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with tmp.open("x", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False, indent=2, allow_nan=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        if json.loads(path.read_text(encoding="utf-8")) != value:
            raise OSError("registration receipt read-back mismatch")
    finally:
        tmp.unlink(missing_ok=True)


def _validate_table(t: dict, repo_root: Path) -> None:
    # Metadata-only checks: do not call check_table(), _check_reference(),
    # load_prices(), load_rf(), a study loader, the engine or code_sha256().
    R._check_fields(t, "fingerprint")
    R._check_place(t, "of-record", repo_root)
    R._check_values(t, "of-record")
    if (t["pilot"] != "E1-SPY" or t["grid"] != GRID or t["cost_bps"] != 50.0
            or (t["start"], t["end"]) != ("2004-12-01", "2026-09-25")
            or t["reference_card"] is not None):
        raise ValueError("A2 accepts only pilot-1 E1-SPY, its approved 12-setting grid, span and cost")
    # U is computed from the 24 documented US/KRX configurations, not an
    # arbitrary list supplied to inflate or suppress the trial count.
    expected = set()
    for symbols, cost in ((["GLD", "QQQ", "SPY", "TLT"], 50.0),
                          (["069500.KS", "132030.KS", "152380.KS", "229200.KS"], 3.0)):
        for theta in GRID:
            expected.add(json.dumps({"symbols": symbols, "cost_bps": cost, "params": theta}, sort_keys=True))
    found = [json.dumps({k: c[k] for k in ("symbols", "cost_bps", "params")}, sort_keys=True)
             for c in t["study_configs"]]
    if len(found) != 24 or set(found) != expected:
        raise ValueError("A2 requires the 24 documented study configurations; U cannot exceed 24")


def _planned_rows(t: dict, stamp: str, anchor: str, tsha: str) -> list[dict]:
    return [G.validate_row({"rule": "E1", "params": dict(theta, symbols=["SPY"], cost_bps=50.0),
            "timing_class": "COMPLIANT", "span": [t["start"], t["end"]], "market": "US",
            "run_utc": stamp, "phase": "research", "script": SCRIPT, "run_kind": "variant",
            "run_utc_anchor": anchor, "source": SOURCE_PREFIX + tsha}) for theta in GRID]


def _check_prefix(rows: list[dict], planned: list[dict]) -> None:
    if len(rows) > 12 or [r["config_id"] for r in rows] != [r["config_id"] for r in planned[:len(rows)]]:
        raise ValueError("E1 contains unrelated/reordered configurations; A2 will not replace or extend it")
    for row, expected in zip(rows, planned):
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f"E1 row differs from this registration intent: {key}")


def _check_receipt(receipt: dict, tsha: str, mode: str, anchor: str, n_rows: int) -> None:
    if not isinstance(receipt, dict):
        raise ValueError("registration receipt must be an object")
    if (receipt.get("schema"), receipt.get("table_sha256"), receipt.get("mode"),
            receipt.get("hostname"), receipt.get("source_anchor")) != (
            SCHEMA, tsha, mode, socket.gethostname(), anchor):
        raise ValueError("registration receipt belongs to another table/mode/host/source")
    if receipt.get("source_module_sha256") != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError("registration source changed after the saved intent")
    status, count = receipt.get("status"), receipt.get("n_registered", 0)
    if status not in ("INTENT", "PARTIAL", "REGISTERED_ONLY") or type(count) is not int or not 0 <= count <= 12:
        raise ValueError("registration receipt status/count is invalid")
    if count > n_rows or (status == "REGISTERED_ONLY" and (count != 12 or n_rows != 12)):
        raise ValueError("E1 lost rows recorded in the receipt; restore/reconcile, do not re-register")
    if any(receipt.get(k) is not False for k in ("prices_read", "pilot_executed", "owner_confirmed_written")):
        raise ValueError("registration-only receipt flags are invalid")
    G.parse_utc(receipt.get("created_utc"))


def register(table_path: Path, *, mode: str, ledger_dir: Path | None = None,
             out_dir: Path | None = None, repo_root: Path = R.REPO_ROOT,
             register_fn=None) -> dict:
    if mode not in ("rehearsal", "owner-windows"):
        raise ValueError("select rehearsal or owner-windows")
    if mode == "owner-windows":
        if sys.platform != "win32":
            raise ValueError("A2 owner registration must run on the owner's Windows PC")
        if ledger_dir is not None or out_dir is not None or register_fn is not None or repo_root != R.REPO_ROOT:
            raise ValueError("owner-windows accepts no directory, repository or writer override")
        import config
        ledger_dir = config.macro_dir() / "ledgers"
        out_dir = repo_root / "docs" / "nautilus_bridge" / "runs"
    else:
        if any(p is None or not R.inside_temp_root(p) for p in (table_path, ledger_dir, out_dir)):
            raise ValueError("rehearsal table, ledger and receipt directories must all be temporary")
    table_path, repo_root = Path(table_path), Path(repo_root)
    ledger_dir, out_dir = Path(ledger_dir), Path(out_dir)
    t, raw = R.load_table(table_path)
    _validate_table(t, repo_root)
    tsha = R.table_sha256(t)
    anchor = G.repo_anchor(repo_root)
    if not G.anchored(anchor):
        raise ValueError("registration requires an anchored repository HEAD")
    if mode == "owner-windows":
        check = R.check_tree(repo_root, G.repo_anchor, R.shutil.which("git"))
        if R.tree_refusal(check, "of-record") is not None:
            raise ValueError("commit the reviewed source before owner registration")
    # Same table lock as normal Nautilus runs. A2 deliberately does not inspect
    # C3 or use the run's freshness delay; normal of-record freshness stays intact.
    lock, _ = R.take_lock(out_dir, tsha, [], None)
    receipt_path = out_dir / f"A2-E1-{tsha[:16]}.json"
    ledger = G.family_ledger("E1", ledger_dir)
    try:
        rows = ledger.rows()      # broken chains refuse; no reset/overwrite
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            _check_receipt(receipt, tsha, mode, anchor, len(rows))
        else:
            if rows:
                raise ValueError("non-empty E1 without this A2 intent; use the ordinary runner")
            receipt = {"schema": SCHEMA, "mode": mode, "status": "INTENT",
                "table_sha256": tsha, "table_raw_sha256": hashlib.sha256(raw).hexdigest(),
                "source_anchor": anchor, "hostname": socket.gethostname(),
                "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "prices_read": False, "pilot_executed": False, "owner_confirmed_written": False}
            out_dir.mkdir(parents=True, exist_ok=True)
            _write(receipt_path, receipt)  # durable intent BEFORE first ledger append
        planned = _planned_rows(t, receipt["created_utc"], receipt["source_anchor"], tsha)
        _check_prefix(rows, planned)
        writer = register_fn or G.register_trial
        for index in range(len(rows), 12):
            writer(ledger, planned[index], script=SCRIPT)
            rows = ledger.rows()
            _check_prefix(rows, planned)
            if len(rows) != index + 1:
                raise ValueError("registration row read-back count differs")
            receipt.update(status="PARTIAL", n_registered=len(rows))
            _write(receipt_path, receipt)
        counts = trial_counts(t, rows)
        if counts["family_n_raw"] != 12 or not (0 <= counts["U"] <= 24) or counts["n_trials"] != 12 + counts["U"]:
            raise ValueError("A2 count contract not satisfied")
        receipt.update(status="REGISTERED_ONLY", n_registered=12, counts=counts,
            config_ids=[row["config_id"] for row in rows], ledger_hash=ledger.hash(rows),
            host_fingerprint=R.host_fingerprint(socket.gethostname(), ledger))
        _write(receipt_path, receipt)
        return dict(receipt, receipt_path=str(receipt_path))
    finally:
        lock.release()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rehearsal", action="store_true")
    modes.add_argument("--owner-windows", action="store_true")
    parser.add_argument("--ledger-dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        out = register(args.table, mode="rehearsal" if args.rehearsal else "owner-windows",
                       ledger_dir=args.ledger_dir, out_dir=args.out_dir)
    except (ValueError, OSError, R.BridgeRefusal, G.LedgerRefused) as exc:
        print(f"STATUS REFUSED registration-only: {exc}")
        return 2
    print(json.dumps({k: out[k] for k in ("status", "counts", "receipt_path")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
