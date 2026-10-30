"""Shared existing crypto workflow; no GUI widgets or replacement models."""
from __future__ import annotations
import math
import numpy as np
import config
from core.crypto import analytics as CA
from .decay_disclosure import decay_text

CRYPTO_DAYS = 365

def _synthetic() -> dict:
    rng = np.random.default_rng(6)
    n = 900
    ds = [str(np.datetime64("2024-04-01") + np.timedelta64(i, "D")) for i in range(n)]
    us = 60000 * np.exp(np.cumsum(rng.normal(0.0004, 0.03, n)))
    fx = 1380 + np.cumsum(rng.normal(0, 3, n))
    prem = np.zeros(n)
    for t in range(1, n):
        prem[t] = 0.92 * prem[t - 1] + rng.normal(0, 0.4)
    kr = us * fx * (1 + prem / 100)
    fund = rng.normal(0.0002, 0.0004, n)
    eth = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.04, n)))    # the same draw ETHUSDT had as the first major
    return {"dates": ds, "upbit": dict(zip(ds, kr)), "binance": dict(zip(ds, us)), "usdkrw": dict(zip(ds, fx)),
            "funding_daily": dict(zip(ds, fund)), "eth": dict(zip(ds, eth)),
            "volume": rng.random(n) * 100, "premium_index": {"premium_pct": 0.01, "last_funding_rate": 0.0001},
            "oi": [], "source": "SYNTHETIC"}

def _live(days: int) -> dict:
    from core.ficc.data import load_series
    from data.crypto.crypto_client import BinancePublic, UpbitPublic
    up = UpbitPublic().daily("KRW-BTC", days=days)
    bn = BinancePublic()
    btc = bn.daily("BTCUSDT", days=days)
    fund = bn.funding("BTCUSDT", days=min(days, 1500)).daily()
    fx = load_series("DEXKOUS", source="auto", days=days + 100)
    return {"dates": btc.dates, "upbit": dict(zip(up.dates, up.close)), "binance": dict(zip(btc.dates, btc.close)),
            "usdkrw": dict(zip(fx.dates, fx.values)), "usdkrw_source": fx.source, "funding_daily": fund,
            "eth": dict(zip(*(lambda c: (c.dates, c.close))(bn.daily("ETHUSDT", days=days)))),
            "volume": np.asarray(btc.quote_volume), "premium_index": bn.premium_index("BTCUSDT"),
            "oi": bn.open_interest_hist("BTCUSDT"), "source": "LIVE"}

def analyze(*, days: int = 730, source: str = "live", card_loader=None, include_balances=True) -> dict:
    d = _live(days) if source == "live" else _synthetic()
    out: dict = {"source": d["source"], "usdkrw_source": d.get("usdkrw_source", "synthetic")}
    out["kimchi"] = CA.kimchi_premium(d["upbit"], d["binance"], d["usdkrw"])
    try:
        out["funding"] = CA.funding_carry(d["funding_daily"], d["binance"])
    except ValueError as exc:
        out["funding"] = None; out["funding_error"] = str(exc)
    btc = np.array([d["binance"][k] for k in sorted(d["binance"])])
    out["ethbtc"] = CA.eth_btc_test(d["eth"], d["binance"])
    out["weekday"] = CA.weekday_table(sorted(d["binance"]), btc, np.asarray(d["volume"])[-btc.size:])
    from core.quant.garch import fit_garch
    r = np.diff(np.log(btc))[-730:]
    fit = fit_garch(r, dist="t", profile=False)
    out["garch"] = {"nu": fit.nu, "alpha": fit.alpha, "beta": fit.beta, "persistence": fit.persistence,
                    "half_life": fit.half_life, "cond_vol_365": fit.cond_vol_last / math.sqrt(252) * math.sqrt(CRYPTO_DAYS),
                    "uncond_vol_365": fit.uncond_vol / math.sqrt(252) * math.sqrt(CRYPTO_DAYS) if math.isfinite(fit.uncond_vol) else float("nan"),
                    "converged": fit.converged, "at_bound": list(fit.at_bound), "n": int(r.size)}
    out["premium_index"] = d["premium_index"]; out["oi"] = d["oi"]
    out["btc_dates"] = sorted(d["binance"]); out["btc"] = btc
    out["balances"] = None
    if include_balances and config.upbit_ready() and source == "live":
        try:
            from data.crypto.crypto_client import UpbitAccount, UpbitPublic
            bal = UpbitAccount().balances()
            tick = {t["market"]: t["price"] for t in UpbitPublic().ticker([f"KRW-{b['currency']}" for b in bal if b["currency"] != "KRW"])} if bal else {}
            for b in bal:
                b["krw_value"] = b["total"] if b["currency"] == "KRW" else b["total"] * tick.get(f"KRW-{b['currency']}", 0.0)
            out["balances"] = bal
        except Exception as exc:
            out["balances_error"] = f"{type(exc).__name__}: {exc}"
    from core.quant.validate import load_cards
    from pathlib import Path
    cards = {c["card_id"]: c for c in (card_loader or load_cards)(Path(__file__).resolve().parents[2] / "docs" / "asset_expansion" / "cards")}
    out["verdicts"] = {k: cards.get(k, {}).get("decision", "not run") for k in
                       ("M_C1_kimchi", "M_C4_funding", "S_C3_crypto_trend_btcusd", "S_C3_crypto_trend_krwbtc",
                        "D_C2_garch_btc", "D_C2_skewt_btc", "M_C8_ethbtc")}
    return out

def narrative(a: dict) -> str:
    kp, fc, g = a["kimchi"], a["funding"], a["garch"]
    parts = [
        f"Korea pays {kp.last_pct:+.2f} % against the world price for bitcoin ({kp.last_z:+.1f} standard deviations from its one-year mean; "
        f"average {kp.mean_pct:+.2f} %, peak {kp.max_pct:.1f} % since {kp.dates[0]}); {decay_text(getattr(kp, "decay", None))} "
        f"(ADF p = {kp.adf_p:.3f}). It is a signal, not a trade: remittance limits, the Travel Rule and the 2027 tax close the arbitrage"
        + (f", and its predictive slope on next-week returns is {kp.pred_slope:+.4f} (t {kp.pred_t:+.1f})." if math.isfinite(kp.pred_t) else "."),
    ]
    if fc:
        parts.append(f"Perpetual funding runs {fc.last_ann_pct:+.1f} % a year on the 7-day mean, the {fc.percentile:.0%} percentile since "
                     f"{fc.dates[0]} ({fc.flag}); after top-decile funding the next 30 days returned {fc.top_decile_fwd30:+.1%} against "
                     f"{fc.bottom_decile_fwd30:+.1%} after bottom-decile funding (bootstrap p {fc.bootstrap_p:.2f}).")
    parts.append(f"GARCH(1,1)-t on {g['n']} days of BTCUSDT: ν {g['nu']:.1f}, persistence {g['persistence']:.3f} "
                 f"(half-life {g['half_life']:.0f} days), conditional vol {g['cond_vol_365']:.0%} on a 365-day basis"
                 f"{'' if g['converged'] else '; the solver did not converge'}"
                 f"{'; at bound: ' + ', '.join(g['at_bound']) if g['at_bound'] else ''}. The validation study's verdict for this fan on "
                 f"Bitcoin is {a['verdicts']['D_C2_garch_btc']}.")
    parts.append(f"ln(ETH/BTC): {a['ethbtc']['verdict']} (ADF p {a['ethbtc']['adf_p']:.3f}). {decay_text(a['ethbtc'].get('decay'))}")
    if a["source"] == "SYNTHETIC":
        parts.append("All series are SYNTHETIC.")
    return " ".join(parts)

def payload(a: dict) -> dict:
    """Market commentary only. Holdings stay in the local read-only display."""
    kp, fc = a["kimchi"], a["funding"]
    return {"source": a["source"], "kimchi": {"last_pct": kp.last_pct, "z": kp.last_z, "mean_pct": kp.mean_pct, "max_pct": kp.max_pct,
                                              "half_life_days": kp.half_life_days, "decay": getattr(kp, "decay", None), "adf_p": kp.adf_p, "pred_t": kp.pred_t, "n": kp.n},
            "funding": ({"last_ann_pct": fc.last_ann_pct, "percentile": fc.percentile, "flag": fc.flag, "top_decile_fwd30": fc.top_decile_fwd30,
                         "bottom_decile_fwd30": fc.bottom_decile_fwd30, "bootstrap_p": fc.bootstrap_p} if fc else None),
            "premium_index": a["premium_index"],
            "garch": a["garch"], "ethbtc": a["ethbtc"], "weekday": a["weekday"], "verdicts": a["verdicts"]}
