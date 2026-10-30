"""Existing Strategy Lab workflow shared by Flet and native Qt.

Preserves existing grid-based trial scoring and registration semantics. The
separate run-registry redesign is not implemented by this UI extraction.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import numpy as np
from core.quant import strategies as S
from core.quant import validate as V
from core.quant.history import convention_warning, load_history
ROOT = Path(__file__).resolve().parents[2]
CARDS_DIR = ROOT / "docs" / "asset_expansion" / "cards"

FAMILIES = {
    "trend_switch": ("Trend switch (Faber SMA / MOP sign)", S.trend_switch,
                     S.grid_from(rule=["sma", "tsmom"], lookback=[126, 210, 252], step=[21, 42]), 21),
    "vol_target": ("Capped volatility target", S.vol_target, S.grid_from(target=[0.08, 0.10, 0.12, 0.15], window=[22, 44], step=[21]), 21),
    "xs_momentum": ("Cross-sectional momentum (long top third)", S.xs_momentum,
                    S.grid_from(lookback=[126, 189, 252], skip=[5, 21], top=[1 / 3], step=[21, 42], long_only=[True]), 21),
    "tsmom": ("Time-series momentum (MOP, long/short)", S.tsmom,
              S.grid_from(lookback=[63, 126, 252], vol_target_ann=[0.20, 0.40], cap=[1.0], step=[21, 42], long_only=[False]), 21),
    "crypto_trend": ("Crypto short-horizon trend (long/flat)", S.crypto_trend, S.grid_from(hysteresis=[0.05, 0.1, 0.2, 0.3, 0.4, 0.5]), 1),
    "risk_parity": ("Risk parity across sleeves", S.risk_parity, S.grid_from(window=[125, 250, 500, 750], step=[21, 63]), 63),
    "pairs": ("Pairs (Engle–Granger spread, y then x)", None,
              S.grid_from(formation=[126, 252], trading=[126], entry=[1.5, 2.0, 2.5, 3.0], exit=[0.0], long_only=[False]), 5),
}

FAMILY_ID = {"trend_switch": "E1", "vol_target": "E2", "risk_parity": "E3", "xs_momentum": "E5", "pairs": "E8",
             "crypto_trend": "C3", "tsmom": "B3"}

_MARKET = {"krx_etf": "KR", "krx_stock": "KR", "us": "US", "crypto": "CRYPTO", "fx": "FX", "futures": "FUTURES"}

def register_trials(family: str, symbols: list[str], grid: list[dict], cost_bps: float, dates, sources,
                    *, ledger_dir=None) -> Optional[int]:
    """Every configuration of a real-data Lab run is a trial of its card family in QUANTGEN's ledger, so a
    later card counts what was tried here. Synthetic runs are toys and register nothing. Returns the family's
    configuration count, or None."""
    if "SYNTHETIC" in sources:
        return None
    import json
    from datetime import datetime, timezone
    import config as QC
    from core.quant import gate_ledger as GL

    ledger = GL.family_ledger(FAMILY_ID[family], Path(ledger_dir) if ledger_dir else QC.macro_dir() / "ledgers")
    symbols = [s.strip().upper() for s in symbols]
    if family != "pairs":                     # pairs keep y-then-x order; elsewhere order is not a configuration
        symbols = sorted(symbols)
    markets = {_MARKET.get(V.cost_class(s) or "", "OTHER") for s in symbols}
    market = next(iter(markets)) if len(markets) == 1 else "MULTI"
    for theta in grid:
        GL.register_trial(ledger, dict(
            rule=FAMILY_ID[family], params=json.loads(json.dumps(dict(theta, symbols=list(symbols), cost_bps=cost_bps),
                                                                 default=str)),
            timing_class="COMPLIANT", span=[str(dates[0])[:10], str(dates[-1])[:10]],
            market=market,
            run_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), phase="research",
            run_kind="variant", run_utc_anchor=GL.repo_anchor(), source="Strategy Lab: " + ", ".join(sources)),
            script="ui/strategy_lab_page.py")
    return ledger.n_raw

def run_family(family: str, symbols: list[str], *, source: str = "auto", cost_bps: Optional[float] = None,
               days: int = 5000, bootstrap_B: int = 1000, history_loader=None, trial_registrar=None) -> dict:
    """`cost_bps=None` charges QUANTGEN's table rate. A typed cost below it still runs, as a cost sensitivity, but
    the PASS / REJECT verdict is withheld: the gate never lowers the cost assumption (validate.py)."""
    label, fn, grid, embargo = FAMILIES[family]
    if not symbols:
        raise ValueError("No symbols given.")
    floor, classes = V.cost_floor_bp(symbols)
    uncosted = [s for s, c in classes.items() if c is None]
    if cost_bps is None:
        if floor is None:
            raise ValueError(f"QUANTGEN has no cost row for {', '.join(uncosted)}; type a cost to run a sensitivity")
        cost_bps = floor
    withheld = ("" if floor is not None and cost_bps >= floor else
                f"No PASS / REJECT: QUANTGEN has no cost row for {', '.join(uncosted)}, so this run is a cost "
                f"sensitivity, not a gate verdict." if floor is None else
                f"No PASS / REJECT: {cost_bps:g} bp per side is below QUANTGEN's table rate for these symbols "
                f"({floor:g} bp; {', '.join(f'{s} {c}' for s, c in classes.items())}), so this run is a cost "
                f"sensitivity, not a gate verdict.")
    hists = [(history_loader or load_history)(s, source=source, days=days) for s in symbols]
    pn = S.align_panel(hists)
    if family == "pairs":
        if pn.prices.shape[1] != 2:
            raise ValueError("pairs needs exactly two symbols: y then x")
        def fn(prices, **theta):
            W, _ = S.pairs(prices, **theta)
            return W
        fn.__name__ = "pairs"
    rf = 0.03 / 252
    M, Ms, Tv = S.pnl_matrix(pn.prices, fn, grid, cost_bps=cost_bps, cash_daily=rf)
    dates = pn.dates[1:]
    wf = V.walk_forward(M, dates, turnover=Tv, pnl_stress=Ms, embargo=embargo)
    # a run that computes is a trial; registered before it is scored, so a broken ledger blocks the verdict
    ledger_n = (trial_registrar or register_trials)(family, [h.symbol for h in hists], grid, cost_bps, pn.dates, [h.source for h in hists])
    bench_all = (pn.prices[1:] / pn.prices[:-1] - 1.0).mean(axis=1) if family != "pairs" else None
    bench = None
    if bench_all is not None:
        bd = dict(zip(dates, bench_all))
        bench = np.array([bd[d] for d in wf.dates])
    saved_b = V.GATE["bootstrap_B"]
    V.GATE["bootstrap_B"] = bootstrap_B
    try:
        sc = V.score_strategy(wf, grid=grid, full_pnl=M, n_trials=len(grid), bench_daily=bench)
    finally:
        V.GATE["bootstrap_B"] = saved_b      # the gate is pre-registered: a Lab run must not leave it changed
    eq = S.equity_curve(wf.pnl)
    beq = S.equity_curve(bench) if bench is not None else None
    return {"family": family, "label": label, "symbols": [h.symbol for h in hists], "sources": [h.source for h in hists],
            "notes": [h.note for h in hists], "convention": convention_warning(hists),
            "panel": pn, "score": sc, "wf": wf, "equity": eq, "bench_equity": beq, "grid": grid,
            "chosen": grid[wf.chosen[-1]] if wf.chosen else {}, "cost_bps": cost_bps, "cost_floor": floor,
            "withheld": withheld, "ledger_n": ledger_n}

def narrative(r: dict) -> str:
    sc = r["score"]
    head = (f"{r['label']} on {', '.join(r['symbols'])} ({len(r['panel'])} shared sessions, {r['cost_bps']:.0f} bp per side, "
            f"{len(r['grid'])} configurations = {sc.n_trials} trials): "
            + (f"decision withheld — {r['withheld']} " if r.get("withheld") else f"decision {sc.decision} — {sc.reason}. ") +
            f"The last in-sample winner was {r['chosen']}.")
    return head + " " + " ".join(sc.lines)

def payload(r: dict) -> dict:
    sc = r["score"]
    hide = ("decision", "reason", "revise_target") if r.get("withheld") else ()   # no verdict leaks into analysis
    return {"family": r["family"], "symbols": r["symbols"], "sources": r["sources"], "cost_bps": r["cost_bps"], "grid_size": len(r["grid"]),
            "decision": "WITHHELD" if r.get("withheld") else sc.decision,
            "reason": r.get("withheld") or sc.reason, "revise_target": None if r.get("withheld") else sc.revise_target,
            "stats": {k: v for k, v in sc.__dict__.items() if isinstance(v, (int, float, str, bool, tuple)) and k not in hide},
            "regime": sc.regime, "lines": sc.lines, "walk_forward": r["wf"].note}

def _study_card(c: dict) -> dict:
    """A card with every key the page indexes, read with .get: a file of another shape (a v2 macro card, a header,
    a draft) shows as UNKNOWN instead of raising inside the page build."""
    def listed(k):
        v = c.get(k)
        return [str(x) for x in v] if isinstance(v, list) else []

    known = c.get("decision") in V.DECISIONS
    return {**c, "card_id": str(c.get("card_id") or "unnamed card"),
            "decision": c.get("decision") if known else "UNKNOWN",
            "kind": str(c.get("kind") or c.get("class") or "unknown"),
            "hypothesis": str(c.get("hypothesis") or c.get("claim") or ""),
            "decision_reason": str(c.get("decision_reason") or ("" if known else
                                   "not an asset-expansion study card (v2 macro cards: Macro → Model cards)")),
            "stats": {k: v for k, v in c["stats"].items() if isinstance(v, (int, float))} if isinstance(c.get("stats"), dict) else {},
            "tests": c.get("tests") if isinstance(c.get("tests"), dict) else {},
            "lines": listed("lines"), "citations": listed("citations")}

def load_cards() -> list[dict]:
    cards = [_study_card(c) for c in V.load_cards(CARDS_DIR) if isinstance(c, dict)]
    return sorted(cards, key=lambda c: ({"PASS": 0, "REVISE": 1, "REJECT": 2}.get(c["decision"], 3), c["card_id"]))
