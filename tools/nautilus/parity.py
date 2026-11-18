"""Parity checks and the gate hand-off of the NautilusTrader bridge (spec 2026-10-26 sections 5.4 and 5.5).

Steps 16 and 17 of the runner (5.3.2), reached through runner.parity_and_gate: per column and cost level the checks
P1 to P10 and P13 of 5.4.1, the benchmark check P0b, QUANTGEN's walk-forward selection applied to both engines'
matrices (5.4.2) with P11 and P12, both matrices scored by the unchanged gate (5.5), and a card only when every hard
check passes for every column at both cost levels and both engines reach the same verdict. Nothing here edits the
gate, the ledger or the study; validate._col_sharpe is a private helper used read-only (5.4.2).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Sequence

import numpy as np

from core.quant import gate_ledger, validate
from core.quant import strategies as S
from tools.nautilus import runner as R

BARS = {"P1": 1e-9, "P2": 0.9999, "P3": 0.01, "P5": 1e-6, "P6": (0.99, 1.005), "P8": 0.005, "P9": 0.001,
        "P10": 1e-9}                                 # 5.4.1's corrected bars (P1: the exempt QUANTGEN margin)
OWNER_BARS = {"P1": 0.98, "P2": 0.99, "P3": 0.05}    # the owner's original bars, printed next to them
HARD = ("P0b", "P1", "P2", "P3", "P4", "P7", "P12", "P13")
WARNINGS = ("P5", "P6", "P8", "P9", "P10")
ENGINE_TEXT = ("per-column event-driven replication (nautilus_trader 1.231.0 BacktestEngine, same-bar close); "
               "walk-forward column switches are not executed in either engine")
SELECTION_TEXT = "QUANTGEN walk-forward selection (wf_qg.origins, wf_qg.chosen) applied to both engines' matrices"
PARITY_SCOPE = "parity validates the engine, not the data; P0 ties the inputs to the study's loaders"
PARITY_BARS_TEXT = "corrected, spec 2026-10-26 §5.4"
CLAIM_PREFIXES = ("exploratory", "pre-specified on historical data", "confirmatory")
STUDY_BENCH = {"trend_switch": "(pn.prices[1:] / pn.prices[:-1] - 1.0).mean(axis=1)",     # study :275
               "crypto_trend": "pn.prices[1:, 0] / pn.prices[:-1, 0] - 1.0"}             # study :334
CITATIONS = {"trend_switch": "trend", "crypto_trend": "crypto_trend"}                   # keys of study.CIT
REFERENCE_FLOATS = ("sr_oos", "ci90", "oos_is", "sr_stress", "years_positive", "plateau", "pbo", "prob_loss_oos")
PROTOCOL_KEYS = ("w_is", "w_oos", "min_is", "ci_level", "bootstrap_B", "block")


def plain(x):
    """JSON-ready values for the run record: numpy scalars and arrays, tuples and Decimals become Python values."""
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, np.ndarray):
        return [plain(v) for v in x.tolist()]
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, Decimal):
        return str(x)
    return x


# --------------------------------------------------------------------------- #
# 5.4.1: the checks
# --------------------------------------------------------------------------- #
def cents(x) -> int:
    """How Money rounds a commission (5.4.1; QA-R2-7): the value as a double, times 100, half away from zero."""
    return int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def corr(a, b) -> float:
    """Pearson correlation; a pair of constant series counts 1.0 when equal to 1e-12 and NaN otherwise (plan ruling
    T5 CI 1: a column that never trades with rf = 0 gives R = pnl = 0 on every row)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size < 2 or not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return float("nan")
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return 1.0 if float(np.max(np.abs(a - b))) <= 1e-12 else float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def mdd(x) -> float:
    """Maximum drawdown of the compounded curve, as score_strategy computes it (P8)."""
    eq = np.cumprod(1.0 + np.asarray(x, dtype=float))
    return float(np.min(eq / np.maximum.accumulate(eq) - 1.0)) if eq.size else float("nan")


def pair_checks(a, b) -> dict:
    """P2 and P3 on one pair of series (also P12): correlation and the absolute Sharpe gap, both bars."""
    c, d = corr(a, b), abs(validate.sharpe(a) - validate.sharpe(b))
    return {"corr": c, "abs_dsr": d, "pass": bool(c >= BARS["P2"] and d <= BARS["P3"]),
            "owner_pass": bool(c >= OWNER_BARS["P2"] and d <= OWNER_BARS["P3"])}


def decision_bars(strategy: str, theta: dict, T: int) -> list[int]:
    """The bars on which a port decides (5.2.5): trend i >= L and (i - L) % s == 0; crypto every bar from warm-up."""
    if strategy == "trend_switch":
        return list(range(int(theta["lookback"]), T, int(theta["step"])))
    p = R.child_params({"strategy": strategy}, theta)
    return list(range(max(max(p["lookbacks"]), max(p["mas"])), T))


def qg_margins(strategy: str, theta: dict, closes: np.ndarray) -> np.ndarray:
    """P1's QUANTGEN margin per bar from QUANTGEN's own arrays (QA-19): sma abs(P - S._sma(P, L)) / P; tsmom
    abs(P[i] / P[i-L] - 1); crypto_trend the smallest abs(P - ref) / P over the votes, ref from S._sma. NaN where
    a bar has no margin."""
    P = np.asarray(closes, dtype=float)
    out = np.full(P.size, np.nan)
    if strategy == "trend_switch":
        L = int(theta["lookback"])
        if theta["rule"] == "sma":
            return np.abs(P - S._sma(P[:, None], L)[:, 0]) / P
        out[L:] = np.abs(P[L:] / P[:-L] - 1.0)
        return out
    p = R.child_params({"strategy": strategy}, theta)
    warm = max(max(p["lookbacks"]), max(p["mas"]))
    refs = [np.concatenate([np.full(k, np.nan), P[:-k]]) for k in p["lookbacks"]]
    refs += [S._sma(P[:, None], n)[:, 0] for n in p["mas"]]
    out[warm:] = np.min(np.abs(P[None, warm:] - np.vstack(refs)[:, warm:]), axis=0) / P[warm:]
    return out


def p1(decisions: list[dict], weights: np.ndarray, margins: np.ndarray, expected_bars: Sequence[int]) -> dict:
    """P1: the child's logged decision against QUANTGEN's W[t] > 0 on every decision bar; a mismatch whose QUANTGEN
    margin is below 1e-9 relative is exempt and listed; the logged bars must be the decision bars."""
    bars = [d["i"] for d in decisions]
    mism = [d["i"] for d in decisions if int(weights[d["i"]] > 0) != d["decision"]]
    exempt = [{"bar": i, "margin": float(margins[i])} for i in mism
              if np.isfinite(margins[i]) and margins[i] < BARS["P1"]]
    agree = (len(bars) - len(mism)) / len(bars) if bars else 1.0
    same_bars = bars == list(expected_bars)
    return {"value": agree, "decision_bars": len(bars), "same_bars": same_bars, "mismatches": mism,
            "exempt": exempt, "pass": same_bars and len(exempt) == len(mism), "owner_pass": agree >= OWNER_BARS["P1"]}


def p7(fills: list[dict], manifest: dict | None, *, cost_bps, stress: int) -> dict:
    """P7 (QUANT-5, QUANT-R2-3): each commission recomputed from the table's cost and the runner's own stress, as
    Money rounds it; USD only; the manifest echoes both values."""
    rate = Decimal(R.cost_text(cost_bps)) * Decimal(stress) / Decimal(10000)
    bad = [k for k, f in enumerate(fills) if f["commission"] * 100 != cents(f["last_qty"] * f["last_px"] * rate)
           or f["commission_ccy"] != "USD"]
    echo = (manifest or {}).get("input") or {}
    echoed = echo.get("cost_bps") == R.cost_text(cost_bps) and echo.get("stress") == str(stress)
    return {"bad_fills": bad, "echo": echoed, "pass": not bad and echoed}


def leg_checks(leg: "R.Leg", *, strategy: str, theta: dict, closes: np.ndarray, rf: np.ndarray, weights: np.ndarray,
               pnl: np.ndarray, turnover: np.ndarray, cost_bps) -> dict:
    """P1 to P10 and P13 for one child (5.4.1); weights is QUANTGEN's (T,) column, pnl the (T-1,) column at this
    leg's cost level, turnover QUANTGEN's (T-1,) abs(dw). An invalid leg gets only P13."""
    out = {"col": leg.col, "stress": leg.stress, "P13": {"pass": not leg.invalid and leg.rebuilt is not None,
                                                         "reasons": list(leg.invalid)}}
    if not out["P13"]["pass"]:
        return out
    T, rb, P = len(closes), leg.rebuilt, np.asarray(closes, dtype=float)
    c = float(R.cost_text(cost_bps)) * leg.stress / 1e4
    out["P1"] = p1(leg.decisions, weights, qg_margins(strategy, theta, P), decision_bars(strategy, theta, T))
    pair = pair_checks(rb.R, pnl)
    out["P2"] = {"value": pair["corr"], "pass": pair["corr"] >= BARS["P2"],
                 "owner_pass": pair["corr"] >= OWNER_BARS["P2"]}
    out["P3"] = {"value": pair["abs_dsr"], "pass": pair["abs_dsr"] <= BARS["P3"],
                 "owner_pass": pair["abs_dsr"] <= OWNER_BARS["P3"]}
    fill_bars, traded = sorted(set(rb.fill_bars) - {T - 1}), sorted(int(t) for t in np.flatnonzero(turnover > 0))
    out["P4"] = {"fill_bars": fill_bars, "dw_bars": traded, "pass": fill_bars == traded}
    gaps = [abs(float(f["last_px"]) / float(P[b]) - 1.0) for f, b in zip(leg.fills, rb.fill_bars)]
    out["P5"] = {"value": max(gaps, default=0.0), "pass": max(gaps, default=0.0) <= BARS["P5"]}
    tv, dw = float(np.sum(rb.TV)), float(np.sum(turnover))
    ratio = tv / dw if dw > 0 else (1.0 if tv == 0 else float("inf"))
    out["P6"] = {"value": ratio, "pass": BARS["P6"][0] <= ratio <= BARS["P6"][1]}
    out["P7"] = p7(leg.fills, leg.manifest, cost_bps=cost_bps, stress=leg.stress)
    out["P8"] = {"value": abs(mdd(rb.R) - mdd(pnl)), "pass": abs(mdd(rb.R) - mdd(pnl)) <= BARS["P8"]}
    te = float(np.std(rb.R - pnl, ddof=1) * math.sqrt(validate.TRADING_DAYS))
    out["P9"] = {"value": te, "pass": te <= BARS["P9"]}
    r_next = np.abs(P[1:] / P[:-1] - 1.0)
    bound = (c / (1.0 + c) + P[:-1] / rb.E_minus[:-1]) * (r_next + c) + np.asarray(rf, dtype=float)[:-1] + BARS["P10"]
    over = [int(t) for t in np.flatnonzero(np.abs(rb.R - pnl) > bound)]
    out["P10"] = {"max_gap": float(np.max(np.abs(rb.R - pnl))), "rows_over": over, "pass": not over}
    return out


def study_benchmark(strategy: str, study_prices: np.ndarray) -> np.ndarray:
    """The study's benchmark expression (STUDY_BENCH) on the study's prices rounded to 9 decimals (P0b)."""
    P = np.round(np.asarray(study_prices, dtype=float), R.PRICE_DECIMALS)
    if strategy == "trend_switch":
        return (P[1:] / P[:-1] - 1.0).mean(axis=1)
    return P[1:, 0] / P[:-1, 0] - 1.0


def p0b(strategy: str, closes: np.ndarray, study_prices: np.ndarray) -> dict:
    """P0b (QUANT-1): the benchmark from the runner's rounded closes equals the study's expression, byte for byte."""
    mine = np.asarray(closes, dtype=float)[1:] / np.asarray(closes, dtype=float)[:-1] - 1.0
    theirs = study_benchmark(strategy, study_prices)
    same = mine.shape == theirs.shape and mine.tobytes() == theirs.tobytes()
    first = None if same or mine.shape != theirs.shape else int(np.flatnonzero(mine != theirs)[0])
    return {"pass": same, "rows": int(mine.size), "study_rows": int(theirs.size), "first_difference": first}


# --------------------------------------------------------------------------- #
# 5.4.2: QUANTGEN's selection on both matrices; P11 and P12
# --------------------------------------------------------------------------- #
def select_matched(pnl_nt: np.ndarray, pnl_stress_nt: np.ndarray, turnover_nt: np.ndarray, dates: Sequence[str],
                   wf_qg: validate.WalkForward, *, embargo: int) -> validate.WalkForward:
    """wf_qg's origins and chosen columns applied to the Nautilus matrices, sliced as walk_forward slices
    (core/quant/validate.py:373-375); on QUANTGEN's own matrices it reproduces wf_qg bit for bit (L1-21)."""
    M, Ms, To = (np.asarray(x, dtype=float) for x in (pnl_nt, pnl_stress_nt, turnover_nt))
    T, G = M.shape
    w_is, w_oos = validate.GATE["w_is"], validate.GATE["w_oos"]
    out_d, out_p, out_s, out_t, is_sr = [], [], [], [], []
    for o, g in zip(wf_qg.origins, wf_qg.chosen):
        a, b = o + embargo, min(o + embargo + w_oos, T)
        out_d.extend(dates[a:b]); out_p.extend(M[a:b, g]); out_s.extend(Ms[a:b, g]); out_t.extend(To[a:b, g])
        is_sr.append(validate._col_sharpe(M[max(0, o - w_is):o]))
    return validate.WalkForward(dates=tuple(out_d), pnl=np.asarray(out_p), pnl_stress=np.asarray(out_s),
                                turnover=np.asarray(out_t), origins=wf_qg.origins, chosen=wf_qg.chosen,
                                is_sharpes=np.asarray(is_sr), n_configs=G, note=wf_qg.note)


def p11(wf_qg: validate.WalkForward, wf_own: validate.WalkForward) -> list[dict]:
    """P11 (diagnostic): per origin, Nautilus's own choice against QUANTGEN's, with QUANTGEN's in-sample Sharpe gap."""
    out = []
    for k, (o, g) in enumerate(zip(wf_qg.origins, wf_qg.chosen)):
        h = wf_own.chosen[k] if k < len(wf_own.chosen) else None
        gap = None if h is None else float(wf_qg.is_sharpes[k, g] - wf_qg.is_sharpes[k, h])
        out.append({"origin": o, "quantgen": g, "nautilus": h, "match": g == h, "is_sharpe_gap": gap})
    return out


def p12(wf_qg: validate.WalkForward, wf_nt: validate.WalkForward) -> dict:
    """P12: P2 and P3 on the selection-matched OOS series, at 1x and at 2x."""
    return {"1x": pair_checks(wf_nt.pnl, wf_qg.pnl), "2x": pair_checks(wf_nt.pnl_stress, wf_qg.pnl_stress)}


# --------------------------------------------------------------------------- #
# 5.5: trial counts, predicates, agreement, reference drift, card
# --------------------------------------------------------------------------- #
def study_config_ids(table: dict) -> list[str]:
    """config_id of every study_configs entry, from a row built as 6.4 builds one (QUANT-4)."""
    out = []
    for c in table["study_configs"]:
        params = json.loads(json.dumps(dict(c["params"], symbols=sorted(c["symbols"]), cost_bps=float(c["cost_bps"])),
                                       default=str))
        out.append(gate_ledger.config_id({"rule": table["rule"], "params": params, "timing_class": "COMPLIANT"}))
    return out


def trial_counts(table: dict, rows: Sequence[dict]) -> dict:
    """5.5 step 3 on the family ledger's rows after registration: n_trials = family_n_raw + U."""
    present = {r["config_id"] for r in rows}
    absent = sorted({i for i in study_config_ids(table) if i not in present})
    return {"len_grid": len(table["grid"]), "family_n_raw": len(rows),
            "market_n_raw": sum(r.get("market") == table["market"] for r in rows), "U": len(absent),
            "n_trials": len(rows) + len(absent), "study_configs_absent": absent}


def gate_predicates(score: validate.StrategyScore, gate: dict) -> dict[str, bool]:
    """Exactly the 18 predicates _decide_strategy reads (core/quant/validate.py:536-622), from the GATE snapshot."""
    g, s = gate, score
    meaningful, flat = s.n_configs >= g["pbo_min_configs"], s.prob_loss_oos <= g["prob_loss_max"]
    out = {"ci_pos": s.ci90[0] > 0, "dsr_ok": s.dsr >= g["dsr_min"], "dsr_finite": math.isfinite(s.dsr),
           "pbo_meaningful": meaningful, "flat": flat,
           "pbo_ok": (s.pbo <= g["pbo_max"] or flat) if meaningful else flat,
           "pbo_reject": meaningful and s.pbo > g["pbo_reject"] and not flat,
           "oos_is_ok": s.oos_is >= g["oos_is_min"], "stress_ok": s.sr_stress > 0,
           "years_ok": s.years_positive >= g["years_pos_min"],
           "plateau_ok": s.plateau >= g["plateau_min"] and not s.edge,
           "sample_ok": s.n_trades >= g["trades_min"], "floor_ok": s.n_trades >= g["trades_floor"],
           "n_years_ok": s.n_years >= g["oos_years_min"],
           "sessions_ok": s.n_sessions >= round(g["oos_years_min"] * validate.TRADING_DAYS),
           "mtr_ok": s.n_sessions >= validate.min_track_record(s.sr_oos, g["ci_level"]),
           "has_bench": math.isfinite(s.bench_p), "bench_ok": s.bench_p <= g["bench_p_max"]}
    return {k: bool(v) for k, v in out.items()}


def agree(sc_qg: validate.StrategyScore, sc_nt: validate.StrategyScore, gate: dict) -> tuple[bool, str | None]:
    """5.5 step 5 (G-02): a card needs a benchmark test in both scores, equal decisions and equal predicate dicts."""
    if not (math.isfinite(sc_qg.bench_p) and math.isfinite(sc_nt.bench_p)):
        return False, "benchmark test dropped"
    if sc_qg.decision != sc_nt.decision or gate_predicates(sc_qg, gate) != gate_predicates(sc_nt, gate):
        return False, "decision mismatch"
    return True, None


def _close(a, b, tol: float) -> bool:
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return (math.isnan(a) and math.isnan(b)) or abs(a - b) <= tol


def reference_drift(sc_qg: validate.StrategyScore, wf_qg: validate.WalkForward, grid: Sequence[dict],
                    ref: dict) -> list[str]:
    """G-08: every field where sc_qg fails to reproduce the stored card's stats `ref` (5.5 step 5): chosen_last,
    n_trades and n_sessions exactly; n_years by the calendar-years rule that wrote the card; the floats within 1e-9;
    bench_p within 1/2000. Never the lines, reason or revise_target text."""
    out = [] if wf_qg.chosen and grid[wf_qg.chosen[-1]] == ref.get("chosen_last") else ["chosen_last"]
    out += [k for k in ("n_trades", "n_sessions") if getattr(sc_qg, k) != ref.get(k)]
    out += [] if len({d[:4] for d in wf_qg.dates}) == ref.get("n_years") else ["n_years"]
    for k in REFERENCE_FLOATS:
        mine, theirs = getattr(sc_qg, k), ref.get(k)
        pairs = list(zip(mine, theirs)) if k == "ci90" and isinstance(theirs, (list, tuple)) and len(theirs) == 2 else [
            (mine, theirs)]
        out += [] if all(_close(a, b, 1e-9) for a, b in pairs) else [k]
    return out + ([] if _close(sc_qg.bench_p, ref.get("bench_p"), 1.0 / 2000) else ["bench_p"])


def card_rules(table: dict, *, stub_child: bool) -> dict:
    """6.5's rules; `engine` is STUB when a stub child ran (5.3.1)."""
    return {"family": table["strategy"], "grid": table["grid"], "cost_bps_per_side": float(table["cost_bps"]),
            "embargo": table["embargo"], "engine": "STUB" if stub_child else ENGINE_TEXT, "selection": SELECTION_TEXT,
            "claim_label": table["claim_label"], "parity_scope": PARITY_SCOPE, "parity_bars": PARITY_BARS_TEXT}


def parity_summary(parity: dict) -> dict:
    """The card's stats.parity: the worst values over every column and cost level, P12, the warnings."""
    legs = [x for x in parity["legs"] if x["P13"]["pass"]]
    return {"hard_pass": parity["hard_pass"], "worst_corr": min((x["P2"]["value"] for x in legs), default=None),
            "worst_abs_dsr": max((x["P3"]["value"] for x in legs), default=None),
            "max_daily_gap": max((x["P10"]["max_gap"] for x in legs), default=None), "P12": parity["P12"],
            "warnings": parity["warnings"], "bars": "corrected (spec 2026-10-26 §5.4); owner bars in the run record"}


def build_card(ctx: "R.RunContext", wf_nt: validate.WalkForward, sc_qg: validate.StrategyScore,
               sc_nt: validate.StrategyScore, counts: dict, ledger_hash_at_run: str) -> validate.ModelCard:
    """6.5's card from sc_nt, whose decision equals sc_qg's; both scores shown (QUANT-2)."""
    t, reg = ctx.table, ctx.record["registration"]
    stats = {k: v for k, v in asdict(sc_nt).items() if k not in ("lines", "regime")}
    stats.update(regime=sc_nt.regime, chosen_last=ctx.grid[wf_nt.chosen[-1]] if wf_nt.chosen else {},
                 bench_sharpe=sc_nt.bench_sr, walk_forward=wf_nt.note,
                 parity=plain(parity_summary(ctx.record["parity"])),
                 quantgen_score={k: v for k, v in asdict(sc_qg).items() if k != "lines"})
    trials = {"N_planned": counts["len_grid"], "N_total": counts["n_trials"], "family_id": t["family_id"],
              "family_n_raw": counts["family_n_raw"], "market_n_raw": counts["market_n_raw"], "U": counts["U"],
              "study_configs_absent": counts["study_configs_absent"],
              "config_ids": [r["config_id"] for r in reg["rows"]], "row_md5s": [r["row_md5"] for r in reg["rows"]],
              "ledger_hash_at_run": ledger_hash_at_run,
              "ledger": (f"{t['family_id']}.jsonl: {reg['n_raw_before']} rows before registration, "
                         f"{reg['n_raw_after']} after; U = {counts['U']} of {len(t['study_configs'])} study "
                         "configurations absent")}
    return validate.ModelCard(
        card_id=t["card_id"], kind="strategy", hypothesis=f"{t['claim_label']}: {t['hypothesis']}",
        rules=card_rules(t, stub_child=ctx.stub_child),
        universe={"symbols": [t["symbol"]], "venue": ctx.record["costs"]["classes"].get(t["symbol"])},
        data={"sessions": len(ctx.dates), "start": ctx.dates[0], "end": ctx.dates[-1], "source": t["prices_file"],
              "prices_md5": ctx.record["data"]["prices_md5"], "rf_md5": ctx.record["data"]["rf_md5"]},
        costs={"cost_bps": float(t["cost_bps"]), "stress_multiplier": ctx.gate_snapshot["cost_stress"]},
        protocol={k: ctx.gate_snapshot[k] for k in PROTOCOL_KEYS}, trials=trials, seed=11, stats=stats,
        tests={"dsr": sc_nt.dsr, "pbo": sc_nt.pbo, "ci90": sc_nt.ci90, "sr_stress": sc_nt.sr_stress},
        decision=sc_nt.decision, decision_reason=sc_nt.reason, revise_target=sc_nt.revise_target, lines=sc_nt.lines,
        citations=list(ctx.study.CIT[CITATIONS[t["strategy"]]]), results_file=ctx.bridge_run_id, results_md5="")


def write_card(path: Path, text: str) -> str:
    """5.5 step 8: open(path, "x"), so a card is never overwritten; LF only (OPS-12). Returns the md5 on disk."""
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Steps 16 and 17
# --------------------------------------------------------------------------- #
def _theta_text(theta: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in theta.items())


def check_parity(ctx: "R.RunContext") -> dict:
    """5.4.1 per column and cost level, and P0b; the hard failures as withheld reasons (G-01)."""
    t, failed, warnings, legs = ctx.table, [], [], []
    for (col, stress), leg in sorted(ctx.legs.items()):
        pnl = ctx.pnl_qg[:, col] if stress == 1 else ctx.pnl_stress_qg[:, col]
        x = leg_checks(leg, strategy=t["strategy"], theta=ctx.grid[col], closes=ctx.closes, rf=ctx.rf,
                       weights=ctx.weights[:, col], pnl=pnl, turnover=ctx.turnover_qg[:, col], cost_bps=t["cost_bps"])
        where = f"column {col} ({_theta_text(ctx.grid[col])}), {stress}x"
        if not x["P13"]["pass"]:                    # the leg's own ids first, so a C-06-only WITHHELD stays re-runnable
            failed += [f"{r} ({where})" for r in x["P13"]["reasons"]] or [f"P13: no rebuild ({where})"]
        failed += [f"{p}: {where}: {plain(x[p])}" for p in HARD if p in x and not x[p]["pass"]]
        warnings += [f"{p}: {where}: {plain(x[p])}" for p in WARNINGS if p in x and not x[p]["pass"]]
        legs.append(x)
    bench = p0b(t["strategy"], ctx.closes, ctx.study_pn.prices)
    failed += [] if bench["pass"] else [f"P0b: the benchmark differs from the study's expression: {bench}"]
    return {"bars": BARS, "owner_bars": OWNER_BARS, "legs": legs, "P0b": bench, "P11": None, "P12": None,
            "failed": failed, "warnings": warnings, "hard_pass": False}


def _walk_forwards(ctx: "R.RunContext", parity: dict):
    """wf_qg, then (when every leg is valid) wf_nt, P11 and P12; G-03 when walk_forward raises (QA-R2-2)."""
    dates, E = ctx.dates[1:], int(ctx.table["embargo"])
    try:
        wf_qg = validate.walk_forward(ctx.pnl_qg, dates, turnover=ctx.turnover_qg, pnl_stress=ctx.pnl_stress_qg,
                                      embargo=E)
    except Exception as exc:                        # noqa: BLE001 - G-03
        return None, None, f"G-03: walk_forward raised {type(exc).__name__}: {exc}"
    if not all(x["P13"]["pass"] for x in parity["legs"]):
        return wf_qg, None, None
    wf_nt = select_matched(ctx.pnl_nt, ctx.pnl_stress_nt, ctx.turnover_nt, dates, wf_qg, embargo=E)
    parity["P12"] = p12(wf_qg, wf_nt)
    parity["failed"] += [f"P12: {k}: {plain(v)}" for k, v in parity["P12"].items() if not v["pass"]]
    try:
        own = validate.walk_forward(ctx.pnl_nt, dates, turnover=ctx.turnover_nt, pnl_stress=ctx.pnl_stress_nt,
                                    embargo=E)
    except Exception as exc:                        # noqa: BLE001 - G-03 in parity (P11)
        return wf_qg, wf_nt, f"G-03: walk_forward (P11, Nautilus's own selection) raised {type(exc).__name__}: {exc}"
    parity["P11"] = p11(wf_qg, own)
    return wf_qg, wf_nt, None


def _hook(ctx: "R.RunContext", n: int) -> None:
    fn = ctx.hooks.get(f"after_step{n}")
    if fn is not None:
        fn(ctx)


def _score(ctx: "R.RunContext", wf_qg, wf_nt, gate: dict) -> dict:
    """5.5 steps 2 to 4 on the rows of the ledger as registration left it; G-03 (scoring), G-05 (no snapshot)."""
    bench = ctx.closes[1:] / ctx.closes[:-1] - 1.0
    by_date = dict(zip(ctx.dates[1:], bench))
    b = np.array([by_date[d] for d in wf_qg.dates])
    try:
        rows = ctx.ledger.snapshot(ctx.hash_after_registration)
    except gate_ledger.LedgerRefused as exc:
        return {"error": f"G-05: ledger moved after registration: {exc}"}
    counts = trial_counts(ctx.table, rows)
    domain = None if ctx.table["domain"] is None else {k: tuple(v) for k, v in ctx.table["domain"].items()}
    kw = {"grid": ctx.grid, "n_trials": counts["n_trials"], "bench_daily": b, "seed": 11, "domain": domain}
    try:
        sc_qg = ctx.score_fn(wf_qg, full_pnl=ctx.pnl_qg, **kw)
        sc_nt = ctx.score_fn(wf_nt, full_pnl=ctx.pnl_nt, **kw)
    except Exception as exc:                        # noqa: BLE001 - G-03 in scoring
        return {"error": f"G-03: score_strategy raised {type(exc).__name__}: {exc}", "trial_counts": counts}
    return {"trial_counts": counts, "sc_qg": sc_qg, "sc_nt": sc_nt,
            "quantgen": {"decision": sc_qg.decision, "reason": sc_qg.reason, "revise_target": sc_qg.revise_target,
                         "predicates": gate_predicates(sc_qg, gate),
                         "stats": {k: v for k, v in asdict(sc_qg).items() if k != "lines"}},
            "nautilus": {"decision": sc_nt.decision, "reason": sc_nt.reason, "revise_target": sc_nt.revise_target,
                         "predicates": gate_predicates(sc_nt, gate),
                         "stats": {k: v for k, v in asdict(sc_nt).items() if k != "lines"}}}


def _mismatch_text(gate_rec: dict) -> str:
    q, n = gate_rec["quantgen"], gate_rec["nautilus"]
    diff = [f"{k} {q['predicates'][k]}/{n['predicates'][k]}" for k in q["predicates"]
            if q["predicates"][k] != n["predicates"][k]]
    return f"quantgen {q['decision']}, nautilus {n['decision']}; predicates differ: {', '.join(diff) or 'none'}"


def _reference(ctx: "R.RunContext", sc_qg, wf_qg) -> dict:
    """G-08 whenever the table names a reference card: the drift list and both year counts."""
    t = ctx.table
    path = Path(t["reference_card"]) if os.path.isabs(t["reference_card"]) else ctx.repo_root / t["reference_card"]
    raw = path.read_bytes()
    drift = [] if hashlib.md5(raw).hexdigest() == t["reference_card_md5"] else ["reference_card_md5"]
    drift += reference_drift(sc_qg, wf_qg, ctx.grid, json.loads(raw.decode("utf-8"))["stats"])
    return {"card": t["reference_card"], "drift": drift, "n_years_calendar": len({d[:4] for d in wf_qg.dates}),
            "n_years_whole": sc_qg.n_years}


def _print_summary(rec: dict, reasons: Sequence[str]) -> None:
    """Printed before Task 4's STATUS line (5.4.1, 5.5 step 3): the worst P2 and P3 next to the corrected and the
    owner's bars, the trial counts, both decisions and every reason the run ends without a card."""
    p, g = rec["parity"], rec["gate"]
    legs = [x for x in p["legs"] if x["P13"]["pass"]]
    worst_corr = min((x["P2"]["value"] for x in legs), default=None)
    worst_dsr = max((x["P3"]["value"] for x in legs), default=None)
    print(f"parity: hard_pass {p['hard_pass']}; worst corr {worst_corr} (bar {BARS['P2']}, owner {OWNER_BARS['P2']}); "
          f"worst abs dSR {worst_dsr} (bar {BARS['P3']}, owner {OWNER_BARS['P3']})")
    if g["trial_counts"] is not None:
        print("trial counts: " + ", ".join(f"{k} {g['trial_counts'][k]}"
                                           for k in ("len_grid", "family_n_raw", "market_n_raw", "U", "n_trials")))
    print(f"decisions: quantgen {(g['quantgen'] or {}).get('decision')}, "
          f"nautilus {(g['nautilus'] or {}).get('decision')}")
    for r in reasons:
        print(f"reason: {r}")


def hand_off(ctx: "R.RunContext") -> "R.Outcome":
    """Steps 16 and 17 (5.4, 5.5): parity, selection, both scores, agreement, reference, GATE, ledger, card."""
    rec, gate = ctx.record, ctx.gate_snapshot
    parity = rec["parity"] = check_parity(ctx)
    rec["provenance"]["p0b"] = parity["P0b"]
    wf_qg, wf_nt, wf_error = _walk_forwards(ctx, parity)
    parity["hard_pass"] = not parity["failed"] and wf_error is None and parity["P12"] is not None
    rec["gate"] = {"trial_counts": None, "quantgen": None, "nautilus": None, "agree": None, "reference": None,
                   "selection": None if wf_qg is None else {"origins": wf_qg.origins, "chosen": wf_qg.chosen,
                                                            "note": wf_qg.note}, "error": wf_error}
    reasons = list(parity["failed"]) + ([wf_error] if wf_error else [])
    scored = _score(ctx, wf_qg, wf_nt, gate) if parity["hard_pass"] else {}
    rec["gate"].update({k: v for k, v in scored.items() if k in ("trial_counts", "quantgen", "nautilus")})
    if "error" in scored:
        rec["gate"]["error"] = scored["error"]
        reasons.append(scored["error"])
    rec["parity"], rec["gate"] = plain(parity), plain(rec["gate"])
    _hook(ctx, 16)
    card_ok = False
    if "sc_qg" in scored:
        ok, why = agree(scored["sc_qg"], scored["sc_nt"], gate)
        rec["gate"]["agree"] = {"ok": ok, "reason": why}
        detail = f": {_mismatch_text(rec['gate'])}" if why == "decision mismatch" else ""
        reasons += [] if ok else [f"G-02: {why}{detail}"]
        if ctx.table["reference_card"] is not None:
            ref = rec["gate"]["reference"] = plain(_reference(ctx, scored["sc_qg"], wf_qg))
            reasons += [f"G-08: reference drift: {', '.join(ref['drift'])}"] if ref["drift"] else []
        card_ok = True
    if validate.GATE != gate:                       # G-04 (5.5 step 6), checked after every run
        diff = sorted(k for k in set(gate) | set(validate.GATE) if gate.get(k) != validate.GATE.get(k))
        rec["error"] = {"message": f"G-04: GATE differs from its snapshot after scoring: {diff}", "traceback": ""}
        _hook(ctx, 17)
        _print_summary(rec, reasons + [rec["error"]["message"]])
        return R.Outcome("ERROR", 4, reasons + [rec["error"]["message"]])
    if card_ok:
        try:
            stored = gate_ledger.assert_hash_at_run(ctx.ledger, ctx.hash_after_registration)
        except gate_ledger.LedgerRefused as exc:
            stored, reasons = None, reasons + [f"G-05: ledger moved after registration: {exc}"]
    if card_ok and not reasons:
        card = build_card(ctx, wf_nt, scored["sc_qg"], scored["sc_nt"], scored["trial_counts"], stored)
        path = ctx.run_dir / f"{card.card_id}.json"
        rec["card"] = {"path": str(path), "md5": write_card(path, card.to_json())}
    _hook(ctx, 17)
    _print_summary(rec, reasons)
    if rec["card"] is not None:
        return R.Outcome("CARD_WRITTEN", 0, [])
    return R.Outcome("WITHHELD", 1, reasons)
