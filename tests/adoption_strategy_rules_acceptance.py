"""Synthetic acceptance for core/adoption/strategy_rules.py (roadmap ⑨-4/2/a; criteria 4.2.2 S-2, S-3, S-4, S-7;
⑨-4/2/b: R-FAM as the N_raw reading of record, owner ruling 7 of 2026-11-11).

Every input is a seeded synthetic array built here. No ledger, card, register, price file, cache, configuration,
environment, provider or network is used. Gate functions are called directly as the golden reference; where an
edge needs an exact p or DSR value, the gate function is replaced by a stub for that one call (unittest.mock).
"""
import ast
import copy
from dataclasses import FrozenInstanceError, fields, replace
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


def gate_fixture(T=1400, G=4, mu=0.0008, seed=21):
    """A synthetic T x G grid, its walk-forward and the gate's own score (review case: gate DSR 0.9619 at N = G)."""
    rng = np.random.default_rng(seed)
    common = rng.normal(mu, 0.01, T)
    full = np.column_stack([common + rng.normal(0.0, 0.004, T) + 0.0001 * g for g in range(G)])
    wf = V.walk_forward(full, [d.isoformat() for d in sessions(T)])
    score = V.score_strategy(wf, grid=[{"lookback": g} for g in range(G)], full_pnl=full, n_trials=G)
    return full, wf, score


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
        res = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.010, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.012,
                          sr_sd_label="synthetic")
        self.assertEqual(res.dsr_grid, V.deflated_sharpe(a, n_trials=12, sr_sd_daily=0.010))
        self.assertEqual((res.sr_sd_grid, res.sr_sd_daily), (0.010, 0.012))
        by = {r.reading: r for r in res.readings}
        self.assertEqual(by["L-FAM"].dsr, V.deflated_sharpe(a, n_trials=17, sr_sd_daily=0.012))
        self.assertEqual(by["R-FAM"].dsr, V.deflated_sharpe(a, n_trials=11, sr_sd_daily=0.012))
        self.assertEqual(res.dsr_min, V.GATE["dsr_min"])
        self.assertEqual(res.n_sessions, 1260)

    def test_s2_with_gate_dispersion_reproduces_score_strategy_dsr(self):
        G = 4
        full, wf, score = gate_fixture(G=G, mu=0.0004)
        sd = S.gate_sr_sd_daily(full)
        res = S.dsr_two_n(wf.pnl, n_grid=G, sr_sd_grid=sd, n_raw={"L-FAM": G}, sr_sd_daily=sd, sr_sd_label="gate term")
        self.assertTrue(math.isfinite(score.dsr))
        self.assertEqual(res.dsr_grid, score.dsr)
        cols = V._col_sharpe(full) / math.sqrt(V.TRADING_DAYS)
        self.assertEqual(sd, float(np.nanstd(cols)))

    def test_gate_term_helper_equals_the_gate_on_constant_columns(self):
        rng = np.random.default_rng(3)
        T = 1400
        for c in (0.03 / 252, 0.025 / 252, 1e-4, 0.0):
            with self.subTest(cash_daily=c):
                full = np.column_stack([rng.normal(0.0004, 0.01, T), rng.normal(0.0003, 0.01, T), np.full(T, c)])
                gate = float(np.nanstd(V._col_sharpe(full) / math.sqrt(V.TRADING_DAYS)))
                self.assertEqual(S.gate_sr_sd_daily(full), gate)
                if c:
                    self.assertGreater(gate, 1e10)   # the gate's own term explodes; reported as the gate forms it
        self.assertIn("floating noise", S.gate_sr_sd_daily.__doc__)

    def test_grid_line_is_the_gate_dsr_when_the_n_raw_term_differs(self):
        G = 4
        full, wf, score = gate_fixture(G=G, mu=0.0008)
        gate_term, family_term = S.gate_sr_sd_daily(full), 0.01595
        res = S.dsr_two_n(wf.pnl, n_grid=G, sr_sd_grid=gate_term, n_raw={"L-FAM": 17}, sr_sd_daily=family_term,
                          sr_sd_label="family term")
        self.assertEqual(res.dsr_grid, score.dsr)
        self.assertGreaterEqual(score.dsr, 0.95)
        self.assertEqual(res.status_grid, "pass")
        raw = res.readings[0]
        self.assertEqual(raw.dsr, V.deflated_sharpe(wf.pnl, n_trials=17, sr_sd_daily=family_term))
        self.assertTrue(0.90 <= raw.dsr < 0.95, raw.dsr)
        self.assertEqual(raw.status, "borderline")             # criteria 6.2: gate DSR >= 0.95, second in [0.90, 0.95)
        self.assertLess(V.deflated_sharpe(wf.pnl, n_trials=G, sr_sd_daily=family_term), 0.95)   # one shared term: below
        text = "\n".join(res.lines())
        self.assertIn("[the gate's own term]", text)
        self.assertIn("[family term]", text)
        # the contract review's numbers: T 1260, mu 0.00073, G 12, L-FAM 17, gate term 0.010, labelled term 0.020
        x = np.random.default_rng(0).normal(0.0, 0.01, 1260)
        x = (x - x.mean()) / x.std(ddof=1) * 0.01 + 0.00073
        two = S.dsr_two_n(x, n_grid=12, sr_sd_grid=0.010, n_raw={"L-FAM": 17}, sr_sd_daily=0.020, sr_sd_label="alt")
        self.assertEqual(two.dsr_grid, V.deflated_sharpe(x, n_trials=12, sr_sd_daily=0.010))
        self.assertEqual((two.status_grid, two.readings[0].status), ("pass", "borderline"))
        self.assertLess(V.deflated_sharpe(x, n_trials=12, sr_sd_daily=0.020), 0.95)

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
            self.assertEqual(got.conforms_to_registration, seed is None)
            self.assertEqual("OFF-REGISTRATION" in got.line(), seed is not None)
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
        equal = S.power_line_s7(a, b, ds, ds, expected_dsr=got.mde80)       # criteria S-7: "크면", strictly greater
        self.assertEqual(equal.mde80, equal.expected_dsr)
        self.assertFalse(equal.underpowered_vs_expected)
        just_below = S.power_line_s7(a, b, ds, ds, expected_dsr=math.nextafter(got.mde80, 0.0))
        self.assertTrue(just_below.underpowered_vs_expected)


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
        self.assertFalse(got.conforms_to_registration)
        self.assertIn("OFF-REGISTRATION: B 400, seed 11; criteria 3.2 item 11 fixes B 2000 and seed 11", got.line())

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
        for c in (0.0, 0.03 / 252):
            with self.subTest(cash_daily=c):
                cash = S.lw_compare(a, np.full(a.size, c), ds, ds, rule="S-4", other_label="cash")
                self.assertEqual(cash.status, "not_run")
                self.assertIn("CASH_BASELINE (criteria 2.3)", cash.reason)
        self.assertNotIn("CASH_BASELINE", same.reason)


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
            res = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.01,
                              sr_sd_label="x")
        by = {r.reading: r.status for r in res.readings}
        self.assertEqual((res.status_grid, by["L-FAM"], by["R-FAM"]), ("pass", "borderline", "below"))
        values = {12: math.nextafter(0.95, 0.0), 17: 0.93, 11: 0.96}
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            res = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 17, "R-FAM": 11}, sr_sd_daily=0.01,
                              sr_sd_label="x")
        by = {r.reading: r.status for r in res.readings}
        self.assertEqual((res.status_grid, by["L-FAM"], by["R-FAM"]), ("below", "below", "pass"))

    def test_n_raw_below_grid_is_printed_not_refused(self):
        a, _ = pair()
        res = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 8}, sr_sd_daily=0.01, sr_sd_label="x")
        by = {r.reading: r for r in res.readings}
        self.assertTrue(by["L-FAM"].below_grid)
        self.assertEqual(by["L-FAM"].dsr, V.deflated_sharpe(a, n_trials=8, sr_sd_daily=0.01))
        text = "\n".join(res.lines())
        self.assertIn("N_raw 8 < G 12: printed only", text)
        self.assertIn("10.2 B Q4", text)
        equal = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 12}, sr_sd_daily=0.01, sr_sd_label="x")
        self.assertFalse(any(r.below_grid for r in equal.readings))

    def test_both_readings_displayed_provisional_and_labelled(self):
        a, _ = pair()
        one = S.dsr_two_n(a, n_grid=5, sr_sd_grid=0.004, n_raw={"R-FAM": 9}, sr_sd_daily=0.0,
                          sr_sd_label="caller term A")
        self.assertEqual([r.reading for r in one.readings], ["L-FAM", "R-FAM"])
        self.assertEqual(one.readings[0].status, "not_supplied")
        self.assertIsNone(one.readings[0].n_raw)
        text = "\n".join(one.lines())
        self.assertIn("L-FAM", text)
        self.assertIn("not supplied", text)
        self.assertIn("dispersion term 0 per period [caller term A]", text)
        self.assertIn("dispersion term 0.004 per period [the gate's own term]", text)
        self.assertTrue(one.provisional)
        self.assertTrue(all("[provisional]" in line for line in one.lines() if line.startswith("S-2")))
        self.assertIn("⑨-3d", text)
        self.assertEqual(one.rule, "S-2")

    def test_r_fam_is_the_reading_of_record_and_l_fam_is_shown_for_comparison(self):
        # Owner ruling 7 of 2026-11-11 (⑨-4/2/b): R-FAM, the R3 run-registry count, is the N_raw reading of record.
        # Until the R3 recorder exists both readings are shown and the second DSR stays provisional.
        self.assertEqual(S.N_RAW_READING_OF_RECORD, "R-FAM")
        self.assertIn(S.N_RAW_READING_OF_RECORD, S.N_RAW_READINGS)
        a, _ = pair()
        kw = dict(n_grid=12, sr_sd_grid=0.01, sr_sd_daily=0.012, sr_sd_label="caller term")
        record, compare = "reading of record (owner ruling 7, 2026-11-11)", "shown for comparison"

        def s2(res):
            lines = [line for line in res.lines() if line.startswith("S-2 [provisional]")]
            return {"G": lines[0], "L-FAM": lines[1], "R-FAM": lines[2]}

        both = S.dsr_two_n(a, n_raw={"L-FAM": 17, "R-FAM": 11}, **kw)
        self.assertEqual([(r.reading, r.of_record) for r in both.readings], [("L-FAM", False), ("R-FAM", True)])
        self.assertEqual((both.reading_of_record, both.provisional), ("R-FAM", True))
        got = s2(both)
        self.assertIn(f"DSR at N_raw R-FAM = 11 [{record}]:", got["R-FAM"])
        self.assertIn(f"DSR at N_raw L-FAM = 17 [{compare}]:", got["L-FAM"])
        self.assertEqual([record in line for line in both.lines()].count(True), 1)     # only the R-FAM line
        self.assertNotIn("record", got["G"])
        self.assertNotIn("not supplied", "\n".join(got.values()))
        self.assertTrue(any("R-FAM, the R3 run-registry count, is the N_raw reading of record "
                            "(owner ruling 7 of 2026-11-11)" in note for note in both.notes))
        self.assertFalse(any("undecided" in line for line in both.lines()))

        only_l = S.dsr_two_n(a, n_raw={"L-FAM": 17}, **kw)       # the reading of record is missing
        got = s2(only_l)
        self.assertIn(f"N_raw R-FAM (", got["R-FAM"])
        self.assertIn(f"[{record}]: not supplied; the reading of record was not supplied, so this result has "
                      "no second DSR of record and stays provisional", got["R-FAM"])
        self.assertIn(f"[{compare}]:", got["L-FAM"])
        self.assertNotIn("not supplied", got["L-FAM"])
        self.assertTrue(only_l.provisional)
        self.assertEqual([(r.reading, r.of_record, r.status == "not_supplied") for r in only_l.readings],
                         [("L-FAM", False, False), ("R-FAM", True, True)])

        only_r = S.dsr_two_n(a, n_raw={"R-FAM": 11}, **kw)       # supplied, and still provisional
        got = s2(only_r)
        self.assertIn(f"[{compare}]: not supplied", got["L-FAM"])
        self.assertTrue(got["L-FAM"].endswith("not supplied"))
        self.assertNotIn("stays provisional", got["L-FAM"])
        self.assertIn(f"DSR at N_raw R-FAM = 11 [{record}]:", got["R-FAM"])
        self.assertTrue(only_r.provisional)

        # Naming the reading of record changes no number and no status (no threshold, gate or verdict rule).
        grid = V.deflated_sharpe(a, n_trials=12, sr_sd_daily=0.01)
        self.assertEqual((both.dsr_grid, both.status_grid), (grid, S.classify_dsr(grid)))
        for res in (both, only_l, only_r):
            for r, n in zip(res.readings, (17, 11)):
                if r.n_raw is None:
                    continue
                value = V.deflated_sharpe(a, n_trials=n, sr_sd_daily=0.012)
                self.assertEqual((r.n_raw, r.dsr, r.status),
                                 (n, value, S.classify_dsr(value, grid_status=both.status_grid)))
        self.assertEqual((both.dsr_min, both.borderline_min), (V.GATE["dsr_min"], 0.90))
        # The reading of record gets the same zones as the comparison reading (criteria 6.2, keyed on the grid line).
        for grid_value, want in ((0.95, "borderline"), (math.nextafter(0.95, 0.0), "below")):
            values = {12: grid_value, 17: 0.93, 11: 0.93}
            with self.subTest(grid=grid_value), patch.object(
                    V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
                edge = S.dsr_two_n(a, n_raw={"L-FAM": 17, "R-FAM": 11}, **kw)
                self.assertEqual([r.status for r in edge.readings], [want, want])

    def test_reading_of_record_has_one_source_and_a_result_cannot_contradict_it(self):
        # /code-review F7. The reading of record was stored three times (the constant, a flag on each reading
        # and a field on the result) and lines() read only the flag, so dataclasses.replace(result,
        # reading_of_record="L-FAM") gave a result whose field named L-FAM while its lines named R-FAM.
        a, _ = pair()
        kw = dict(n_grid=12, sr_sd_grid=0.01, sr_sd_daily=0.012, sr_sd_label="caller term")
        res = S.dsr_two_n(a, n_raw={"L-FAM": 17, "R-FAM": 11}, **kw)
        # The constructors are those of main before PR #100 (7ddb568): no stored copy of the reading of record.
        self.assertEqual([f.name for f in fields(S.RawReading)],
                         ["reading", "meaning", "n_raw", "dsr", "status", "below_grid"])
        self.assertNotIn("reading_of_record", {f.name for f in fields(S.DsrTwoN)})
        self.assertEqual(S.DsrTwoN.__dataclass_fields__["provisional"].default, True)
        built = S.RawReading("L-FAM", "meaning", 17, 0.5, "below", False)        # six arguments, as at 7ddb568
        self.assertEqual((built.of_record, built.role()), (False, "shown for comparison"))
        with self.assertRaises(TypeError):
            S.RawReading("L-FAM", "meaning", 17, 0.5, "below", False, True)        # no seventh, stored flag
        # Nothing on a result can be set to disagree with the constant.
        with self.assertRaises(TypeError):
            replace(res, reading_of_record="L-FAM")
        for r in res.readings:
            with self.assertRaises(TypeError):
                replace(r, of_record=not r.of_record)
            with self.assertRaises(AttributeError):
                r.of_record = not r.of_record
        with self.assertRaises(AttributeError):
            res.reading_of_record = "L-FAM"
        # A reading rebuilt by hand under either key still gets its role from the constant.
        moved = replace(res, readings=tuple(replace(r, reading=other) for r, other in
                                            zip(res.readings, ("R-FAM", "L-FAM"))))
        self.assertEqual([(r.reading, r.of_record) for r in moved.readings], [("R-FAM", True), ("L-FAM", False)])
        self.assertEqual(["[reading of record" in line for line in moved.lines()[1:3]], [True, False])
        # The field-like names, the roles and the printed lines all follow the one constant.
        self.assertEqual((res.reading_of_record, [r.of_record for r in res.readings]), ("R-FAM", [False, True]))
        with patch.object(S, "N_RAW_READING_OF_RECORD", "L-FAM"):
            self.assertEqual((res.reading_of_record, [r.of_record for r in res.readings]), ("L-FAM", [True, False]))
            self.assertEqual([r.role() for r in res.readings],
                             ["reading of record (owner ruling 7, 2026-11-11)", "shown for comparison"])
            self.assertEqual(["[reading of record" in line for line in res.lines()[1:3]], [True, False])
        self.assertEqual(["[reading of record" in line for line in res.lines()[1:3]], [False, True])

    def test_s2_lines_text_is_exact(self):
        # The text of the S-2 lines is pinned in full, so a change of structure cannot change a printed word.
        a, _ = pair()
        kw = dict(n_grid=12, sr_sd_grid=0.01, sr_sd_daily=0.012, sr_sd_label="caller term")
        grid = V.deflated_sharpe(a, n_trials=12, sr_sd_daily=0.01)
        d17 = V.deflated_sharpe(a, n_trials=17, sr_sd_daily=0.012)
        d11 = V.deflated_sharpe(a, n_trials=11, sr_sd_daily=0.012)
        g_line = (f"S-2 [provisional] DSR at N = G = 12: {grid:.4f} ({S.classify_dsr(grid)}); "
                  "dispersion term 0.01 per period [the gate's own term]")
        status = lambda value: S.classify_dsr(value, grid_status=S.classify_dsr(grid))
        l_line = (f"S-2 [provisional] DSR at N_raw L-FAM = 17 [shown for comparison]: {d17:.4f} ({status(d17)}); "
                  "dispersion term 0.012 per period [caller term]")
        r_line = ("S-2 [provisional] DSR at N_raw R-FAM = 11 [reading of record (owner ruling 7, 2026-11-11)]: "
                  f"{d11:.4f} ({status(d11)}); dispersion term 0.012 per period [caller term]; "
                  "N_raw 11 < G 12: printed only")
        l_missing = ("S-2 [provisional] N_raw L-FAM (family ledger row count (gate_ledger.FamilyLedger.n_raw, the "
                     "number of ledger rows), read on the owner PC) [shown for comparison]: not supplied")
        r_missing = ("S-2 [provisional] N_raw R-FAM (R3 registry literal family-wide count (R3 design 3.13: |K| + "
                     "|L minus cfg(K)|)) [reading of record (owner ruling 7, 2026-11-11)]: not supplied; the reading "
                     "of record was not supplied, so this result has no second DSR of record and stays provisional")
        for n_raw, want in (({"L-FAM": 17, "R-FAM": 11}, (g_line, l_line, r_line)),
                            ({"L-FAM": 17}, (g_line, l_line, r_missing)),
                            ({"R-FAM": 11}, (g_line, l_missing, r_line))):
            with self.subTest(n_raw=sorted(n_raw)):
                self.assertEqual(S.dsr_two_n(a, n_raw=n_raw, **kw).lines()[:3], want)

    def test_counts_and_dispersion_inputs_refused(self):
        a, _ = pair()
        good = dict(n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 17}, sr_sd_daily=0.01, sr_sd_label="x")
        bad = [dict(n_grid=0), dict(n_grid=-3), dict(n_grid=12.0), dict(n_grid=True), dict(n_grid="12"),
               dict(n_raw={}), dict(n_raw={"L-FAM": 0}), dict(n_raw={"L-FAM": 17.0}), dict(n_raw={"L-FAM": False}),
               dict(n_raw={"ledger": 17}), dict(n_raw=17), dict(n_raw=[("L-FAM", 17)]),
               dict(sr_sd_daily=-0.01), dict(sr_sd_daily=float("nan")), dict(sr_sd_daily=float("inf")),
               dict(sr_sd_daily=None), dict(sr_sd_label=""), dict(sr_sd_label="  "), dict(sr_sd_label=None),
               dict(sr_sd_grid=-0.01), dict(sr_sd_grid=float("nan")), dict(sr_sd_grid=None), dict(sr_sd_grid="0.01")]
        for change in bad:
            with self.subTest(change=change):
                with self.assertRaises(S.AdoptionInputError):
                    S.dsr_two_n(a, **{**good, **change})
        with self.assertRaises(S.AdoptionInputError):
            S.dsr_two_n(np.array([0.01, float("nan"), 0.02]), **good)
        for bad in ([str(v) for v in a[:60]], [True, False] * 30, np.array(a, dtype=object), a + 0j):
            with self.subTest(dtype=np.asarray(bad).dtype):
                with self.assertRaisesRegex(S.AdoptionInputError, "integer or float"):
                    S.dsr_two_n(bad, **good)
        with self.assertRaises(S.AdoptionInputError):
            S.dsr_two_n(np.ones((3, 2)), **good)
        with self.assertRaises(TypeError):
            S.dsr_two_n(a, **{k: v for k, v in good.items() if k != "sr_sd_grid"})
        self.assertEqual(S.dsr_two_n(a, **{**good, "n_grid": np.int64(12)}).n_grid, 12)

    def test_nan_dsr_does_not_meet_s2(self):
        short = S.dsr_two_n(np.array([0.01, 0.02]), n_grid=1, sr_sd_grid=0.0, n_raw={"L-FAM": 1}, sr_sd_daily=0.0,
                            sr_sd_label="x")
        self.assertTrue(math.isnan(V.deflated_sharpe(np.array([0.01, 0.02]), n_trials=1, sr_sd_daily=0.0)))
        self.assertEqual(short.status_grid, "nan")
        self.assertEqual(short.readings[0].status, "nan")
        self.assertIn("a NaN DSR does not meet S-2 (criteria 6.4, N12)", short.lines())
        a, _ = pair()
        values = {12: 0.97, 17: float("nan")}
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            res = S.dsr_two_n(a, n_grid=12, sr_sd_grid=0.01, n_raw={"L-FAM": 17}, sr_sd_daily=0.01, sr_sd_label="x")
        self.assertEqual((res.status_grid, res.readings[0].status), ("pass", "nan"))
        self.assertIn("(nan)", res.lines()[1])

    def test_gate_dispersion_helper_refuses_bad_matrices(self):
        for bad in (np.ones(5), np.ones((1, 3)), np.ones((4, 0)), np.array([[0.1, float("nan")], [0.2, 0.3]]),
                    [["0.1", "0.2"], ["0.3", "0.4"]], [[True, False], [False, True]],
                    np.array([[0.1, 0.2], [0.3, 0.4]], dtype=object)):
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
        for bad in (datetime(2026, 12, 31, 9, 0), "2026/12/31", "", 20261231, None, "20270101", "2027-W01-5",
                    "2026-12-31T00:00", "2026-12-31 ", "\uff12026-12-31"):
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
            ([str(v) for v in a], b, ds, ds, "numeric daily P&L (integer or float), got dtype <U"),
            ([True, False] * 30, b, ds, ds, "got dtype bool"),
            (a, np.array(list(b), dtype=object), ds, ds, "got dtype object"),
            (a[:-1], b, ds, ds, "challenger: 59 values but 60 sessions"),
        ]
        for x_a, x_b, d_a, d_b, needle in cases:
            with self.subTest(needle=needle):
                with self.assertRaisesRegex(S.AdoptionInputError, re.escape(needle)):
                    S.lw_compare(x_a, x_b, d_a, d_b, rule="S-4", other_label="baseline")
        iso = S.lw_compare(a, b, [d.isoformat() for d in ds], ds, rule="S-4", other_label="baseline")
        self.assertEqual(iso.n_sessions, 60)
        ints = S.lw_compare(np.round(a * 1e6).astype(np.int64), b, ds, ds, rule="S-4", other_label="baseline")
        self.assertEqual(ints.n_sessions, 60)
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
        self.common = dict(challenger=self.a, challenger_dates=self.ds, n_grid=12, sr_sd_grid=0.011,
                           n_raw={"L-FAM": 17}, sr_sd_daily=0.01, sr_sd_label="caller term", baselines=self.base)

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
        self.assertTrue(all(c.conforms_to_registration for c in (res.s3,) + res.s4))
        self.assertEqual(res.s2.dsr_grid, V.deflated_sharpe(self.a, n_trials=12, sr_sd_daily=0.011))
        for name in ("B", "seed"):
            with self.subTest(override=name), self.assertRaises(TypeError):
                S.strategy_lines(kind="replace", incumbent=self.inc, incumbent_dates=self.ds, expected_dsr=0.25,
                                 **{name: 50}, **self.common)
        self.assertTrue(all(r.status in S.DSR_STATUSES for r in res.s2.readings))
        self.assertIn(res.s2.status_grid, S.DSR_STATUSES)
        # ruling 7 (2026-11-11): this registration supplies L-FAM only, so the reading of record is missing
        missing = [line for line in lines if "N_raw R-FAM" in line]
        self.assertEqual(len(missing), 1)
        self.assertIn("[reading of record (owner ruling 7, 2026-11-11)]: not supplied", missing[0])
        self.assertIn("stays provisional", missing[0])
        self.assertTrue(res.provisional and res.s2.provisional)
        with_record = S.strategy_lines(kind="replace", incumbent=self.inc, incumbent_dates=self.ds,
                                       expected_dsr=0.25, **{**self.common, "n_raw": {"L-FAM": 17, "R-FAM": 11}})
        self.assertTrue(with_record.provisional and with_record.s2.provisional)   # until the R3 recorder exists
        self.assertTrue(any("DSR at N_raw R-FAM = 11 [reading of record" in line for line in with_record.lines()))
        self.assertEqual((with_record.s3, with_record.s4, with_record.s7), (res.s3, res.s4, res.s7))

    def test_add_prints_the_incumbent_comparison_only(self):
        res = S.strategy_lines(kind="add", incumbent=self.inc, incumbent_dates=self.ds, **self.common)
        self.assertFalse(res.s3.counts)
        self.assertIn("printed only, addition (M-19)", res.s3.line())
        self.assertIsNone(res.s7)
        self.assertTrue(all(c.rule == "S-4" and c.counts for c in res.s4))   # criteria 4.2.2: S-1, S-2, S-4 judge
        bare = S.strategy_lines(kind="add", **self.common)
        self.assertIsNone(bare.s3)
        self.assertEqual(len(bare.s4), 2)
        for bad in (-5.0, 0.0, float("nan"), "0.2", True):
            with self.subTest(expected_dsr=bad), self.assertRaisesRegex(S.AdoptionInputError, "expected_dsr"):
                S.strategy_lines(kind="add", expected_dsr=bad, **self.common)
        noted = S.strategy_lines(kind="add", expected_dsr=0.2, **self.common)
        self.assertIsNone(noted.s7)
        self.assertIn("no incumbent was supplied, so no S-7 line is printed", "\n".join(noted.lines()))

    def test_declared_cash_baseline_is_replaced_by_the_gate_interval_check(self):
        res = S.strategy_lines(kind="add", **{**self.common, "baselines": {"cash": S.CASH_BASELINE,
                                                                           "equal-weight": self.base["equal-weight"]}})
        cash, ew = res.s4
        self.assertIsInstance(cash, S.CashBaseline)
        self.assertEqual((cash.rule, cash.other, cash.status, cash.replaced_by, cash.counts),
                         ("S-4", "cash", "replaced", "S-1", True))
        self.assertIn(cash.status, S.COMPARISON_STATUSES)
        line = cash.line()
        for token in ("S-4 vs cash: REPLACED", "criteria 2.3", "Sharpe interval", "S-1", "no LW test is run"):
            self.assertIn(token, line)
        self.assertIn(line, res.lines())
        self.assertEqual(ew.status, S.lw_compare(self.a, self.base["equal-weight"][0], self.ds, self.ds, rule="S-4",
                                                 other_label="equal-weight").status)
        only_cash = S.strategy_lines(kind="add", **{**self.common, "baselines": {"cash": S.CASH_BASELINE}})
        self.assertEqual([c.status for c in only_cash.s4], ["replaced"])
        with self.assertRaises(FrozenInstanceError):
            cash.status = "win"
        with self.assertRaisesRegex(S.AdoptionInputError, "CASH_BASELINE"):
            S.strategy_lines(kind="add", **{**self.common, "baselines": {"cash": "cash"}})

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
        res = S.strategy_lines(kind="add", challenger=self.a, challenger_dates=late, n_grid=3, sr_sd_grid=0.0,
                               n_raw={"R-FAM": 3}, sr_sd_daily=0.0, sr_sd_label="x", baselines=base)
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


class OutcomeAssembly(unittest.TestCase):
    """⑨-4/2/c: criteria 6.1, 6.2 and 6.4 N12 with the owner's answers B-Q1, B-Q2, B-Q3 of 2026-11-11."""
    G, L, R = 12, 17, 11

    def setUp(self):
        self.a, self.inc = pair(T=756, seed=5, edge=0.0002)
        self.ds = sessions(756)
        self.mde = S.power_line_s7(self.a, self.inc, self.ds, self.ds, expected_dsr=1.0).mde80

    def build(self, *, kind="replace", grid=0.97, rfam=0.96, lfam=0.96, count=0, d_sr=0.3, expected=None,
              n_raw=None, ds=None, term=0.01, with_incumbent=False):
        """Real strategy_lines with the DSRs and the LW bootstrap stubbed to exact values (as in DsrLines)."""
        ds = self.ds if ds is None else ds
        values = {self.G: grid, self.L: lfam, self.R: rfam}
        rng = np.random.default_rng(9)
        kw = dict(kind=kind, challenger=self.a, challenger_dates=ds, n_grid=self.G, sr_sd_grid=0.01,
                  n_raw={"L-FAM": self.L, "R-FAM": self.R} if n_raw is None else n_raw, sr_sd_daily=term,
                  sr_sd_label="the gate's term" if term == 0.01 else "stricter term",
                  baselines={"equal-weight": (rng.normal(0.0002, 0.008, 756), ds), "cash": S.CASH_BASELINE})
        if kind == "replace":
            kw.update(incumbent=self.inc, incumbent_dates=ds,
                      expected_dsr=self.mde * 2 if expected is None else expected)
        elif with_incumbent:
            kw.update(incumbent=self.inc, incumbent_dates=ds)
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]), \
                patch.object(GS, "lw_studentized_boot", side_effect=fake_boot(d_sr, count)):
            return S.strategy_lines(**kw)

    def test_each_outcome_name_is_reachable(self):
        got = {}
        for name, verdict, lines in (
                ("adopt-replace", "PASS", self.build()), ("adopt-add", "PASS", self.build(kind="add")),
                ("keep", "PASS", self.build(count=300)), ("revise", "REVISE", self.build()),
                ("reject-gate", "REJECT", self.build()), ("reject-bq1", "PASS", self.build(rfam=0.85)),
                ("insufficient-gate", "INSUFFICIENT_DATA", self.build()),
                ("insufficient-bq3", "PASS", self.build(expected=self.mde / 2)),
                ("none", "PASS", self.build(n_raw={"L-FAM": self.L}))):
            out = S.strategy_outcome(gate_verdict=verdict, lines=lines)
            got[name] = out.outcome
            self.assertIn(out.outcome, S.OUTCOMES + (S.NO_OUTCOME,))
            self.assertTrue(out.provisional)                      # every outcome, while the second DSR is provisional
            self.assertIn("[provisional]", out.lines()[0])
            self.assertTrue(out.lines()[0].startswith(f"⑨-4/2/c strategy outcome ({lines.kind}) [provisional]: "))
            self.assertIn(S._OUTCOME_PROVISIONAL_NOTE, out.lines())
        self.assertEqual(got, {"adopt-replace": "ADOPT", "adopt-add": "ADOPT", "keep": "KEEP", "revise": "REVISE",
                               "reject-gate": "REJECT", "reject-bq1": "REJECT",
                               "insufficient-gate": "INSUFFICIENT_DATA",
                               "insufficient-bq3": "INSUFFICIENT_DATA", "none": "NO_OUTCOME"})
        self.assertEqual(set(got.values()), set(S.OUTCOMES) | {S.NO_OUTCOME})
        self.assertEqual(S.OUTCOMES, ("ADOPT", "KEEP", "REVISE", "REJECT", "INSUFFICIENT_DATA"))
        self.assertNotIn(S.NO_OUTCOME, S.OUTCOMES)
        adopt = S.strategy_outcome(gate_verdict="PASS", lines=self.build())
        self.assertTrue(adopt.replaces_incumbent)
        self.assertIn("the incumbent is replaced", "\n".join(adopt.lines()))
        self.assertFalse(S.strategy_outcome(gate_verdict="PASS", lines=self.build(kind="add")).replaces_incumbent)
        self.assertIn(S._NOT_COVERED_NOTE, adopt.lines())

    def test_b_q1_second_dsr_of_record_below_0p90_is_reject_labelled_provisional(self):
        below = math.nextafter(0.90, 0.0)
        out = S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=below))
        self.assertEqual((out.outcome, out.basis, out.provisional_basis), ("REJECT", "B-Q1", True))
        self.assertTrue(out.lines()[0].endswith(": REJECT [잠정 기준]"))
        text = "\n".join(out.lines())
        self.assertIn("B-Q1 (owner answer of 2026-11-11, \"전부승인\"): the second DSR of record is below 0.90: "
                      "REJECT, 잠정 기준 (provisional (M-3):", text)
        # Without B-Q1 the same lines would be adopted (R-FAM passing) or kept (R-FAM borderline at 0.90).
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=0.96)).outcome, "ADOPT")
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=0.90)).outcome, "KEEP")
        # B-Q1 names the outcome even when S-7 is short (B-Q3 would give INSUFFICIENT_DATA) or a comparison is lost.
        for kw in (dict(expected=self.mde / 2), dict(count=1000), dict(kind="add", count=300)):
            with self.subTest(**{k: v for k, v in kw.items() if k != "expected"}):
                self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=0.85, **kw)).basis,
                                 "B-Q1")
        # Only the reading of record decides: L-FAM below 0.90 with R-FAM passing is adopted.
        lfam_low = S.strategy_outcome(gate_verdict="PASS", lines=self.build(lfam=0.5))
        self.assertEqual(lfam_low.outcome, "ADOPT")
        self.assertIn("S-2 DSR at N_raw L-FAM = 17: 0.5000 (below); shown for comparison; decides nothing",
                      "\n".join(lfam_low.lines()))
        # A gate REJECT is not B-Q1 and carries no 잠정 기준 label.
        gate = S.strategy_outcome(gate_verdict="REJECT", lines=self.build(rfam=0.85))
        self.assertEqual((gate.outcome, gate.basis, gate.provisional_basis), ("REJECT", "criteria 6.1 gate", False))
        self.assertNotIn("잠정 기준", gate.lines()[0])

    def test_b_q2_the_gate_term_decides_and_another_term_is_a_reference_line(self):
        lines = self.build(rfam=0.96)
        values = {self.G: 0.97, self.L: 0.80, self.R: 0.85}       # the stricter term: R-FAM would be below 0.90
        with patch.object(V, "deflated_sharpe", side_effect=lambda d, *, n_trials, sr_sd_daily: values[n_trials]):
            strict = S.dsr_two_n(self.a, n_grid=self.G, sr_sd_grid=0.01, n_raw={"L-FAM": self.L, "R-FAM": self.R},
                                 sr_sd_daily=0.03, sr_sd_label="SE_null pairing")
        self.assertEqual([r.status for r in strict.readings], ["below", "below"])
        out = S.strategy_outcome(gate_verdict="PASS", lines=lines, reference_s2=strict)
        self.assertEqual(out.outcome, "ADOPT")                  # had the stricter term decided, B-Q1 gives REJECT
        self.assertEqual(out.references, (
            "S-2 reference only (B-Q2, never decides): DSR at N_raw L-FAM = 17 [shown for comparison] with the term "
            "0.03 per period [SE_null pairing]: 0.8000 (below)",
            "S-2 reference only (B-Q2, never decides): DSR at N_raw R-FAM = 11 [reading of record (owner ruling 7, "
            "2026-11-11)] with the term 0.03 per period [SE_null pairing]: 0.8500 (below)"))
        self.assertTrue(set(out.references) <= set(out.lines()))
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=0.85)).outcome, "REJECT")
        # Lines whose N_raw term is not the gate's cannot decide.
        with self.assertRaisesRegex(S.AdoptionInputError, "B-Q2 .*the gate's dispersion term.*reference_s2"):
            S.strategy_outcome(gate_verdict="PASS", lines=self.build(term=0.03))
        with self.assertRaisesRegex(S.AdoptionInputError, "B-Q2"):
            S.strategy_outcome(gate_verdict="REJECT", lines=self.build(term=0.03))
        same_term = replace(strict, sr_sd_daily=0.01)
        other_counts = replace(strict, readings=tuple(replace(r, n_raw=r.n_raw + 1) for r in strict.readings))
        for bad, needle in ((same_term, "gate's own term"), (other_counts, "not for the same series"),
                            (replace(strict, n_grid=13), "not for the same series"),
                            (replace(strict, dsr_grid=0.5), "not for the same series"),
                            (strict.readings[0], "dsr_two_n result")):
            with self.subTest(needle=needle), self.assertRaisesRegex(S.AdoptionInputError, needle):
                S.strategy_outcome(gate_verdict="PASS", lines=lines, reference_s2=bad)

    def test_b_q3_a_won_comparison_with_short_power_is_insufficient_data(self):
        won_short = S.strategy_outcome(gate_verdict="PASS", lines=self.build(expected=self.mde / 2))
        self.assertEqual(won_short.strategy.s3.status, "win")
        self.assertTrue(won_short.strategy.s7.underpowered_vs_expected)
        self.assertEqual((won_short.outcome, won_short.basis, won_short.replaces_incumbent),
                         ("INSUFFICIENT_DATA", "B-Q3", False))
        self.assertIn("so S-3 (win) is INSUFFICIENT_DATA even when won", "\n".join(won_short.lines()))
        self.assertIn("the incumbent is not replaced", "\n".join(won_short.lines()))
        won_powered = S.strategy_outcome(gate_verdict="PASS", lines=self.build(expected=self.mde * 2))
        self.assertEqual((won_powered.outcome, won_powered.replaces_incumbent), ("ADOPT", True))
        # The S-7 boundary (criteria S-7 "크면": strictly greater) carries into the outcome.
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(expected=self.mde)).outcome, "ADOPT")
        below = math.nextafter(self.mde, 0.0)
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(expected=below)).outcome,
                         "INSUFFICIENT_DATA")
        # Short power makes S-3 INSUFFICIENT_DATA whatever it says, and that outranks KEEP (criteria 4.2.2).
        for count, status in ((300, "borderline"), (1000, "not_won")):
            with self.subTest(s3=status):
                res = self.build(expected=self.mde / 2, count=count)
                self.assertEqual(res.s3.status, status)
                self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=res).outcome, "INSUFFICIENT_DATA")
        borderline_record = self.build(expected=self.mde / 2, rfam=0.92)
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=borderline_record).basis, "B-Q3")
        # An addition has no S-7 and its incumbent comparison claims nothing.
        for count in (0, 1000):                                    # S-3 won or lost: printed only, claims nothing
            with self.subTest(add_s3=count):
                add = S.strategy_outcome(gate_verdict="PASS", lines=replace(
                    self.build(kind="add", with_incumbent=True),
                    s3=self.build(kind="add", with_incumbent=True, count=count).s3))
                self.assertEqual((add.strategy.s3.counts, add.strategy.s7), (False, None))
                self.assertEqual((add.outcome, add.replaces_incumbent), ("ADOPT", False))
                self.assertFalse(any("S-3" in line for line in add.reasons))

    def test_borderline_cases_of_6_2(self):
        for count, want in ((200, "ADOPT"), (201, "KEEP"), (400, "KEEP"), (401, "KEEP"), (0, "ADOPT")):
            with self.subTest(count=count):
                out = S.strategy_outcome(gate_verdict="PASS", lines=self.build(kind="add", count=count))
                self.assertEqual(out.outcome, want)
                if count in (201, 400):
                    self.assertIn("S-4 vs equal-weight: borderline: borderline, never adopted (criteria 6.2, M-11)",
                                  out.reasons)
        res = self.build()
        s3_border = S.strategy_outcome(gate_verdict="PASS", lines=replace(res, s3=replace(res.s3, status="borderline")))
        self.assertEqual((s3_border.outcome, s3_border.basis), ("KEEP", "criteria 6.1 KEEP"))
        for value, want in ((0.95, "ADOPT"), (math.nextafter(0.95, 0.0), "KEEP"), (0.90, "KEEP"),
                            (math.nextafter(0.90, 0.0), "REJECT")):
            with self.subTest(rfam=value):
                self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=value)).outcome, want)
        keep = S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=0.93))
        self.assertIn("S-2: the second DSR of record is in [0.90, 0.95) while the gate's DSR passes: borderline, never "
                      "adopted (criteria 6.2, M-11)", keep.reasons)
        # 6.2: a gate DSR below 0.95 is not borderline but the gate's REJECT; a PASS with it is not one run.
        low_gate = self.build(grid=0.94, rfam=0.93)
        self.assertEqual((low_gate.s2.status_grid, low_gate.s2.readings[1].status), ("below", "below"))
        self.assertEqual(S.strategy_outcome(gate_verdict="REJECT", lines=low_gate).outcome, "REJECT")
        for verdict in ("PASS", "REVISE"):
            with self.subTest(verdict=verdict), self.assertRaisesRegex(S.AdoptionInputError, "not from one run"):
                S.strategy_outcome(gate_verdict=verdict, lines=low_gate)

    def test_undecided_cases_name_no_outcome_or_are_refused(self):
        only_l = S.strategy_outcome(gate_verdict="PASS", lines=self.build(n_raw={"L-FAM": self.L}))
        self.assertEqual((only_l.outcome, only_l.basis), ("NO_OUTCOME", "R-FAM, the reading of record, not supplied"))
        self.assertIn("NO_OUTCOME (no outcome: R-FAM, the reading of record, not supplied)", only_l.lines()[0])
        self.assertEqual(S.strategy_outcome(gate_verdict="REJECT", lines=self.build(n_raw={"L-FAM": self.L})).outcome,
                         "REJECT")
        late = sessions(756, date(2024, 6, 3))
        touched = S.strategy_outcome(gate_verdict="PASS", lines=self.build(ds=late))
        self.assertEqual(touched.outcome, "NO_OUTCOME")
        self.assertIn("HOLDOUT_TOUCHED", touched.basis)
        self.assertIn("HOLDOUT_TOUCHED", "\n".join(touched.reasons))
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=self.build(ds=late, count=300)).outcome, "KEEP")
        res = self.build()
        not_run = replace(res.s4[0], status="not_run", reason="HAC SE is zero")
        lone = S.strategy_outcome(gate_verdict="PASS", lines=replace(res, s4=(not_run, res.s4[1])))
        self.assertEqual(lone.outcome, "NO_OUTCOME")
        self.assertIn("S-4 vs equal-weight: not run (HAC SE is zero)", lone.reasons)
        lost = replace(res, s3=replace(res.s3, status="not_won"), s4=(not_run, res.s4[1]))
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=lost).outcome, "KEEP")
        s7_off = replace(res, s7=replace(res.s7, status="not_run", reason="HAC SE is zero or non-finite"))
        self.assertEqual(S.strategy_outcome(gate_verdict="PASS", lines=s7_off).basis, "S-7 power line not run")
        # criteria 6.4 N12: a NaN DSR does not meet S-2 and is INSUFFICIENT_DATA, the gate's REVISE included.
        nan_record = S.strategy_outcome(gate_verdict="PASS", lines=self.build(rfam=float("nan")))
        self.assertEqual((nan_record.outcome, nan_record.basis), ("INSUFFICIENT_DATA", "criteria 6.4 N12"))
        nan_gate = self.build(grid=float("nan"), rfam=float("nan"))
        self.assertEqual(S.strategy_outcome(gate_verdict="REVISE", lines=nan_gate).outcome, "INSUFFICIENT_DATA")
        self.assertEqual(S.strategy_outcome(gate_verdict="REJECT", lines=nan_gate).outcome, "REJECT")
        self.assertEqual(S.strategy_outcome(gate_verdict="REVISE", lines=res).outcome, "REVISE")
        with self.assertRaisesRegex(S.AdoptionInputError, "not from one run"):
            S.strategy_outcome(gate_verdict="PASS", lines=nan_gate)
        # Refused inputs.
        for bad in ("pass", "ADOPT", "KEEP", " PASS", "", None, 1):
            with self.subTest(verdict=bad), self.assertRaisesRegex(S.AdoptionInputError, "validate.DECISIONS"):
                S.strategy_outcome(gate_verdict=bad, lines=res)
        off = replace(res.s4[0], conforms_to_registration=False, B=50)
        for bad, needle in ((res.s2, "strategy_lines result"), (replace(res, s3=None), "counting S-3"),
                            (replace(res, s3=replace(res.s3, counts=False)), "counting S-3"),
                            (replace(res, s7=None), "S-7 power line"), (replace(res, s4=()), "registered baseline"),
                            (replace(res, s4=(off,)), "OFF-REGISTRATION"), (replace(res, kind="swap"), "kind"),
                            (replace(res, s2=replace(res.s2, readings=res.s2.readings[:1])), "R-FAM line")):
            with self.subTest(needle=needle), self.assertRaisesRegex(S.AdoptionInputError, needle):
                S.strategy_outcome(gate_verdict="PASS", lines=bad)
        with self.assertRaises(TypeError):
            S.strategy_outcome("PASS", res)                       # keyword-only

    def test_outcome_changes_no_number_or_line_of_earlier_units(self):
        a, inc = pair(T=756, seed=5, edge=0.0008)                # the gate's DSR at N = G passes (0.9952)
        rng = np.random.default_rng(2)
        base = {"equal-weight": (rng.normal(0.0002, 0.008, 756), self.ds), "cash": S.CASH_BASELINE}
        kw = dict(kind="replace", challenger=a, challenger_dates=self.ds, n_grid=self.G, sr_sd_grid=0.011,
                  n_raw={"L-FAM": self.L, "R-FAM": self.R}, sr_sd_daily=0.011, sr_sd_label="the gate's term",
                  baselines=base, incumbent=inc, incumbent_dates=self.ds, expected_dsr=0.25)
        res = S.strategy_lines(**kw)                              # real numbers, nothing stubbed
        self.assertEqual(res.s2.status_grid, "pass")
        before, snapshot = res.lines(), copy.deepcopy(res)
        strict = S.dsr_two_n(a, n_grid=self.G, sr_sd_grid=0.011, n_raw={"L-FAM": self.L, "R-FAM": self.R},
                             sr_sd_daily=0.03, sr_sd_label="stricter")
        strict_before = strict.lines()
        outs = [S.strategy_outcome(gate_verdict=v, lines=res, reference_s2=strict) for v in V.DECISIONS]
        self.assertEqual(res.lines(), before)
        self.assertEqual(res, snapshot)
        self.assertEqual(res, S.strategy_lines(**kw))
        self.assertEqual(strict.lines(), strict_before)
        for out in outs:
            self.assertIs(out.strategy, res)
            with self.assertRaises(FrozenInstanceError):
                out.outcome = "ADOPT"
            for name in ("provisional", "replaces_incumbent", "provisional_basis", "kind"):
                with self.subTest(name=name), self.assertRaises(AttributeError):
                    setattr(out, name, True)
        d11 = V.deflated_sharpe(a, n_trials=self.R, sr_sd_daily=0.011)
        self.assertEqual(res.s2.readings[1].dsr, d11)
        text = "\n".join(outs[0].lines())
        self.assertIn(f"S-2 DSR at N_raw R-FAM = 11: {d11:.4f} ({res.s2.readings[1].status}); the second DSR of "
                      "record, with the gate's dispersion term (B-Q2)", text)
        self.assertIn(f"DSR at N = G = 12: {res.s2.dsr_grid:.4f} ({res.s2.status_grid})", text)
        if res.s7.status == "printed":
            self.assertTrue(f"MDE80 {res.s7.mde80:.4f}" in text or res.s2.status_grid != "pass")
        self.assertEqual(res.notes[0], "no outcome label on these lines: strategy_outcome (⑨-4/2/c) assembles the "
                                       "outcome of criteria 6.1 from them and the gate's verdict")
        self.assertEqual(res.unit, "⑨-4/2/a")
        self.assertEqual(outs[0].unit, "⑨-4/2/c")


class ScopeGuards(unittest.TestCase):
    def test_no_file_network_or_process_effects(self):
        a, inc = pair()
        ds = sessions(a.size)
        base = {"equal-weight": (np.random.default_rng(2).normal(0.0002, 0.008, a.size), ds)}

        def run_all():
            S.check_sample_end("2026-06-30")
            S.gate_sr_sd_daily(np.column_stack([a, inc]))
            S.strategy_lines(kind="replace", challenger=a, challenger_dates=ds, n_grid=4, sr_sd_grid=0.01,
                             n_raw={"L-FAM": 6, "R-FAM": 5}, sr_sd_daily=0.01, sr_sd_label="x",
                             baselines={**base, "cash": S.CASH_BASELINE}, incumbent=inc, incumbent_dates=ds,
                             expected_dsr=0.2)
            S.lw_compare(a[:20], inc[:20], ds[:20], ds[:20], rule="S-4", other_label="short")
            S.lw_compare(inc, inc.copy(), ds, ds, rule="S-4", other_label="itself", B=200)
            S.strategy_outcome(gate_verdict="PASS", lines=S.strategy_lines(
                kind="add", challenger=a, challenger_dates=ds, n_grid=4, sr_sd_grid=0.01, n_raw={"R-FAM": 5},
                sr_sd_daily=0.01, sr_sd_label="gate term", baselines={"cash": S.CASH_BASELINE}))

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
                self.assertEqual(mods, {"__future__", "math", "re", "collections.abc", "dataclasses", "datetime",
                                        "types", "typing", "numpy", "core.quant"})
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
                "power_line_s7": ("S-7", "M-6"), "strategy_lines": ("M-19", "M-20"),
                "strategy_outcome": ("6.1", "B-Q1")}
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
