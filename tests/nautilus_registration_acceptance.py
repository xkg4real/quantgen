"""Bounded O11 A2 acceptance: metadata + disposable ledgers, no production data.

Run: python -B -m unittest tests.nautilus_registration_acceptance -v
The existing full Nautilus acceptance suite is deliberately not imported.
"""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


def _no_private_io(event, args):
    if event == "socket.connect":
        raise AssertionError("O11 acceptance must not connect to a provider")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0])
    if path.name == ".env" or set(path.parts) & {"cache", "paper_live", "grokteam", "_backup",
                                               "QUANTGEN_techfund_research_bundle"}:
        raise AssertionError(f"protected input must not be opened: {path}")
    if path.suffix in (".jsonl", ".csv") and not path.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise AssertionError(f"test ledger/data must be temporary: {path}")


sys.addaudithook(_no_private_io)
# Existing History imports config. Disable .env loading only in this test
# process; leave application configuration and its environment untouched.
with patch("dotenv.load_dotenv", return_value=False):
    from tools.nautilus import register_e1 as A
G, R = A.G, A.R
FIXTURE = R.REPO_ROOT / "docs/nautilus_bridge/registration/pilot1_E1_spy.json"


class RegistrationAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qg-a2-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        (self.repo / ".git").mkdir(parents=True)
        (self.repo / ".git/HEAD").write_text("a" * 40 + "\n", encoding="utf-8")
        self.table = self.root / "table.json"
        self.table.write_bytes(FIXTURE.read_bytes())
        self.ledger_dir, self.out = self.root / "ledgers", self.root / "out"
        self.ledger = G.family_ledger("E1", self.ledger_dir)
        self.guards = self.enterContext(ExitStack())
        for name in ("load_prices", "load_rf", "_check_reference", "code_sha256"):
            self.guards.enter_context(patch.object(R, name, side_effect=AssertionError(f"forbidden {name}")))
        self.guards.enter_context(patch.object(R.launch, "run_child", side_effect=AssertionError("no engine")))

    def run_a2(self, **kwargs):
        return A.register(self.table, mode="rehearsal", ledger_dir=self.ledger_dir,
                          out_dir=self.out, repo_root=self.repo, **kwargs)

    def mutate_table(self, fn):
        t = json.loads(self.table.read_text(encoding="utf-8"))
        fn(t)
        self.table.write_text(json.dumps(t), encoding="utf-8")

    def test_12_unique_rows_counts_and_no_data_or_owner_write(self):
        before = self.table.read_bytes()
        out = self.run_a2()
        rows = self.ledger.rows()
        self.assertEqual((out["status"], len(rows)), ("REGISTERED_ONLY", 12))
        self.assertEqual({k: out["counts"][k] for k in ("family_n_raw", "market_n_raw", "U", "n_trials")},
                         {"family_n_raw": 12, "market_n_raw": 12, "U": 24, "n_trials": 36})
        self.assertEqual(len(set(out["config_ids"])), 12)
        self.assertTrue(self.ledger.verify_chain())
        self.assertEqual(before, self.table.read_bytes())
        self.assertFalse((self.ledger_dir / "C3.jsonl").exists())
        self.assertEqual(list(self.repo.rglob("*.csv")), [])
        for key in ("prices_read", "pilot_executed", "owner_confirmed_written"):
            self.assertIs(out[key], False)
        # Identity must match the existing runner; pin lookup is metadata and
        # replaced here to keep the test independent of installed engines.
        t = json.loads(before)
        with patch.object(R.launch, "expected_versions", return_value={"nautilus-trader": "test-metadata-only"}):
            expected = [G.config_id(R.ledger_row(t, theta, span=[t["start"], t["end"]],
                        run_utc=out["created_utc"], anchor=out["source_anchor"], bridge_run_id="test"))
                        for theta in t["grid"]]
        self.assertEqual(out["config_ids"], expected)

    def test_retry_is_byte_idempotent(self):
        first = self.run_a2()
        before = self.ledger.path.read_bytes()
        second = self.run_a2()
        self.assertEqual(before, self.ledger.path.read_bytes())
        self.assertEqual(first, second)

    def test_crash_after_append_before_receipt_resumes_only_remaining(self):
        calls = []
        def interrupted(ledger, row, **kw):
            result = G.register_trial(ledger, row, **kw)
            calls.append(result)
            if len(calls) == 4:
                raise OSError("simulated power loss after fourth append")
            return result
        with self.assertRaisesRegex(OSError, "power loss"):
            self.run_a2(register_fn=interrupted)
        prefix = self.ledger.path.read_bytes()
        self.assertEqual(len(self.ledger.rows()), 4)
        out = self.run_a2()
        self.assertEqual(out["n_registered"], 12)
        self.assertTrue(self.ledger.path.read_bytes().startswith(prefix))

    def test_changed_grid_refuses_before_append(self):
        self.mutate_table(lambda t: t["grid"].pop())
        with self.assertRaises((ValueError, R.BridgeRefusal)):
            self.run_a2()
        self.assertFalse(self.ledger.path.exists())

    def test_duplicate_study_configuration_refuses_before_append(self):
        self.mutate_table(lambda t: t["study_configs"].__setitem__(1, copy.deepcopy(t["study_configs"][0])))
        with self.assertRaisesRegex(ValueError, "24 documented"):
            self.run_a2()
        self.assertFalse(self.ledger.path.exists())

    def test_existing_unrelated_ledger_is_not_overwritten(self):
        t = json.loads(self.table.read_text())
        row = A._planned_rows(t, "2026-10-30T00:00:00Z", "git:" + "a" * 40, R.table_sha256(t))[0]
        row["params"]["lookback"] = 99
        G.register_trial(self.ledger, row, script=A.SCRIPT)
        before = self.ledger.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "non-empty E1"):
            self.run_a2()
        self.assertEqual(before, self.ledger.path.read_bytes())

    def test_broken_chain_refuses_without_modification(self):
        self.run_a2()
        bad = self.ledger.path.read_bytes().replace(b'"US"', b'"ZZ"', 1)
        self.ledger.path.write_bytes(bad)
        with self.assertRaises(G.LedgerRefused):
            self.run_a2()
        self.assertEqual(bad, self.ledger.path.read_bytes())

    def test_receipt_prevents_recreation_of_lost_rows(self):
        self.run_a2()
        self.ledger.path.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "lost rows"):
            self.run_a2()
        self.assertEqual(self.ledger.path.read_bytes(), b"")

    def test_invalid_receipt_refuses(self):
        out = self.run_a2()
        path = Path(out["receipt_path"])
        for invalid in ([], {"schema": A.SCHEMA}, dict(out, status="PILOT_PASS")):
            with self.subTest(invalid=invalid.get("status") if isinstance(invalid, dict) else "list"):
                path.write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.run_a2()
                self.assertEqual(len(self.ledger.rows()), 12)

    def test_same_table_lock_blocks_registration(self):
        t = json.loads(self.table.read_text())
        lock, _ = R.take_lock(self.out, R.table_sha256(t), [], None)
        try:
            with self.assertRaisesRegex(R.BridgeRefusal, "R-16"):
                self.run_a2()
            self.assertFalse(self.ledger.path.exists())
        finally:
            lock.release()

    def test_competing_writer_is_detected_before_success(self):
        def competing(ledger, row, **kw):
            result = G.register_trial(ledger, row, **kw)
            foreign = copy.deepcopy(row)
            foreign["params"]["lookback"] = 99
            G.register_trial(ledger, foreign, **kw)
            return result
        with self.assertRaisesRegex(ValueError, "unrelated/reordered"):
            self.run_a2(register_fn=competing)
        self.assertEqual(len(self.ledger.rows()), 2)
        with self.assertRaises(ValueError):
            self.run_a2()

    def test_owner_mode_refuses_non_windows_without_table_io(self):
        with patch.object(A.sys, "platform", "linux"), patch.object(R, "load_table", side_effect=AssertionError("read")):
            with self.assertRaisesRegex(ValueError, "Windows PC"):
                A.register(Path("does-not-exist"), mode="owner-windows")

    def test_rehearsal_refuses_non_temp_directory_before_table_read(self):
        with patch.object(R, "load_table", side_effect=AssertionError("read")):
            with self.assertRaisesRegex(ValueError, "all be temporary"):
                A.register(self.table, mode="rehearsal", ledger_dir=Path.home() / "not-a-test-ledger", out_dir=self.out)

    def test_normal_runner_still_needs_owner_confirmation_and_freshness(self):
        self.run_a2()
        t = json.loads(self.table.read_text())
        with self.assertRaisesRegex(R.BridgeRefusal, "owner_confirmed"):
            R._check_fields(t, "of-record")
        with self.assertRaisesRegex(R.BridgeRefusal, "R-16"):
            R.take_lock(self.out, R.table_sha256(t), [self.ledger.path], None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
