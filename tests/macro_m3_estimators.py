"""M3 package B tests: estimator family, forecast-evaluation harness, B5 and the staged estimator gate
(core/quant/vol_estimators.py, core/quant/forecast_eval.py, docs/vol_backtest.py; TASK-M3-01..05).

Spec tests carried: T-EST-04 in full; the report-structure clause of T-EST-02; the synthetic and refusal clauses of
T-B5-01 (the sigma x 0.7 clause applied to the out-of-sample forecast only, brief F-16; the switch-refusal sentence
runs from M3, F-19); the SYNTH companions of T-EST-01 (MCS) and I-10 (fallback); the band arithmetic of G-B5-01..03.
Every numeric golden clause (T-B5-01 4.70%, T-EST-01 / I-10 DLB-T1a, T-EST-02 p-values, G-B5-01..04, G-EST-01..04,
G-US-01c, the G-POST-01 M3 row) raises NotRun("REFDATA: <fixture>") naming its fixture; G-B5-02 adds a labelled
SMOKE check on the local yf_SPY cache that is never asserted against the golden. Once ^KS11 (F13) is listed, T-B5-01
runs the B5 harness (docs/vol_backtest.spec_form) on it and asserts the SMA20 FHS line against goldens.csv (look-ahead
audit LA-02, part 2); that body is shown to PASS and to FAIL on invented closes.
Hermetic: synthetic series (seeds fixed), PIT stores in tempfile directories, no network, nothing under ~/.nextgen.
"""
from __future__ import annotations

import csv
import io
import json
import math
import tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from core.ficc import contracts as C
from core.ficc import macro_schema as S
from core.ficc import pit as P
from core.quant import forecast_eval as F
from core.quant import validate as V
from core.quant import vol_estimators as E
from core.quant.gjr import GJRFit, fit_gjr, simulate_gjr_series
from core.rules.macro_rules import MacroRefusal
from tests.golden_tools import assert_class, assert_close, assert_golden, golden, near_threshold, p_kind
from tests.notrun import NotRun, require_fixture

REG = C.load_registry()
FIT = dict(min_years=1, refit_every=42)        # synthetic series are short: 252-session first fit, refit every 42


def U(*a):
    return datetime(*a, tzinfo=timezone.utc)


def _raises(fn, exc=Exception, needle=""):
    try:
        fn()
    except exc as e:
        assert needle.lower() in str(e).lower(), f"{needle!r} not in {e}"
        return e
    raise AssertionError(f"expected {exc.__name__}")


def _gjr(n=700, seed=4):
    return simulate_gjr_series(2e-6, 0.03, 0.10, 0.90, 6.0, n=n, seed=seed)


def _ohlc(r, seed=1, *, equal_open_share=0.0, flat_share=0.0, window=252):
    """Synthetic regular-session bars around a close path; `equal_open_share` sets open == prior close on that
    share of the last `window` rows (KR flag), `flat_share` sets high == low (US flag)."""
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + r)
    prev = np.r_[np.nan, close[:-1]]
    opn = prev * np.exp(rng.normal(0, 0.002, r.size))
    opn[0] = close[0]
    hi = np.maximum(opn, close) * np.exp(np.abs(rng.normal(0, 0.004, r.size)))
    lo = np.minimum(opn, close) * np.exp(-np.abs(rng.normal(0, 0.004, r.size)))
    T = r.size
    k = int(round(equal_open_share * window))
    if k:
        idx = np.arange(T - window, T)[:k]
        opn[idx] = prev[idx]
        hi[idx], lo[idx] = np.maximum(hi[idx], opn[idx]), np.minimum(lo[idx], opn[idx])
    k = int(round(flat_share * window))
    if k:
        idx = np.arange(T - window, T)[:k]
        hi[idx] = lo[idx] = opn[idx] = close[idx]
    return E.OHLC(tuple(range(T)), opn, hi, lo, close)


# --------------------------------------------------------------------------- #
# Estimator definitions (brief D.3 items 1-4)
# --------------------------------------------------------------------------- #
def test_sma20_and_ewma_definitions():
    r = _gjr(300)
    s = E.sma(r, 21)
    assert not s.ok[:19].any() and s.ok[19:].all()
    for t in (19, 100, 299):
        assert math.isclose(s.var[t], 21 * np.var(r[t - 19:t + 1], ddof=1))
    # stale-carry exclusion: the window extends to the last 20 valid returns (L1561)
    valid = np.ones(r.size, bool)
    valid[290] = False
    s2 = E.sma(r, 1, valid=valid)
    want = np.var(np.r_[r[270:290], r[291:300]][-20:], ddof=1)
    assert math.isclose(s2.var[299], want) and math.isclose(s2.var[290], s2.var[289])
    # EWMA hand-computed (RiskMetrics recursion, zero mean, seeded with the sample variance of the first 20)
    for lam in (0.94, 0.97):
        e = E.ewma(r, 5, lam)
        s2v = np.var(r[:20], ddof=1)
        assert math.isclose(e.var[19], 5 * s2v) and not e.ok[:19].any()
        for t in range(20, 25):
            s2v = lam * s2v + (1 - lam) * r[t] ** 2
            assert math.isclose(e.var[t], 5 * s2v)
    assert E.ewma(r, 1, 0.94).name == "ewma094" and E.ewma(r, 1, 0.97).name == "ewma097"
    assert E.forecast("sma20", r, 1).name == "sma20" and E.forecast("ewma097", r, 1).name == "ewma097"
    _raises(lambda: E.forecast("sma60", r, 1), ValueError, "unknown estimator")
    assert E.COMPLEXITY_ORDER == ("sma20", "ewma094", "ewma097", "garch_t", "gjr_t", "log_har_range", "comb")


test_sma20_and_ewma_definitions.test_ids = []


def test_causality_no_lookahead():
    r = _gjr(520)
    ohlc = _ohlc(r)
    k = 420
    sub = E.OHLC(ohlc.dates[:k], ohlc.open[:k], ohlc.high[:k], ohlc.low[:k], ohlc.close[:k])
    for name in E.ESTIMATORS:
        full = E.forecast(name, r, 5, ohlc=ohlc, market="KR", **FIT)
        part = E.forecast(name, r[:k], 5, ohlc=sub, market="KR", **FIT)
        assert part.ok.any(), name
        np.testing.assert_allclose(full.var[:k], part.var, equal_nan=True, err_msg=name)
        assert (full.ok[:k] == part.ok).all(), name


test_causality_no_lookahead.test_ids = []


def test_range_proxy_and_quality_flag():
    o = E.OHLC(("d0", "d1"), np.array([100.0, 101.0]), np.array([103.0, 104.0]), np.array([99.0, 100.5]),
               np.array([102.0, 103.0]), prev_close=np.array([100.0, 102.0]))
    kr = E.range_proxy(o, "KR")
    hl, co, on = math.log(104 / 100.5), math.log(103 / 101), math.log(101 / 102)
    assert math.isclose(kr[1], on ** 2 + 0.5 * hl ** 2 - (2 * math.log(2) - 1) * co ** 2)
    assert math.isclose(kr[0], 0.5 * math.log(103 / 99) ** 2 - (2 * math.log(2) - 1) * math.log(102 / 100) ** 2)
    us = E.range_proxy(o, "US")
    assert math.isclose(us[1], hl ** 2 / (4 * math.log(2)))
    _raises(lambda: E.range_proxy(o, "JP"), ValueError, "no range proxy")
    assert o.open_equals_prior_close.tolist() == [True, False]
    # the flag trips at > 5% of the trailing window, not at exactly 5% (L3204)
    r = _gjr(400)
    w = 240
    at5 = _ohlc(r, equal_open_share=0.05, window=w)
    above = _ohlc(r, equal_open_share=13 / w, window=w)
    assert not E.range_quality_flag(at5, "KR", window_sessions=w)[-1]
    assert E.range_quality_flag(above, "KR", window_sessions=w)[-1]
    assert not E.range_quality_flag(_ohlc(r, flat_share=0.05, window=w), "US", window_sessions=w)[-1]
    assert E.range_quality_flag(_ohlc(r, flat_share=13 / w, window=w), "US", window_sessions=w)[-1]
    assert not E.range_quality_flag(above, "US", window_sessions=w)[-1]          # a KR-only defect never trips Parkinson


test_range_proxy_and_quality_flag.test_ids = []


def test_comb_is_half_sum_and_fails_when_either_leg_fails():
    r = _gjr(600)
    ohlc = _ohlc(r)
    g = E.gjr_t(r, 21, **FIT)
    har = E.log_har_range(r, ohlc, "KR", 21, **FIT)
    c = E.comb(r, ohlc, "KR", 21, **FIT)
    both = g.ok & har.ok
    assert both.sum() > 200 and (c.ok == both).all()
    np.testing.assert_allclose(c.var[both], 0.5 * (g.var[both] + har.var[both]))
    assert np.isnan(c.var[~both]).all()
    # a tripped KR open-quality flag fails the HAR leg at the last origins: COMB fails there too (no one-legged COMB)
    bad = _ohlc(r, equal_open_share=0.10)
    c2 = E.comb(r, bad, "KR", 21, **FIT)
    assert not c2.ok[-1] and c2.reason[-1] == "open_quality" and g.ok[-1]
    assert c2.ok[:300].sum() == both[:300].sum()                                  # the flag is trailing, earlier origins unchanged
    # the registry dispatch returns a typed null without OHLC
    m = E.forecast("comb", r, 21, **FIT)
    assert isinstance(m, P.MissingInput) and m.reason == "missing" and "OHLC" in m.detail
    assert isinstance(E.forecast("log_har_range", r, 21, ohlc=ohlc), P.MissingInput)      # market missing


test_comb_is_half_sum_and_fails_when_either_leg_fails.test_ids = []


# --------------------------------------------------------------------------- #
# T-EST-04 and the I-10 fallback clause (rule 7): bounds, non-convergence, nu, quality flags; no blend
# --------------------------------------------------------------------------- #
def test_t_est_04_fallback_to_sma20_no_blend():
    r = _gjr(600)
    ohlc = _ohlc(r)
    good = fit_gjr(r, dist="t")
    assert E.fit_ok(good) == (True, None)
    cases = {"persistence": replace(good, persistence=0.99995), "not_converged": replace(good, converged=False),
             "nu_150": replace(good, nu=150.0), "nu_inf": replace(good, nu=math.inf), "omega_0": replace(good, omega=0.0),
             "beta_neg": replace(good, beta=-0.01), "alpha_gamma": replace(good, alpha=0.0, gamma=-0.01)}
    for label, fit in cases.items():
        ok, why = E.fit_ok(fit)
        assert not ok and why and (why.startswith("gjr_bounds") or why == "gjr_not_converged"), (label, why)
    assert E.fit_ok(replace(good, alpha=0.5, beta=0.5))[1].startswith("gjr_bounds:persistence")
    sig_sma = math.sqrt(E.sma(r, 1).var[-1] * 252)
    log = []
    # a GJR fit with alpha + beta + gamma/2 > 0.9999 at this decision -> sigma from SMA20 exactly, logged
    bad_fit = lambda w: replace(fit_gjr(w, dist="t"), persistence=0.99995)                       # noqa: E731
    d = E.sigma_for_decision("comb", r, ohlc=ohlc, market="KR", log=log, fitter=bad_fit, **FIT)
    assert d.sigma_ann == sig_sma and d.fallback_used and d.status == "fallback_to_sma20"
    assert d.estimator_used == "sma20" and d.reason.startswith("gjr_bounds") and log[-1]["reason"] == d.reason
    # non-convergence
    d = E.sigma_for_decision("gjr_t", r, log=log, fitter=lambda w: replace(fit_gjr(w, dist="t"), converged=False), **FIT)
    assert d.sigma_ann == sig_sma and d.fallback_used and d.reason == "gjr_not_converged"
    # an effectively normal fit (nu > 100) is outside nu in (2, 100] (brief F-6)
    d = E.sigma_for_decision("gjr_t", r, fitter=lambda w: replace(fit_gjr(w, dist="t"), nu=150.0), **FIT)
    assert d.fallback_used and "nu" in d.reason
    # a tripped OHLC quality flag: KR open == prior close on 6% (15 rows) of the trailing 252; 12 rows (4.8%) do not
    # trip (the exact-5% boundary is asserted on a 240-session window in test_range_proxy_and_quality_flag)
    d = E.sigma_for_decision("comb", r, ohlc=_ohlc(r, equal_open_share=0.06), market="KR", log=log, **FIT)
    assert d.sigma_ann == sig_sma and d.fallback_used and d.reason == "open_quality" and d.status == "fallback_to_sma20"
    d5 = E.sigma_for_decision("comb", r, ohlc=_ohlc(r, equal_open_share=12 / 252), market="KR", **FIT)
    assert not d5.fallback_used and d5.status == "challenger_selected" and d5.estimator_used == "comb"
    assert d5.sigma_ann != sig_sma                                               # a challenger value, not a blend
    us = E.sigma_for_decision("log_har_range", r, ohlc=_ohlc(r, flat_share=0.06), market="US", **FIT)
    assert us.fallback_used and us.reason == "flat_range" and us.sigma_ann == sig_sma
    # the next decision with a good fit uses the challenger again: fallback is per decision
    again = E.sigma_for_decision("comb", r, ohlc=ohlc, market="KR", **FIT)
    assert again.status == "challenger_selected" and not again.fallback_used and again.estimator_used == "comb"
    comb_var = E.comb(r, ohlc, "KR", 21, **FIT).var[-1]
    assert math.isclose(again.sigma_ann, math.sqrt(comb_var / 21 * 252))
    # a failed refit never keeps the previous parameters (no stale challenger forecast, L3235)
    calls = {"n": 0}

    def flaky(w):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("solver blew up")
        return fit_gjr(w, dist="t")
    fc = E.gjr_t(r, 21, fitter=flaky, min_years=1, refit_every=100)
    first = int(np.flatnonzero(fc.ok)[0])
    assert fc.ok[first:first + 100].all() and not fc.ok[first + 100:first + 200].any()
    assert fc.reason[first + 100].startswith("error:") and fc.ok[first + 200:].all()
    # the OHLC input itself missing -> SMA20, logged (typed null, never a one-legged COMB)
    d = E.sigma_for_decision("comb", r, log=log, **FIT)
    assert d.fallback_used and d.reason.startswith("ohlc_missing") and d.sigma_ann == sig_sma
    # fewer than 20 valid returns: the M2 contract (insufficient_history), no value invented
    short = E.sigma_for_decision("sma20", r[:10])
    assert short.sigma_ann is None and short.status == "NOT_RUN" and short.reason == "insufficient_history"


test_t_est_04_fallback_to_sma20_no_blend.test_ids = ["T-EST-04", "I-10"]


# --------------------------------------------------------------------------- #
# Harness: MCS (T-EST-01 SYNTH companion), DM with HLN, B5 (T-B5-01 synthetic clauses), sized book
# --------------------------------------------------------------------------- #
def _garch_dgp(n, seed, omega=2e-6, alpha=0.08, beta=0.90, nu=6.0):
    rng = np.random.default_rng(seed)
    z = rng.standard_t(nu, size=n + 500) * math.sqrt((nu - 2) / nu)
    r, s2 = np.empty(n + 500), np.empty(n + 500)
    v = omega / (1 - alpha - beta)
    for t in range(n + 500):
        s2[t] = v
        r[t] = math.sqrt(v) * z[t]
        v = omega + alpha * r[t] ** 2 + beta * v
    return r[500:], s2[500:], v


def test_t_est_01_mcs_synthetic_companion():
    r, s2, _ = _garch_dgp(1500, 11)
    y = F.realised_target(r, 1)
    true = np.r_[s2[1:], np.nan]                      # the DGP's own next-day variance, known at t
    bad = 0.4 * true
    sma = E.sma(r, 1).var
    mask = np.isfinite(y) & np.isfinite(true) & np.isfinite(sma)
    losses = {"true_dgp": F.qlike(y[mask], true[mask]), "misscaled": F.qlike(y[mask], bad[mask]), "sma20": F.qlike(y[mask], sma[mask])}
    out = F.mcs(losses, h=1, B=2000, seed=11)
    p = out["p"]
    assert p["misscaled"] <= 1 / 2000 and not out["in_set"]["misscaled"]
    assert p["true_dgp"] >= 0.10 and out["in_set"]["true_dgp"]
    assert max(p.values()) == 1.0 and all(abs(v * 2000 - round(v * 2000)) < 1e-9 for v in p.values())
    assert out["block"] == 10 and F.mcs(losses, h=21)["block"] == 42
    assert F.mcs(losses, h=1, B=2000, seed=11)["p"] == p                        # deterministic under seed 11
    assert F.mcs(losses, h=1, B=2000, seed=12)["n"] == out["n"]
    _raises(lambda: F.mcs(losses, stat="T_R"), ValueError, "T_max")
    idx = F.stationary_bootstrap_indices(100, 10, np.random.default_rng(1))
    assert idx.size == 100 and idx.min() >= 0 and idx.max() < 100
    # the pure harness: the mis-scaled forecaster is not registered, the registered seven are
    assert tuple(F.FORECAST_REGISTRY) == E.ESTIMATORS and all(s.loss == "qlike" and s.benchmark == "sma20" for s in F.FORECAST_REGISTRY.values())


test_t_est_01_mcs_synthetic_companion.test_ids = ["T-EST-01"]


def test_dm_hln_factor_and_legacy_dm_unchanged():
    rng = np.random.default_rng(3)
    a = rng.random(400)
    b = a + 0.05 + rng.normal(0, 0.1, 400)
    legacy = V.dm_test(a, b, lag=5)
    out = F.dm_test(a, b, h=5)
    n = 400
    assert out["lag"] == 10 and math.isclose(out["hln"], math.sqrt((n + 1 - 10 + 20 / n) / n))
    assert math.isclose(out["t"], V.dm_test(a, b, lag=10)["t"] * out["hln"]) and 0 < out["p"] < 0.05
    assert F.dm_test(a, b, h=21)["lag"] == 42 and F.dm_test(a, b, h=1, lag=3)["lag"] == 3
    assert V.dm_test(a, b, lag=5) == legacy                                     # the legacy call is untouched
    assert set(F.cw_test(a, a + 0.1, a)) >= {"t", "p"} and set(F.gw_test(a, b, h=5)) >= {"stat", "p"}
    assert F.LOSSES["mse"](np.array([1.0, 2.0]), np.array([0.0, 2.0])).tolist() == [1.0, 0.0]
    assert math.isclose(F.qlike(np.array([2.0]), np.array([2.0]))[0], 0.0, abs_tol=1e-12)
    assert np.allclose(F.tick_loss(np.array([-0.1, 0.1]), np.array([0.0, 0.0]), 0.05), [0.095, 0.005])


test_dm_hln_factor_and_legacy_dm_unchanged.test_ids = []


def test_t_b5_01_synthetic_clauses_and_bands():
    rng = np.random.default_rng(11)
    n = 1500
    sigma = 0.01 * np.ones(n)
    r = rng.normal(0, 0.01, n)
    good = F.b5(r, sigma, form="fhs")
    assert good["status"] == "PASS" and good["n_origins"] == n - 1 - 252 and good["form"] == "fhs"
    assert F.b5(r, sigma, form="normal")["status"] == "PASS"
    # fewer than 200 origins -> NOT_RUN
    assert F.b5(r[:400], sigma[:400], form="fhs")["status"] == "NOT_RUN"
    # sigma x 0.7 applied to the out-of-sample forecast only (residual pool standardised by the unscaled sigma)
    bad = F.b5(r, 0.7 * sigma, form="fhs", pool_sigma=sigma)
    assert bad["status"] == "FAIL" and bad["exceedance"] > bad["band"][1]
    assert F.b5(r, 0.7 * sigma, form="normal")["status"] == "FAIL"
    # pure FHS cancels a constant rescaling (F-16): that is why the clause scales the forecast alone
    assert F.b5(r, 0.7 * sigma, form="fhs")["status"] == "PASS"
    # a normal quantile on fat-tailed data fails PIT: a sigma is never shown as a normal VaR (L1561)
    rt = rng.standard_t(4, size=n) * math.sqrt(0.5) * 0.01
    assert F.b5(rt, sigma, form="normal")["pit_chi2_p"] < 0.01
    _raises(lambda: F.b5(r, sigma, form="t"), ValueError, "nu")
    _raises(lambda: F.b5(r, sigma, form="lognormal"), ValueError, "form")
    # band arithmetic (L1561, L5801-5803) and the G-B5 ARITH rows
    for n_, lo, hi in ((2594, 0.0414, 0.0586), (2663, 0.0416, 0.0584), (8961, 0.0454, 0.0546)):
        got = F.band(n_)
        assert abs(got[0] - lo) < 5e-5 and abs(got[1] - hi) < 5e-5, (n_, got)
    assert_golden("G-B5-01", {"sample_band_lo": F.band(2594)[0], "sample_band_hi": F.band(2594)[1],
                              "subsample_band_lo": F.band(371)[0], "subsample_band_hi": F.band(371)[1],
                              "garch_fhs_band_lo": F.band(2123)[0], "garch_fhs_band_hi": F.band(2123)[1]})
    assert_golden("G-B5-02", {"sample_band_lo": F.band(2663)[0], "sample_band_hi": F.band(2663)[1]})
    # Kupiec / Christoffersen come from validate, unchanged
    assert F.kupiec is V.kupiec and F.christoffersen_cc is V.christoffersen


test_t_b5_01_synthetic_clauses_and_bands.test_ids = ["T-B5-01", "G-B5-01", "G-B5-02"]


def test_sized_book_timing_cost_and_cap():
    r = _gjr(800, seed=9)
    var21 = E.sma(r, 21).var
    bk = F.sized_book(r, var21, h=21, target_ann=0.20, cost_bps=3.0, cap=1.0)
    w = bk["weights"]
    assert np.nanmin(w) >= 0 and np.nanmax(w) <= 1.0 and bk["n"] == r.size - 1 - 19
    # t+1 timing: w decided at close t earns r[t+1]
    f = bk["first_origin"]
    assert math.isclose(bk["daily"][0], w[f] * r[f + 1]) and math.isclose(bk["daily"][1], w[f + 1] * r[f + 2] - 3e-4 * abs(w[f + 1] - w[f]))
    shifted = F.sized_book(r, np.r_[np.nan, var21[:-1]], h=21, target_ann=0.20, cost_bps=3.0)
    assert not math.isclose(shifted["sharpe"], bk["sharpe"])
    free = F.sized_book(r, var21, h=21, target_ann=0.20, cost_bps=0.0)
    costed = F.sized_book(r, var21, h=21, target_ann=0.20, cost_bps=35.0)
    dw = np.abs(np.diff(w[f:-1]))
    assert math.isclose(free["daily"].sum() - costed["daily"].sum(), 35e-4 * dw.sum())      # initial entry free
    assert math.isclose(costed["turnover_per_year"], dw.sum() / (bk["n"] / 252))
    _raises(lambda: F.sized_book(r, var21, cap=1.5), ValueError, "cap")
    assert math.isfinite(bk["vol_of_vol"]) and bk["vol_of_vol"] > 0 and math.isfinite(bk["max_dd"]) and bk["max_dd"] <= 0
    s3 = F.stage3({"sma20": bk, "ewma094": F.sized_book(r, E.ewma(r, 21, 0.94).var)}, r)
    row = s3["rows"]["ewma094"]
    assert s3["rank"] is None and s3["winner"] is None and row["dSR_ci90"] is None
    assert math.isclose(row["dMDD_vs_sma20"], s3["rows"]["ewma094"]["max_dd"] - bk["max_dd"]) and 0 < row["pc2_tail_ratio"] < 2
    assert F.reliability_table(var21[19:], F.realised_target(r, 21)[19:])[0]["n"] > 0


test_sized_book_timing_cost_and_cap.test_ids = []


# --------------------------------------------------------------------------- #
# Stage-1 report (T-EST-02 structure clause) and the gate object (always schema-valid)
# --------------------------------------------------------------------------- #
def _vol_state(sel: F.EstimatorSelection) -> dict:
    from tests.macro_m0_schemas import filled
    state = filled()["macro_state"]
    state["vol"].update(sel.vol_fields())
    return state


def test_t_est_02_stage1_report_structure():
    r = _gjr(1200, seed=5)
    rep = F.stage1(r, E.sma(r, 21).var, E.sma(r, 1).var)
    assert rep["horizon_days"] == 21
    for key in ("fhs_var_exceedance_h21", "fan_pit_h21", "christoffersen_cc"):
        assert isinstance(rep[key], dict), key
    assert {"n_origins", "exceedance", "band", "in_band"} <= set(rep["fhs_var_exceedance_h21"])
    assert "chi2_p" in rep["fan_pit_h21"] and {"p_ind", "p_cc"} <= set(rep["christoffersen_cc"])
    assert {"kupiec_1d", "cc_1d_95_99", "es975_z2"} == set(rep["printed"])
    assert set(rep["printed"]["kupiec_1d"]) == {"95", "99"} and set(rep["printed"]["cc_1d_95_99"]) == {"95", "99"}
    z2 = rep["printed"]["es975_z2"]
    assert {"z2", "p", "n", "n_sim", "seed"} <= set(z2) and z2["seed"] == 11 and z2["n_sim"] == 2000
    assert rep["b5_1d"]["status"] in ("PASS", "FAIL", "NOT_RUN") and isinstance(rep["pass"], bool)
    json.dumps(rep)                                                               # an acting field: plain JSON only
    assert rep["fhs_var_exceedance_h21"]["n_origins"] == F.fhs_eval(r, E.sma(r, 21).var, 21)["n_origins"]
    assert F.fan_pit(r, E.sma(r, 21).var, 21)["chi2_p"] == rep["fan_pit_h21"]["chi2_p"]


test_t_est_02_stage1_report_structure.test_ids = ["T-EST-02"]


def _session_dates(n: int, end: date = date(2026, 10, 2)) -> list[date]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def _store(closes: np.ndarray, *, last_status="official_close", sid="KOSPI_OFFICIAL_CLOSE", vendor_idx=()):
    dates = _session_dates(closes.size)
    rows = []
    for i, (d, px) in enumerate(zip(dates, closes)):
        status = last_status if i == closes.size - 1 else ("vendor_close" if i in vendor_idx else "official_close")
        src = "KRX" if status == "official_close" else "Yahoo"
        obs = datetime(d.year, d.month, d.day, 6, 30, 30, tzinfo=timezone.utc)
        rows.append(P.make_row(series_id=sid, value=float(px), obs_date=d, session_date=d, obs_utc=obs, obs_kind="close",
                               value_status=status, available_at_utc=obs, available_at_source="calendar_bound",
                               retrieved_at_utc=obs + timedelta(minutes=11), vintage=None, source=src, channel=None))
    store = P.PITStore(Path(tempfile.mkdtemp(prefix="m3gate_")) / "store", registry=REG)
    store.append(rows)
    return store


def test_estimator_gate_reads_through_pit_and_is_schema_valid():
    r = _gjr(900, seed=2)
    closes = 2000.0 * np.cumprod(1.0 + r)
    store = _store(closes)
    ctx = P.RunContext(U(2026, 10, 2, 6, 30, 30), U(2026, 10, 2, 7, 0))
    spec = {"card_id": "MACRO-R06-KR-ETF", "estimator": "sma", "parameters": {"estimator": "sma", "window": 20},
            "market": "KR", "instrument_book": "KRX_ETF_line"}
    log = []
    sel = F.estimator_gate(spec, REG, store, ctx=ctx, log=log)
    assert sel.status == "registered_default" and sel.estimator == "sma20" and not sel.fallback_used and sel.reason is None
    assert sel.estimator_b5 in ("PASS", "FAIL") and sel.stage2_mcs_p is None and sel.stage3_rank is None
    assert sel.stage1 is not None and sel.stage1["horizon_days"] == 21 and not log
    assert sel.var_1d_displayable == (sel.estimator_b5 == "PASS")
    want = math.sqrt(np.var(r[-20:], ddof=1) * 252)
    assert math.isclose(sel.sigma_ann, want, rel_tol=1e-9)
    assert S.validate("macro_state", _vol_state(sel)) == []
    assert sel.gate_dict() == {"status": "registered_default", "stage1": sel.stage1, "stage2_mcs_p": None,
                               "stage3_rank": None, "fallback_used": False, "reason": None}
    json.dumps(sel.gate_dict())
    # knowledge before the close: nothing visible -> NOT_RUN, still schema-valid
    early = F.estimator_gate(spec, REG, store, ctx=P.RunContext(U(2026, 10, 2, 6, 30, 30), U(2026, 10, 2, 6, 35)))
    assert early.status == "NOT_RUN" and early.estimator == "sma20" and early.estimator_b5 == "NOT_RUN"
    assert "provisional_intraday" in early.reason or "missing" in early.reason
    assert S.validate("macro_state", _vol_state(early)) == []
    # the decided session's close is a vendor row -> the acting read refuses (provisional_intraday) -> NOT_RUN
    vend = F.estimator_gate(spec, REG, _store(closes, last_status="vendor_close"), ctx=ctx)
    assert vend.status == "NOT_RUN" and "provisional_intraday" in vend.reason
    back = F.estimator_gate(spec, REG, _store(closes, last_status="vendor_close"),
                            ctx=P.RunContext(ctx.decision_utc, ctx.knowledge_utc, "backtest"), vendor="Yahoo")
    assert back.status == "registered_default"                                   # a declared vendor in a backtest
    # an interior session with only a vendor close: live drops it as market_vol_target does (_close_ok), a backtest
    # declaring that vendor keeps it
    gap = _store(closes, vendor_idx=(closes.size - 5,))
    live = F.estimator_gate(spec, REG, gap, ctx=ctx, with_stage1=False)
    c_wo = np.delete(closes, closes.size - 5)
    assert math.isclose(live.sigma_ann, math.sqrt(np.var((c_wo[1:] / c_wo[:-1] - 1.0)[-20:], ddof=1) * 252), rel_tol=1e-9)
    kept = F.estimator_gate(spec, REG, gap, ctx=P.RunContext(ctx.decision_utc, ctx.knowledge_utc, "backtest"), vendor="Yahoo", with_stage1=False)
    assert math.isclose(kept.sigma_ann, want, rel_tol=1e-9)
    # too little history for B5 (< 200 origins) -> estimator_b5 NOT_RUN, stage1 None, sigma still SMA20
    few = F.estimator_gate(spec, REG, _store(closes[-300:]), ctx=ctx)
    assert few.status == "registered_default" and few.estimator_b5 == "NOT_RUN" and few.stage1 is None
    tiny = F.estimator_gate(spec, REG, _store(closes[-10:]), ctx=ctx)
    assert tiny.status == "NOT_RUN" and "insufficient_history" in tiny.reason
    # an internal error never escapes as an invalid object
    class Boom:
        def rows(self, sid):
            raise RuntimeError("disk")
    boom = F.estimator_gate(spec, REG, Boom(), ctx=ctx)
    assert boom.status == "NOT_RUN" and boom.reason.startswith("error:RuntimeError") and S.validate("macro_state", _vol_state(boom)) == []
    # an unbound consumer is a registry refusal (R-19 rule 5), reported as NOT_RUN with the cause: SPX_OFFICIAL_CLOSE
    # binds only R-28_R-29 / corr63 / korea_covariance, so the default R-06 consumer has no binding there
    unb = F.estimator_gate(dict(spec, market="US"), REG, store, ctx=ctx)
    assert unb.status == "NOT_RUN" and "UnboundConsumer" in unb.reason and "SPX_OFFICIAL_CLOSE" in unb.reason
    assert F.ACTING_CLOSE["US"] == "SPX_OFFICIAL_CLOSE"
    assert F.estimator_gate(dict(spec, market="JP"), REG, store, ctx=ctx).reason.startswith("no acting close series")
    _raises(lambda: F.EstimatorSelection("sma60", "PASS", "registered_default", None, None, None, False, None), ValueError)
    assert F.GateResult is F.EstimatorSelection


test_estimator_gate_reads_through_pit_and_is_schema_valid.test_ids = []


# --------------------------------------------------------------------------- #
# Refusals: the switch-refusal sentence of T-B5-01 (runs from M3), the stock book, the registry
# --------------------------------------------------------------------------- #
def test_t_b5_01_switch_refusals_and_registry():
    store, ctx = object(), P.RunContext(U(2026, 10, 2, 6, 30, 30), U(2026, 10, 2, 7, 0))
    etf = {"market": "KR", "instrument_book": "KRX_ETF_line", "card_id": "MACRO-R06-KR-COMB"}
    # an estimator switch without a counted revision is refused; nothing is read or written (the store is a dummy)
    _raises(lambda: F.estimator_gate(dict(etf, estimator="comb"), REG, store, ctx=ctx), F.EstimatorSwitchRefused, "counted revision")
    _raises(lambda: F.estimator_gate(dict(etf, estimator="ewma094"), REG, store, ctx=ctx), F.EstimatorSwitchRefused, "counted revision")
    # at M3 a revision object does not help either: the R-23 ledger and CARD-P arrive in M7
    _raises(lambda: F.estimator_gate(dict(etf, estimator="comb"), REG, store, ctx=ctx, revision={"ledger_row": 1}),
            F.EstimatorSwitchRefused, "M7")
    # COMB or log-HAR on a stock book, or on a book outside books_allowed, is refused (L3237; item 33; F-12)
    _raises(lambda: F.estimator_gate(dict(etf, estimator="comb", instrument_book="KRX_stock_book"), REG, store, ctx=ctx),
            F.EstimatorSwitchRefused, "stock")
    _raises(lambda: F.estimator_gate(dict(etf, estimator="log_har_range", instrument_book="US_shares_KIS"), REG, store, ctx=ctx),
            F.EstimatorSwitchRefused, "books only")
    # never on the registered R-06 KR card (L3201)
    _raises(lambda: F.estimator_gate(dict(etf, estimator="comb", card_id="MACRO-R06-KR-ETF"), REG, store, ctx=ctx),
            F.EstimatorSwitchRefused, "MACRO-R06-KR-ETF")
    _raises(lambda: F.estimator_gate(dict(etf, estimator={"name": "xgb_state", "kind": "ml"}), REG, store, ctx=ctx),
            F.EstimatorSwitchRefused, "ml")
    _raises(lambda: F.estimator_gate(dict(etf, estimator="sma60"), REG, store, ctx=ctx), F.EstimatorSwitchRefused, "not an R-30")
    assert F.canonical_estimator("sma", {"parameters": {"window": 20}}) == "sma20"
    assert F.canonical_estimator("ewma", {"parameters": {"lambda": 0.97}}) == "ewma097"
    assert F.check_declaration("sma20", "KRX_stock_book", "MACRO-R06-KR-ETF", None) == "sma20"
    # the forecast registry refuses kind ml, max(sigma, implied) and duplicates; an unregistered name is refused
    _raises(lambda: F.register_forecast(F.ForecastSpec("vol_state_gbm", "ml")), MacroRefusal, "11a")
    _raises(lambda: F.register_forecast(F.ForecastSpec("sma20_iv", "sma", definition="max(sma20, implied_vol)")), MacroRefusal, "item 30")
    _raises(lambda: F.register_forecast(F.ForecastSpec("sma20", "sma")), MacroRefusal, "already")
    _raises(lambda: F.require_registered("har_iv"), MacroRefusal, "not a registered")
    assert F.require_registered("comb").definition == "0.5*(gjr_t + log_har_range)"
    assert "vol_state_gbm" not in F.FORECAST_REGISTRY and len(F.FORECAST_REGISTRY) == 7
    assert issubclass(F.EstimatorSwitchRefused, MacroRefusal)


test_t_b5_01_switch_refusals_and_registry.test_ids = ["T-B5-01"]


# --------------------------------------------------------------------------- #
# REFDATA goldens: NotRun naming the fixture (never a pass); G-B5-02 with a labelled SMOKE check on yf_SPY
# --------------------------------------------------------------------------- #
KS11 = "yahoo_KS11_1996-12_2026-10-02.csv"
GSPC = "yahoo_GSPC_1990_2026-10-01.csv"
SPY = "yahoo_SPY_2015-12_2026-10-01.csv"
MKTRF = "french_daily_mktrf_rf_1926-07_2026-08.csv"


# T-B5-01 on the fixture (look-ahead audit LA-02, part 2; the pattern of docs/product/LOOKAHEAD_LA02_PART1_2026-11-10.md).
# F13 yahoo_KS11_1996-12_2026-10-02.csv layout: docs/macro_fixtures.py writes the reference file's own columns followed
# by the section 4.1 provenance columns, and neither ACQUISITION.csv nor the spec names the close column. One row per
# date, in date order; the body reads the declared close layout through the one reader the part 2 bodies share,
# tests.macro_m1_calendars.read_close_layout (a blank or "." close and a repeated date are refused there):
#   close                                           the ^KS11 close, finite and > 0
#   series_id / value_status / available_at_source  KS11 / vendor_close / calendar_bound (docs/macro_fixtures.py:59)
#   obs_date = session_date                         ISO dates
#   obs_utc, available_at_utc                       YYYY-MM-DDTHH:MM:SSZ, available_at_utc not before obs_utc
# The replay is the product's B5 harness, `docs/vol_backtest.spec_form` (spec L6365 names docs/vol_backtest.py as the
# B5 harness): SMA20 and EWMA(0.94) in FHS and normal form, origins from vol_backtest.ORIGINS_FROM (2016-03-01), the
# residual pool from the earlier history, seed 11. Its own fixture reader `vol_backtest.fixture_closes` reads the same
# `close` column since owner ruling 1 of 2026-11-11 (before it, a column named `value`); the body still parses the file
# through the shared test reader, which also checks the provenance and the instants, and calls spec_form.
B501_COLUMNS = ("close", "series_id", "obs_date", "session_date", "obs_utc", "available_at_utc", "available_at_source",
                "value_status")
B501_PROVENANCE = (("series_id", "KS11"), ("value_status", "vendor_close"), ("available_at_source", "calendar_bound"))
B501_WINDOW = ("2016-03", "2026-10-02")     # spec L5642 / L5801 "KOSPI 2016-03 -> 2026-10"; F13 ends 2026-10-02
                                            # (docs/macro_fixtures.py:59; ACQUISITION.csv:17 "1996-12 -> 2026-10-02")
# The harness's look-back before its first origin: the SMA20 forecast exists from the 20th return
# (core.quant.vol_estimators.SMA_WINDOW; R-06 L1563 window 20), and an FHS origin is evaluated only once the residual
# pool holds forecast_eval.MIN_POOL (252; brief F-9) residuals, the first of them the 20th return's. So the first origin
# on or after 2016-03-01 is evaluated only if F13 holds SMA_WINDOW - 1 + MIN_POOL = 271 returns before it (a probe of
# spec_form: 271 give the full origin count, 270 one origin fewer); the window clause reads the parsed history for it,
# since spec_form writes its sample as ORIGINS_FROM..last whatever the history.
B501_LOOKBACK = E.SMA_WINDOW - 1 + F.MIN_POOL
B501_SIGMA_SCALE = 0.7                      # spec L5642 "A synthetic estimator with sigma x 0.7 fails" (forecast only,
                                            # brief F-16, as in test_t_b5_01_synthetic_clauses_and_bands)
# Expected values: goldens.csv (read only), never typed here. G-B5-01/sample_origins 2,594 (count_exact; spec L5801),
# G-B5-01/sma20_exceed 0.047 (kind exceedance, +/- 0.3 pp; spec L5642), G-B5-01/sma20_pit_p 0.107 (p_hi, +/- 0.01;
# spec L5642 "PIT p 0.11"), G-B5-01/sma20_verdict PASS, and G-POST-01/gb501_pit_p, the same 0.107 (spec L5819-5834).
# The PIT p is the chi-square p on 10 bins, the B5 rule's (spec L3207; core/quant/forecast_eval.py b5).


def _b501_closes(text: str) -> tuple[list[str], np.ndarray]:
    """F13 in the declared layout as (ISO session dates, closes), read by tests.macro_m1_calendars.read_close_layout;
    AssertionError naming the file and line on any departure from it."""
    from tests.macro_m1_calendars import read_close_layout
    rows = read_close_layout("F13", text)
    assert len(rows) > 1, f"{KS11}: {len(rows)} rows"
    return [r["date"].isoformat() for r in rows], np.asarray([r["close"] for r in rows], dtype=float)


def _b501_replay(text: str, *, harness=None, scale: float = B501_SIGMA_SCALE) -> tuple[list[dict], dict, list[str]]:
    """The B5 harness on F13: `docs/vol_backtest.spec_form` (or `harness`, a wrapper a FAIL demonstration passes) on
    the parsed closes, and for the sigma x 0.7 clause `forecast_eval.b5` on the same returns with the SMA20 forecast
    scaled by `scale` and the residual pool standardised by the unscaled sigma (brief F-16), from the same origin.
    Returns the harness lines, the scaled run and the parsed session dates."""
    from docs import vol_backtest as VB
    dates, closes = _b501_closes(text)
    rows = (VB.spec_form if harness is None else harness)(dates, closes, "KR", "G-B5-01")
    r = closes[1:] / closes[:-1] - 1.0
    start = next((i for i, d in enumerate(dates[1:]) if d >= VB.ORIGINS_FROM), None)
    fc = E.sma(r, 1)
    sig = np.sqrt(np.where(fc.ok & (fc.var > 0), fc.var, np.nan))
    return rows, F.b5(r, scale * sig, form="fhs", pool_sigma=sig, origins_from=start), dates


def _check_b501(rows: list[dict], scaled: dict, dates: list[str]) -> dict:
    """T-B5-01 (spec L5642) on the harness lines and the parsed F13 session dates: the history covers the window
    KOSPI 2016-03 -> 2026-10-02 (its first session on or after 2016-03-01 lies in 2016-03, its last row is 2026-10-02,
    and it holds the harness's B501_LOOKBACK returns before 2016-03-01, so the first origin is evaluated); the SMA20 FHS
    line has the G-B5-01 origin count exactly, its exceedance and PIT chi-square p at Level 1 and the verdict PASS,
    asserted through tests/golden_tools.assert_class: a class, not a point, when a statistic lies within tolerance of
    its B5 threshold (spec L5737); the SMA20 forecast x 0.7 fails B5. The other harness lines (normal form,
    EWMA(0.94)) are printed beside their goldens, not asserted. Returns the SMA20 FHS line."""
    from docs import vol_backtest as VB
    g, gpost = golden("G-B5-01"), golden("G-POST-01")
    for x in rows:
        print(f"PRINTED T-B5-01 harness line {x['model']} {x['form']}: n {x['n_origins']}, exceedance "
              f"{x['exceedance']:.4f}, PIT chi2 p {x['pit_chi2_p']:.4f}, {x['b5_status']} ({x['sample']})")
    print("PRINTED G-B5-01 goldens not asserted here: " + ", ".join(
        f"{s} {g.want(s)}" for s in ("normal_exceed", "normal_pit_p", "normal_verdict", "ewma094_exceed",
                                     "ewma094_pit_p", "ewma094_verdict")))
    before = sum(1 for d in dates[1:] if d < VB.ORIGINS_FROM)             # returns dated before the first origin
    first = next((d for d in dates if d >= VB.ORIGINS_FROM), None)
    assert (first or "")[:7] == B501_WINDOW[0] and dates[-1] == B501_WINDOW[1] and before >= B501_LOOKBACK, (
        f"T-B5-01: F13 {dates[0]}..{dates[-1]} does not cover the window {B501_WINDOW[0]} -> {B501_WINDOW[1]} (spec "
        f"L5642, L5801): first session from {VB.ORIGINS_FROM} {first}, {before} returns before it, the harness needs "
        f"{B501_LOOKBACK} (SMA20 window + the FHS pool of {F.MIN_POOL})")
    sma = [x for x in rows if (x["model"], x["form"]) == ("sma20", "fhs")]
    assert len(sma) == 1, f"T-B5-01: {len(sma)} SMA20 FHS lines from the harness, not one"
    sma = sma[0]
    row = g.row("sample_origins")
    assert_close(sma["n_origins"], row.want(), row.kind, label="T-B5-01 origins (G-B5-01/sample_origins, spec L5801)")
    row = g.row("sma20_exceed")
    assert_close(sma["exceedance"], row.want(), row.kind,
                 label="T-B5-01 SMA20 FHS exceedance (G-B5-01/sma20_exceed, spec L5642)")
    row, post = g.row("sma20_pit_p"), gpost.row("gb501_pit_p")
    assert (post.want(), post.kind) == (row.want(), row.kind), (
        "goldens.csv: G-POST-01/gb501_pit_p != G-B5-01/sma20_pit_p")
    assert_close(sma["pit_chi2_p"], row.want(), row.kind,
                 label="T-B5-01 SMA20 FHS PIT chi2 p (G-B5-01/sma20_pit_p, G-POST-01/gb501_pit_p, spec L5642)")
    # the verdict: PASS or FAIL as a class when any deciding statistic lies within tolerance of its threshold, else
    # the golden verdict (golden_tools.assert_class against each threshold, the point verdict unless one is near)
    ex, p = sma["exceedance"], sma["pit_chi2_p"]
    thresholds = ((ex, sma["band_lo"], "exceedance", "exceedance band low"),
                  (ex, sma["band_hi"], "exceedance", "exceedance band high"), (p, F.PIT_P_MIN, p_kind(p), "PIT p floor"))
    point = None if any(near_threshold(stat, t, k) for stat, t, k, _ in thresholds) else g.want("sma20_verdict")
    for stat, t, k, what in thresholds:
        assert_class(stat, t, k, sma["b5_status"], ("PASS", "FAIL"), point=point,
                     label=f"T-B5-01 verdict (G-B5-01/sma20_verdict; {what}; spec L5737)")
    assert scaled["status"] == "FAIL" and scaled["exceedance"] > scaled["band"][1], (
        f"T-B5-01: the SMA20 forecast x {B501_SIGMA_SCALE} did not fail B5 (status {scaled['status']}, exceedance "
        f"{scaled['exceedance']:.4f}, band {scaled['band']}; spec L5642)")
    return sma


def test_t_b5_01_kospi_golden_refdata():
    """T-B5-01 on the ^KS11 fixture (spec L5642): the B5 harness reproduces SMA20 FHS exceedance 4.70% +- 0.3 pp on
    KOSPI 2016-03 -> 2026-10 (2,594 origins), PIT p 0.11 (0.107) and PASS, and the forecast x 0.7 fails. NOT_RUN
    (REFDATA) until F13 is listed with its md5; then PASS or FAIL on `_check_b501`."""
    text = require_fixture(KS11).read_text(encoding="utf-8")
    _check_b501(*_b501_replay(text))


test_t_b5_01_kospi_golden_refdata.test_ids = ["T-B5-01", "G-B5-01", "G-POST-01"]


# The invented path of the demonstration below (no KOSPI data): weekdays from 2015-01-02, with invented holidays spread
# evenly over 2016-03-01..2026-10-01 so that the window holds the G-B5-01 origin count (+ `extra_sessions`), and the
# last row on 2026-10-02; returns Student-t(6) at unit variance x 1.2% x exp(0.3 sin(i / 150)) from `seed`. Seed 293
# was found by a scan of seeds 0-399 for a path that lands within Level 1 of the goldens (exceedance 0.0486, PIT p
# 0.1031); seed 9 misses the exceedance (0.0544, PIT p 0.7983, harness verdict PASS) and seed 8 the PIT p (0.9987,
# exceedance 0.0466). Every invented path of the scan has 2,594 origins and its x 0.7 run FAILs.
B501_DEMO_SEED, B501_DEMO_EXCEED_MISS, B501_DEMO_PIT_MISS = 293, 9, 8


def _b501_invented(seed: int = B501_DEMO_SEED, *, extra_sessions: int = 0, last: bool = True,
                   first: date = date(2015, 1, 2), skip: tuple[date, date] | None = None) -> str:
    """Invented ^KS11-like rows in the declared F13 layout, in memory (see the comment above); `first` moves the start
    of the history and `skip` drops the sessions of a (from, to) span."""
    def weekdays(a: date, b: date) -> list[date]:
        return [a + timedelta(days=i) for i in range((b - a).days + 1) if (a + timedelta(days=i)).weekday() < 5]
    n_window = int(golden("G-B5-01").want("sample_origins")) + extra_sessions
    window = weekdays(date(2016, 3, 1), date(2026, 10, 1))
    drop = {int(round((i + 0.5) * len(window) / (len(window) - n_window))) for i in range(len(window) - n_window)}
    days = weekdays(date(2015, 1, 2), date(2016, 2, 29)) + [d for i, d in enumerate(window) if i not in drop]
    days += [date(2026, 10, 2)] if last else []
    days = [d for d in days if d >= first and not (skip and skip[0] <= d <= skip[1])]
    rng = np.random.default_rng(seed)
    n = len(days) - 1
    r = rng.standard_t(6, size=n) * math.sqrt(4 / 6) * 0.012 * np.exp(0.3 * np.sin(np.arange(n) / 150.0))
    closes = 2000.0 * np.cumprod(np.r_[1.0, 1.0 + r])
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(("date",) + B501_COLUMNS)
    for d, c in zip(days, closes):
        out.writerow((d.isoformat(), repr(float(c)), "KS11", d.isoformat(), d.isoformat(), f"{d.isoformat()}T06:30:00Z",
                      f"{d.isoformat()}T06:30:30Z", "calendar_bound", "vendor_close"))
    return buf.getvalue()


def _b501_edit(text: str, edit) -> str:
    """`text` with `edit(header, rows)` applied to its parsed rows (lists of strings), rewritten in memory."""
    rows = list(csv.reader(io.StringIO(text)))
    header, body = edit(rows[0], rows[1:])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows([header] + body)
    return buf.getvalue()


def test_t_b5_01_body_passes_and_fails_on_invented_closes():
    """LA-02 part 2: the T-B5-01 body can PASS and can FAIL. On an invented path built to the goldens the harness line
    passes every clause. It fails, each on its own clause, when the history does not cover the window: the path ends on
    2026-10-01, starts in 2018 (spec_form still writes its sample from 2016-03-01), starts in June 2015 or one session
    after the harness's 271-return look-back, or skips March 2016; when it holds one more session (2,595 origins),
    misses the exceedance (5.44%) or the PIT p (0.999), when a wrapped harness reports FAIL for the passing line or
    NOT_RUN, and when the sigma x 0.7 run is not scaled. A wrapped harness that moves the band edge next to the
    exceedance may report FAIL: the verdict is then a class (golden_tools.assert_class, spec L5737). At the layout (the
    shared reader) it fails when the close is in a column named `value` (the product reader's column before owner
    ruling 1 of 2026-11-11), when a row carries F01's series id, when two rows are out of date order, and on a "."
    close. The declared provenance equals the generator's table (docs/macro_fixtures.REFERENCE_FILES F13), and the
    declared columns are part 1's F01 layout."""
    from docs import macro_fixtures as MF
    from docs import vol_backtest as VB
    from tests.macro_m1_calendars import F01_COLUMNS
    f13 = [(("series_id", series.split(";")[0]), ("value_status", status), ("available_at_source", source))
           for fid, _rel, series, status, source, *_rest in MF.REFERENCE_FILES if fid == "F13"]
    assert f13 == [B501_PROVENANCE], f13
    assert B501_COLUMNS == F01_COLUMNS
    assert B501_LOOKBACK == 271                                 # 20 - 1 + 252: a probe of spec_form found the same edge
    good = _b501_invented()
    sma = _check_b501(*_b501_replay(good))
    assert sma["b5_status"] == "PASS" and sma["n_origins"] == golden("G-B5-01").want("sample_origins")
    assert abs(sma["exceedance"] - 0.0486) < 1e-4 and abs(sma["pit_chi2_p"] - 0.1031) < 1e-4     # the scan's seed 293
    window = "does not cover the window 2016-03 -> 2026-10-02 (spec L5642, L5801)"
    pre = [d for d in _b501_closes(good)[0] if d < VB.ORIGINS_FROM]       # 302 rows, 301 returns, before 2016-03-01
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(last=False))), AssertionError,
            f"T-B5-01: F13 2015-01-02..2026-10-01 {window}")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(first=date(2018, 1, 2)))), AssertionError,
            f"T-B5-01: F13 2018-01-02..2026-10-02 {window}: first session from 2016-03-01 2018-01-02, 0 returns")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(first=date(2015, 6, 1)))), AssertionError,
            "returns before it, the harness needs 271 (SMA20 window + the FHS pool of 252)")
    edge = date.fromisoformat(pre[len(pre) - B501_LOOKBACK])          # 271 rows before 2016-03-01: 270 returns
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(first=edge))), AssertionError,
            "270 returns before it, the harness needs 271")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(skip=(date(2016, 3, 1), date(2016, 3, 31))))),
            AssertionError, "first session from 2016-03-01 2016-04-01")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(extra_sessions=1))), AssertionError,
            "T-B5-01 origins (G-B5-01/sample_origins, spec L5801): got 2595")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(B501_DEMO_EXCEED_MISS))), AssertionError,
            "T-B5-01 SMA20 FHS exceedance (G-B5-01/sma20_exceed, spec L5642): got 0.054")
    _raises(lambda: _check_b501(*_b501_replay(_b501_invented(B501_DEMO_PIT_MISS))), AssertionError,
            "T-B5-01 SMA20 FHS PIT chi2 p (G-B5-01/sma20_pit_p, G-POST-01/gb501_pit_p, spec L5642): got 0.99")

    def wrapped(**kw):
        def harness(dates, closes, market, symbol):
            return [{**x, **{k: f(x) for k, f in kw.items()}} if (x["model"], x["form"]) == ("sma20", "fhs") else x
                    for x in VB.spec_form(dates, closes, market, symbol)]
        return harness
    _raises(lambda: _check_b501(*_b501_replay(good, harness=wrapped(b5_status=lambda x: "FAIL"))), AssertionError,
            "T-B5-01 verdict (G-B5-01/sma20_verdict; exceedance band low; spec L5737): 'FAIL' != 'PASS' although stat")
    _raises(lambda: _check_b501(*_b501_replay(good, harness=wrapped(b5_status=lambda x: "NOT_RUN"))), AssertionError,
            "T-B5-01 verdict (G-B5-01/sma20_verdict; exceedance band low; spec L5737): 'NOT_RUN' not in ['FAIL', 'PASS']")
    near = wrapped(band_hi=lambda x: x["exceedance"] + 0.001, b5_status=lambda x: "FAIL")   # within 0.3 pp of the edge
    assert _check_b501(*_b501_replay(good, harness=near))["b5_status"] == "FAIL"           # a class: PASS or FAIL
    _raises(lambda: _check_b501(*_b501_replay(good, scale=1.0)), AssertionError,
            "T-B5-01: the SMA20 forecast x 0.7 did not fail B5 (status PASS")

    def renamed(header, rows):
        return [("value" if c == "close" else c) for c in header], rows

    def f01_row(header, rows):
        rows[3][header.index("series_id")] = "KOSPI_OFFICIAL_CLOSE"
        return header, rows

    def swapped(header, rows):
        rows[10], rows[11] = rows[11], rows[10]
        return header, rows

    def dot(header, rows):
        rows[20][header.index("close")] = "."
        return header, rows
    _raises(lambda: _b501_closes(_b501_edit(good, renamed)), AssertionError, "declared columns ['close'] absent")
    _raises(lambda: _b501_closes(_b501_edit(good, f01_row)), AssertionError,
            f"{KS11} line 5: not a KS11 / vendor_close / calendar_bound row (series_id 'KOSPI_OFFICIAL_CLOSE'")
    _raises(lambda: _b501_closes(_b501_edit(good, swapped)), AssertionError,
            f"{KS11} line 13: rows out of date order or repeated")
    _raises(lambda: _b501_closes(_b501_edit(good, dot)), AssertionError,
            f"{KS11} line 22: close '.' is not a finite number > 0")


def test_g_b5_02_spy_refdata_with_smoke_on_local_cache():
    """G-B5-02 needs the frozen SPY file; the local `yf_SPY.csv` (auto-adjusted, ends 2026-09-25 with an intraday
    last row) runs the same harness as a labelled SMOKE line that is never compared with the golden."""
    from docs import vol_backtest as VB
    if (VB.CACHE / "yf_SPY.csv").is_file():
        dates, closes = VB.load_closes("yf_SPY.csv")
        rows = VB.spec_form(dates, closes, "US", "SPY")
        sma = next(x for x in rows if x["model"] == "sma20" and x["form"] == "fhs")
        assert sma["label"].startswith("SMOKE") and sma["n_origins"] >= 200 and sma["b5_status"] in ("PASS", "FAIL")
        assert abs(sma["band_lo"] - F.band(sma["n_origins"])[0]) < 1e-12
        assert next(x for x in rows if x["model"] == "sma20" and x["form"] == "normal")["b5_status"] != "NOT_RUN"
        assert VB.incumbent_b5_status(rows) == {"US": sma["b5_status"]}
    require_fixture(SPY)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_g_b5_02_spy_refdata_with_smoke_on_local_cache.test_ids = ["G-B5-02"]


def test_g_b5_03_us_market_refdata():
    require_fixture(MKTRF)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_g_b5_03_us_market_refdata.test_ids = ["G-B5-03"]


def test_g_b5_04_display_labels_refdata():
    require_fixture(KS11)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_g_b5_04_display_labels_refdata.test_ids = ["G-B5-04"]


def test_t_est_01_i_10_dlb_t1a_refdata():
    """SMA20 outside the 90% QLIKE MCS at h 1/5/21 (p <= 0.0005), COMB inside all six cells; SMA20 MSE MCS p printed."""
    require_fixture(KS11)
    require_fixture(GSPC)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_t_est_01_i_10_dlb_t1a_refdata.test_ids = ["T-EST-01", "I-10", "G-EST-01", "G-EST-02"]


def test_t_est_02_christoffersen_lines_refdata():
    """KOSPI 2001-26 1-day independence p < 0.0001 for SMA20, 0.17 for COMB, 0.16 for log-HAR-range (OHLC needed)."""
    require_fixture(KS11)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_t_est_02_christoffersen_lines_refdata.test_ids = ["T-EST-02", "G-EST-03"]


def test_g_est_04_sizing_books_refdata():
    require_fixture(KS11)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_g_est_04_sizing_books_refdata.test_ids = ["G-EST-04"]


def test_g_us_01c_ewma_challenger_refdata():
    """EWMA(0.94) at the 15% target: Sharpe 0.605 gross / 0.520 at 50 bp / 0.434 at 100 bp (French Mkt-RF + ^GSPC)."""
    require_fixture(MKTRF)
    raise AssertionError("fixture listed: golden assertion not implemented")


test_g_us_01c_ewma_challenger_refdata.test_ids = ["G-US-01c"]


if __name__ == "__main__":
    from tests.macro_acceptance import run_module
    raise SystemExit(run_module(globals()))
