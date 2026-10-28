"""The layer-1 stub child of the NautilusTrader bridge (spec 2026-10-26 section 8.1; QA-R2-2). Standard library only.

    <stub python> -I <abs tests/nautilus_stub_child.py> [failure flags] {--check-env | --guard-selftest | --probe |
                                                                         run --in <dir>}

It answers the sandbox's two self-checks as the sandbox does, `--probe` as a blocked egress probe, and in `run` mode
reads input.json and bars.csv, applies the decision rules of spec 5.2.5 (plain_mean for every moving average, the
fee-inclusive Decimal sizing), fills every order at its bar's close, rounds each commission with `cents` (5.4.1) and
writes fills.csv, decisions.csv, onbar_equity.csv and manifest.json with every field of spec 6.2, so a correct input
passes every hard check. The failure flags select one failure mode each; a `--doctor <id>` manifest still says
`valid: true` and the stub exits 0, so only the parent's own re-derivation can catch it (QA-R3-2).
"""
import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path

PRECISION = {"HIGH_PRECISION": True, "FIXED_PRECISION": 16, "QUANTITY_MAX": 34028236692093.0,
             "PRICE_MAX": 17014118346046.0}                   # the Linux wheel's, as --check-env prints them (C3)
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}
DOCTORS = ("C-01", "C-02", "C-03", "C-04", "C-07", "C-09", "C-11", "C-14", "C-15")
CRYPTO_DEFAULTS = {"lookbacks": [7, 14, 21, 28], "mas": [10, 20, 50, 100, 200]}


def text(d: Decimal) -> str:
    """A Decimal as plain digits, "0" for zero (never "0E-8" or "1E+4")."""
    return "0" if d == 0 else format(d, "f")


def cents(x) -> int:
    """How Money rounds a commission (spec 5.4.1): the value as a double, times 100, half away from zero."""
    return int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def plain_mean(xs) -> float:
    """A left-to-right loop, never sum() (spec 5.2.5)."""
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)


def decide(inp: dict, P: list[float], i: int, held: int):
    """(decision or None, margin) on bar i: the table of spec 5.2.5."""
    prm = inp["params"]
    if inp["strategy"] == "trend_switch":
        L, s = prm["lookback"], prm["step"]
        if i < L or (i - L) % s:
            return None, None
        if prm["rule"] == "sma":
            mean = plain_mean(P[i - L + 1:i + 1])
            return (1 if P[i] > mean else 0), abs(P[i] - mean) / P[i]
        r = P[i] / P[i - L] - 1.0
        return (1 if r > 0.0 else 0), abs(r)
    lookbacks, mas = prm.get("lookbacks", CRYPTO_DEFAULTS["lookbacks"]), prm.get("mas", CRYPTO_DEFAULTS["mas"])
    if i < max(max(lookbacks), max(mas)):
        return None, None
    refs = [P[i - k] for k in lookbacks] + [plain_mean(P[i - n + 1:i + 1]) for n in mas]
    votes = [(P[i] - ref > 0) - (P[i] - ref < 0) for ref in refs]
    comp = sum(votes) / len(votes)
    state = 1 if comp > prm["hysteresis"] else 0 if comp < -prm["hysteresis"] else held
    return state, min(abs(P[i] - ref) / P[i] for ref in refs)


def write_csv(path: Path, header: list[str], rows: list[list]) -> str:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simulate(inp: dict, closes: list[str], ts: list[int], fee_1x: bool) -> dict:
    """The port's bar loop with a fill at every order's bar close; returns the rows and the final state."""
    P = [float(c) for c in closes]
    sp = inp["size_precision"]
    unit = Decimal(1).scaleb(-sp)
    c_size = Decimal(inp["cost_bps"]) * Decimal(inp["stress"]) / Decimal(10000)
    c_fee = Decimal(inp["cost_bps"]) / Decimal(10000) if fee_1x else c_size
    cash, qty, held = Decimal(inp["capital_usd"]), Decimal(0), 0
    fills, decisions, equity = [], [], []
    for i, (close, t) in enumerate(zip(closes, ts)):
        px = Decimal(close)
        equity.append([i, t, close, text(cash), text(qty), text(cash + qty * px)])
        decision, margin = decide(inp, P, i, held)
        if decision is None:
            continue
        action = "hold"
        if decision != held:
            if decision == 1:
                q = (cash / (px * (1 + c_size)) / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
            else:
                q = qty
            action = "skip_zero_qty"
            if q > 0:
                action = "buy" if decision == 1 else "sell"
                held = decision
                fee = Decimal(cents(q * px * c_fee)) / 100
                cash += -(q * px + fee) if decision == 1 else q * px - fee
                qty += q if decision == 1 else -q
                n = len(fills) + 1
                fills.append([t, "BUY" if decision == 1 else "SELL", f"{q:.{sp}f}", close, f"{fee:.2f}", "USD",
                              f"STUB-T{n}", f"STUB-O{n}"])
        decisions.append([i, t, decision, repr(margin), action])
    return {"fills": fills, "decisions": decisions, "equity": equity, "cash": cash, "qty": qty}


def manifest(inp: dict, raw: bytes, ts: list[int], sim: dict, hashes: dict) -> dict:
    """Every field of spec 6.2, valid by the child's own checks."""
    u = platform.uname()
    n = len(ts)
    return {"schema": "nautilus-bridge-manifest/2", "read_only": True, "mode": "run",
            "python": platform.python_version(), "system": u.system, "machine": u.machine,
            "precision": dict(PRECISION), "environment": "BACKTEST", "strategy_started": True,
            "input": {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                      "bars_fed": n, "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                      "stress": inp["stress"],
                      "ledger_hash_after_registration": inp["ledger_hash_after_registration"]},
            "engine": {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                       "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True,
                       "fill_seed": inp["fill_seed"]},
            "result": {"bars_seen": n, "iterations": n, "backtest_end": ts[-1], "force_stop": False,
                       "orders_total": len(sim["fills"]), "orders_filled": len(sim["fills"]), "denied": 0,
                       "rejected": 0, "orders_not_filled": [], "account_balance_usd": f"{sim['cash']:.2f}",
                       "final_qty": text(sim["qty"]), "stats_pnls_empty": True},
            "hashes": hashes, "valid": True, "invalid_reasons": []}


def doctor(m: dict, sim: dict, cid: str) -> None:
    """One planted condition the parent must re-derive (spec 5.2.7, section 7); the manifest stays `valid: true`."""
    r = m["result"]
    if cid == "C-01":
        r["force_stop"] = True
    elif cid == "C-02":                                   # bars_seen and bars_fed lowered together (QA-R4-3)
        r["bars_seen"] -= 1
        m["input"]["bars_fed"] -= 1
    elif cid == "C-03":
        r["orders_not_filled"] = ["O-STUB-1"]
    elif cid == "C-04":
        r["denied"] = 1
    elif cid == "C-07":
        m["precision"] = dict(m["precision"], FIXED_PRECISION=9)
    elif cid == "C-09":                                   # the first fill one nanosecond off its bar
        sim["fills"][0][0] += 1
    elif cid == "C-11":
        m["input"]["bars_sha256"] = "0" * 64
    elif cid == "C-14":
        m["input"]["ledger_hash_after_registration"] = "0" * 32
    elif cid == "C-15":
        m["strategy_started"] = False


def run(root: Path, a: argparse.Namespace) -> int:
    if a.exit is not None:
        return a.exit
    if a.sleep:
        time.sleep(a.sleep)
    raw = (root / "input.json").read_bytes()
    inp = json.loads(raw.decode("utf-8"))
    lines = (root / "bars.csv").read_text(encoding="utf-8").splitlines()[1:]
    closes = [line.split(",")[2] for line in lines]
    ts = [int(line.split(",")[1]) for line in lines]
    sim = simulate(inp, closes, ts, a.fee_1x)
    m = manifest(inp, raw, ts, sim, {})
    if a.doctor:
        doctor(m, sim, a.doctor)
    m["hashes"] = {
        "fills.csv": write_csv(root / "fills.csv", ["ts_event", "order_side", "last_qty", "last_px", "commission",
                                                    "commission_ccy", "trade_id", "venue_order_id"], sim["fills"]),
        "decisions.csv": write_csv(root / "decisions.csv", ["i", "ts_event", "decision", "margin", "action"],
                                   sim["decisions"]),
        "onbar_equity.csv": write_csv(root / "onbar_equity.csv", ["i", "ts_event", "close", "cash", "qty",
                                                                  "equity_pre"], sim["equity"])}
    if a.no_manifest:
        return 0
    body = "{not json\n" if a.bad_json else json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    (root / "manifest.json").write_text(body, encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="nautilus_stub_child.py")
    ap.add_argument("--exit", type=int)
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--no-manifest", action="store_true")
    ap.add_argument("--bad-json", action="store_true")
    ap.add_argument("--doctor", choices=DOCTORS)
    ap.add_argument("--fee-1x", action="store_true")
    ap.add_argument("--selftest-wrong", action="store_true")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv)
    if a.check_env:
        u = platform.uname()
        print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                          "system": u.system, "machine": u.machine, "environment": "BACKTEST",
                          "precision": PRECISION}))
        return 0
    if a.guard_selftest:
        out = dict(SELFTEST, sandbox="passed") if a.selftest_wrong else dict(SELFTEST)
        print(json.dumps(out, sort_keys=True))
        return 0
    if a.probe:
        print(json.dumps({"blocked": True, "errno": 101, "error": "stub"}))
        return 0
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute():
        return 20
    return run(root, a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
