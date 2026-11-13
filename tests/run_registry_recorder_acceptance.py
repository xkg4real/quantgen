"""Synthetic detached recorder checks; no Lab, real ledger or user state."""
import ast
import copy
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.quant import run_registry_codec as codec
from core.quant.run_registry_fold import fold_runs
from core.quant import run_registry_recorder as recorder
from core.quant.run_registry_store import (
    AppendOutcomeUncertain, LockTimeout, SingleSegmentStore, StoreError,
)


AT = datetime(2026, 11, 14, tzinfo=timezone.utc)
KEYS = [{"theta_index": 0, "config_id": "1" * 32}]
# Literal expected list is independent of the implementation constant.
Q12 = (
    "core/quant/strategies.py", "core/quant/validate.py",
    "core/quant/history.py", "core/quant/gate_ledger.py",
    "core/research/strategy_workflow.py", "core/quant/optimize.py",
    "core/quant/risk.py",
)


def request():
    return {"family": "synthetic trend", "family_id": "E1",
            "symbols_typed": ["TEST"], "source_requested": "synthetic",
            "cost_bps_requested": 1.0, "days": 100, "bootstrap_B": 10,
            "seed": 11, "intent": "exploratory", "declaration_id": None,
            "planned": copy.deepcopy(KEYS), "fn_qualname": "fixture.trend",
            "fn_source_sha256": "2" * 64, "fn_source_sha256_raw": "3" * 64,
            "repo_anchor": "UNVERSIONED", "gate_version": "fixture",
            "files": {p: {"lf": "4" * 64, "raw": "5" * 64} for p in Q12},
            "canonical_panel": {"path": "fixture-only.npy", "sha256": "6" * 64},
            "env": {"python": "fixture", "numpy": "fixture", "scipy": "fixture",
                    "pandas": "fixture", "system": "fixture", "machine": "fixture"},
            "grid": [{"length": 2}], "grid_sha256": "7" * 64}


def pnl():
    return {"registered": copy.deepcopy(KEYS), "synthetic": True,
            "symbols_resolved": ["TEST"], "span": ["2020-01-01", "2020-01-03"],
            "sessions": 3, "data_md5": "8" * 32, "holdout_touched": False,
            "per_symbol": [], "cost": {"cost_bps": 1.0},
            "keys_changed_by_symbol_resolution": False}


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.jsonl"
        self.small = SingleSegmentStore(self.path, lock_timeout=2)
        self.large = SingleSegmentStore(self.path, lock_timeout=10)
        self.outages = []
        self.at = AT
        self.rec = self.make()

    def make(self, **overrides):
        args = dict(in_run_store=self.small, after_run_store=self.large,
                    clock=lambda: self.at, monotonic=lambda: 0.0, token_source=lambda: "0123abcd",
                    outage_sink=self.outages.append, writer="synthetic test caller")
        args.update(overrides)
        return recorder.DetachedRecorder(**args)

    def rows(self):
        return self.small.read()

    def started(self):
        self.assertTrue(self.rec.started(request()))

    def computed(self):
        self.started()
        self.assertTrue(self.rec.advance("COST_RESOLVED"))
        self.assertTrue(self.rec.advance("DATA_LOADED"))
        self.assertTrue(self.rec.pnl_computed(pnl()))

    def folded(self, *, outage_ids=frozenset(), age=0):
        return fold_runs(self.rows(), as_of=self.at + timedelta(hours=age),
                         outage_run_ids=outage_ids).runs[0]

    def test_construction_has_no_clock_token_sink_or_file_side_effect(self):
        def forbidden():
            self.fail("constructor called an injected source")
        self.make(clock=forbidden, monotonic=forbidden, token_source=forbidden,
                  outage_sink=lambda _: self.fail("constructor wrote outage"))
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_q12_exact_seven_supplied_paths(self):
        self.assertEqual(recorder.SOURCE_PATHS, Q12)
        self.started()
        self.assertEqual(set(self.rows()[0]["files"]), set(Q12))

    def test_success_chain_and_lifecycle(self):
        self.computed()
        for stage in ("WALK_FORWARD_DONE", "LEDGER_REGISTERED", "SCORED"):
            self.assertTrue(self.rec.advance(stage))
        self.assertTrue(self.rec.after_run({"existing": {"decision": "fixture"}}, displayed=True))
        self.assertTrue(self.rec.fingerprint({"fingerprints": [], "cache_key": {}}))
        self.assertTrue(self.rec.shadow({"counts": {}, "classes": [], "rows": [],
                                       "error": None, "classifier_version": "fixture"}))
        self.at += timedelta(seconds=9)
        self.assertTrue(self.rec.finish(class_summary={"fixture": 1}))
        events = self.rows()
        self.assertEqual([x["event"] for x in events],
                         ["STARTED", "PROGRESS", "PROGRESS", "FINGERPRINT", "SHADOW", "FINISHED"])
        self.assertEqual([x["stage"] for x in events if x["event"] == "PROGRESS"],
                         ["PNL_COMPUTED", "DISPLAYED"])
        self.assertEqual(events[-1]["duration_s"], 9)
        record = self.folded()
        self.assertEqual(record.effective_status, "COMPLETED")
        self.assertEqual(record.flags, ())
        self.assertEqual(record.keys, ((0, "1" * 32),))
        self.assertEqual(self.outages, [])

    def test_early_stages_are_memory_only_owner_ruling_9(self):
        self.started()
        before = self.path.read_bytes()
        for stage in ("REQUESTED", "COST_RESOLVED", "DATA_LOADED"):
            self.assertTrue(self.rec.advance(stage))
            self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.rec.stage, "DATA_LOADED")

    def test_pre_stats_failure_is_recorded_only_on_close(self):
        self.started()
        self.rec.advance("DATA_LOADED")
        exc = ValueError("synthetic loader failure")
        self.assertTrue(self.rec.after_run({}, displayed=False, error=exc))
        self.assertTrue(self.rec.finish())
        self.assertEqual(self.folded().effective_status, "FAILED_BEFORE_STATS")
        self.assertEqual(self.folded().keys, None)
        self.assertEqual(self.rows()[-1]["error"], {"type": "ValueError", "message": str(exc)})

    def test_post_stats_failure_keeps_registered_keys(self):
        self.computed()
        self.assertTrue(self.rec.finish(error=ValueError("walk forward failed")))
        self.assertEqual(self.folded().effective_status, "FAILED_AFTER_STATS")
        self.assertEqual(self.folded().keys_source, "registered")
        self.assertEqual(self.folded().flags, ())

    def test_failure_finally_preserves_original_exception_object(self):
        self.computed()
        original = ValueError("original computation failure")
        caught = None
        with patch.object(self.large, "append", side_effect=OSError("sink unavailable")):
            try:
                try:
                    raise original
                finally:
                    self.rec.finish(error=original)
            except ValueError as exc:
                caught = exc
        self.assertIs(caught, original)
        self.assertEqual(self.rec.state, "DISABLED")
        self.assertEqual(self.rec.errors[0]["hook"], "finish")

    def test_shadow_computation_error_does_not_change_success(self):
        self.computed()
        self.rec.after_run({}, displayed=True)
        self.assertTrue(self.rec.shadow({"error": {"type": "ValueError", "message": "shadow only"}}))
        self.rec.finish()
        self.assertEqual(self.folded().effective_status, "COMPLETED")
        self.assertIsNone(self.rows()[-1]["error"])

    def test_rendering_failure_after_display_keeps_display_evidence(self):
        self.computed()
        self.assertTrue(self.rec.after_run({}, displayed=True, error=ValueError("later render failed")))
        self.assertTrue(self.rec.finish())
        self.assertEqual(self.rows()[-1]["displayed"], True)
        self.assertEqual(self.rows()[-1]["status"], "FAILED_AFTER_STATS")
        self.assertEqual(self.folded().flags, ())

    def test_abort_before_and_after_pnl(self):
        self.started()
        self.assertTrue(self.rec.finish(aborted=True))
        self.assertEqual(self.rows()[-1]["status"], "ABORTED")
        self.assertEqual(self.folded().effective_status, "FAILED_BEFORE_STATS")
        other = self.make(token_source=lambda: "0123abce")
        other.started(request())
        other.pnl_computed(pnl())
        other.finish(aborted=True)
        self.assertEqual(fold_runs(self.rows(), as_of=self.at).runs[1].effective_status,
                         "FAILED_AFTER_STATS")

    def test_repeated_terminal_hooks_do_not_append(self):
        self.started()
        self.rec.finish(error=ValueError("argument"))
        before = self.path.read_bytes()
        for call in (lambda: self.rec.finish(), lambda: self.rec.started(request()),
                     lambda: self.rec.advance("DATA_LOADED"), lambda: self.rec.pnl_computed(pnl()),
                     lambda: self.rec.after_run({}, displayed=False), lambda: self.rec.shadow({}),
                     lambda: self.rec.fingerprint({})):
            self.assertFalse(call())
        self.assertEqual(self.path.read_bytes(), before)

    def test_duplicate_start_id_draws_new_token(self):
        self.started()
        tokens = iter(("0123abcd", "abcd0123"))
        other = self.make(token_source=lambda: next(tokens))
        self.assertTrue(other.started(request()))
        self.assertTrue(other.run_id.endswith("abcd0123"))
        self.assertEqual(len(self.rows()), 2)

    def test_five_collisions_disable_without_naming_someone_elses_id(self):
        self.started()
        other = self.make()
        before = self.path.read_bytes()
        with patch.object(self.small, "append", wraps=self.small.append) as append:
            self.assertFalse(other.started(request()))
        self.assertEqual(append.call_count, 5)
        self.assertIsNone(other.run_id)
        self.assertIsNone(self.outages[-1]["run_id"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_uncertain_started_append_is_never_retried(self):
        with patch.object(self.small, "append", side_effect=AppendOutcomeUncertain("unknown")) as append:
            self.assertFalse(self.rec.started(request()))
        self.assertEqual(append.call_count, 1)
        self.assertEqual(self.outages[0]["run_id"], self.rec.run_id)
        self.assertIsNotNone(self.rec.run_id)

    def test_prewrite_failure_does_not_attribute_outage_to_unreserved_id(self):
        self.started()
        other = self.make()
        with patch.object(self.small, "append", side_effect=LockTimeout("busy")):
            self.assertFalse(other.started(request()))
        self.assertIsNone(other.run_id)
        self.assertIsNone(self.outages[-1]["run_id"])
        self.assertEqual(self.folded(age=7).effective_status, "FAILED_BEFORE_STATS")

    def test_collision_retries_share_one_two_second_lock_budget(self):
        self.started()
        ticks = iter((0.0, 0.75, 1.5))
        tokens = iter(("0123abcd", "abcd0123"))
        other = self.make(monotonic=lambda: next(ticks), token_source=lambda: next(tokens))
        with patch.object(self.small, "append", wraps=self.small.append) as append:
            self.assertTrue(other.started(request()))
        self.assertEqual([c.kwargs["lock_timeout"] for c in append.call_args_list], [1.25, 0.5])
        self.assertEqual(self.small.lock_timeout, 2)

    def test_exhausted_collision_budget_stops_before_another_append(self):
        self.started()
        ticks = iter((0.0, 1.0, 2.01))
        tokens = iter(("0123abcd", "abcd0123"))
        other = self.make(monotonic=lambda: next(ticks), token_source=lambda: next(tokens))
        with patch.object(self.small, "append", wraps=self.small.append) as append:
            self.assertFalse(other.started(request()))
        self.assertEqual(append.call_count, 1)
        self.assertIsNone(other.run_id)
        self.assertIsNone(self.outages[-1]["run_id"])

    def test_two_post_run_appends_share_the_ten_second_budget(self):
        self.computed()
        ticks = iter((0.0, 2.0, 7.0))
        self.rec._monotonic = lambda: next(ticks)
        with patch.object(self.large, "append", wraps=self.large.append) as append:
            self.assertTrue(self.rec.finish(error=ValueError("failure")))
        self.assertEqual([c.kwargs["lock_timeout"] for c in append.call_args_list], [8, 3])

    def test_per_call_store_timeout_does_not_mutate_or_wait_for_default(self):
        self.started()
        event = {"schema": codec.SCHEMA, "event": "PROGRESS", "run_id": self.rec.run_id,
                 "recorded_utc": "2026-11-14T00:00:00.000000Z", "writer": "test", "stage": "PNL_COMPUTED"}
        with self.small._locked(create=True):
            with self.assertRaises(LockTimeout):
                self.large.append(event, lock_timeout=0)
        self.assertEqual(self.large.lock_timeout, 10)
        self.assertEqual(len(self.rows()), 1)
        for bad in (True, -1, float("nan"), float("inf"), 11, "0"):
            with self.subTest(bad=bad), self.assertRaises(StoreError):
                self.large.append(event, lock_timeout=bad)

    def test_actual_fsync_failure_keeps_bytes_and_disables_later_events(self):
        self.started()
        before = self.path.read_bytes()
        with patch("core.quant.run_registry_store.os.fsync", side_effect=OSError("fixture fsync")):
            self.assertFalse(self.rec.pnl_computed(pnl()))
        after = self.path.read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertGreater(len(after), len(before))
        self.assertEqual(self.rec.errors[0]["type"], "AppendOutcomeUncertain")
        self.assertFalse(self.rec.finish())
        self.assertEqual(self.path.read_bytes(), after)

    def test_pnl_outage_without_progress_is_fail_closed_when_folded(self):
        self.started()
        self.rec.advance("DATA_LOADED")
        with patch.object(self.small, "append", side_effect=OSError("before writing PNL")):
            self.assertFalse(self.rec.pnl_computed(pnl()))
        self.assertEqual([e["event"] for e in self.rows()], ["STARTED"])
        record = self.folded(outage_ids=frozenset((self.rec.run_id,)), age=7)
        self.assertEqual(record.effective_status, "FAILED_AFTER_STATS")
        self.assertEqual(record.keys_source, "planned")
        self.assertIn("STAGE_UNKNOWN", record.flags)
        self.assertEqual(self.outages[0]["stage"], "PNL_COMPUTED")

    def test_broken_chain_is_not_repaired(self):
        self.started()
        with self.path.open("ab") as f:
            f.write(b'{"torn":')
        before = self.path.read_bytes()
        self.assertFalse(self.rec.pnl_computed(pnl()))
        self.assertEqual(self.rec.errors[0]["type"], "IntegrityError")
        self.assertEqual(self.path.read_bytes(), before)

    def test_outage_sink_failure_is_visible_and_does_not_escape(self):
        def outage(_):
            raise OSError("outage sink also failed")
        rec = self.make(outage_sink=outage)
        with patch.object(self.small, "append", side_effect=OSError("event sink failed")):
            self.assertFalse(rec.started(request()))
        self.assertEqual(rec.outage_error, {"type": "OSError", "message": "outage sink also failed"})
        exposed = rec.outage_error
        exposed["type"] = "edited"
        self.assertEqual(rec.outage_error["type"], "OSError")

    def test_first_failure_only_no_later_callback_side_effect(self):
        self.started()
        with patch.object(self.small, "append", side_effect=OSError("fail")) as append:
            self.rec.pnl_computed(pnl())
            for _ in range(3):
                self.rec.pnl_computed(pnl())
                self.rec.finish()
                self.rec.shadow({})
        self.assertEqual(append.call_count, 1)
        self.assertEqual(len(self.outages), 1)

    def test_caller_inputs_and_existing_verdict_are_unchanged(self):
        req, data = request(), pnl()
        verdict = {"decision": "REJECT", "reason": "original", "n_trials": 1}
        result = {"stats": {"sharpe": 0.25}, "existing": verdict}
        originals = copy.deepcopy((req, data, result))
        self.rec.started(req)
        self.rec.pnl_computed(data)
        self.rec.after_run(result, displayed=True)
        self.rec.finish()
        self.assertEqual((req, data, result), originals)
        req["symbols_typed"].append("LATER")
        data["registered"][0]["config_id"] = "0" * 32
        verdict["decision"] = "LATER"
        rows = self.rows()
        self.assertEqual(rows[0]["symbols_typed"], ["TEST"])
        self.assertEqual(rows[1]["registered"], KEYS)
        self.assertEqual(rows[2]["existing"]["decision"], "REJECT")

    def test_nonfinite_results_use_codec_markers(self):
        self.computed()
        self.rec.after_run({"stats": {"bench_p": float("nan")}}, displayed=True)
        self.rec.finish()
        closing = self.rows()[2]
        self.assertIsNone(closing["stats"]["bench_p"])
        self.assertEqual(closing["nonfinite"], ["/stats/bench_p"])

    def test_clock_failure_is_contained_and_not_invented(self):
        rec = self.make(clock=lambda: (_ for _ in ()).throw(OSError("clock")))
        self.assertFalse(rec.started(request()))
        self.assertIsNone(self.outages[-1]["recorded_utc"])
        self.assertFalse(self.path.exists())

    def test_naive_or_non_utc_clock_is_refused(self):
        for at in (AT.replace(tzinfo=None), AT.astimezone(timezone(timedelta(hours=9))), "now"):
            with self.subTest(at=at):
                rec = self.make(clock=lambda: at)
                self.assertFalse(rec.started(request()))
                self.assertEqual(rec.state, "DISABLED")
        self.assertFalse(self.path.exists())

    def test_bad_elapsed_clock_is_contained(self):
        for value in (float("nan"), float("inf"), True, "0"):
            with self.subTest(value=value):
                rec = self.make(monotonic=lambda: value)
                self.assertFalse(rec.started(request()))
                self.assertEqual(rec.state, "DISABLED")
        ticks = iter((1.0, 0.5))
        rec = self.make(monotonic=lambda: next(ticks))
        self.assertFalse(rec.started(request()))
        self.assertFalse(self.path.exists())

    def test_backward_clock_is_reported_at_last_observed_time(self):
        self.started()
        self.at -= timedelta(seconds=1)
        self.assertFalse(self.rec.pnl_computed(pnl()))
        self.assertEqual(self.outages[-1]["recorded_utc"], "2026-11-14T00:00:00.000000Z")

    def test_bad_exception_string_cannot_escape(self):
        class BadMessage(Exception):
            def __str__(self):
                raise ValueError("broken formatting")
        self.started()
        self.assertTrue(self.rec.finish(error=BadMessage()))
        self.assertEqual(self.rows()[-1]["error"]["message"], "Exception message unavailable")

    def test_error_messages_are_bounded(self):
        self.started()
        self.rec.finish(error=ValueError("한" * 600))
        self.assertEqual(len(self.rows()[-1]["error"]["message"]), 500)

    def test_base_exception_is_not_swallowed(self):
        class Stop(BaseException):
            pass
        original = Stop()
        with patch.object(self.small, "append", side_effect=original):
            with self.assertRaises(Stop) as caught:
                self.rec.started(request())
        self.assertIs(caught.exception, original)

    def test_stores_and_lock_budgets_are_checked_before_use(self):
        wrong = SingleSegmentStore(Path(self.temp.name) / "other.jsonl")
        for overrides in ({"after_run_store": wrong}, {"in_run_store": object()},
                          {"in_run_store": self.large}, {"clock": None},
                          {"token_source": None}, {"outage_sink": None}, {"writer": ""}):
            with self.subTest(overrides=overrides), self.assertRaises(recorder.RecorderError):
                self.make(**overrides)
        self.assertFalse(self.path.exists())

    def test_lock_budget_changes_are_refused(self):
        self.started()
        self.small.lock_timeout = 3
        self.assertFalse(self.rec.pnl_computed(pnl()))
        self.assertEqual(len(self.rows()), 1)

    def test_phase_store_selection(self):
        with patch.object(self.small, "append", wraps=self.small.append) as early, \
                patch.object(self.large, "append", wraps=self.large.append) as late:
            self.computed()
            self.rec.after_run({}, displayed=True)
            self.rec.finish()
        self.assertEqual([c.args[0]["event"] for c in early.call_args_list], ["STARTED", "PROGRESS"])
        self.assertEqual([c.args[0]["event"] for c in late.call_args_list], ["PROGRESS", "FINISHED"])

    def test_missing_or_old_q12_metadata_is_refused(self):
        for mutate in (lambda x: x.pop("env"),
                       lambda x: x["files"].pop(Q12[-1]),
                       lambda x: x["files"].update({"ui/strategy_lab_page.py": {"raw": "1" * 64, "lf": "1" * 64}}),
                       lambda x: x["files"][Q12[0]].update({"raw": "invalid"})):
            req = request()
            mutate(req)
            self.assertFalse(self.make().started(req))
        self.assertFalse(self.path.exists())

    def test_envelope_injection_and_unknown_fields_are_refused(self):
        for key in ("writer", "run_id", "schema", "row_md5", "nonfinite", "unknown"):
            req = request()
            req[key] = "injected"
            self.assertFalse(self.make().started(req))
        self.assertFalse(self.path.exists())

    def test_cross_phase_fields_are_refused(self):
        self.started()
        data = pnl()
        data["existing"] = {"decision": "too early"}
        self.assertFalse(self.rec.pnl_computed(data))
        self.assertEqual(len(self.rows()), 1)

    def test_bad_key_is_refused_before_pnl_append(self):
        self.started()
        data = pnl()
        data["registered"][0]["theta_index"] = True
        self.assertFalse(self.rec.pnl_computed(data))
        self.assertEqual(len(self.rows()), 1)

    def test_no_duplicate_or_backward_progress(self):
        self.computed()
        self.rec.advance("SCORED")
        self.assertFalse(self.rec.advance("DATA_LOADED"))
        self.assertEqual(len(self.rows()), 2)

    def test_pnl_requires_dedicated_hook_and_cannot_repeat(self):
        self.started()
        self.assertFalse(self.rec.advance("PNL_COMPUTED"))
        other = self.make(token_source=lambda: "0123abce")
        other.started(request())
        other.pnl_computed(pnl())
        self.assertFalse(other.pnl_computed(pnl()))
        self.assertEqual(sum(e["event"] == "PROGRESS" for e in self.rows()), 1)

    def test_display_cannot_precede_pnl(self):
        self.started()
        self.assertFalse(self.rec.after_run({}, displayed=True))
        self.assertEqual(len(self.rows()), 1)

    def test_post_run_events_cannot_be_written_inside_run(self):
        self.started()
        self.assertFalse(self.rec.fingerprint({"fingerprints": []}))
        self.assertEqual(len(self.rows()), 1)

    def test_run_cannot_resume_after_closing_progress(self):
        self.computed()
        self.rec.after_run({}, displayed=True)
        before = self.path.read_bytes()
        self.assertFalse(self.rec.advance("SCORED"))
        self.assertEqual(self.path.read_bytes(), before)

    def test_errors_are_exposed_as_copies(self):
        self.started()
        self.rec.advance("bad")
        error = self.rec.errors[0]
        error["hook"] = "changed"
        self.assertEqual(self.rec.errors[0]["hook"], "advance")

    def test_static_no_runtime_imports_discovery_or_direct_io(self):
        tree = ast.parse(inspect.getsource(recorder))
        forbidden = {"config", "gate_ledger", "strategies", "validate", "history",
                     "paper_live", "grokteam", "socket", "os", "subprocess", "time", "secrets"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names]
                if isinstance(node, ast.ImportFrom):
                    names.append(node.module or "")
                self.assertTrue(all(not forbidden.intersection(s.split(".")) for s in names))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                self.assertNotIn(name, {"open", "read_text", "write_text", "read_bytes", "write_bytes", "getenv", "getsource", "utcnow"})


if __name__ == "__main__":
    unittest.main()
