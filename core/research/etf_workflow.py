"""Shared existing etf workflow; no GUI widgets or replacement models."""
from __future__ import annotations
import math
from pathlib import Path
from typing import Optional
import numpy as np
import config
from core.ficc.common import BP
from core.ficc.equity_deriv import letf_drag, letf_drag_scenario
from core.quant import strategies as S
from core.quant.history import HistoryError, load_history, synthetic_history
from core.quant.validate import load_cards
from .decay_disclosure import decay_text
from .letf_disclosure import letf_context, letf_text, letf_unavailable_text
from .sleeve_disclosure import conventions_text, sharpe_note, sharpe_text, sleeve_conventions, sleeve_summary
from core.ficc.letf_assumptions import resolve_letf_assumptions
ROOT = Path(__file__).resolve().parents[2]

LETF = {"122630": (2.0, "KODEX 레버리지", 0.0064), "252670": (-2.0, "KODEX 200선물인버스2X", 0.0064),
        "114800": (-1.0, "KODEX 인버스", 0.0064), "233740": (2.0, "KODEX 코스닥150레버리지", 0.0064),
        "251340": (-1.0, "KODEX 코스닥150선물인버스", 0.0064)}

LETF_INDEX = {"122630": "KOSPI200", "252670": "KOSPI200", "114800": "KOSPI200",
              "233740": "KOSDAQ150", "251340": "KOSDAQ150"}

_CARD_FOR = {"trend": ("S_E1_trend_krx", "S_E1_trend_us"), "vol": ("S_E2_voltarget_kodex200", "S_E2_voltarget_spy")}

# Sleeve rule parameters, named once: the same values go to the strategy functions and to the
# conventions record the screens disclose (§10 NEW-M6-05).
SLEEVE_TREND_LOOKBACK = 210     # sessions in the 10-month SMA; the trend switch first decides at this row
SLEEVE_VOL_WINDOW = 22          # realised-vol window; the vol target first decides at row window + 1
SLEEVE_CASH_RATE = 0.03         # fixed annual cash rate, an assumption (not an observed rate)

def _clean(code: str) -> str:
    c = (code or "").strip().upper()
    return c.split(".")[0] if c.endswith((".KS", ".KQ")) else c

def analyze(code: str, *, days: int = 504, source: str = "auto", card_loader=None, history_loader=None,
            letf_funding_rate=None, letf_annual_fee=None, letf_benchmark="zero_rate_reference",
            letf_dividend_yield=None) -> dict:
    # Validate before provider/history access, not inside the model fallback.
    assumptions = resolve_letf_assumptions(funding_rate=letf_funding_rate, annual_fee=letf_annual_fee,
                                          benchmark=letf_benchmark, dividend_yield=letf_dividend_yield)
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
                                "adf_p": S.adf_pvalue(prem), "half_life": S.half_life(prem), "decay": S.ar1_decay(prem),
                                "abs_mean": float(np.abs(prem).mean())}
    # sleeve rules on the fund's own history, with a costed summary
    if px.size > 300:
        lookback, window, rf = SLEEVE_TREND_LOOKBACK, SLEEVE_VOL_WINDOW, SLEEVE_CASH_RATE / 252
        W_t = S.trend_switch(px[:, None], rule="sma", lookback=lookback, step=21, cash_rate_daily=rf)
        W_v = S.vol_target(px[:, None], target=0.12, window=window, step=21)
        cost = 3.0 if out["is_krx"] else 50.0
        pt, _ = S.simulate(px[:, None], W_t, cost_bps=cost, cash_daily=rf)
        pv, _ = S.simulate(px[:, None], W_v, cost_bps=cost, cash_daily=rf)
        bh = px[1:] / px[:-1] - 1.0
        # S.summary's numbers unchanged; a Sharpe that is 0/0 (P&L without variation) is None (§10 NEW-M6-04).
        out["sleeves"] = {"trend": sleeve_summary(pt), "vol_target": sleeve_summary(pv), "buy_hold": sleeve_summary(bh),
                          "equity_trend": S.equity_curve(pt), "equity_bh": S.equity_curve(bh), "cost_bps": cost,
                          "exposure_trend": float(W_t[lookback:].mean()) if px.size > lookback else float("nan"),
                          "conventions": sleeve_conventions(
                              window_sessions=int(pt.size), trend_lookback=lookback, vol_window=window,
                              cash_rate_annual=SLEEVE_CASH_RATE,
                              trend_card=_CARD_FOR["trend"][0 if out["is_krx"] else 1],
                              vol_target_card=_CARD_FOR["vol"][0 if out["is_krx"] else 1])}
    # leveraged-fund drag from the index's GARCH variance term structure
    c = _clean(code)
    if c in LETF:
        beta, name, fee = LETF[c]
        assumptions = resolve_letf_assumptions(funding_rate=letf_funding_rate, annual_fee=letf_annual_fee,
                                              benchmark=letf_benchmark, dividend_yield=letf_dividend_yield,
                                              reference_fee=fee)
        fee = assumptions["annual_fee"]
        index = LETF_INDEX[c]
        lt = {"beta": beta, "name": name, "fee": fee, "underlying_index": index,
              "index_code": None, "index_source": None, "index_mapping_source": None,
              "index_status": "UNAVAILABLE", "calculation_status": "NOT_RUN", "assumptions": assumptions}
        out["letf"] = lt
        try:
            if source == "synthetic":
                h = synthetic_history(index, days=600)
                r = h.log_returns()
                lt.update(index_source=f"SYNTHETIC {index} demo (not market data)", index_status="SYNTHETIC",
                          index_mapping_source="EXPLICIT_SYNTHETIC_DEMO")
            elif km is not None:
                from data.kis_markets import domestic_index_code
                index_code = domestic_index_code(index)
                lt.update(index_code=index_code, index_mapping_source=("KIS_IDXCODE_MASTER_EXACT_NAME"
                          if index == "KOSDAQ150" else "EXISTING_KIS_KOSPI200_MAPPING"))
                idx = km.index_daily(index_code, days=600)
                prices = np.asarray(idx.close, dtype=float)
                if (idx.symbol != f"INDEX:{index_code}" or idx.source != "KIS" or
                        prices.ndim != 1 or prices.size < 64 or not np.all(np.isfinite(prices)) or
                        np.any(prices <= 0) or len(idx.dates) != prices.size or
                        list(idx.dates) != sorted(set(idx.dates))):
                    raise ValueError("Invalid underlying-index history")
                r = np.diff(np.log(prices))
                lt.update(index_source=f"{index} (KIS; code={index_code})", index_status="AVAILABLE")
            else:
                raise HistoryError("No supported real underlying-index provider")
            from core.quant.garch import fit_garch, forecast_variance
            fit = fit_garch(r, dist="t", profile=False)
            def proxy(variances):
                reference = letf_drag(beta, variances, fee=LETF[c][2])
                if assumptions["mode"] == "ZERO_RATE_REFERENCE":
                    return {**reference, "funding_term": 0.0, "fee_term": reference["financing_term"],
                            "dividend_term": 0.0, "reference_drag_bp": reference["drag_bp"]}
                scenario = letf_drag_scenario(beta, variances, funding_rate=assumptions["funding_rate"],
                                              annual_fee=fee, benchmark=assumptions["benchmark"],
                                              dividend_yield=assumptions["dividend_yield"])
                return {**scenario, "reference_drag_bp": reference["drag_bp"]}
            rows = []
            for n in (21, 63, 252):
                d = proxy(forecast_variance(fit, n))
                rows.append({"sessions": n, "drag_bp": d["drag_bp"], "variance_bp": d["variance_term"] / BP,
                             "fee_bp": d["fee_term"] / BP, "funding_bp": d["funding_term"] / BP,
                             "dividend_bp": d["dividend_term"] / BP,
                             "reference_drag_bp": d["reference_drag_bp"]})
            # A variance-based formula proxy, not the study's observed realised-drag benchmark.
            last_q = proxy(np.full(63, float(np.var(r[-63:]))))
            lt.update(rows=rows, cond_vol=fit.cond_vol_last, uncond_vol=fit.uncond_vol, nu=fit.nu,
                      converged=fit.converged, calculation_status="COMPUTED",
                      last_quarter_drag_bp=last_q["drag_bp"], last_quarter_reference_drag_bp=last_q["reference_drag_bp"],
                      last_quarter_vol=float(np.sqrt(np.var(r[-63:]) * 252)))
        except Exception:
            # Do not expose provider exception URLs/credentials or create a demo fallback.
            lt["error"] = ("Required index history or exact code mapping unavailable; no substitute index used."
                           if lt["index_status"] == "UNAVAILABLE" else "Index model calculation failed.")
    # the study's verdict for the sleeve families
    cards = {c["card_id"]: c for c in (card_loader or load_cards)(ROOT / "docs" / "asset_expansion" / "cards")}
    pick = 0 if out["is_krx"] else 1
    out["verdicts"] = {fam: cards.get(ids[pick], {}).get("decision", "not run") for fam, ids in _CARD_FOR.items()}
    out["verdict_reasons"] = {fam: cards.get(ids[pick], {}).get("decision_reason", "") for fam, ids in _CARD_FOR.items()}
    if "letf" in out:
        lc = cards.get("M_E4_letf_drag", {})
        out["letf"]["verdict"] = lc.get("decision", "not run")
        out["letf"]["verdict_reason"] = (lc.get("lines") or [lc.get("decision_reason", "")])[0]
    if "rows" in out.get("letf", {}):
        out["letf"]["interpretation"] = letf_context(out["letf"])
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
                     f"today's reading sits {ps['z']:+.1f} standard deviations from that mean; ADF p = {ps['adf_p']:.3f}. "
                     + decay_text(ps.get('decay')))
    sl = a.get("sleeves")
    if sl:
        # §10 NEW-M6-04: an undefined Sharpe reads "n/a" and the note says why; NEW-M6-05: the conventions
        # follow the price basis. A defined Sharpe keeps its text, so valid inputs read as before plus that sentence.
        t, b, v = (sharpe_text(sl[k]) or "n/a" for k in ("trend", "buy_hold", "vol_target"))
        note = sharpe_note(sl)
        parts.append(f"On this fund's own history the 10-month trend switch earned Sharpe {t} "
                     f"(max drawdown {sl['trend']['max_drawdown']:.0%}, {sl['exposure_trend']:.0%} invested) against buy-and-hold "
                     f"{b} ({sl['buy_hold']['max_drawdown']:.0%}); the 12 % vol target earned "
                     f"{v}. " + (note + " " if note else "") + "These are in-sample descriptive numbers; the validation study's verdict "
                     f"for this family is trend: {a['verdicts']['trend']}, vol target: {a['verdicts']['vol']}. "
                     f"Price basis for these sleeve numbers: {a.get('sleeve_basis', a.get('data_source'))}."
                     + (" " + conventions_text(sl["conventions"]) if sl.get("conventions") else ""))
    lt = a.get("letf")
    if lt and "rows" in lt:
        r63 = next(r for r in lt["rows"] if r["sessions"] == 63)
        parts.append(f"{lt['name']} ({lt['beta']:+.0f}×): prior-quarter variance AZ proxy "
                     f"{lt['last_quarter_drag_bp']:+.0f} bp over 63 observations; GARCH variance proxy "
                     f"{r63['drag_bp']:+.0f} bp over 63 observations. " + letf_text(lt))
    elif lt:
        parts.append(letf_unavailable_text(lt))
    if a.get("data_source") == "SYNTHETIC":
        parts.append("The series is SYNTHETIC; nothing above is market data.")
    return " ".join(parts) or "No history could be loaded."

def payload(a: dict) -> dict:
    return {"code": a["code"], "data_source": a.get("data_source"), "sleeve_price_basis": a.get("sleeve_basis"),
            "quote": a.get("quote"),
            "premium_stats": a.get("premium_stats"), "letf": a.get("letf"),
            "sleeves": {k: v for k, v in (a.get("sleeves") or {}).items() if not k.startswith("equity")},
            "verdicts": a.get("verdicts"), "top_components": (a.get("components") or [])[:10]}
