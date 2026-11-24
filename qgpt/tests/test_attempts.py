"""Attempt ledger: append only, no way around the count, and a DSR that matches a hand calculation."""
import ast
import importlib.util
import json
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path
from statistics import NormalDist

from _path import HOST, ROOT

from quantgpt.registry import AttemptLedger, LedgerRefused, attempt_id
from quantgpt.registry import dsr

BASE = {"family": "lora-explain", "objective": "T-EXPLAIN number accuracy", "data_version": "sft-v0@abc123",
        "hyperparameters": {"rank": 8, "lr": 0.0002, "epochs": 3}, "seed": 11, "model_version": "base-a@r1",
        "run_utc": "2026-11-24T10:00:00Z"}
HAND = [0.02, -0.01, 0.03, 0.00, 0.01]


def attempt(**changes):
    row = json.loads(json.dumps(BASE))
    row.update(changes)
    return row


def series(seed, mean=0.0006, n=400):
    rng = random.Random(seed)
    return [rng.gauss(mean, 0.01) for _ in range(n)]


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name) / "attempts.jsonl"
        self.ledger = AttemptLedger(self.path)

    def run_one(self, seed, returns=None, family="lora-explain"):
        row, _ = self.ledger.register(attempt(seed=seed, family=family))
        if returns is not None:
            self.ledger.record_result({"attempt_id": row["attempt_id"], "metrics": {"loss": 0.1},
                                       "run_utc": "2026-11-24T11:00:00Z",
                                       "sharpe_per_period": dsr.per_period_sharpe(returns),
                                       "n_periods": len(returns)})
        return row["attempt_id"]


class IdentityTests(LedgerCase):
    def test_each_of_the_five_fields_makes_a_new_attempt(self):
        first, appended = self.ledger.register(attempt())
        self.assertTrue(appended)
        changes = [{"objective": "T-EXPLAIN abstain calibration"}, {"data_version": "sft-v1@def456"},
                   {"hyperparameters": {"rank": 16, "lr": 0.0002, "epochs": 3}}, {"seed": 12},
                   {"model_version": "base-b@r1"}]
        ids = {first["attempt_id"]}
        for change in changes:
            row, appended = self.ledger.register(attempt(**change))
            self.assertTrue(appended, change)
            ids.add(row["attempt_id"])
        self.assertEqual(len(ids), 6)
        self.assertEqual(self.ledger.n_trials("lora-explain"), 6)

    def test_the_same_five_fields_are_counted_once(self):
        first, _ = self.ledger.register(attempt())
        again, appended = self.ledger.register(attempt(run_utc="2026-11-25T10:00:00Z", note="second start"))
        self.assertFalse(appended)
        self.assertEqual(again, first)
        reordered = attempt(hyperparameters={"epochs": 3, "lr": 0.0002, "rank": 8})
        self.assertEqual(attempt_id(reordered), first["attempt_id"])
        self.assertEqual(self.ledger.n_trials("lora-explain"), 1)

    def test_refused_rows(self):
        bad = [attempt(seed=-1), attempt(seed=1.5), attempt(objective=""), attempt(run_utc="2026-11-24 10:00"),
               attempt(run_utc="2026-11-24T10:00:00+09:00"), attempt(hyperparameters={"lr": float("nan")}),
               attempt(n_trials=1), attempt(family="has space"),
               {k: v for k, v in BASE.items() if k != "model_version"}]
        for row in bad:
            with self.subTest(row=str(row)[:60]), self.assertRaises(LedgerRefused):
                self.ledger.register(row)
        self.assertEqual(self.ledger.rows(), [])


class NoWayAroundTests(LedgerCase):
    def test_the_ledger_has_no_method_that_changes_or_removes_a_line(self):
        public = sorted(n for n in dir(AttemptLedger) if not n.startswith("_"))
        self.assertEqual(public, ["attempts", "deflated_sharpe", "head", "n_trials", "path", "record_result",
                                  "register", "results", "rows", "verify_chain"])
        with self.assertRaises(AttributeError):
            self.ledger.path = self.path.with_name("other.jsonl")

    def test_the_source_only_appends(self):
        source = (ROOT / "quantgpt/registry/attempts.py").read_text(encoding="utf-8")
        calls = {ast.unparse(n.func) for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call)}
        for banned in ("open", "os.remove", "os.unlink", "os.rename", "os.replace", "os.truncate", "os.ftruncate",
                       "shutil.move", "shutil.rmtree"):
            self.assertNotIn(banned, calls)
        self.assertFalse([c for c in calls if c.endswith((".write_text", ".write_bytes", ".unlink", ".rename",
                                                          ".replace", ".truncate", ".seek"))])
        self.assertIn("os.O_APPEND", source)
        self.assertNotIn("O_TRUNC", source)

    def test_every_write_keeps_the_earlier_bytes(self):
        before = b""
        for seed in range(5):
            self.run_one(seed, series(seed))
            now = self.path.read_bytes()
            self.assertTrue(now.startswith(before) and len(now) > len(before))
            before = now
        self.assertEqual(self.ledger.verify_chain().n_rows, 10)

    def test_a_result_needs_a_registered_attempt_and_there_is_only_one(self):
        result = {"attempt_id": "0" * 64, "metrics": {}, "run_utc": "2026-11-24T11:00:00Z"}
        with self.assertRaises(LedgerRefused):
            self.ledger.record_result(result)
        identity = self.run_one(1, series(1))
        with self.assertRaises(LedgerRefused):
            self.ledger.record_result({**result, "attempt_id": identity})
        with self.assertRaises(LedgerRefused):
            self.ledger.record_result({**result, "attempt_id": identity, "n_trials": 1})
        self.assertEqual(len(self.ledger.results()), 1)

    def test_attempts_without_a_result_still_count(self):
        best = self.run_one(0, series(0))
        alone = self.ledger.deflated_sharpe(best, series(0))
        for seed in range(1, 8):
            self.run_one(seed, series(seed) if seed < 3 else None)      # five runs are never reported
        after = self.ledger.deflated_sharpe(best, series(0))
        self.assertEqual((alone["n_trials"], after["n_trials"], after["n_with_result"]), (1, 8, 3))
        self.assertLess(after["dsr"], alone["dsr"])

    def test_the_caller_cannot_choose_the_trial_count_or_the_returns(self):
        best = self.run_one(0, series(0))
        with self.assertRaises(TypeError):
            self.ledger.deflated_sharpe(best, series(0), n_trials=1)
        with self.assertRaises(LedgerRefused):
            self.ledger.deflated_sharpe(best, series(99))               # not the recorded run
        with self.assertRaises(LedgerRefused):
            self.ledger.deflated_sharpe("f" * 64, series(0))
        unreported = self.run_one(5)
        with self.assertRaises(LedgerRefused):
            self.ledger.deflated_sharpe(unreported, series(5))

    def test_another_family_does_not_dilute_or_hide_the_count(self):
        best = self.run_one(0, series(0))
        self.run_one(1, series(1), family="other")
        self.assertEqual(self.ledger.deflated_sharpe(best, series(0))["n_trials"], 1)
        self.assertEqual(self.ledger.n_trials("other"), 1)

    def test_no_other_module_of_the_package_computes_a_dsr(self):
        users = []
        for path in (ROOT / "quantgpt").rglob("*.py"):
            if path.parent.name == "registry":
                continue
            text = path.read_text(encoding="utf-8")
            if "deflated_sharpe" in text or "registry.dsr" in text or "import dsr" in text:
                users.append(path.name)
        self.assertEqual(users, [])
        import quantgpt.registry as registry
        self.assertEqual(registry.__all__, ["AttemptLedger", "LedgerRefused", "attempt_id"])


class TamperTests(LedgerCase):
    def setUp(self):
        super().setUp()
        self.ids = [self.run_one(seed, series(seed)) for seed in range(3)]
        self.lines = self.path.read_bytes().split(b"\n")[:-1]

    def write(self, lines):
        self.path.write_bytes(b"\n".join(lines) + b"\n")

    def test_edits_are_found_and_stop_every_read_and_write(self):
        edited = json.loads(self.lines[2]); edited["seed"] = 99
        cases = {
            "edited": self.lines[:2] + [json.dumps(edited, sort_keys=True, separators=(",", ":")).encode()]
                      + self.lines[3:],
            "dropped": self.lines[:2] + self.lines[3:],
            "moved": [self.lines[2], self.lines[3], self.lines[0], self.lines[1]] + self.lines[4:],
            "reformatted": [json.dumps(json.loads(self.lines[0]), indent=1).replace("\n", " ").encode()]
                           + self.lines[1:],
            "garbage": self.lines + [b"not json"],
            "head_cut": self.lines[2:],
        }
        for name, lines in cases.items():
            with self.subTest(name=name):
                self.write(lines)
                self.assertFalse(self.ledger.verify_chain())
                for call in (self.ledger.rows, self.ledger.head, lambda: self.ledger.register(attempt(seed=50)),
                             lambda: self.ledger.n_trials("lora-explain"),
                             lambda: self.ledger.deflated_sharpe(self.ids[0], series(0))):
                    with self.assertRaises(LedgerRefused):
                        call()

    def test_a_result_cannot_be_moved_to_another_attempt_or_ahead_of_it(self):
        self.write([self.lines[0], self.lines[1]])
        self.assertTrue(self.ledger.verify_chain())
        self.write([self.lines[1], self.lines[0]])
        self.assertFalse(self.ledger.verify_chain())

    def test_a_cut_tail_is_found_against_a_pinned_head(self):
        self.write(self.lines)
        pin = self.ledger.head()
        self.assertTrue(self.ledger.verify_chain(pin))
        self.run_one(7, series(7))
        self.assertTrue(self.ledger.verify_chain(pin))                  # growing keeps the pin
        self.write(self.lines[:4])                                      # the last attempt and result removed
        self.assertTrue(self.ledger.verify_chain())                     # the chain alone cannot see it
        self.assertFalse(self.ledger.verify_chain(pin))
        self.assertEqual(self.ledger.n_trials("lora-explain"), 2)


class DsrHandCalculationTests(unittest.TestCase):
    """x = [0.02, -0.01, 0.03, 0.00, 0.01]: mean 0.01; deviations 0.01, -0.02, 0.02, -0.01, 0.

    Squares sum to 1e-3: variance 2e-4 (dividing by 5), 2.5e-4 (dividing by 4), so SR = 0.01 / sqrt(2.5e-4)
    = sqrt(0.4) = 0.632456. Cubes sum to 0: skewness 0. Fourth powers sum to 3.4e-7: m4 = 6.8e-8,
    kurtosis 6.8e-8 / (2e-4)^2 = 1.7. Denominator 1 - 0 + (1.7 - 1)/4 * 0.4 = 1.07; sqrt(T - 1) = 2.
    """

    def test_moments(self):
        sr, g3, g4, t = dsr.moments(HAND)
        self.assertAlmostEqual(sr, math.sqrt(0.4), places=12)
        self.assertAlmostEqual(g3, 0.0, places=12)
        self.assertAlmostEqual(g4, 1.7, places=12)
        self.assertEqual(t, 5)
        self.assertEqual(dsr.moments([0.01] * 5), (0.0, 0.0, 3.0, 5))
        with self.assertRaises(ValueError):
            dsr.moments([0.01, 0.02])

    def test_one_trial_has_no_deflation(self):
        # z = 0.632456 * 2 / sqrt(1.07) = 1.222836; Phi(1.222836) = 0.889305
        self.assertEqual(dsr.expected_max_sharpe(1, 0.5), 0.0)
        self.assertAlmostEqual(dsr.deflated_sharpe(HAND, n_trials=1, sr_sd=0.5), 0.889305, places=5)

    def test_two_trials(self):
        # N = 2: Z(1 - 1/2) = 0 and Z(1 - 1/(2e)) = Z(0.816060) = 0.900458, so e(2) = 0.5772157 * 0.900458
        # = 0.519759 (the host's "closed-form 0.520"). With sd 0.1: SR0 = 0.0519759;
        # z = (0.632456 - 0.051976) * 2 / 1.034408 = 1.122343; Phi = 0.869140
        self.assertAlmostEqual(dsr.expected_max_sharpe(2, 1.0), 0.519759, places=5)
        self.assertAlmostEqual(dsr.deflated_sharpe(HAND, n_trials=2, sr_sd=0.1), 0.869140, places=5)

    def test_twelve_trials_and_the_null_case(self):
        # N = 12: Z(11/12) = 1.382994, Z(1 - 1/(12e)) = Z(0.969343) = 1.871230;
        # e(12) = 0.4227843 * 1.382994 + 0.5772157 * 1.871230 = 0.584708 + 1.080103 = 1.664811
        self.assertAlmostEqual(dsr.expected_max_sharpe(12, 1.0), 1.664811, places=5)
        # SR equal to the expected maximum gives exactly one half.
        sr = math.sqrt(0.4)
        self.assertAlmostEqual(dsr.deflated_sharpe(HAND, n_trials=12, sr_sd=sr / 1.6648114), 0.5, places=6)

    def test_deflated_delta(self):
        # Phi((0.30 - 0.10 * 1.664811) / 0.12) = Phi(1.112657) = 0.867072
        self.assertAlmostEqual(dsr.deflated_delta(0.30, 0.12, 0.10, 1.664811), 0.867072, places=5)
        self.assertAlmostEqual(dsr.deflated_delta(0.0, 0.12, 0.0, 5.0), 0.5, places=12)
        with self.assertRaises(ValueError):
            dsr.deflated_delta(0.3, 0.0, 0.1, 1.0)

    def test_the_ledger_uses_the_family_count_and_population_dispersion(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = AttemptLedger(Path(folder) / "a.jsonl")
            runs = {seed: series(seed) for seed in range(4)}
            ids = {}
            for seed, returns in runs.items():
                row, _ = ledger.register(attempt(seed=seed))
                ids[seed] = row["attempt_id"]
                ledger.record_result({"attempt_id": row["attempt_id"], "metrics": {}, "run_utc": BASE["run_utc"],
                                      "sharpe_per_period": dsr.per_period_sharpe(returns), "n_periods": 400})
            out = ledger.deflated_sharpe(ids[0], runs[0])
            sharpes = [dsr.per_period_sharpe(r) for r in runs.values()]
            mean = sum(sharpes) / 4
            sd = math.sqrt(sum((s - mean) ** 2 for s in sharpes) / 4)
            self.assertAlmostEqual(out["sr_sd"], sd, places=15)
            self.assertEqual(out["n_trials"], 4)
            sr, g3, g4, t = dsr.moments(runs[0])
            z = (sr - out["expected_max_sharpe"]) * math.sqrt(t - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr * sr)
            self.assertAlmostEqual(out["dsr"], NormalDist().cdf(z), places=12)
            self.assertEqual(out["ledger_head"], ledger.head())


def _host_validate():
    path = HOST / "core" / "quant" / "validate.py"
    if not path.is_file() or importlib.util.find_spec("scipy") is None or importlib.util.find_spec("numpy") is None:
        return None
    spec = importlib.util.spec_from_file_location("_host_quant_validate", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class HostDefinitionTests(unittest.TestCase):
    def test_same_numbers_as_the_host_definitions(self):
        host = _host_validate()
        if host is None:
            self.skipTest("the host module, numpy or scipy is not present")
        import numpy as np
        self.assertEqual(host.EULER_GAMMA, dsr.EULER_GAMMA)
        for n in (1, 2, 3, 12, 34, 21408):
            self.assertAlmostEqual(host.expected_max_sharpe(n, 0.02), dsr.expected_max_sharpe(n, 0.02), places=10)
        for seed in range(6):
            x = series(seed, mean=0.0002 * seed, n=300 + 50 * seed)
            for n, sd in ((1, 0.0), (12, 0.02), (200, 0.05)):
                with self.subTest(seed=seed, n=n):
                    self.assertAlmostEqual(host.deflated_sharpe(np.array(x), n_trials=n, sr_sd_daily=sd),
                                           dsr.deflated_sharpe(x, n_trials=n, sr_sd=sd), places=9)
        self.assertAlmostEqual(host.deflated_sharpe(np.array(HAND), n_trials=2, sr_sd_daily=0.1), 0.869140, places=5)
        columns = np.array([series(s, n=300) for s in range(5)]).T
        host_sd = float(np.nanstd(host._col_sharpe(columns) / math.sqrt(host.TRADING_DAYS)))
        mine = dsr.population_sd([dsr.per_period_sharpe(list(columns[:, j])) for j in range(5)])
        self.assertAlmostEqual(host_sd, mine, places=12)


if __name__ == "__main__":
    unittest.main()
