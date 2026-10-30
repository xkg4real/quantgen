"""Shared existing etf workflow; no GUI widgets or replacement models."""
from __future__ import annotations
import math
from pathlib import Path
from typing import Optional
import numpy as np
import config
from core.ficc.common import BP
from core.ficc.equity_deriv import letf_drag
from core.quant import strategies as S
from core.quant.history import HistoryError, load_history, synthetic_history
from core.quant.validate import load_cards
ROOT = Path(__file__).resolve().parents[2]

LETF = {"122630": (2.0, "KODEX 레버리지", 0.0064), "252670": (-2.0, "KODEX 200선물인버스2X", 0.0064),
        "114800": (-1.0, "KODEX 인버스", 0.0064), "233740": (2.0, "KODEX 코스닥150레버리지", 0.0064),
        "251340": (-1.0, "KODEX 코스닥150선물인버스", 0.0064)}

_CARD_FOR = {"trend": ("S_E1_trend_krx", "S_E1_trend_us"), "vol": ("S_E2_voltarget_kodex200", "S_E2_voltarget_spy")}

def _clean(code: str) -> str:
    c = (code or "").strip().upper()
    return c.split(".")[0] if c.endswith((".KS", ".KQ")) else c

def analyze(code: str, *, days: int = 504, source: str = "auto", card_loader=None, history_loader=None) -> dict:
    history_loader = history_loader or load_history
    out: dict = {"code": code, "source": source, "is_krx": _clean(code).isdigit() and len(_clean(code)) == 6}
    km = None
    if out["is_krx"] and source in ("auto", "kis") and config.kis_ready():
        from data.kis_markets import KISMarkets
        km = KISMarkets()
        q = km.etf_quote(_clean(code))
        nav = km.etf_nav_daily(_clean(code), days=days)
        comps = km.etf_components(_clean(code))
        out.update(quote=q, dates=nav.dates, price=np.asarray(nav.close), nav=np.asarray(nav.extra["nav"]),
                   premium_pct=np.asarray(nav.extra["premium_pct"]), components=comps, data_source="KIS")
    else:
        h = history_loader(code, source=("synthetic" if source == "synthetic" else source), days=days)
        out.update(quote=None, dates=h.dates, price=h.prices(), nav=None, premium_pct=None, components=[],
                   data_source=h.source, note=h.note)
    px, out["sleeve_dates"], out["sleeve_basis"] = out["price"], out["dates"], out.get("note") or out["data_source"]
    if km is not None:
        # The NAV series carries the raw close — it has to, the premium is raw price against raw NAV — so an
        # ETF split or consolidation would read as a one-day crash in the sleeve statistics. Those run on
        # KIS 수정주가 (split-adjusted) instead; the premium chart above keeps the raw pair.
        try:
            adj = history_loader(_clean(code), source="kis", days=days)
            px, out["sleeve_dates"], out["sleeve_basis"] = adj.prices(), adj.dates, adj.note
        except Exception as exc:
            # Quote, premium and basket are already in hand (a fund listed for
            # under 30 sessions lands here). Losing the adjusted series must
            # not lose them: keep the raw close and say so.
            out["sleeve_basis"] = f"raw NAV-series close, NOT split-adjusted (KIS 수정주가 unavailable: {exc})"
    if out.get("premium_pct") is not None and out["premium_pct"].size > 60:
        prem = out["premium_pct"]
        out["premium_stats"] = {"last": float(prem[-1]), "mean": float(prem.mean()), "sd": float(prem.std(ddof=1)),
                                "z": float((prem[-1] - prem.mean()) / prem.std(ddof=1)) if prem.std(ddof=1) > 0 else 0.0,
                                "adf_p": S.adf_pvalue(prem), "half_life": S.half_life(prem),
                                "abs_mean": float(np.abs(prem).mean())}
    # sleeve rules on the fund's own history, with a costed summary
    if px.size > 300:
        rf = 0.03 / 252
        W_t = S.trend_switch(px[:, None], rule="sma", lookback=210, step=21, cash_rate_daily=rf)
        W_v = S.vol_target(px[:, None], target=0.12, window=22, step=21)
        cost = 3.0 if out["is_krx"] else 50.0
        pt, _ = S.simulate(px[:, None], W_t, cost_bps=cost, cash_daily=rf)
        pv, _ = S.simulate(px[:, None], W_v, cost_bps=cost, cash_daily=rf)
        bh = px[1:] / px[:-1] - 1.0
        out["sleeves"] = {"trend": S.summary(pt), "vol_target": S.summary(pv), "buy_hold": S.summary(bh),
                          "equity_trend": S.equity_curve(pt), "equity_bh": S.equity_curve(bh), "cost_bps": cost,
                          "exposure_trend": float(W_t[210:].mean()) if px.size > 210 else float("nan")}
    # leveraged-fund drag from the index's GARCH variance term structure
    c = _clean(code)
    if c in LETF:
        beta, name, fee = LETF[c]
        try:
            if km is not None:
                idx = km.index_daily("2001", days=600)
                r = np.diff(np.log(np.asarray(idx.close)))
                src = "KOSPI200 (KIS)"
            else:
                h = synthetic_history("KOSPI200", days=600)
                r = h.log_returns()
                src = "synthetic index"
            from core.quant.garch import fit_garch, forecast_variance
            fit = fit_garch(r, dist="t", profile=False)
            rows = []
            for n in (21, 63, 252):
                d = letf_drag(beta, forecast_variance(fit, n), fee=fee)
                rows.append({"sessions": n, "drag_bp": d["drag_bp"], "variance_bp": d["variance_term"] / BP,
                             "fee_bp": d["financing_term"] / BP})
            # the study (M_E4_letf_drag) found the last quarter's realised variance the better quarterly
            # reference (MAE 91 bp against 136 bp for the GARCH path): both are shown, the realised one first
            last_q = letf_drag(beta, np.full(63, float(np.var(r[-63:]))), fee=fee)
            out["letf"] = {"beta": beta, "name": name, "fee": fee, "rows": rows, "cond_vol": fit.cond_vol_last,
                           "uncond_vol": fit.uncond_vol, "nu": fit.nu, "index_source": src, "converged": fit.converged,
                           "last_quarter_drag_bp": last_q["drag_bp"], "last_quarter_vol": float(np.sqrt(np.var(r[-63:]) * 252))}
        except Exception as exc:
            out["letf"] = {"beta": beta, "name": name, "error": f"{type(exc).__name__}: {exc}"}
    # the study's verdict for the sleeve families
    cards = {c["card_id"]: c for c in (card_loader or load_cards)(ROOT / "docs" / "asset_expansion" / "cards")}
    pick = 0 if out["is_krx"] else 1
    out["verdicts"] = {fam: cards.get(ids[pick], {}).get("decision", "not run") for fam, ids in _CARD_FOR.items()}
    out["verdict_reasons"] = {fam: cards.get(ids[pick], {}).get("decision_reason", "") for fam, ids in _CARD_FOR.items()}
    if "letf" in out:
        lc = cards.get("M_E4_letf_drag", {})
        out["letf"]["verdict"] = lc.get("decision", "not run")
        out["letf"]["verdict_reason"] = (lc.get("lines") or [lc.get("decision_reason", "")])[0]
    return out

def narrative(a: dict) -> str:
    parts = []
    q = a.get("quote")
    if q:
        parts.append(f"{a['code']} trades at {q['price']:,.0f} against an NAV of {q['nav']:,.2f}, a premium of "
                     f"{q['premium_pct']:+.2f} % with tracking error {q['tracking_error_pct']:.2f} %, "
                     f"{q['cu_units']:,.0f} shares per creation unit and LPs holding {q['lp_holding_pct']:.1f} %.")
    ps = a.get("premium_stats")
    if ps:
        parts.append(f"Over {len(a['dates'])} sessions the premium averaged {ps['mean']:+.2f} % (|premium| {ps['abs_mean']:.2f} %), "
                     f"today's reading sits {ps['z']:+.1f} standard deviations from that mean; ADF p = {ps['adf_p']:.3f} and "
                     f"the half-life is {ps['half_life']:.0f} sessions, so " +
                     ("a discount reverts within days, which is why the flagship trackers carry no tradeable premium after a 4–5 bp round trip."
                      if ps["half_life"] < 5 else "the deviation is slow-moving enough to matter for entry timing."))
    sl = a.get("sleeves")
    if sl:
        parts.append(f"On this fund's own history the 10-month trend switch earned Sharpe {sl['trend']['sharpe']:.2f} "
                     f"(max drawdown {sl['trend']['max_drawdown']:.0%}, {sl['exposure_trend']:.0%} invested) against buy-and-hold "
                     f"{sl['buy_hold']['sharpe']:.2f} ({sl['buy_hold']['max_drawdown']:.0%}); the 12 % vol target earned "
                     f"{sl['vol_target']['sharpe']:.2f}. These are in-sample descriptive numbers; the validation study's verdict "
                     f"for this family is trend: {a['verdicts']['trend']}, vol target: {a['verdicts']['vol']}. "
                     f"Price basis for these sleeve numbers: {a.get('sleeve_basis', a.get('data_source'))}.")
    lt = a.get("letf")
    if lt and "rows" in lt:
        r63 = next(r for r in lt["rows"] if r["sessions"] == 63)
        parts.append(f"{lt['name']} is a {lt['beta']:+.0f}× fund: at the last quarter's realised vol ({lt['last_quarter_vol']:.1%}) the "
                     f"Avellaneda–Zhang drag versus {lt['beta']:+.0f}× the index is {lt['last_quarter_drag_bp']:+.0f} bp a quarter; the "
                     f"GARCH-t variance term structure (conditional vol {lt['cond_vol']:.1%}, ν {lt['nu']:.1f}) puts it at "
                     f"{r63['drag_bp']:+.0f} bp ({r63['variance_bp']:+.0f} bp from variance, {r63['fee_bp']:+.0f} bp from the fee), "
                     f"{next(r for r in lt['rows'] if r['sessions'] == 252)['drag_bp']:+.0f} bp over a year: the price of daily rebalancing. "
                     f"The validation study's verdict on the GARCH forecast is {lt.get('verdict', 'not run')}: the realised last quarter "
                     f"is the better guide, which is why it is quoted first.")
    if a.get("data_source") == "SYNTHETIC":
        parts.append("The series is SYNTHETIC; nothing above is market data.")
    return " ".join(parts) or "No history could be loaded."

def payload(a: dict) -> dict:
    return {"code": a["code"], "data_source": a.get("data_source"), "sleeve_price_basis": a.get("sleeve_basis"),
            "quote": a.get("quote"),
            "premium_stats": a.get("premium_stats"), "letf": a.get("letf"),
            "sleeves": {k: v for k, v in (a.get("sleeves") or {}).items() if not k.startswith("equity")},
            "verdicts": a.get("verdicts"), "top_components": (a.get("components") or [])[:10]}
