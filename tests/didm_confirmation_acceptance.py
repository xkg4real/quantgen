"""DIDM-8: market confirmation and macro surprise, PREREG_V0 section 4. Synthetic returns only: every
series is drawn from a seeded generator or written out by hand. No market data, no network, no clock."""
from __future__ import annotations

import ast
import math
import unittest
from pathlib import Path

import numpy as np

from core.didm.llm.schema import MarketConfirmation as MC
from core.didm.models import confirmation as cf
from core.didm.models import surprise as su

ROOT = Path(__file__).resolve().parents[1]
EVENT = 200            # position of day 0 in the synthetic series
SIGMA = 0.01


def series(seed=1, n=260, beta=1.2, alpha=0.0002):
    """Market and asset returns with a known market model; residual SD exactly SIGMA in the estimation window."""
    rng = np.random.default_rng(seed)
    market = 0.01 * rng.standard_normal(n)
    resid = rng.standard_normal(n)
    lo, hi = EVENT + cf.ESTIMATION_FIRST, EVENT + cf.ESTIMATION_LAST + 1
    # make the estimation-window residual orthogonal to the regressors and of the wanted size
    x = np.column_stack([np.ones(hi - lo), market[lo:hi]])
    seg = resid[lo:hi] - x @ np.linalg.lstsq(x, resid[lo:hi], rcond=None)[0]
    resid[lo:hi] = seg * SIGMA * math.sqrt((hi - lo - 2) / float(seg @ seg))
    resid[hi:] = 0.0                                   # the days after the estimation window carry no noise
    return alpha + beta * market + resid, market


def shocked(asset, moves: dict[int, float]):
    out = asset.copy()
    for day, move in moves.items():
        out[EVENT + day] += move
    return out


def run(asset, market, direction=1, known=EVENT + 1):
    return cf.confirm_daily(asset, market, event_index=EVENT, last_known_index=known, predicted_direction=direction)


class RegisteredValues(unittest.TestCase):
    def test_constants_are_the_registered_ones(self):
        self.assertEqual((cf.ESTIMATION_FIRST, cf.ESTIMATION_LAST, cf.ESTIMATION_DAYS), (-125, -6, 120))
        self.assertEqual((cf.EVENT_FIRST, cf.EVENT_LAST), (0, 1))
        self.assertEqual((cf.PRE_FIRST, cf.PRE_LAST), (-5, -1))
        self.assertEqual((cf.SIGMA_MULTIPLE, cf.INTRADAY_WINDOW_MINUTES, su.KALSHI_MIN_VOLUME), (2.0, 60, 1000))
        prereg = (ROOT / "docs" / "didm" / "PREREG_V0.md").read_text(encoding="utf-8")
        for text in ("사건 전 [−125, −6] 거래일 120일로 r_i = α + β·r_m",
                     "기업 [0, +1] 거래일. 거시는 일중 자료가 있으면 [0, +60분], 없으면 [0, +1] 거래일",
                     r"\|AR\| > 2σ (σ = 추정 창 잔차 표준편차, 창 길이에 맞춰 √n배) → CONFIRMED",
                     r"\|CAR[−5, −1]\| > 2σ·√5이고 같은 방향 → ALREADY_PRICED (먼저 판정)",
                     "창이 안 끝났거나 나머지 → PENDING",
                     "거래량 1,000계약 미만 시장은 `liquid = false`",
                     '컨센서스가 있으면 (발표치 − 컨센서스) / 과거 표준편차. 없으면 "미상"'):
            self.assertIn(text, prereg)


class MarketModel(unittest.TestCase):
    def test_recovers_alpha_beta_and_residual_sd(self):
        asset, market = series()
        lo, hi = EVENT + cf.ESTIMATION_FIRST, EVENT + cf.ESTIMATION_LAST + 1
        model = cf.fit_market_model(asset[lo:hi], market[lo:hi])
        self.assertEqual(model.n, 120)
        self.assertAlmostEqual(model.beta, 1.2, places=9)
        self.assertAlmostEqual(model.alpha, 0.0002, places=9)
        self.assertAlmostEqual(model.sigma, SIGMA, places=12)

    def test_bad_estimation_input(self):
        with self.assertRaises(cf.ConfirmationError):
            cf.fit_market_model([0.01, 0.02], [0.01, 0.02])
        with self.assertRaises(cf.ConfirmationError):
            cf.fit_market_model([0.01] * 10, [0.0] * 10)
        with self.assertRaises(cf.ConfirmationError):
            cf.fit_market_model([0.01, float("nan"), 0.0], [0.01, 0.02, 0.03])


class DailyRule(unittest.TestCase):
    """Thresholds: event window 2 * sigma * sqrt(2) = 0.02828; pre-window 2 * sigma * sqrt(5) = 0.04472."""

    def setUp(self):
        self.asset, self.market = series()

    def test_confirmed_and_contradicted(self):
        up = shocked(self.asset, {0: 0.02, 1: 0.01})                      # +0.030 over [0, +1]
        result = run(up, self.market, direction=1)
        self.assertIs(result.status, MC.CONFIRMED)
        self.assertAlmostEqual(result.window_move, 0.03, places=9)
        self.assertAlmostEqual(result.window_threshold, 2 * SIGMA * math.sqrt(2), places=12)
        self.assertIs(run(up, self.market, direction=-1).status, MC.CONTRADICTED)
        down = shocked(self.asset, {0: -0.03})
        self.assertIs(run(down, self.market, direction=-1).status, MC.CONFIRMED)
        self.assertIs(run(down, self.market, direction=1).status, MC.CONTRADICTED)

    def test_threshold_is_two_sigma_scaled_by_root_n_and_strict(self):
        limit = 2 * SIGMA * math.sqrt(2)
        self.assertIs(run(shocked(self.asset, {0: limit - 1e-6}), self.market).status, MC.PENDING)
        self.assertIs(run(shocked(self.asset, {0: limit + 1e-6}), self.market).status, MC.CONFIRMED)
        # one day at 2.5 sigma would pass an unscaled 2-sigma test; over the two-day window it does not
        self.assertIs(run(shocked(self.asset, {0: 2.5 * SIGMA}), self.market).status, MC.PENDING)

    def test_market_move_is_not_an_abnormal_move(self):
        market = self.market.copy()
        asset = self.asset.copy()
        market[EVENT] += 0.05                                              # the index jumps 5%
        asset[EVENT] += 1.2 * 0.05                                         # the asset moves with its beta
        self.assertIs(run(asset, market).status, MC.PENDING)

    def test_already_priced_is_decided_first(self):
        pre_limit = 2 * SIGMA * math.sqrt(5)
        leaked = shocked(self.asset, {-3: 0.03, -2: 0.02, 0: 0.05})        # +0.05 before, +0.05 in the window
        result = run(leaked, self.market, direction=1)
        self.assertIs(result.status, MC.ALREADY_PRICED)
        self.assertAlmostEqual(result.pre_move, 0.05, places=9)
        self.assertAlmostEqual(result.pre_threshold, pre_limit, places=12)
        # a run-up against the prediction is not "already priced"
        self.assertIs(run(leaked, self.market, direction=-1).status, MC.CONTRADICTED)
        # just under the pre-window threshold: the event window decides
        nearly = shocked(self.asset, {-2: pre_limit - 1e-6, 0: 0.05})
        self.assertIs(run(nearly, self.market, direction=1).status, MC.CONFIRMED)
        # decided from the pre-window alone, even before the event window has finished
        self.assertIs(run(leaked, self.market, direction=1, known=EVENT - 1).status, MC.ALREADY_PRICED)
        # day -6 belongs to the estimation window, not to the pre-window
        early = shocked(self.asset, {-6: 0.06})
        self.assertIsNot(run(early, self.market, direction=1).status, MC.ALREADY_PRICED)

    def test_unfinished_window_is_pending_and_later_data_is_never_read(self):
        up = shocked(self.asset, {0: 0.02, 1: 0.02})
        for known in (EVENT - 1, EVENT):
            result = run(up, self.market, known=known)
            self.assertIs(result.status, MC.PENDING)
            self.assertIsNone(result.window_move)
        poisoned = up.copy()
        poisoned[EVENT + 1:] = np.nan                                       # anything after the cut is unreadable
        self.assertEqual(run(poisoned, self.market, known=EVENT), run(up, self.market, known=EVENT))
        self.assertIs(run(up, self.market, known=EVENT + 1).status, MC.CONFIRMED)

    def test_neutral_prediction_and_no_move_are_pending(self):
        up = shocked(self.asset, {0: 0.05})
        self.assertIs(run(up, self.market, direction=0).status, MC.PENDING)
        self.assertIs(run(self.asset, self.market, direction=1).status, MC.PENDING)

    def test_too_little_history_is_pending_not_a_short_estimate(self):
        asset, market = series()
        short = cf.confirm_daily(asset[100:], market[100:], event_index=EVENT - 100, last_known_index=EVENT - 99,
                                 predicted_direction=1)
        self.assertIs(short.status, MC.PENDING)
        self.assertIn("120", short.reason)
        gap = shocked(self.asset, {0: 0.05})
        gap[EVENT - 50] = np.nan
        self.assertIs(run(gap, self.market).status, MC.PENDING)

    def test_bad_arguments(self):
        for kwargs in (dict(event_index=EVENT, last_known_index=EVENT + 1, predicted_direction=2),
                       dict(event_index=EVENT, last_known_index=EVENT + 1, predicted_direction=True),
                       dict(event_index=10_000, last_known_index=EVENT, predicted_direction=1),
                       dict(event_index=EVENT, last_known_index=10_000, predicted_direction=1),
                       dict(event_index=1.5, last_known_index=EVENT, predicted_direction=1)):
            with self.subTest(kwargs=kwargs), self.assertRaises(cf.ConfirmationError):
                cf.confirm_daily(self.asset, self.market, **kwargs)
        with self.assertRaises(cf.ConfirmationError):
            cf.confirm_daily(self.asset, self.market[:-1], event_index=EVENT, last_known_index=EVENT,
                             predicted_direction=1)

    def test_result_is_one_of_the_four_schema_values(self):
        self.assertEqual({m.value for m in MC}, {"CONFIRMED", "CONTRADICTED", "ALREADY_PRICED", "PENDING"})
        self.assertIsInstance(run(self.asset, self.market).status, MC)


class Readings(unittest.TestCase):
    """The two readings that can change a verdict live in config objects; the defaults are unchanged."""

    def test_already_priced_timing(self):
        asset, market = series()
        leaked = shocked(asset, {-3: 0.03, -2: 0.02, 0: 0.05})
        later = cf.ConfirmationConfig(already_priced="after_event_window")
        self.assertEqual(cf.DEFAULT_CONFIG.already_priced, "pre_window_alone")

        def status(known, config=cf.DEFAULT_CONFIG):
            return cf.confirm_daily(leaked, market, event_index=EVENT, last_known_index=known,
                                    predicted_direction=1, config=config).status
        # before the event window has finished the two readings differ ...
        self.assertEqual([status(k) for k in (EVENT - 1, EVENT)], [MC.ALREADY_PRICED, MC.ALREADY_PRICED])
        self.assertEqual([status(k, later) for k in (EVENT - 1, EVENT)], [MC.PENDING, MC.PENDING])
        # ... and once it has finished they agree
        self.assertIs(status(EVENT + 1), MC.ALREADY_PRICED)
        self.assertIs(status(EVENT + 1, later), MC.ALREADY_PRICED)
        clean = shocked(asset, {0: 0.05})
        for config in (cf.DEFAULT_CONFIG, later):
            self.assertIs(cf.confirm_daily(clean, market, event_index=EVENT, last_known_index=EVENT + 1,
                                           predicted_direction=1, config=config).status, MC.CONFIRMED)
        with self.assertRaises(cf.ConfirmationError):
            cf.ConfirmationConfig(already_priced="whenever")

    def test_surprise_scale(self):
        past_surprises = [0.1, -0.1, 0.2, -0.2, 0.1, -0.1, 0.2, -0.2]          # SD 0.169
        past_releases = [2.4, 2.6, 2.9, 3.1, 3.0, 3.2, 3.5, 3.7]              # a trending indicator, SD 0.431
        default = su.macro_surprise(released=3.4, consensus=3.1, past_surprises=past_surprises,
                                    past_releases=past_releases)
        other = su.macro_surprise(released=3.4, consensus=3.1, past_surprises=past_surprises,
                                  past_releases=past_releases, config=su.SurpriseConfig(scale="past_releases"))
        self.assertAlmostEqual(default.value, 1.775, places=3)
        self.assertAlmostEqual(other.value, 0.696, places=3)
        self.assertEqual(su.SurpriseConfig().scale, "past_surprises")
        self.assertEqual(su.SurpriseConfig().min_history, 8)
        short = su.macro_surprise(released=3.4, consensus=3.1, past_surprises=past_surprises[:6],
                                  config=su.SurpriseConfig(min_history=6))
        self.assertEqual(short.kind, su.STANDARDISED)
        for bad in (dict(scale="range"), dict(min_history=1), dict(min_history=True)):
            with self.subTest(bad=bad), self.assertRaises(su.SurpriseError):
                su.SurpriseConfig(**bad)


class IntradayRule(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(3)
        self.past = 0.002 * rng.standard_normal(120)             # past 60-minute moves
        self.sigma = float(self.past.std(ddof=1))

    def judge(self, move, direction=1, pre=None, daily_sigma=None):
        return cf.confirm_intraday(window_move=move, past_window_moves=self.past, pre_daily_move=pre,
                                   daily_sigma=daily_sigma, predicted_direction=direction)

    def test_sixty_minute_move_against_past_sixty_minute_moves(self):
        self.assertIs(self.judge(2.1 * self.sigma).status, MC.CONFIRMED)
        self.assertIs(self.judge(1.9 * self.sigma).status, MC.PENDING)
        self.assertIs(self.judge(-2.1 * self.sigma).status, MC.CONTRADICTED)
        self.assertIs(self.judge(None).status, MC.PENDING)
        self.assertIs(self.judge(5 * self.sigma, direction=0).status, MC.PENDING)

    def test_pre_event_days_still_come_first(self):
        priced = self.judge(3 * self.sigma, pre=0.05, daily_sigma=0.01)       # 0.05 > 2 * 0.01 * sqrt(5)
        self.assertIs(priced.status, MC.ALREADY_PRICED)
        self.assertIs(self.judge(3 * self.sigma, pre=0.04, daily_sigma=0.01).status, MC.CONFIRMED)
        self.assertIs(self.judge(3 * self.sigma, pre=-0.05, daily_sigma=0.01).status, MC.CONFIRMED)

    def test_needs_enough_past_windows(self):
        with self.assertRaises(cf.ConfirmationError):
            cf.confirm_intraday(window_move=0.01, past_window_moves=[0.001] * 5, pre_daily_move=None,
                                daily_sigma=None, predicted_direction=1)


class MacroSurprise(unittest.TestCase):
    PAST = [0.1, -0.1, 0.2, -0.2, 0.1, -0.1, 0.2, -0.2]             # mean 0, sample SD sqrt(0.2 / 7)

    def test_standardised_surprise_by_hand(self):
        sd = math.sqrt(0.2 / 7)
        self.assertAlmostEqual(su.standardised_surprise(3.4, 3.1, self.PAST), 0.3 / sd)
        result = su.macro_surprise(released=3.4, consensus=3.1, past_surprises=self.PAST)
        self.assertEqual(result.kind, su.STANDARDISED)
        self.assertAlmostEqual(result.value, 0.3 / sd)
        self.assertLess(su.macro_surprise(released=2.9, consensus=3.1, past_surprises=self.PAST).value, 0)

    def test_no_consensus_is_unknown_never_filled_in(self):
        move = su.probability_move(0.62, 0.71, 5000)
        result = su.macro_surprise(released=3.4, probability=move)
        self.assertEqual((result.kind, result.value), (su.UNKNOWN, None))
        self.assertAlmostEqual(result.probability.change, 0.09)
        with_history = su.macro_surprise(released=3.4, past_surprises=self.PAST)      # history but no consensus
        self.assertEqual((with_history.kind, with_history.value, with_history.reason), (su.UNKNOWN, None, "no consensus"))
        thin_history = su.macro_surprise(released=3.4, consensus=3.1, past_surprises=self.PAST[:7])
        self.assertEqual((thin_history.kind, thin_history.value), (su.UNKNOWN, None))
        self.assertIsNone(su.macro_surprise(released=3.4).probability)

    def test_liquidity_floor_is_1000_contracts(self):
        self.assertFalse(su.is_liquid(999))
        self.assertTrue(su.is_liquid(1000))
        self.assertTrue(su.is_liquid(250_000))
        for bad in (None, "5000", True, float("nan"), -1):
            self.assertFalse(su.is_liquid(bad), bad)
        thin = su.probability_move(0.2, 0.9, 999)
        self.assertEqual((thin.change, thin.liquid), (None, False))       # a thin market's jump is left out
        self.assertAlmostEqual(su.probability_move(0.2, 0.9, 1000).change, 0.7)

    def test_bad_numbers(self):
        with self.assertRaises(su.SurpriseError):
            su.standardised_surprise(3.4, 3.1, [0.1] * 8)                 # no variation
        with self.assertRaises(su.SurpriseError):
            su.standardised_surprise(float("inf"), 3.1, self.PAST)
        with self.assertRaises(su.SurpriseError):
            su.probability_move(0.2, 1.4, 5000)
        with self.assertRaises(su.SurpriseError):
            su.macro_surprise(released=3.4, probability=0.1)


from datetime import datetime, timedelta, timezone      # noqa: E402  (used by the side-record tests below)

from core.didm.models import confirmation_log as cl     # noqa: E402

T0 = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)
SEAL = "ab" * 32


def entry(status, hours, record_id="art-1/SYN:001", seal=SEAL, config=cf.DEFAULT_CONFIG):
    return cl.make_entry(record_id=record_id, judgement_sha256=seal, status=status, known_at=T0 + timedelta(hours=hours),
                         config=config)


class ConfirmationSideRecord(unittest.TestCase):
    """DIDM-8/a: didm-confirmation-v0. The record is never rewritten; verdicts are appended with the time
    they became known, and a reader only sees what was known at its decision time."""

    def setUp(self):
        self.log = cl.append(cl.append((), entry(MC.PENDING, 0)), entry(MC.CONFIRMED, 48))

    def test_reader_sees_only_what_was_known_at_the_decision(self):
        rid = "art-1/SYN:001"
        self.assertIsNone(cl.as_of(self.log, rid, T0 - timedelta(minutes=1)))
        self.assertIs(cl.status_as_of(self.log, rid, T0 - timedelta(minutes=1)), MC.PENDING)     # unknown = PENDING
        self.assertIs(cl.status_as_of(self.log, rid, T0), MC.PENDING)
        self.assertIs(cl.status_as_of(self.log, rid, T0 + timedelta(hours=47, minutes=59)), MC.PENDING)
        self.assertIs(cl.status_as_of(self.log, rid, T0 + timedelta(hours=48)), MC.CONFIRMED)    # at known_at
        self.assertIs(cl.status_as_of(self.log, rid, T0 + timedelta(days=30)), MC.CONFIRMED)
        self.assertIs(cl.status_as_of(self.log, "another/record", T0 + timedelta(days=30)), MC.PENDING)
        with self.assertRaises(cl.ConfirmationLogError):
            cl.as_of(self.log, rid, datetime(2026, 11, 3, 9, 0))

    def test_a_future_verdict_never_shows_even_if_it_is_already_in_the_log(self):
        future = cl.append(self.log[:1], entry(MC.CONTRADICTED, 24 * 365))
        for hours in (0, 24, 24 * 364):
            self.assertIs(cl.status_as_of(future, "art-1/SYN:001", T0 + timedelta(hours=hours)), MC.PENDING)
        self.assertIs(cl.status_as_of(future, "art-1/SYN:001", T0 + timedelta(hours=24 * 365)), MC.CONTRADICTED)

    def test_append_only(self):
        before = tuple(self.log)
        longer = cl.append(self.log, entry(MC.CONFIRMED, 72))                  # the same verdict again is fine
        self.assertEqual(longer[:2], before)
        self.assertEqual(self.log, before)                                     # the old log object is untouched
        with self.assertRaisesRegex(cl.ConfirmationLogError, "before the record's last entry"):
            cl.append(self.log, entry(MC.CONFIRMED, 24))
        with self.assertRaisesRegex(cl.ConfirmationLogError, "final verdict cannot change"):
            cl.append(self.log, entry(MC.CONTRADICTED, 72))
        with self.assertRaisesRegex(cl.ConfirmationLogError, "final verdict cannot change"):
            cl.append(self.log, entry(MC.PENDING, 72))
        with self.assertRaisesRegex(cl.ConfirmationLogError, "another judgement"):
            cl.append(self.log, entry(MC.CONFIRMED, 72, seal="cd" * 32))
        with self.assertRaises(cl.ConfirmationLogError):
            cl.append(self.log, {"record_id": "x"})
        other = cl.append(self.log, entry(MC.PENDING, 1, record_id="art-2/SYN:002"))     # other records are independent
        self.assertEqual(len(other), 3)

    def test_rule_version_marks_the_reading_and_a_new_rule_is_a_new_line(self):
        later = cf.ConfirmationConfig(already_priced="after_event_window")
        self.assertRegex(cl.rule_version(), r"^conf-rule-[0-9a-f]{16}$")
        self.assertNotEqual(cl.rule_version(), cl.rule_version(later))
        self.assertEqual(self.log[0].rule_version, cl.rule_version())
        both = cl.append(self.log, entry(MC.ALREADY_PRICED, 72, config=later))          # re-evaluated under another rule
        when = T0 + timedelta(days=10)
        self.assertIs(cl.status_as_of(both, "art-1/SYN:001", when, rule=cl.rule_version()), MC.CONFIRMED)
        self.assertIs(cl.status_as_of(both, "art-1/SYN:001", when, rule=cl.rule_version(later)), MC.ALREADY_PRICED)

    def test_line_round_trip_and_field_list(self):
        line = cl.dumps(self.log[1])
        self.assertEqual(cl.loads(line), self.log[1])
        data = __import__("json").loads(line)
        self.assertEqual(tuple(sorted(data)), tuple(sorted(cl.FIELDS)))
        self.assertEqual(data["schema"], "didm-confirmation-v0")
        self.assertEqual(data["window"], {"kind": "daily", "first": 0, "last": 1})
        self.assertEqual(cl.intraday_window(), ("intraday", 0, 60))
        self.assertTrue(data["known_at"].endswith("+00:00"))

    def test_bad_entries_are_rejected_not_repaired(self):
        good = self.log[1].as_dict()
        for change in (dict(schema="didm-confirmation-v1"), dict(status="MAYBE"), dict(known_at="2026-11-04T09:00:00"),
                       dict(known_at=5), dict(record_id="bad id"), dict(judgement_sha256="xyz"),
                       dict(rule_version="rule-1"), dict(window={"kind": "weekly", "first": 0, "last": 1}),
                       dict(window={"kind": "daily", "first": 1, "last": 0}),
                       dict(window={"kind": "daily", "first": 0}), dict(extra=1)):
            with self.subTest(change=change), self.assertRaises(cl.ConfirmationLogError):
                cl.validate_entry(dict(good, **change))
        with self.assertRaises(cl.ConfirmationLogError):
            cl.validate_entry({k: v for k, v in good.items() if k != "known_at"})
        with self.assertRaises(cl.ConfirmationLogError):
            cl.loads("not json")


class Boundaries(unittest.TestCase):
    ALLOWED = {"core/didm/models/confirmation.py": ("__future__", "math", "dataclasses", "typing", "numpy",
                                                    "core.didm.llm.schema"),
               "core/didm/models/confirmation_log.py": ("__future__", "hashlib", "json", "re", "dataclasses", "datetime",
                                                        "typing", "core.didm.llm.schema", "core.didm.models"),
               "core/didm/models/surprise.py": ("__future__", "math", "dataclasses", "typing")}

    def test_reads_no_price_source_network_or_clock(self):
        for rel, allowed in self.ALLOWED.items():
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertIn(a.name, allowed, f"{rel} imports {a.name}")
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, allowed, f"{rel} imports {node.module}")
                elif isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("now", "today", "utcnow", "import_module"), rel)
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, ("open", "__import__", "exec", "eval"), rel)


if __name__ == "__main__":
    unittest.main()
