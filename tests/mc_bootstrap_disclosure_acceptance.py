"""N-M1-02/a: the Monte Carlo block bootstrap says what it is, and no number changes.

Offline: dotenv is suppressed before engine imports and every test refuses HTTP.
Covers the disclosure constant against the engine defaults, the fixed circular
block structure, the within-block clustering retention (5-k)/5, the unchanged
numbers of all four models, and the Flet, narrative and Native surfaces in both
languages. Part (b) of ARCHITECTURE_REVIEW C1 (a data-driven block length) is a
maths change left to the owner; nothing here asserts that the paths match the
sample's clustering at lag 5.
"""
import ast
from datetime import date, timedelta
from functools import lru_cache
import inspect
import math
import os
import re
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.history import History
    import core.quant.montecarlo as MC
    from core.quant.garch import Z_BOUND, bounded_t_stats, fit_garch, horizon_vol, simulate_returns
    from core.quant import insights
    from ui import quant_lab_page
from core.research.mc_disclosure import (BOOTSTRAP_BLOCK_SESSIONS, BOOTSTRAP_TEXT, BOOTSTRAP_TEXT_KO,
                                         bootstrap_disclosure)
from core.research.analysis import AnalysisRequest, execute_analysis
from core.research.runs import SessionResearch, export_bytes, read_export
from core.ui_legacy_messages import static_text
from core.i18n import LocaleContext
from ui.localization import translate_controls
from quantgen_desktop.translations import translate
import flet as ft

B = BOOTSTRAP_BLOCK_SESSIONS
DAYS = 252

# The Flet AI payload keys before this change (a32106b); the change adds one key.
OLD_PAYLOAD_KEYS = {
    "symbol", "data_source", "model", "n_paths", "horizon_days", "spot", "drift_annual",
    "vol_annual", "volatility_definition", "median_terminal", "mean_terminal", "p05", "p95",
    "prob_loss", "prob_target", "target", "prob_target_basis", "var_level", "var_pct",
    "cvar_pct", "jump_note", "drift_mode", "drift_note", "rf_rate", "erp",
    "convexity_correction_annual", "z_bound", "bound_note",
}

# run_monte_carlo(VOL_FIXTURE, n_paths=300, horizon_days=30, seed=23, rf_rate=.03, erp=.04,
# target=spot) on the engine before this change (a32106b), for every model in a rate and a
# log drift mode. Unlike engine_parts, these values do not come from the engine's own
# building blocks, so a change inside _simulate_gbm, _simulate_jump or the GARCH code fails.
GOLDEN_NAMES = ("mean_terminal", "median_terminal", "p05", "p95", "var_pct", "cvar_pct",
                "mu_annual", "sigma_annual", "correction_annual")
GOLDEN_A32106B = {
    ("garch_t", "premium"): (95.90980363559014, 95.98768625488103, 81.05025090411962, 110.90802582538733, 0.15466303058852646, 0.21533161764778033, 0.03479701518024998, 0.27953997032639216, 0.035202984819750024),
    ("garch_t", "zero"): (95.51056365351249, 95.46571565889921, 80.74805962156745, 110.31682181462673, 0.15781482173199154, 0.2156540947963074, 0.0, 0.27953997032639216, 0.0),
    ("gbm", "premium"): (96.54900525325547, 96.55210485204465, 90.2966101739603, 103.51247432068402, 0.05822545962402349, 0.08467603881953625, 0.06250168034426917, 0.12246076641709239, 0.0074983196557308306),
    ("gbm", "zero"): (95.83328140151052, 95.83635802277882, 89.62723572039968, 102.74512983453297, 0.06520689355744567, 0.09146139294485436, 0.0, 0.12246076641709239, 0.0),
    ("jump", "premium"): (96.74704680188646, 96.68377278519414, 90.65939696915375, 105.0633074704941, 0.054441670103691026, 0.0799688076142728, 0.06186519314446903, 0.12246076641709239, 0.00813480685553097),
    ("jump", "zero"): (96.03713153295747, 95.97432181147687, 89.99415195850149, 104.29236873238237, 0.06138003482123067, 0.08671985803861325, 0.0, 0.12246076641709239, 0.0),
    ("bootstrap", "premium"): (96.70288141240006, 96.44919823524599, 91.32040384556339, 103.10408505236721, 0.04754750822965455, 0.06099630082742819, 0.0644065963585174, 0.12246076641709239, 0.005593403641482597),
    ("bootstrap", "zero"): (95.9642520372654, 95.71250652571018, 90.62288654468964, 102.31656243873086, 0.05482246610646883, 0.06816853505084432, 0.0, 0.12246076641709239, 0.0),
}


def _history(symbol, returns, note):
    dates = tuple((date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(returns.size + 1))
    return History(symbol, "SYNTHETIC", dates, tuple(100 * np.exp(np.r_[0, np.cumsum(returns)])), note=note)


def garch_returns(seed, n=504):
    """GARCH(1,1) with unit-variance t6 innovations, 20% unconditional vol."""
    g = np.random.default_rng(seed)
    alpha, beta, nu = .08, .90, 6
    omega = (0.20 ** 2 / DAYS) * (1 - alpha - beta)
    h, r = omega / (1 - alpha - beta), np.empty(n)
    for t in range(n):
        r[t] = math.sqrt(h) * g.standard_t(nu) / math.sqrt(nu / (nu - 2))
        h = omega + alpha * r[t] ** 2 + beta * h
    return r


@lru_cache
def histories():
    rng = np.random.default_rng(7303)
    calm = rng.normal(0, .005, 300); calm[-40:] *= 4
    trend = np.random.default_rng(41).normal(-.0012, .014, 150)
    return (_history("GARCH_FIXTURE", garch_returns(1034), "synthetic GARCH-t fixture"),
            _history("VOL_FIXTURE", calm, "synthetic volatility fixture"),
            _history("TREND_FIXTURE", trend, "synthetic negative-drift fixture"))


@lru_cache
def result(model, drift="zero"):
    return MC.run_monte_carlo(histories()[1], model=model, n_paths=200, horizon_days=20, drift=drift, seed=7)


# --------------------------------------------------------------------------- helpers
def derived(paths, spot, *, target, var_level=.95, n_sample=40):
    """What run_monte_carlo reads off a path matrix, written out independently."""
    n = paths.shape[0]
    terminal = paths[:, -1]
    losses = 1.0 - terminal / spot
    var = float(np.percentile(losses, var_level * 100))
    tail = losses[losses >= var]
    return {
        "fan": {p: np.percentile(paths, p, axis=0) for p in (5, 25, 50, 75, 95)},
        "terminal": terminal,
        "sample_paths": paths[:: max(1, n // n_sample)][:n_sample],
        "mean_terminal": float(np.mean(terminal)), "median_terminal": float(np.median(terminal)),
        "p05": float(np.percentile(terminal, 5)), "p95": float(np.percentile(terminal, 95)),
        "prob_loss": float(np.mean(terminal < spot)),
        "prob_target": float(np.mean(terminal >= target)) if target else None,
        "var_pct": max(0.0, var), "cvar_pct": max(0.0, float(np.mean(tail)) if tail.size else var),
    }


def fields(mc):
    return {"fan": mc.fan, "terminal": mc.terminal, "sample_paths": mc.sample_paths,
            "mean_terminal": mc.mean_terminal, "median_terminal": mc.median_terminal,
            "p05": mc.p05, "p95": mc.p95, "prob_loss": mc.prob_loss, "prob_target": mc.prob_target,
            "var_pct": mc.var_pct, "cvar_pct": mc.cvar_pct}


def drift_terms(drift, r, rf, erp):
    """(kind, annual value) of each drift mode, as documented in the engine docstring."""
    if drift == "premium":
        return "rate", float(rf + erp)
    if drift == "rf":
        return "rate", float(rf)
    if drift == "zero":
        return "log", 0.0
    return "log", float(np.mean(r)) * DAYS


def old_bootstrap_recipe(history, *, n_paths, horizon, seed, drift, rf, erp):
    """The documented bootstrap recipe, rebuilt without calling the engine: demean the
    window's daily log returns, draw ceil(H/5) uniform block starts per path, take five
    consecutive returns from each start wrapping at the end, cut to H, subtract the
    exact block log-MGF increments in rate modes, add the drift, exponentiate."""
    closes = np.asarray(history.closes, dtype=float)
    r = np.diff(np.log(closes))
    r_dm = r - float(np.mean(r))
    n = r_dm.size
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(n_paths, math.ceil(horizon / 5)))
    shocks = np.empty((n_paths, starts.shape[1] * 5))
    for j in range(5):
        shocks[:, j::5] = r_dm[(starts + j) % n]
    shocks = shocks[:, :horizon]
    partial = np.empty((n, 5))
    partial[:, 0] = r_dm
    for j in range(1, 5):
        partial[:, j] = partial[:, j - 1] + r_dm[(np.arange(n) + j) % n]
    log_m = np.r_[0.0, np.log(np.mean(np.exp(partial), axis=0))]
    corr = (log_m[1:] - log_m[:-1])[np.arange(horizon) % 5]
    kind, value = drift_terms(drift, r, rf, erp)
    if kind == "rate":
        shocks = shocks + (value / DAYS - corr)
        corr_daily = float(np.mean(corr))
        mu = value - corr_daily * DAYS
    else:
        shocks = shocks + value / DAYS
        corr_daily, mu = 0.0, value
    paths = history.last * np.exp(np.hstack([np.zeros((n_paths, 1)), np.cumsum(shocks, axis=1)]))
    sigma = float(np.std(r, ddof=1)) * math.sqrt(DAYS)
    return paths, {"mu_annual": mu, "sigma_annual": sigma, "correction_annual": corr_daily * DAYS}


def engine_parts(history, model, *, n_paths, horizon, seed, drift, rf, erp):
    """gbm, jump and garch_t assembled from the engine's own building blocks, which this
    change leaves untouched, to check that run_monte_carlo still assembles them the same."""
    mu_s, sigma, r = MC._calibrate(history)
    kind, value = MC.resolve_drift(drift, sample_mu=mu_s, rf_rate=rf, erp=erp)
    rate = value / DAYS if kind == "rate" else None
    log_drift = value / DAYS if kind == "log" else None
    extra = {}
    if model == "garch_t":
        fit = fit_garch(r, dist="t")
        shocks, corr_daily = simulate_returns(fit, n_paths=n_paths, horizon=horizon, seed=seed,
                                              drift_daily=log_drift, rate_daily=rate)
        sigma_report = fit.cond_vol_last
        _, v_in = bounded_t_stats(fit.nu, Z_BOUND)
        extra = {"garch_horizon_vol": horizon_vol(fit, horizon, var_in=v_in),
                 "z_bound": Z_BOUND if fit.innovation == "t" else None}
    else:
        rng = np.random.default_rng(seed)
        if model == "gbm":
            shocks = MC._simulate_gbm(rng, sigma, n_paths, horizon)
            corr = 0.5 * (sigma / math.sqrt(DAYS)) ** 2
        else:
            shocks, note, corr = MC._simulate_jump(rng, r, sigma, n_paths, horizon)
            extra = {"jump_note": note}
        if rate is None:
            shocks, corr_daily = shocks + log_drift, 0.0
        else:
            shocks, corr_daily = shocks + (rate - corr), float(np.mean(corr))
        sigma_report = sigma
    mu = value if kind == "log" else value - corr_daily * DAYS
    paths = history.last * np.exp(np.hstack([np.zeros((n_paths, 1)), np.cumsum(shocks, axis=1)]))
    return paths, dict(extra, mu_annual=mu, sigma_annual=sigma_report, correction_annual=corr_daily * DAYS)


def numbers(text):
    return sorted(re.findall(r"[+-]?\d+(?:[.,]\d+)*", text))


def r2_acf_pooled(shocks, k):
    """Lag-k autocorrelation of squared shocks, pooled over the paths (within a path only)."""
    x = shocks ** 2
    x = x - x.mean()
    return float(np.sum(x[:, :-k] * x[:, k:]) / x[:, :-k].size / np.mean(x * x))


def r2_acf_circular(r, k):
    x = r ** 2
    x = x - x.mean()
    return float(np.dot(x, np.roll(x, -k)) / np.dot(x, x))


def r2_acf_sample(r, k):
    x = r ** 2
    x = x - x.mean()
    return float(np.dot(x[:-k], x[k:]) / np.dot(x, x))


def walk(root):
    yield root
    for child in getattr(root, "controls", None) or []:
        yield from walk(child)
    content = getattr(root, "content", None)
    if isinstance(content, ft.Control):
        yield from walk(content)


class _Offline(unittest.TestCase):
    def setUp(self):
        p = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        p.start(); self.addCleanup(p.stop)


# --------------------------------------------------------------------------- engine facts
class BootstrapEngineTests(_Offline):
    def test_block_constant_is_pinned_to_both_engine_defaults_and_no_call_overrides_it(self):
        self.assertEqual(B, 5)
        for fn in (MC._simulate_bootstrap, MC._bootstrap_correction):
            self.assertEqual(inspect.signature(fn).parameters["block"].default, B, fn.__name__)
        tree = ast.parse(inspect.getsource(MC.run_monte_carlo))
        calls = {"_simulate_bootstrap": [], "_bootstrap_correction": []}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in calls:
                calls[node.func.id].append(node)
        self.assertEqual({k: len(v) for k, v in calls.items()}, {"_simulate_bootstrap": 1, "_bootstrap_correction": 1})
        self.assertEqual(len(calls["_simulate_bootstrap"][0].args), 4)    # rng, r_dm, n_paths, horizon
        self.assertEqual(len(calls["_bootstrap_correction"][0].args), 2)  # r_dm, horizon
        for node in calls["_simulate_bootstrap"] + calls["_bootstrap_correction"]:
            self.assertEqual(node.keywords, [], "run_monte_carlo must not pass a block length")

    def test_blocks_are_fixed_circular_and_start_anywhere(self):
        n, horizon, paths = 37, 23, 3000
        idx = MC._simulate_bootstrap(np.random.default_rng(5), np.arange(n, dtype=float), paths, horizon)
        self.assertEqual(idx.shape, (paths, horizon))
        step = np.diff(idx, axis=1)
        inside = (step % n) == 1                      # the next return of the sample, wrapping
        breaks = np.argwhere(~inside)[:, 1] + 1       # positions where a new block begins
        self.assertTrue(np.all(breaks % B == 0), "a block ends before 5 sessions")
        for pos in range(1, horizon):
            if pos % B:
                self.assertTrue(np.all(inside[:, pos - 1]), f"position {pos} is not inside its block")
        self.assertTrue(np.any(step == -(n - 1)), "no wrap from the sample end to its start")
        starts = idx[:, ::B]
        self.assertEqual(set(np.unique(starts).astype(int)), set(range(n)))   # every return can start a block
        self.assertGreater(np.mean(~inside[:, B - 1::B]), .9)                 # blocks are drawn independently

    def test_clustering_is_kept_only_within_a_block_and_lost_from_lag_5(self):
        h = histories()[0]
        r = h.log_returns(); r_dm = r - r.mean()
        n_paths, horizon = 4000, 125
        mc = MC.run_monte_carlo(h, model="bootstrap", n_paths=n_paths, horizon_days=horizon, drift="zero",
                                seed=11, n_sample_paths=n_paths)
        self.assertEqual(mc.sample_paths.shape, (n_paths, horizon + 1))
        shocks = np.diff(np.log(mc.sample_paths), axis=1)
        self.assertGreater(r2_acf_sample(r_dm, B), 2 / math.sqrt(r.size))   # the sample does cluster at lag 5
        for k in range(1, B):
            circular = r2_acf_circular(r_dm, k)
            paths = r2_acf_pooled(shocks, k)
            self.assertGreater(circular, .1, k)
            self.assertAlmostEqual(paths, (B - k) / B * circular, delta=.01, msg=f"lag {k}")
            self.assertAlmostEqual(paths / circular, (B - k) / B, delta=.05, msg=f"lag {k} retention")
        for k in (B, 2 * B, 4 * B):
            self.assertLess(abs(r2_acf_pooled(shocks, k)), .01, f"lag {k}")
        # (5-k)/5 is the long-horizon value; a short path keeps more ("more over a shorter one").
        short = MC.run_monte_carlo(h, model="bootstrap", n_paths=20000, horizon_days=2 * B, drift="zero",
                                   seed=11, n_sample_paths=20000)
        shocks = np.diff(np.log(short.sample_paths), axis=1)
        for k in range(1, B):
            self.assertGreater(r2_acf_pooled(shocks, k) / r2_acf_circular(r_dm, k), (B - k) / B + .05, f"lag {k}")

    def test_bootstrap_numbers_equal_the_documented_recipe_in_every_drift_mode(self):
        for h in histories():
            for drift in MC.DRIFTS:
                with self.subTest(history=h.symbol, drift=drift):
                    kw = dict(n_paths=600, horizon=37, seed=19, drift=drift, rf=.035, erp=.045)
                    mc = MC.run_monte_carlo(h, model="bootstrap", n_paths=600, horizon_days=37, seed=19,
                                            drift=drift, rf_rate=.035, erp=.045, target=h.last * 1.05)
                    paths, scalars = old_bootstrap_recipe(h, **kw)
                    self.assert_same(fields(mc), derived(paths, h.last, target=h.last * 1.05))
                    for name, value in scalars.items():
                        self.assertEqual(getattr(mc, name), value, name)
                    self.assertEqual((mc.jump_note, mc.bound_note, mc.z_bound, mc.garch), ("", "", None, None))

    def test_other_models_are_assembled_exactly_as_before(self):
        h = histories()[1]
        for model in ("gbm", "jump", "garch_t"):
            for drift in MC.DRIFTS:
                with self.subTest(model=model, drift=drift):
                    mc = MC.run_monte_carlo(h, model=model, n_paths=300, horizon_days=30, seed=23,
                                            drift=drift, rf_rate=.03, erp=.04, target=h.last)
                    paths, scalars = engine_parts(h, model, n_paths=300, horizon=30, seed=23,
                                                  drift=drift, rf=.03, erp=.04)
                    self.assert_same(fields(mc), derived(paths, h.last, target=h.last))
                    for name, value in scalars.items():
                        self.assertEqual(getattr(mc, name), value, name)
                    self.assertIsNone(bootstrap_disclosure(model))

    def test_every_model_matches_the_numbers_pinned_from_a32106b(self):
        h = histories()[1]
        for (model, drift), want in GOLDEN_A32106B.items():
            with self.subTest(model=model, drift=drift):
                mc = MC.run_monte_carlo(h, model=model, n_paths=300, horizon_days=30, seed=23, drift=drift,
                                        rf_rate=.03, erp=.04, target=h.last)
                got = tuple(float(getattr(mc, name)) for name in GOLDEN_NAMES)
                # Tight enough to catch any change of method; loose enough for last-digit libm and
                # optimizer differences between platforms (the GARCH fit is an L-BFGS-B solve).
                rtol = 1e-5 if model == "garch_t" else 1e-9
                np.testing.assert_allclose(got, want, rtol=rtol, atol=1e-12, err_msg=f"{model} {drift}")

    def test_module_docstring_names_the_scheme(self):
        doc = MC.__doc__
        self.assertNotIn("stationary block bootstrap", doc)
        self.assertNotIn("exactly as far as they exist in the data", doc)
        self.assertIn("circular block bootstrap", doc)
        self.assertIn("fixed blocks of 5", doc)
        self.assertIn("not the stationary", doc)
        self.assertIn("kept only within a block", doc)
        self.assertNotIn("only partly kept within a block", doc)

    def assert_same(self, got, want):
        self.assertEqual(set(got), set(want))
        for key in want:
            if key == "fan":
                self.assertEqual(set(got[key]), set(want[key]))
                for p in want[key]:
                    self.assertTrue(np.array_equal(got[key][p], want[key][p]), f"fan {p}")
            elif isinstance(want[key], np.ndarray):
                self.assertTrue(np.array_equal(got[key], want[key]), key)
            else:
                self.assertEqual(got[key], want[key], key)


# --------------------------------------------------------------------------- the disclosure itself
class BootstrapDisclosureTests(_Offline):
    def test_record_is_keyed_on_the_model_id(self):
        info = bootstrap_disclosure("bootstrap")
        self.assertEqual(info, {
            "method": "circular_block_bootstrap", "block_sessions": 5, "block_length": "fixed",
            "resampled": "demeaned_daily_log_returns",
            "within_block_lag_retention": "(5-k)/5 for k=1..4 over a long horizon, more over a short one",
            "clustering_from_lag": 5, "current_vol_level": "not_used", "description": BOOTSTRAP_TEXT})
        for model in ("garch_t", "gbm", "jump", None, "", "BOOTSTRAP"):
            self.assertIsNone(bootstrap_disclosure(model), model)

    def test_text_matches_the_constant_and_the_existing_drift_note(self):
        for needle in (f"fixed {B}-session blocks", f"({B}-k)/{B}", f"lags 1-{B - 1}", f"none is kept from lag {B}",
                       "circular", "demeaned daily log returns", "not a stationary bootstrap",
                       f"over a horizon well beyond {B} sessions (more over a shorter one)",
                       "current volatility level", "drift added on top"):
            self.assertIn(needle, BOOTSTRAP_TEXT)
        for needle in (f"{B}거래일 고정 길이 블록", f"({B}-k)/{B}", f"시차 1-{B - 1}", f"시차 {B}부터",
                       f"분석 기간이 {B}거래일보다 충분히 길 때", "기간이 짧으면 더 많이 남음",
                       "원형", "평균을 뺀", "정상(stationary) 부트스트랩이 아닙니다", "변동성 군집", "팬 차트",
                       "드리프트(추세 가정)를 더합니다"):   # Flet labels the input 드리프트, Native 추세 가정
            self.assertIn(needle, BOOTSTRAP_TEXT_KO)
        self.assertEqual(numbers(BOOTSTRAP_TEXT), numbers(BOOTSTRAP_TEXT_KO))
        for false_claim in ("survives within a block", "outside the sample", "exactly as far as",
                            "larger than any", "only partly kept"):
            self.assertNotIn(false_claim, BOOTSTRAP_TEXT)
        self.assertNotIn("재표본", BOOTSTRAP_TEXT_KO)
        mc = result("bootstrap", "premium")
        self.assertIn("(the empirical block log-MGF of the demeaned sample)", mc.drift_note)

    def test_both_catalogs_carry_the_pair(self):
        self.assertEqual(translate(BOOTSTRAP_TEXT, "ko"), BOOTSTRAP_TEXT_KO)
        self.assertEqual(translate(BOOTSTRAP_TEXT_KO, "en"), BOOTSTRAP_TEXT)
        self.assertEqual(static_text(BOOTSTRAP_TEXT, "ko"), BOOTSTRAP_TEXT_KO)
        self.assertEqual(static_text(BOOTSTRAP_TEXT_KO, "en"), BOOTSTRAP_TEXT)
        self.assertEqual(LocaleContext("ko_KR").text(BOOTSTRAP_TEXT), BOOTSTRAP_TEXT_KO)
        self.assertEqual(LocaleContext("en_US").text(BOOTSTRAP_TEXT_KO), BOOTSTRAP_TEXT)

    def test_narrative_adds_one_sentence_for_bootstrap_only(self):
        for drift in MC.DRIFTS:
            for model in MC.MODELS:
                with self.subTest(model=model, drift=drift):
                    mc = result(model, drift)
                    text = insights.narrate_monte_carlo(mc)
                    with patch.object(insights, "bootstrap_disclosure", return_value=None):
                        without = insights.narrate_monte_carlo(mc)
                    if model == "bootstrap":
                        self.assertEqual(text.count(BOOTSTRAP_TEXT), 1)
                        self.assertEqual(text.replace(" " + BOOTSTRAP_TEXT, "", 1), without)
                        calibration = text.index("historical sample log-return volatility")
                        self.assertLess(calibration, text.index(BOOTSTRAP_TEXT))
                    else:
                        self.assertEqual(text, without)
                        self.assertNotIn("Block bootstrap:", text)


# --------------------------------------------------------------------------- Flet
class FletQuantLabTests(_Offline):
    def build(self, model):
        captured = {}
        mc = result(model)

        def panel(page, **kw):
            captured.update(kw["payload_fn"]())
            return ft.Text("injected AI panel")
        page = Mock(); page.run_thread.side_effect = lambda work: work()
        with patch.object(quant_lab_page, "session_for", return_value=SessionResearch()), \
             patch.object(quant_lab_page, "load_history", return_value=histories()[1]), \
             patch.object(quant_lab_page, "run_monte_carlo", return_value=mc), \
             patch.object(quant_lab_page, "_lab_grade", return_value=None), \
             patch.object(quant_lab_page, "analysis_panel", side_effect=panel):
            root = quant_lab_page.build_quant_lab_page(page); inputs = root.controls[1].controls
            inputs[0].value = "VOL_FIXTURE"; inputs[1].value = "synthetic"
            inputs[2].value = model; inputs[3].value = "zero"; inputs[5].value = "20"; inputs[6].value = "200"
            next(c for c in inputs if isinstance(c, ft.Button)).on_click(None)
        return root, captured, mc

    @staticmethod
    def texts(root):
        return [str(c.value) for c in walk(root) if isinstance(c, ft.Text)]

    def test_text_shows_under_the_drift_note_and_payload_names_the_scheme(self):
        for model in MC.MODELS:
            with self.subTest(model=model):
                root, payload, mc = self.build(model)
                texts = self.texts(root)
                expected_keys = OLD_PAYLOAD_KEYS | {"resampling_definition"} | ({"garch"} if model == "garch_t" else set())
                self.assertEqual(set(payload), expected_keys)
                self.assertEqual(payload["model"], model)
                if model == "bootstrap":
                    self.assertEqual(payload["resampling_definition"], bootstrap_disclosure("bootstrap"))
                    self.assertEqual(payload["resampling_definition"]["block_sessions"], 5)
                    self.assertEqual(texts.index(BOOTSTRAP_TEXT), texts.index(mc.drift_note) + 1)
                    self.assertIn("Block bootstrap (empirical)", texts)          # _MODEL_LABELS unchanged
                else:
                    self.assertIsNone(payload["resampling_definition"])
                    self.assertNotIn(BOOTSTRAP_TEXT, texts)
                self.assertEqual(payload["volatility_definition"]["value"], mc.sigma_annual)

    def test_korean_locale_shows_the_korean_text_and_switches_back(self):
        root, _, _ = self.build("bootstrap")
        translate_controls(root, LocaleContext("ko_KR"))
        texts = self.texts(root)
        self.assertIn(BOOTSTRAP_TEXT_KO, texts)
        self.assertNotIn(BOOTSTRAP_TEXT, texts)
        translate_controls(root, LocaleContext("en_US"))
        texts = self.texts(root)
        self.assertIn(BOOTSTRAP_TEXT, texts)
        self.assertNotIn(BOOTSTRAP_TEXT_KO, texts)


# --------------------------------------------------------------------------- Native
def native_history(*a, **k):
    return histories()[2]


def native_runner(request, run):
    return execute_analysis(request, run, history_loader=native_history,
                            rate_reader=lambda s: (.03, "assumed fixture rate"))


class NativeNotesTests(_Offline):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        super().setUp()
        from quantgen_desktop.app import ResearchWindow
        self.window = ResearchWindow(auto_refresh=False, market_loader=lambda: [], analysis_runner=native_runner)
        self.window.show(); self.app.processEvents()
        self.addCleanup(self.cleanup_window)

    def cleanup_window(self):
        from PyQt6.QtWidgets import QMessageBox
        self.wait_idle()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater(); self.app.processEvents()

    def wait_idle(self):
        from PyQt6.QtTest import QTest
        for _ in range(1500):
            self.app.processEvents()
            if not self.window.jobs.busy:
                return
            QTest.qWait(10)
        self.fail("Worker did not finish in 15 seconds")

    def run_model(self, model):
        w = self.window
        w.symbol.setText("TEST"); w.source.setCurrentIndex(w.source.findData("synthetic"))
        w.model.setCurrentIndex(w.model.findData(model)); w.drift.setCurrentIndex(w.drift.findData("zero"))
        w.paths.setValue(200); w.horizon.setValue(5)
        w.run_analysis(); self.wait_idle()
        return w.session.runs()[0]

    def test_bootstrap_notes_carry_the_text_in_both_languages(self):
        w = self.window
        run = self.run_model("bootstrap")
        self.assertEqual(run["parameters"]["model"], "bootstrap")
        notes = w.quant_notes.source_text.split("\n")
        self.assertEqual(notes.count(BOOTSTRAP_TEXT), 1)
        self.assertIn(BOOTSTRAP_TEXT, w.quant_notes.text())
        w.set_language("ko"); self.app.processEvents()
        self.assertIn(BOOTSTRAP_TEXT_KO, w.quant_notes.text())
        self.assertNotIn(BOOTSTRAP_TEXT, w.quant_notes.text())
        self.assertEqual(w.quant_notes.source_text.split("\n"), notes)     # display only; the source stays
        w.set_language("en"); self.app.processEvents()
        self.assertIn(BOOTSTRAP_TEXT, w.quant_notes.text())
        self.assertEqual(run["verdict"], "NOT_RUN")
        self.assertEqual(set(run["metrics"]), {"spot", "p05", "p50", "p95", "prob_loss", "var_pct", "cvar_pct"})
        self.assertEqual(read_export(export_bytes(run)), run)

    def test_only_the_bootstrap_gains_a_line(self):
        from quantgen_desktop import app as native_app
        w = self.window
        for model in MC.MODELS:
            with self.subTest(model=model):
                self.run_model(model)
                notes = w.quant_notes.source_text
                rows = [(w.quant_metrics.item(i, 0).text(), w.quant_metrics.item(i, 1).text())
                        for i in range(w.quant_metrics.rowCount())]
                with patch.object(native_app, "bootstrap_disclosure", return_value=None):
                    self.run_model(model)
                without = w.quant_notes.source_text
                self.assertEqual(rows, [(w.quant_metrics.item(i, 0).text(), w.quant_metrics.item(i, 1).text())
                                        for i in range(w.quant_metrics.rowCount())])
                if model == "bootstrap":
                    self.assertEqual(notes.replace(BOOTSTRAP_TEXT + "\n", "", 1), without)
                else:
                    self.assertEqual(notes, without)
                    self.assertNotIn(BOOTSTRAP_TEXT, notes)


if __name__ == "__main__":
    unittest.main()
