"""Synthetic acceptance for core/adoption/strategy_rules.py (roadmap ⑨-4/2/a; criteria 4.2.2 S-2, S-3, S-4, S-7).

Every input is a seeded synthetic array built here. No ledger, card, register, price file, cache, configuration,
environment, provider or network is used. Gate functions are called directly as the golden reference; where an
edge needs an exact p or DSR value, the gate function is replaced by a stub for that one call (unittest.mock).
"""
import ast
import copy
from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

import numpy as np

from core.adoption import strategy_rules as S
from core.quant import gate_stats as GS
from core.quant import validate as V

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "core" / "adoption"
MODULE = PACKAGE / "strategy_rules.py"

_RECORD = {"active": False, "thread": None, "events": []}
_WATCHED = ("open", "socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system", "os.listdir",
            "os.scandir", "os.remove", "os.rename", "os.mkdir")


def _recorder(event, args):
    if _RECORD["active"] and event in _WATCHED and threading.get_ident() == _RECORD["thread"]:
        _RECORD["events"].append((event, repr(args)[:160]))


sys.addaudithook(_recorder)        # inert until a test sets "active", and then only for that test's thread


def sessions(n, start=date(2015, 1, 2)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def pair(T=756, seed=3, edge=0.0001, noise=0.0025):
    """A challenger close to its incumbent (correlation about 0.97) plus a daily edge."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0003, 0.01, T)
    return base + rng.normal(0.0, noise, T) + edge, base


def code_only(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def fake_boot(d_sr, count, B=2000):
    def run(a, b, block, B=B, seed=11, **_):
        return {"dSR": d_sr, "se": 0.1, "se_nw10": 0.1, "t_obs": d_sr / 0.1, "p_lw": GS.pstr(count, B),
                "count": count, "p_hac": 0.5, "block": block, "n_blocks": 1, "B": B, "seed": seed, "null": 0.0,
                "ci": (0.0, 0.0), "level": 0.9}
    return run


class GoldenEquality(unittest.TestCase):
    def test_s2_values_equal_direct_validate_calls(self):
        a, _ = pair(T=1260, seed=5, edge=0.0004)
        res = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.012, sr_sd_label="synthetic")
        self.assertEqual(res.dsr_grid, V.deflated_sharpe(a, n_trials=12, sr_sd_daily=0.012))
        by = {r.reading: r for r in res.readings}
        self.assertEqual(by["L-FAM"].dsr, V.deflated_sharpe(a, n_trials=17, sr_sd_daily=0.012))
        self.assertEqual(by["R-FAM"].dsr, V.deflated_sharpe(a, n_trials=11, sr_sd_daily=0.012))
        self.assertEqual(res.dsr_min, V.GATE["dsr_min"])
        self.assertEqual(res.n_sessions, 1260)

    def test_s2_with_gate_dispersion_reproduces_score_strategy_dsr(self):
        T, G = 1400, 4
        rng = np.random.default_rng(21)
        common = rng.normal(0.0004, 0.01, T)
        full = np.column_stack([common + rng.normal(0.0, 0.004, T) + 0.0001 * g for g in range(G)])
        dates = [d.isoformat() for d in sessions(T)]
        wf = V.walk_forward(full, dates)
        grid = [{"lookback": g} for g in range(G)]
        score = V.score_strategy(wf, grid=grid, full_pnl=full, n_trials=G)
        sd = S.gate_sr_sd_daily(full)
        res = S.dsr_two_n(wf.pnl, n_grid=G, n_raw={"L-FAM": G}, sr_sd_daily=sd, sr_sd_label="gate term")
        self.assertTrue(math.isfinite(score.dsr))
        self.assertAlmostEqual(res.dsr_grid, score.dsr, places=12)
        cols = V._col_sharpe(full) / math.sqrt(V.TRADING_DAYS)
        self.assertAlmostEqual(sd, float(np.nanstd(cols)), places=14)

    def test_s3_s4_equal_direct_gate_stats_calls_and_seed_passes_through(self):
        a, b = pair()
        ds = sessions(a.size)
        for seed in (None, 12):
            got = S.lw_compare(a, b, ds, ds, rule="S-3", other_label="incumbent", seed=seed)
            log = []
            block = GS.pw_block_psi(a, b, log=log)
            use_seed = GS.SEED_STUDY if seed is None else seed
            ref = GS.lw_studentized_boot(a, b, block, B=V.GATE["bootstrap_B"], seed=use_seed)
            self.assertEqual((got.block, got.B, got.seed), (block, V.GATE["bootstrap_B"], use_seed))
            self.assertEqual((got.d_sr, got.se, got.t_obs, got.count, got.p_hac),
                             (ref["dSR"], ref["se"], ref["t_obs"], ref["count"], ref["p_hac"]))
            self.assertEqual(got.p_lw, ref["p_lw"])
            self.assertEqual(got.p, GS.p_numeric(ref["p_lw"], ref["B"]))
            self.assertEqual(got.status, S.classify_comparison(ref["dSR"], got.p))
        self.assertEqual((S.ALPHA_ONE_SIDED, S.BORDERLINE_P_MAX, S.DSR_BORDERLINE_MIN), (0.10, 0.20, 0.90))
        self.assertEqual(GS.SEED_STUDY, 11)
        self.assertEqual(V.GATE["bootstrap_B"], 2000)

    def test_s7_equals_direct_lw_hac_se(self):
        a, b = pair()
        ds = sessions(a.size)
        hac = GS.lw_hac_se(a, b)
        got = S.power_line_s7(a, b, ds, ds, expected_dsr=0.2)
        self.assertEqual((got.se, got.se_nw10), (hac.se, hac.se_nw10))
        self.assertEqual(got.mde80, GS.MDE_FACTOR * hac.se)
        self.assertEqual(got.underpowered_vs_expected, GS.MDE_FACTOR * hac.se > 0.2)
        self.assertTrue(got.printed_only)
        self.assertEqual((got.rule, got.status), ("S-7", "printed"))
        low = S.power_line_s7(a, b, ds, ds, expected_dsr=got.mde80 / 2)
        high = S.power_line_s7(a, b, ds, ds, expected_dsr=got.mde80 * 2)
        self.assertTrue(low.underpowered_vs_expected)
        self.assertFalse(high.underpowered_vs_expected)
        self.assertIn("printed only", low.line())


class DirectionAndPValues(unittest.TestCase):
    def test_one_sided_direction(self):
        a, b = pair(T=1260, seed=7, edge=0.0008)
        ds = sessions(a.size)
        better = S.lw_compare(a, b, ds, ds, rule="S-3", other_label="incumbent")
        worse = S.lw_compare(b, a, ds, ds, rule="S-3", other_label="incumbent")
        self.assertGreater(better.d_sr, 0)
        self.assertEqual(better.status, "win")
        self.assertLess(worse.d_sr, 0)
        self.assertEqual(worse.status, "not_won")
        self.assertGreater(worse.p, 0.5)
        self.assertAlmostEqual(better.d_sr, -worse.d_sr, places=12)

    def test_p_printed_below_one_over_b_compares_as_one_over_b(self):
        a, b = pair(T=1260, seed=7, edge=0.0008)
        ds = sessions(a.size)
        got = S.lw_compare(a, b, ds, ds, rule="S-4", other_label="SMA-200", B=400)
        self.assertEqual(got.count, 0)
        self.assertEqual(got.p_lw, GS.P_FLOOR)
        self.assertEqual(got.p, 1.0 / 400)
        self.assertEqual(got.status, "win")
        self.assertIn("< 1/B", got.line())

    def test_comparison_edges_at_0p10_and_0p20(self):
        cases = [(0.3, 0.10, "win"), (0.3, math.nextafter(0.10, 1.0), "borderline"), (0.3, 0.20, "borderline"),
                 (0.3, math.nextafter(0.20, 1.0), "not_won"), (0.3, 0.0005, "win"), (0.3, 1.0, "not_won"),
                 (-0.3, 0.01, "not_won"), (0.0, 0.01, "not_won"), (-0.1, 0.15, "not_won")]
        for d_sr, p, want in cases:
            with self.subTest(d_sr=d_sr, p=p):
                self.assertEqual(S.classify_comparison(d_sr, p), want)
        for bad in ((float("nan"), 0.1), (0.1, float("nan")), (0.1, -0.01), (0.1, 1.01)):
            with self.subTest(bad=bad):
                with self.assertRaises(S.AdoptionInputError):
                    S.classify_comparison(*bad)

    def test_edges_through_lw_compare_with_resample_counts(self):
        a, b = pair()
        ds = sessions(a.size)
        for count, want in ((0, "win"), (200, "win"), (201, "borderline"), (400, "borderline"), (401, "not_won")):
            with self.subTest(count=count), patch.object(GS, "lw_studentized_boot", side_effect=fake_boot(0.3, count)):
                got = S.lw_compare(a, b, ds, ds, rule="S-4", other_label="baseline")
                self.assertEqual(got.status, want)
                self.assertEqual(got.p, 1.0 / 2000 if count == 0 else count / 2000)
        with patch.object(GS, "lw_studentized_boot", side_effect=fake_boot(-0.3, 10)):
            self.assertEqual(S.lw_compare(a, b, ds, ds, rule="S-4", other_label="baseline").status, "not_won")

    def test_not_run_when_the_statistic_is_undefined(self):
        a, b = pair()
        ds = sessions(a.size)
        same = S.lw_compare(b, b.copy(), ds, ds, rule="S-4", other_label="itself")
        self.assertEqual(same.status, "not_run")
        self.assertIn("HAC SE is zero", same.reason)
        self.assertIsNone(same.p_lw)
        self.assertIn("NOT_RUN", same.line())
        short = S.lw_compare(a[:20], b[:20], ds[:20], ds[:20], rule="S-4", other_label="short")
        self.assertEqual(short.status, "not_run")
        self.assertEqual(short.block_events[0][:2], ("pw_block_psi_fallback", GS.BLOCK_FALLBACK))
        self.assertIn(">= 30", short.reason)
        power = S.power_line_s7(b, b.copy(), ds, ds, expected_dsr=0.1)
        self.assertEqual(power.status, "not_run")


class DsrLines(unittest.TestCase):
    def test_dsr_edges_at_0p90_and_0p95(self):
        dmin = V.GATE["dsr_min"]
        self.assertEqual(dmin, 0.95)
        cases = [(0.95, None, "pass"), (math.nextafter(0.95, 0.0), None, "below"), (0.95, "pass", "pass"),
                 (math.nextafter(0.95, 0.0), "pass", "borderline"), (0.90, "pass", "borderline"),
                 (math.nextafter(0.90, 0.0), "pass", "below"), (0.92, "below", "below"), (0.92, "nan", "below"),
                 (float("nan"), None, "nan"), (float("nan"), "pass", "nan"), (1.0, "below", "pass")]
        for value, grid, want in cases:
            with self.subTest(value=value, grid=grid):
                self.assertEqual(S.classify_dsr(value, grid_status=grid), want)

    def test_dsr_edges_through_dsr_two_n(self):
        a, _ = pair()
        values = {12: 0.95, 17: 0.90, 11: math.nextafter(0.90, 0.0)}
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            res = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.01, sr_sd_label="x")
        by = {r.reading: r.status for r in res.readings}
        self.assertEqual((res.status_grid, by["L-FAM"], by["R-FAM"]), ("pass", "borderline", "below"))
        values = {12: math.nextafter(0.95, 0.0), 17: 0.93, 11: 0.96}
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            res = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.01, sr_sd_label="x")
        by = {r.reading: r.status for r in res.readings}
        self.assertEqual((res.status_grid, by["L-FAM"], by["R-FAM"]), ("below", "below", "pass"))

    def test_n_raw_below_grid_is_printed_not_refused(self):
        a, _ = pair()
        res = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 8}, sr_sd_daily=0.01, sr_sd_label="x")
        by = {r.reading: r for r in res.readings}
        self.assertTrue(by["L-FAM"].below_grid)
        self.assertEqual(by["L-FAM"].dsr, V.deflated_sharpe(a, n_trials=8, sr_sd_daily=0.01))
        text = "\n".join(res.lines())
        self.assertIn("N_raw 8 < G 12: printed only", text)
        self.assertIn("10.2 B Q4", text)
        equal = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 12}, sr_sd_daily=0.01, sr_sd_label="x")
        self.assertFalse(any(r.below_grid for r in equal.readings))

    def test_both_readings_displayed_provisional_and_labelled(self):
        a, _ = pair()
        one = S.dsr_two_n(a, n_grid=5, n_raw={"R-FAM": 9}, sr_sd_daily=0.0, sr_sd_label="caller term A")
        self.assertEqual([r.reading for r in one.readings], ["L-FAM", "R-FAM"])
        self.assertEqual(one.readings[0].status, "not_supplied")
        self.assertIsNone(one.readings[0].n_raw)
        text = "\n".join(one.lines())
        self.assertIn("L-FAM", text)
        self.assertIn("not supplied", text)
        self.assertIn("[caller term A]", text)
        self.assertTrue(one.provisional)
        self.assertTrue(all("[provisional]" in line for line in one.lines() if line.startswith("S-2")))
        self.assertIn("⑨-3d", text)
        self.assertEqual(one.rule, "S-2")

    def test_counts_and_dispersion_inputs_refused(self):
        a, _ = pair()
        good = dict(n_grid=12, n_raw={"L-FAM": 17}, sr_sd_daily=0.01, sr_sd_label="x")
        bad = [dict(n_grid=0), dict(n_grid=-3), dict(n_grid=12.0), dict(n_grid=True), dict(n_grid="12"),
               dict(n_raw={}), dict(n_raw={"L-FAM": 0}), dict(n_raw={"L-FAM": 17.0}), dict(n_raw={"L-FAM": False}),
               dict(n_raw={"ledger": 17}), dict(n_raw=17), dict(n_raw=[("L-FAM", 17)]),
               dict(sr_sd_daily=-0.01), dict(sr_sd_daily=float("nan")), dict(sr_sd_daily=float("inf")),
               dict(sr_sd_daily=None), dict(sr_sd_label=""), dict(sr_sd_label="  "), dict(sr_sd_label=None)]
        for change in bad:
            with self.subTest(change=change):
                with self.assertRaises(S.AdoptionInputError):
                    S.dsr_two_n(a, **{**good, **change})
        with self.assertRaises(S.AdoptionInputError):
            S.dsr_two_n(np.array([0.01, float("nan"), 0.02]), **good)
        with self.assertRaises(S.AdoptionInputError):
            S.dsr_two_n(np.ones((3, 2)), **good)
        self.assertEqual(S.dsr_two_n(a, **{**good, "n_grid": np.int64(12)}).n_grid, 12)

    def test_nan_dsr_does_not_meet_s2(self):
        short = S.dsr_two_n(np.array([0.01, 0.02]), n_grid=1, n_raw={"L-FAM": 1}, sr_sd_daily=0.0, sr_sd_label="x")
        self.assertTrue(math.isnan(V.deflated_sharpe(np.array([0.01, 0.02]), n_trials=1, sr_sd_daily=0.0)))
        self.assertEqual(short.status_grid, "nan")
        self.assertEqual(short.readings[0].status, "nan")
        self.assertIn("a NaN DSR does not meet S-2 (criteria 6.4, N12)", short.lines())
        a, _ = pair()
        values = {12: 0.97, 17: float("nan")}
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            res = S.dsr_two_n(a, n_grid=12, n_raw={"L-FAM": 17}, sr_sd_daily=0.01, sr_sd_label="x")
        self.assertEqual((res.status_grid, res.readings[0].status), ("pass", "nan"))
        self.assertIn("(nan)", res.lines()[1])

    def test_gate_dispersion_helper_refuses_bad_matrices(self):
        for bad in (np.ones(5), np.ones((1, 3)), np.ones((4, 0)), np.array([[0.1, float("nan")], [0.2, 0.3]])):
            with self.subTest(shape=np.shape(bad)):
                with self.assertRaises(S.AdoptionInputError):
                    S.gate_sr_sd_daily(bad)
        self.assertEqual(S.gate_sr_sd_daily(np.arange(10.0).reshape(10, 1)), 0.0)


class SessionsAndHoldout(unittest.TestCase):
    def test_holdout_boundary(self):
        last_ok = S.check_sample_end(date(2026, 12, 31))
        self.assertEqual((last_ok.holdout_touched, last_ok.adopt_allowed), (False, True))
        first_bad = S.check_sample_end("2027-01-01")
        self.assertEqual((first_bad.holdout_touched, first_bad.adopt_allowed), (True, False))
        self.assertIn("HOLDOUT_TOUCHED", first_bad.line())
        self.assertEqual(S.check_sample_end("2026-12-31").last_session, date(2026, 12, 31))
        self.assertEqual(S.HOLDOUT_LAST_SESSION, date(2026, 12, 31))
        for bad in (datetime(2026, 12, 31, 9, 0), "2026/12/31", "", 20261231, None):
            with self.subTest(bad=bad):
                with self.assertRaises(S.AdoptionInputError):
                    S.check_sample_end(bad)

    def test_misaligned_or_malformed_sessions_refused(self):
        a, b = pair(T=60)
        ds = sessions(60)
        shifted = ds[1:] + (ds[-1] + timedelta(days=7),)
        duplicate = ds[:30] + (ds[29],) + ds[31:]
        backwards = tuple(reversed(ds))
        monday = next(i for i in range(1, 60) if ds[i].weekday() == 0)
        sunday = ds[:monday] + (ds[monday] - timedelta(days=1),) + ds[monday + 1:]
        cases = [
            (a, b[:-1], ds, ds[:-1], "unequal sessions"),
            (a, b, ds, shifted, "misaligned sessions at index 0"),
            (a, b, ds, sunday, f"misaligned sessions at index {monday}"),
            (a, b, ds, duplicate, "strictly increasing"),
            (a, b, backwards, backwards, "strictly increasing"),
            (a, b[:-1], ds, ds, "59 values but 60 sessions"),
            (a, np.where(np.arange(60) == 5, np.inf, b), ds, ds, "non-finite"),
            (a.reshape(30, 2), b, ds, ds, "one-dimensional"),
            (a, b, "2015-01-02", ds, "sequence of sessions"),
            (a, b, [d.isoformat() for d in ds[:-1]] + ["bad"], ds, "ISO date"),
            (a[:0], b[:0], (), (), "no sessions"),
            (["x"] * 60, b, ds, ds, "numeric daily P&L"),
        ]
        for x_a, x_b, d_a, d_b, needle in cases:
            with self.subTest(needle=needle):
                with self.assertRaisesRegex(S.AdoptionInputError, re.escape(needle)):
                    S.lw_compare(x_a, x_b, d_a, d_b, rule="S-4", other_label="baseline")
        iso = S.lw_compare(a, b, [d.isoformat() for d in ds], ds, rule="S-4", other_label="baseline")
        self.assertEqual(iso.n_sessions, 60)
        with self.assertRaisesRegex(S.AdoptionInputError, "misaligned"):
            S.power_line_s7(a, b, ds, shifted, expected_dsr=0.2)
        for bad in (dict(rule="S-5"), dict(other_label=""), dict(B=0), dict(B=2000.0), dict(seed=-1), dict(seed=1.5)):
            with self.subTest(bad=bad):
                kwargs = {**dict(rule="S-4", other_label="baseline"), **bad}
                with self.assertRaises(S.AdoptionInputError):
                    S.lw_compare(a, b, ds, ds, **kwargs)
        with self.assertRaises(S.AdoptionInputError):
            S.power_line_s7(a, b, ds, ds, expected_dsr=0.0)


class CollectedLines(unittest.TestCase):
    def setUp(self):
        self.a, self.inc = pair(T=756, seed=5, edge=0.0002)
        self.ds = sessions(756)
        rng = np.random.default_rng(9)
        self.base = {"equal-weight": (rng.normal(0.0002, 0.008, 756), self.ds),
                     "SMA-200": (rng.normal(0.0001, 0.007, 756), [d.isoformat() for d in self.ds])}
        self.common = dict(challenger=self.a, challenger_dates=self.ds, n_grid=12, n_raw={"L-FAM": 17},
                           sr_sd_daily=0.01, sr_sd_label="caller term", baselines=self.base)

    def test_replace_runs_s2_s3_s4_s7_without_an_outcome(self):
        res = S.strategy_lines(kind="replace", incumbent=self.inc, incumbent_dates=self.ds, expected_dsr=0.25,
                               **self.common)
        self.assertEqual(res.kind, "replace")
        self.assertEqual((res.s3.rule, res.s3.counts), ("S-3", True))
        self.assertEqual([c.other for c in res.s4], ["equal-weight", "SMA-200"])
        self.assertTrue(all(c.rule == "S-4" and c.counts for c in res.s4))
        self.assertEqual(res.s7.rule, "S-7")
        self.assertEqual(res.s2.rule, "S-2")
        self.assertEqual(res.l1_note, "L1 미적용(브리지 미지원)")
        self.assertTrue(res.provisional)
        self.assertEqual(res.unit, "⑨-4/2/a")
        lines = res.lines()
        self.assertIn("L1 미적용(브리지 미지원)", lines[0])
        self.assertFalse(res.sample_end.holdout_touched)
        names = {f.name for f in fields(res)}
        self.assertFalse(names & {"outcome", "decision", "verdict", "adopt", "keep", "result"})
        for line in lines:
            self.assertIsNone(re.search(r"\b(ADOPT|KEEP|REVISE|REJECT|INSUFFICIENT_DATA|PASS)\b", line), line)
        direct = S.lw_compare(self.a, self.inc, self.ds, self.ds, rule="S-3", other_label="incumbent")
        self.assertEqual((res.s3.d_sr, res.s3.p_lw, res.s3.status), (direct.d_sr, direct.p_lw, direct.status))
        self.assertTrue(all(c.status in S.COMPARISON_STATUSES for c in (res.s3,) + res.s4))
        self.assertTrue(all(r.status in S.DSR_STATUSES for r in res.s2.readings))
        self.assertIn(res.s2.status_grid, S.DSR_STATUSES)

    def test_add_prints_the_incumbent_comparison_only(self):
        res = S.strategy_lines(kind="add", incumbent=self.inc, incumbent_dates=self.ds, **self.common)
        self.assertFalse(res.s3.counts)
        self.assertIn("printed only, addition (M-19)", res.s3.line())
        self.assertIsNone(res.s7)
        bare = S.strategy_lines(kind="add", **self.common)
        self.assertIsNone(bare.s3)
        self.assertEqual(len(bare.s4), 2)

    def test_registration_fields_refused_when_missing(self):
        with self.assertRaisesRegex(S.AdoptionInputError, "incumbent"):
            S.strategy_lines(kind="replace", expected_dsr=0.25, **self.common)
        with self.assertRaisesRegex(S.AdoptionInputError, "expected dSR"):
            S.strategy_lines(kind="replace", incumbent=self.inc, incumbent_dates=self.ds, **self.common)
        with self.assertRaisesRegex(S.AdoptionInputError, "baseline"):
            S.strategy_lines(kind="add", **{**self.common, "baselines": {}})
        with self.assertRaisesRegex(S.AdoptionInputError, "daily_pnl, sessions"):
            S.strategy_lines(kind="add", **{**self.common, "baselines": {"cash": self.a}})
        with self.assertRaisesRegex(S.AdoptionInputError, "kind"):
            S.strategy_lines(kind="swap", **self.common)
        with self.assertRaisesRegex(S.AdoptionInputError, "go together"):
            S.strategy_lines(kind="add", incumbent=self.inc, **self.common)
        with self.assertRaisesRegex(S.AdoptionInputError, "misaligned"):
            S.strategy_lines(kind="add", **{**self.common, "baselines": {"cash": (self.a, sessions(756, date(2015, 1, 5)))}})
        with self.assertRaisesRegex(S.AdoptionInputError, "values and sessions differ"):
            S.strategy_lines(kind="add", **{**self.common, "challenger": self.a[:-1]})

    def test_holdout_read_from_the_challenger_sessions(self):
        late = sessions(756, date(2024, 6, 3))
        self.assertGreater(late[-1], date(2026, 12, 31))
        base = {"cash": (np.full(756, 0.0001) + np.random.default_rng(1).normal(0, 1e-4, 756), late)}
        res = S.strategy_lines(kind="add", challenger=self.a, challenger_dates=late, n_grid=3, n_raw={"R-FAM": 3},
                               sr_sd_daily=0.0, sr_sd_label="x", baselines=base)
        self.assertTrue(res.sample_end.holdout_touched)
        self.assertFalse(res.sample_end.adopt_allowed)
        self.assertIn("HOLDOUT_TOUCHED", res.lines()[1])

    def test_results_are_immutable(self):
        res = S.strategy_lines(kind="replace", incumbent=self.inc, incumbent_dates=self.ds, expected_dsr=0.25,
                               **self.common)
        for obj, name in ((res, "kind"), (res.s2, "dsr_grid"), (res.s3, "status"), (res.s4[0], "p"),
                          (res.s7, "mde80"), (res.sample_end, "adopt_allowed"), (res.s2.readings[0], "status")):
            with self.subTest(obj=type(obj).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(obj, name, None)
        for value in (res.s4, res.s2.readings, res.s2.notes, res.notes, res.s3.block_events):
            self.assertIsInstance(value, tuple)
        with self.assertRaises(TypeError):
            S.N_RAW_READINGS["X-FAM"] = "x"


class ScopeGuards(unittest.TestCase):
    def test_no_file_network_or_process_effects(self):
        a, inc = pair()
        ds = sessions(a.size)
        base = {"equal-weight": (np.random.default_rng(2).normal(0.0002, 0.008, a.size), ds)}

        def run_all():
            S.check_sample_end("2026-06-30")
            S.gate_sr_sd_daily(np.column_stack([a, inc]))
            S.strategy_lines(kind="replace", challenger=a, challenger_dates=ds, n_grid=4, n_raw={"L-FAM": 6, "R-FAM": 5},
                             sr_sd_daily=0.01, sr_sd_label="x", baselines=base, incumbent=inc, incumbent_dates=ds,
                             expected_dsr=0.2, B=200)
            S.lw_compare(a[:20], inc[:20], ds[:20], ds[:20], rule="S-4", other_label="short")
            S.lw_compare(inc, inc.copy(), ds, ds, rule="S-4", other_label="itself", B=200)

        run_all()                          # warm lazy imports inside numpy / scipy first
        gate_before = copy.deepcopy(V.GATE)
        functions_before = (V.deflated_sharpe, V.sharpe, GS.lw_studentized_boot, GS.pw_block_psi, GS.lw_hac_se,
                            GS.p_numeric, GS.MDE_FACTOR, GS.SEED_STUDY)
        _RECORD["events"].clear()
        _RECORD["thread"] = threading.get_ident()
        _RECORD["active"] = True
        try:
            run_all()
        finally:
            _RECORD["active"] = False
        self.assertEqual(_RECORD["events"], [])
        self.assertEqual(V.GATE, gate_before)
        self.assertEqual(functions_before, (V.deflated_sharpe, V.sharpe, GS.lw_studentized_boot, GS.pw_block_psi,
                                            GS.lw_hac_se, GS.p_numeric, GS.MDE_FACTOR, GS.SEED_STUDY))

    def test_isolated_import_loads_no_strategies_history_config_or_env(self):
        script = r'''
import json, os, sys
root = sys.argv[1]
def guard(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise PermissionError("network refused")
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.abspath(os.fsdecode(args[0])).replace("\\", "/")
        if "asset_expansion/cache" in path or any(p.startswith(".env") for p in path.split("/")):
            raise PermissionError("protected path refused")
sys.addaudithook(guard)
sys.path.insert(0, root)
import core.adoption.strategy_rules as S
loaded = sorted(m for m in sys.modules if m in ("config", "dotenv", "core") or m.startswith("core."))
print(json.dumps({"loaded": loaded, "file": os.path.abspath(S.__file__)}))
'''
        proc = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(ROOT)], capture_output=True, text=True,
                              timeout=180, cwd=str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        out = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(Path(out["file"]).resolve(), MODULE.resolve())
        self.assertEqual(set(out["loaded"]), {"core", "core.quant", "core.quant.validate", "core.quant.gate_stats",
                                              "core.adoption", "core.adoption.strategy_rules"})

    def test_module_imports_only_validate_and_gate_stats(self):
        for path in (MODULE, PACKAGE / "__init__.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            mods |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "core.quant"
                     for a in n.names}
            if path == MODULE:
                self.assertEqual(mods, {"__future__", "math", "collections.abc", "dataclasses", "datetime", "types",
                                        "typing", "numpy", "core.quant"})
                self.assertEqual(names, {"validate", "gate_stats"})
            else:
                self.assertEqual(mods, set())
        self.assertEqual(sorted(p.name for p in PACKAGE.glob("*.py")), ["__init__.py", "strategy_rules.py"])

    def test_module_never_edits_or_monkeypatches_the_gate(self):
        tree = ast.parse(code_only(MODULE))
        bad = []
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, (ast.Assign, ast.Delete)):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for t in targets:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Subscript) and re.search(r"\b(GATE|V|GS|STATS)\b", ast.unparse(sub.value)):
                        bad.append(ast.unparse(t))
                    if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id in ("V", "GS"):
                        bad.append(ast.unparse(t))
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                bad.append("global/nonlocal")
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name) and f.id in ("setattr", "delattr", "exec", "eval", "open", "__import__"):
                    bad.append(f.id)
                if (isinstance(f, ast.Attribute) and f.attr in ("update", "pop", "popitem", "clear", "setdefault",
                                                                 "__setitem__", "__delitem__")
                        and re.search(r"\b(GATE|V|GS|STATS)\b", ast.unparse(f.value))):
                    bad.append(ast.unparse(f))
        self.assertEqual(bad, [])
        numbers = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                   and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)}
        self.assertFalse(numbers & {0.95, 2000, 11, 2.1232, 21, 250, 1.2816, 0.05, 0.6}, numbers)
        text = code_only(MODULE)
        for attr in ("GATE['dsr_min']", "GATE['bootstrap_B']", "SEED_STUDY", "MDE_FACTOR", "pw_block_psi",
                     "lw_studentized_boot", "p_numeric", "lw_hac_se", "deflated_sharpe"):
            self.assertIn(attr, text)

    def test_docstrings_map_each_check_to_rule_ids_and_rulings(self):
        want = {"check_sample_end": ("4.0 rule 6", "M-14"), "classify_dsr": ("S-2", "M-3"),
                "gate_sr_sd_daily": ("S-2", "M-3"), "dsr_two_n": ("S-2", "M-3"),
                "classify_comparison": ("S-3", "M-2"), "lw_compare": ("S-4", "M-6"),
                "power_line_s7": ("S-7", "M-6"), "strategy_lines": ("M-19", "M-20")}
        public = {n for n in dir(S) if callable(getattr(S, n)) and not n.startswith("_")
                  and getattr(getattr(S, n), "__module__", "") == S.__name__ and not isinstance(getattr(S, n), type)}
        self.assertEqual(public, set(want))
        for name, tokens in want.items():
            doc = getattr(S, name).__doc__ or ""
            for token in tokens:
                with self.subTest(function=name, token=token):
                    self.assertIn(token, doc)
        self.assertIn("MODEL_ADOPTION_CRITERIA_DRAFT_2026-11-04.md", S.__doc__)
        self.assertIn("M-21", S.__doc__)

    def test_no_forbidden_counting_shapes(self):
        from core.quant import gate_ledger as GL
        sources = {}
        for path in sorted(PACKAGE.glob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            sources[rel + ":code"] = code_only(path)
            sources[rel + ":text"] = path.read_text(encoding="utf-8")
        self.assertEqual(GL.scan_forbidden(sources), [])
        self.assertTrue(GL.scan_forbidden({"control": "n_raw = len(h['revis' 'ions'])".replace("' '", "")}))


if __name__ == "__main__":
    unittest.main()
