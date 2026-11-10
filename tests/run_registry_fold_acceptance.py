"""Synthetic acceptance for the pure R3 lifecycle and orphan fold.

Every event is invented in memory and chained with the existing codec. The one
round trip writes through SingleSegmentStore in a fresh TemporaryDirectory under
a scoped audit hook. No ledger, macro directory, configuration, environment,
provider, network or real registry is used.
"""
import ast
import builtins
from collections import OrderedDict
import copy
import dataclasses
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from core.quant import run_registry_codec as C
from core.quant import run_registry_fold as F
from core.quant import run_registry_store as S
from core.quant.run_registry_fold import FoldError


T0 = datetime(2026, 11, 10, 8, 0, 0, tzinfo=timezone.utc)
WRITER = "ui/strategy_lab_page.py"
R1 = "LAB-20261110T080000Z-E1-0000000a"
R2 = "LAB-20261110T080001Z-E1-0000000b"
R3 = "LAB-20261110T080002Z-C3-0000000c"
R4 = "LAB-20261110T080003Z-CRY-1-0000000d"
PLANNED = [{"theta_index": 0, "config_id": "0" * 31 + "a"},
           {"theta_index": 1, "config_id": "0" * 31 + "b"}]
REGISTERED = [{"theta_index": 0, "config_id": "1" * 31 + "a"},
              {"theta_index": 1, "config_id": "1" * 31 + "b"}]
P_KEYS = ((0, "0" * 31 + "a"), (1, "0" * 31 + "b"))
R_KEYS = ((0, "1" * 31 + "a"), (1, "1" * 31 + "b"))
HOUR = timedelta(hours=1)
SEC = timedelta(seconds=1)
UNSET = object()


def stamp(offset):
    return (T0 + offset).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def family(run):
    return run[len("LAB-YYYYMMDDTHHMMSSZ-"):-len("-0123abcd")]


def envelope(kind, run, at, **extra):
    event = {"schema": C.SCHEMA, "event": kind, "run_id": run,
             "recorded_utc": stamp(at), "writer": WRITER}
    event.update(extra)
    return event


def started(run, at=timedelta(0), planned=UNSET, **extra):
    extra.setdefault("family_id", family(run))
    return envelope("STARTED", run, at, planned=PLANNED if planned is UNSET else planned, **extra)


def progress(run, at, stage, **extra):
    return envelope("PROGRESS", run, at, stage=stage, **extra)


def pnl(run, at, registered=UNSET):
    return progress(run, at, "PNL_COMPUTED",
                    registered=REGISTERED if registered is UNSET else registered)


def finished(run, at, status, reached, displayed=True):
    return envelope("FINISHED", run, at, status=status, stage_reached=reached, displayed=displayed)


def lines(*events):
    result, previous = [], None
    for event in events:
        previous = C.encode_event_line(event, previous_line=previous)
        result.append(previous)
    return result


def chain(*events):
    return C.verify_event_lines(lines(*events))


def fold(events, as_of=T0 + HOUR, **kwargs):
    return F.fold_runs(events, as_of=as_of, **kwargs)


def completed_run(run, start=timedelta(0)):
    return [started(run, start), pnl(run, start + SEC),
            envelope("FINGERPRINT", run, start + 2 * SEC, fingerprints=[]),
            envelope("SHADOW", run, start + 3 * SEC, error=None),
            progress(run, start + 4 * SEC, "DISPLAYED", displayed=True),
            finished(run, start + 5 * SEC, "COMPLETED", "DISPLAYED")]


_GUARD = {"mode": None, "root": None}
_PROTECTED = ("holdout", "frozen", "paper_live", "grokteam", "cards", ".nextgen", "_backup")


def _audit(name, args):
    mode = _GUARD["mode"]
    if mode is None:
        return
    if name.startswith("socket.") or name.startswith("subprocess.") or name in (
            "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.listdir", "os.scandir"):
        raise AssertionError(f"{name} forbidden while guarded")
    if name == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0]))
        if mode == "no-io":
            raise AssertionError("file access forbidden in the pure fold")
        if any(part.startswith(".env") or part in _PROTECTED for part in path.parts):
            raise AssertionError("protected path forbidden")
        if "asset_expansion" in path.parts and "cache" in path.parts:
            raise AssertionError("protected cache forbidden")
        if not path.resolve().is_relative_to(_GUARD["root"]):
            raise AssertionError("file access escaped the temporary root")


_INSTALLED = []


def guarded(mode, root=None):
    """Install one process audit hook once; it acts only while a mode is set."""
    if not _INSTALLED:
        sys.addaudithook(_audit)
        _INSTALLED.append(True)

    class Scope:
        def __enter__(self):
            _GUARD["mode"], _GUARD["root"] = mode, root

        def __exit__(self, *exc):
            _GUARD["mode"], _GUARD["root"] = None, None
            return False
    return Scope()


class GoldenAndLifecycleTests(unittest.TestCase):
    def test_golden_completed_run_with_all_machine_event_types(self):
        events = completed_run(R1)
        stored = lines(*events)
        result = fold(chain(*events))
        self.assertEqual(result.runs, (F.RunRecord(
            run_id=R1, family_id="E1", started_utc="2026-11-10T08:00:00.000000Z",
            status="COMPLETED", status_source="FINISHED", stage="DISPLAYED",
            effective_status="COMPLETED", flags=(), keys=R_KEYS, keys_source="registered",
            displayed=True, event_count=6),))
        self.assertEqual(result.as_of, T0 + HOUR)
        self.assertEqual(result.events_folded, 6)
        self.assertEqual(result.tail_line_md5, hashlib.md5(stored[-1], usedforsecurity=False).hexdigest())
        self.assertEqual(dict(result.total_by_family), {"E1": 1})
        self.assertEqual(dict(result.open_by_family), {"E1": 0})
        self.assertEqual(result.open_run_ids, ())
        self.assertEqual(result.unmatched_outage_run_ids, ())

    def test_failed_before_stats_at_requested_has_no_keys(self):
        result = fold(chain(started(R1), progress(R1, SEC, "REQUESTED"),
                            finished(R1, 2 * SEC, "FAILED_BEFORE_STATS", "REQUESTED", False)))
        run = result.runs[0]
        self.assertEqual((run.status, run.effective_status, run.stage, run.flags),
                         ("FAILED_BEFORE_STATS", "FAILED_BEFORE_STATS", "REQUESTED", ()))
        self.assertEqual((run.keys, run.keys_source, run.displayed), (None, None, False))

    def test_finished_without_closing_progress_is_flagged_progress_missing(self):
        run = fold(chain(started(R1), finished(R1, SEC, "FAILED_BEFORE_STATS", "COST_RESOLVED", False))).runs[0]
        self.assertEqual((run.effective_status, run.stage, run.flags),
                         ("FAILED_BEFORE_STATS", "COST_RESOLVED", ("PROGRESS_MISSING",)))
        run = fold(chain(started(R1), pnl(R1, SEC),
                         finished(R1, 2 * SEC, "FAILED_AFTER_STATS", "SCORED"))).runs[0]
        self.assertEqual((run.effective_status, run.stage, run.flags, run.keys),
                         ("FAILED_AFTER_STATS", "SCORED", ("PROGRESS_MISSING",), R_KEYS))

    def test_failed_after_stats_at_walk_forward_done_uses_registered_keys(self):
        run = fold(chain(started(R1), pnl(R1, SEC), progress(R1, 2 * SEC, "WALK_FORWARD_DONE"),
                         finished(R1, 3 * SEC, "FAILED_AFTER_STATS", "WALK_FORWARD_DONE", False))).runs[0]
        self.assertEqual((run.status, run.effective_status, run.stage, run.flags),
                         ("FAILED_AFTER_STATS", "FAILED_AFTER_STATS", "WALK_FORWARD_DONE", ()))
        self.assertEqual((run.keys, run.keys_source, run.event_count), (R_KEYS, "registered", 4))

    def test_recorded_aborted_takes_its_effective_status_from_the_stage(self):
        after = fold(chain(started(R1), pnl(R1, SEC),
                           finished(R1, 2 * SEC, "ABORTED", "PNL_COMPUTED", False))).runs[0]
        self.assertEqual((after.status, after.status_source, after.effective_status, after.keys),
                         ("ABORTED", "FINISHED", "FAILED_AFTER_STATS", R_KEYS))
        before = fold(chain(started(R1), progress(R1, SEC, "DATA_LOADED"),
                            finished(R1, 2 * SEC, "ABORTED", "DATA_LOADED", False))).runs[0]
        self.assertEqual((before.status, before.effective_status, before.keys, before.flags),
                         ("ABORTED", "FAILED_BEFORE_STATS", None, ()))


class OrphanTests(unittest.TestCase):
    def test_orphan_at_exactly_six_hours_is_open(self):
        result = fold(chain(started(R1)), as_of=T0 + F.ORPHAN_AGE)
        run = result.runs[0]
        self.assertEqual((run.status, run.status_source, run.effective_status, run.stage),
                         ("OPEN", "NONE", "OPEN", None))
        self.assertEqual((run.flags, run.keys, run.keys_source, run.displayed), ((), None, None, None))
        self.assertEqual(result.open_run_ids, (R1,))

    def test_orphan_one_microsecond_past_six_hours_is_inferred_aborted(self):
        as_of = T0 + F.ORPHAN_AGE + timedelta(microseconds=1)
        run = fold(chain(started(R1)), as_of=as_of).runs[0]
        self.assertEqual((run.status, run.status_source, run.effective_status, run.stage, run.flags),
                         ("ABORTED", "INFERRED", "FAILED_BEFORE_STATS", None, ("STAGE_INFERRED",)))
        self.assertIsNone(run.keys)

    def test_orphan_with_progress_takes_the_last_progress_stage(self):
        as_of = T0 + 7 * HOUR
        after = fold(chain(started(R1), pnl(R1, SEC), progress(R1, 2 * SEC, "SCORED")), as_of=as_of).runs[0]
        self.assertEqual((after.status, after.status_source, after.stage, after.effective_status, after.flags),
                         ("ABORTED", "INFERRED", "SCORED", "FAILED_AFTER_STATS", ()))
        self.assertEqual((after.keys, after.keys_source), (R_KEYS, "registered"))
        before = fold(chain(started(R1), progress(R1, SEC, "DATA_LOADED")), as_of=as_of).runs[0]
        self.assertEqual((before.stage, before.effective_status, before.flags, before.keys),
                         ("DATA_LOADED", "FAILED_BEFORE_STATS", (), None))

    def test_orphan_without_progress_and_with_outage_fails_closed_on_planned_keys(self):
        run = fold(chain(started(R1)), as_of=T0 + 7 * HOUR, outage_run_ids=frozenset({R1})).runs[0]
        self.assertEqual((run.status, run.effective_status, run.stage),
                         ("ABORTED", "FAILED_AFTER_STATS", None))
        self.assertEqual(run.flags, ("REGISTERED_KEYS_MISSING", "STAGE_UNKNOWN"))
        self.assertEqual((run.keys, run.keys_source), (P_KEYS, "planned"))

    def test_orphan_with_outage_and_null_planned_keys_is_keys_unavailable(self):
        run = fold(chain(started(R1, planned=None)), as_of=T0 + 7 * HOUR,
                   outage_run_ids=frozenset({R1})).runs[0]
        self.assertEqual(run.effective_status, "FAILED_AFTER_STATS")
        self.assertEqual(run.flags, ("KEYS_UNAVAILABLE", "REGISTERED_KEYS_MISSING", "STAGE_UNKNOWN"))
        self.assertEqual((run.keys, run.keys_source), (None, None))

    def test_outage_record_changes_neither_finished_runs_nor_orphans_with_progress(self):
        events = chain(*completed_run(R1), started(R2, 6 * SEC), pnl(R2, 7 * SEC))
        as_of = T0 + 7 * HOUR
        plain = fold(events, as_of=as_of)
        marked = fold(events, as_of=as_of, outage_run_ids=frozenset({R1, R2}))
        self.assertEqual(plain.runs, marked.runs)
        self.assertEqual(marked.unmatched_outage_run_ids, ())

    def test_unmatched_outage_run_ids_are_sorted_and_respect_the_prefix(self):
        events = chain(started(R2), started(R1, SEC))
        result = fold(events[:1], outage_run_ids=frozenset({R4, R1, R3}))
        self.assertEqual(result.unmatched_outage_run_ids, tuple(sorted((R1, R3, R4))))
        self.assertEqual(fold(events, outage_run_ids=frozenset({R1})).unmatched_outage_run_ids, ())

    def test_open_runs_count_in_total_and_are_reported_separately(self):
        events = chain(*completed_run(R1), started(R2, 10 * SEC), pnl(R2, 11 * SEC),
                       started(R3, 12 * SEC), started(R4, 13 * SEC),
                       finished(R4, 14 * SEC, "FAILED_BEFORE_STATS", "REQUESTED", False))
        result = fold(events, as_of=T0 + 2 * HOUR)
        self.assertEqual(dict(result.total_by_family), {"C3": 1, "CRY-1": 1, "E1": 2})
        self.assertEqual(list(result.total_by_family), ["C3", "CRY-1", "E1"])
        self.assertEqual(dict(result.open_by_family), {"C3": 1, "CRY-1": 0, "E1": 1})
        self.assertEqual(result.open_run_ids, (R2, R3))
        open_r2 = result.runs[1]
        self.assertEqual((open_r2.effective_status, open_r2.stage, open_r2.keys), ("OPEN", "PNL_COMPUTED", None))
        later = fold(events, as_of=T0 + 7 * HOUR)
        self.assertEqual(dict(later.total_by_family), dict(result.total_by_family))
        self.assertEqual(dict(later.open_by_family), {"C3": 0, "CRY-1": 0, "E1": 0})


class ConflictTests(unittest.TestCase):
    def test_failed_before_stats_with_a_statistic_is_raised_to_after_stats(self):
        run = fold(chain(started(R1), pnl(R1, SEC),
                         finished(R1, 2 * SEC, "FAILED_BEFORE_STATS", "DATA_LOADED", False))).runs[0]
        self.assertEqual((run.status, run.effective_status, run.stage, run.flags, run.keys),
                         ("FAILED_BEFORE_STATS", "FAILED_AFTER_STATS", "PNL_COMPUTED",
                          ("STATUS_STAGE_CONFLICT",), R_KEYS))
        run = fold(chain(started(R1), finished(R1, SEC, "FAILED_BEFORE_STATS", "WALK_FORWARD_DONE", False))).runs[0]
        self.assertEqual((run.effective_status, run.keys, run.keys_source), ("FAILED_AFTER_STATS", P_KEYS, "planned"))
        self.assertEqual(run.flags, ("PROGRESS_MISSING", "REGISTERED_KEYS_MISSING", "STATUS_STAGE_CONFLICT"))

    def test_failed_after_stats_below_pnl_keeps_after_stats(self):
        run = fold(chain(started(R1), progress(R1, SEC, "DATA_LOADED"),
                         finished(R1, 2 * SEC, "FAILED_AFTER_STATS", "DATA_LOADED", False))).runs[0]
        self.assertEqual((run.effective_status, run.keys_source),
                         ("FAILED_AFTER_STATS", "planned"))
        self.assertEqual(run.flags, ("REGISTERED_KEYS_MISSING", "STATUS_STAGE_CONFLICT"))

    def test_completed_below_displayed_keeps_completed(self):
        run = fold(chain(started(R1), pnl(R1, SEC), progress(R1, 2 * SEC, "SCORED"),
                         finished(R1, 3 * SEC, "COMPLETED", "SCORED"))).runs[0]
        self.assertEqual((run.effective_status, run.stage, run.keys), ("COMPLETED", "SCORED", R_KEYS))
        self.assertEqual(run.flags, ("PROGRESS_MISSING", "STATUS_STAGE_CONFLICT"))

    def test_completed_without_displayed_progress_is_progress_missing(self):
        run = fold(chain(started(R1), pnl(R1, SEC), finished(R1, 2 * SEC, "COMPLETED", "DISPLAYED"))).runs[0]
        self.assertEqual((run.effective_status, run.stage, run.flags), ("COMPLETED", "DISPLAYED", ("PROGRESS_MISSING",)))

    def test_progress_beyond_finished_stage_is_a_conflict_and_the_larger_stage_wins(self):
        run = fold(chain(started(R1), pnl(R1, SEC), progress(R1, 2 * SEC, "SCORED"),
                         finished(R1, 3 * SEC, "FAILED_AFTER_STATS", "PNL_COMPUTED", False))).runs[0]
        self.assertEqual((run.stage, run.effective_status, run.flags),
                         ("SCORED", "FAILED_AFTER_STATS", ("STATUS_STAGE_CONFLICT",)))

    def test_a_conflict_never_lowers_the_counting_status(self):
        order = {"FAILED_BEFORE_STATS": 0, "FAILED_AFTER_STATS": 1, "COMPLETED": 1}
        checked = 0
        for status in sorted(F.FINISHED_STATUSES):
            for reached in F.STAGES:
                for last in (None,) + F.STAGES:
                    events = [started(R1)]
                    if last is not None:
                        events.append(progress(R1, SEC, last))
                    events.append(finished(R1, 2 * SEC, status, reached, False))
                    run = fold(chain(*events)).runs[0]
                    top = max(F.STAGES.index(reached), -1 if last is None else F.STAGES.index(last))
                    by_stage = "FAILED_AFTER_STATS" if top >= F.STAGES.index("PNL_COMPUTED") else "FAILED_BEFORE_STATS"
                    with self.subTest(status=status, reached=reached, last=last):
                        self.assertIn(run.effective_status, F.EFFECTIVE_STATUSES - {"OPEN"})
                        self.assertEqual(run.stage, F.STAGES[top])
                        if status == "COMPLETED":
                            self.assertEqual(run.effective_status, "COMPLETED")
                        elif status == "FAILED_AFTER_STATS":
                            self.assertEqual(run.effective_status, "FAILED_AFTER_STATS")
                        else:
                            self.assertEqual(run.effective_status, by_stage)
                        if status != "ABORTED":
                            self.assertGreaterEqual(order[run.effective_status], order[status])
                        if by_stage == "FAILED_AFTER_STATS":
                            self.assertNotEqual(run.effective_status, "FAILED_BEFORE_STATS")
                    checked += 1
        self.assertEqual(checked, 4 * 8 * 9)


class KeyTests(unittest.TestCase):
    def test_missing_or_null_registered_keys_fall_back_to_planned(self):
        for pnl_event in (progress(R1, SEC, "PNL_COMPUTED"), pnl(R1, SEC, registered=None)):
            with self.subTest(pnl_event=pnl_event):
                run = fold(chain(started(R1), pnl_event, progress(R1, 2 * SEC, "DISPLAYED"),
                                 finished(R1, 3 * SEC, "COMPLETED", "DISPLAYED"))).runs[0]
                self.assertEqual((run.keys, run.keys_source, run.flags),
                                 (P_KEYS, "planned", ("REGISTERED_KEYS_MISSING",)))

    def test_missing_registered_and_null_or_absent_planned_is_keys_unavailable(self):
        absent = started(R1)
        del absent["planned"]
        for first in (started(R1, planned=None), absent):
            with self.subTest(first=first):
                run = fold(chain(first, progress(R1, SEC, "DISPLAYED"),
                                 finished(R1, 2 * SEC, "COMPLETED", "DISPLAYED"))).runs[0]
                self.assertEqual((run.keys, run.keys_source), (None, None))
                self.assertEqual(run.flags, ("KEYS_UNAVAILABLE", "REGISTERED_KEYS_MISSING"))

    def test_duplicate_and_empty_keys_are_kept_as_supplied(self):
        twice = [REGISTERED[1], REGISTERED[0], REGISTERED[1], {"theta_index": 1, "config_id": "f" * 32}]
        run = fold(chain(started(R1), pnl(R1, SEC, registered=twice),
                         finished(R1, 2 * SEC, "FAILED_AFTER_STATS", "PNL_COMPUTED", False))).runs[0]
        self.assertEqual(run.keys, (R_KEYS[1], R_KEYS[0], R_KEYS[1], (1, "f" * 32)))
        run = fold(chain(started(R1, planned=[]), pnl(R1, SEC, registered=[]),
                         finished(R1, 2 * SEC, "FAILED_AFTER_STATS", "PNL_COMPUTED", False))).runs[0]
        self.assertEqual((run.keys, run.keys_source, run.flags), ((), "registered", ()))


class PrefixTests(unittest.TestCase):
    def test_two_interleaved_runs_keep_started_order_and_their_own_events(self):
        events = chain(started(R1), started(R3, SEC), pnl(R3, 2 * SEC), pnl(R1, 3 * SEC),
                       finished(R3, 4 * SEC, "FAILED_AFTER_STATS", "PNL_COMPUTED", False),
                       progress(R1, 5 * SEC, "DISPLAYED"), finished(R1, 6 * SEC, "COMPLETED", "DISPLAYED"))
        result = fold(events)
        self.assertEqual([r.run_id for r in result.runs], [R1, R3])
        self.assertEqual([(r.family_id, r.effective_status, r.event_count, r.flags) for r in result.runs],
                         [("E1", "COMPLETED", 4, ()), ("C3", "FAILED_AFTER_STATS", 3, ())])
        self.assertEqual(dict(result.total_by_family), {"C3": 1, "E1": 1})

    def test_empty_prefix_folds_to_nothing(self):
        for empty in ((), []):
            result = fold(empty, outage_run_ids=frozenset({R1}))
            self.assertEqual((result.runs, result.events_folded, result.tail_line_md5), ((), 0, None))
            self.assertEqual((dict(result.total_by_family), dict(result.open_by_family)), ({}, {}))
            self.assertEqual(result.unmatched_outage_run_ids, (R1,))

    def test_a_prefix_cut_by_position_folds_the_earlier_state(self):
        events = chain(*completed_run(R1))
        stored = lines(*completed_run(R1))
        for cut in range(1, 7):
            with self.subTest(cut=cut):
                result = fold(events[:cut], as_of=T0 + 5 * SEC)
                self.assertEqual(result.events_folded, cut)
                self.assertEqual(result.tail_line_md5, hashlib.md5(stored[cut - 1], usedforsecurity=False).hexdigest())
                self.assertEqual(result.runs[0].effective_status, "COMPLETED" if cut == 6 else "OPEN")
        self.assertEqual(fold(events[:2], as_of=T0 + 7 * HOUR).runs[0].effective_status, "FAILED_AFTER_STATS")


class StructureRefusalTests(unittest.TestCase):
    def assertRefused(self, events, index, **kwargs):
        with self.assertRaises(FoldError) as caught:
            fold(chain(*events), **kwargs)
        self.assertTrue(str(caught.exception).startswith(f"event {index}:"), str(caught.exception))

    def test_a_run_whose_first_event_is_not_started_is_refused(self):
        for kind in ("PROGRESS", "FINGERPRINT", "SHADOW", "FINISHED"):
            with self.subTest(kind=kind):
                orphan_event = envelope(kind, R2, SEC, stage="REQUESTED") if kind == "PROGRESS" else (
                    finished(R2, SEC, "COMPLETED", "DISPLAYED") if kind == "FINISHED" else envelope(kind, R2, SEC))
                self.assertRefused([started(R1), orphan_event], 1)

    def test_second_started_and_second_finished_are_refused(self):
        self.assertRefused([started(R1), started(R1, SEC)], 1)
        done = finished(R1, SEC, "FAILED_BEFORE_STATS", "REQUESTED", False)
        self.assertRefused([started(R1), done, finished(R1, 2 * SEC, "COMPLETED", "DISPLAYED")], 2)

    def test_any_event_after_finished_is_refused(self):
        done = finished(R1, SEC, "FAILED_BEFORE_STATS", "REQUESTED", False)
        for late in (progress(R1, 2 * SEC, "REQUESTED"), envelope("FINGERPRINT", R1, 2 * SEC),
                     envelope("SHADOW", R1, 2 * SEC)):
            with self.subTest(late=late["event"]):
                self.assertRefused([started(R1), done, late], 2)

    def test_family_id_missing_or_different_from_the_run_id_is_refused(self):
        missing = started(R1)
        del missing["family_id"]
        for first in (missing, started(R1, family_id="C3"), started(R1, family_id=None),
                      started(R4, family_id="CRY")):
            with self.subTest(first=first.get("family_id")):
                self.assertRefused([first], 0)
        self.assertRefused([started(R1), progress(R1, SEC, "REQUESTED", family_id="C3")], 1)
        ok = fold(chain(started(R4), progress(R4, SEC, "REQUESTED", family_id="CRY-1")))
        self.assertEqual(ok.runs[0].family_id, "CRY-1")

    def test_unknown_stages_statuses_and_displayed_values_are_refused(self):
        no_stage = envelope("PROGRESS", R1, SEC)
        for bad in (no_stage, progress(R1, SEC, "LOADED"), progress(R1, SEC, ["PNL_COMPUTED"]),
                    progress(R1, SEC, "pnl_computed"), progress(R1, SEC, None)):
            with self.subTest(stage=bad.get("stage", "absent")):
                self.assertRefused([started(R1), bad], 1)
        for status in ("STARTED", "SUPERSEDED", "OPEN", "completed", None, ["COMPLETED"]):
            with self.subTest(status=status):
                self.assertRefused([started(R1), finished(R1, SEC, status, "DISPLAYED")], 1)
        for reached in ("DONE", None, 3):
            with self.subTest(reached=reached):
                self.assertRefused([started(R1), finished(R1, SEC, "COMPLETED", reached)], 1)
        no_reached = finished(R1, SEC, "COMPLETED", "DISPLAYED")
        del no_reached["stage_reached"]
        self.assertRefused([started(R1), no_reached], 1)
        for displayed in ("yes", 1, []):
            with self.subTest(displayed=displayed):
                self.assertRefused([started(R1), finished(R1, SEC, "COMPLETED", "DISPLAYED", displayed)], 1)
        run = fold(chain(started(R1), finished(R1, SEC, "FAILED_BEFORE_STATS", "REQUESTED", None))).runs[0]
        self.assertIsNone(run.displayed)

    def test_decreasing_progress_stages_are_refused_and_equal_stages_allowed(self):
        self.assertRefused([started(R1), progress(R1, SEC, "SCORED"), progress(R1, 2 * SEC, "PNL_COMPUTED")], 2)
        run = fold(chain(started(R1), progress(R1, SEC, "DATA_LOADED"), progress(R1, 2 * SEC, "DATA_LOADED"))).runs[0]
        self.assertEqual((run.stage, run.event_count), ("DATA_LOADED", 3))

    def test_malformed_planned_or_registered_keys_are_refused(self):
        good = PLANNED[0]
        bad_lists = ({"theta_index": 0, "config_id": good["config_id"]}, "keys", [good, None], [["0", good["config_id"]]],
                     [dict(good, extra=1)], [{"theta_index": 0}], [dict(good, theta_index=True)],
                     [dict(good, theta_index=-1)], [dict(good, theta_index=1.0)], [dict(good, theta_index="0")],
                     [dict(good, config_id="A" * 32)], [dict(good, config_id="a" * 31)],
                     [dict(good, config_id=None)])
        for value in bad_lists:
            with self.subTest(planned=value):
                self.assertRefused([started(R1, planned=value)], 0)
            with self.subTest(registered=value):
                self.assertRefused([started(R1), pnl(R1, SEC, registered=value)], 1)
        self.assertRefused([started(R1), progress(R1, SEC, "SCORED", registered=REGISTERED)], 1)
        self.assertRefused([started(R1), pnl(R1, SEC), pnl(R1, 2 * SEC, registered=None)], 2)

    def test_outage_run_ids_must_be_a_frozenset_of_lab_run_ids(self):
        events = chain(started(R1))
        for value in ({R1}, [R1], (R1,), None, frozenset({R1, "LAB-bad"}), frozenset({1}),
                      frozenset({R1.lower()}), frozenset({"STUDY-20261110T080000Z-E1-0000000a"})):
            with self.subTest(value=value):
                with self.assertRaises(FoldError):
                    fold(events, outage_run_ids=value)

    def test_human_and_segment_events_are_refused(self):
        for kind in ("SUPERSEDED", "ANNOTATION"):
            with self.subTest(kind=kind):
                self.assertRefused([started(R1), envelope(kind, R1, SEC, person="owner", owner_ruling=None)], 1)
        for kind in ("DECLARATION", "BACKFILL"):
            with self.subTest(kind=kind):
                human = {"schema": C.SCHEMA, "event": kind, "recorded_utc": stamp(SEC),
                         "writer": "tools/r3/annotate.py", "person": "owner", "owner_ruling": None}
                self.assertRefused([started(R1), human], 1)
        segment = {"schema": C.SCHEMA, "event": "SEGMENT_START", "recorded_utc": stamp(timedelta(0)),
                   "writer": "tools/r3/registry_segment.py", "person": "owner"}
        self.assertRefused([segment, started(R1, SEC)], 0)


class InputRefusalTests(unittest.TestCase):
    def test_as_of_must_be_an_aware_utc_datetime(self):
        events = chain(started(R1))

        class Instant(datetime):
            pass
        for value in (T0.replace(tzinfo=None) + HOUR, (T0 + HOUR).astimezone(timezone(timedelta(hours=9))),
                      date(2026, 11, 11), "2026-11-10T09:00:00.000000Z", 0,
                      Instant(2026, 11, 10, 9, tzinfo=timezone.utc), None):
            with self.subTest(as_of=value):
                with self.assertRaises(FoldError):
                    fold(events, as_of=value)
        zulu = (T0 + HOUR).replace(tzinfo=timezone(timedelta(0), "Z"))
        self.assertEqual(fold(events, as_of=zulu), fold(events))
        self.assertIs(fold(events, as_of=zulu).as_of.tzinfo, timezone.utc)

    def test_recorded_utc_after_as_of_is_refused_only_as_a_guard_inside_the_prefix(self):
        events = chain(started(R1), started(R2, HOUR + timedelta(microseconds=1)))
        with self.assertRaises(FoldError) as caught:
            fold(events, as_of=T0 + HOUR)
        self.assertTrue(str(caught.exception).startswith("event 1:"))
        self.assertEqual(len(fold(events[:1], as_of=T0 + HOUR).runs), 1)
        self.assertEqual(len(fold(events, as_of=T0 + HOUR + timedelta(microseconds=1)).runs), 2)
        self.assertEqual(fold(chain(started(R1, HOUR)), as_of=T0 + HOUR).open_run_ids, (R1,))

    def test_non_sequence_and_non_dict_inputs_are_refused(self):
        event, second = chain(started(R1), started(R2, SEC))
        self.assertEqual(len(fold([event, second]).runs), 2)
        for value in (None, {"0": event}, "events", (e for e in [event]), {event["run_id"]}):
            with self.subTest(events=type(value).__name__):
                with self.assertRaises(FoldError):
                    fold(value)
        for item in (None, [second], "event", OrderedDict(second), 1):
            with self.subTest(item=type(item).__name__):
                with self.assertRaises(FoldError) as caught:
                    fold([event, item])
                self.assertTrue(str(caught.exception).startswith("event 1:"))

    def test_unchained_input_is_refused(self):
        with self.assertRaises(FoldError) as caught:
            fold([started(R1)])
        self.assertTrue(str(caught.exception).startswith("event 0:"))
        partial = dict(chain(started(R1))[0])
        del partial["prev_row_md5"]
        with self.assertRaises(FoldError):
            fold([partial])

    def test_misordered_spliced_dropped_edited_or_mid_chain_input_is_refused(self):
        events = chain(*completed_run(R1))
        edited = [dict(e) for e in events]
        edited[3]["error"] = {"type": "X", "message": "edited"}
        other = chain(started(R2))
        cases = {"swapped": ([events[0], events[2], events[1]] + list(events[3:]), 1),
                 "dropped": ([events[0], events[1]] + list(events[3:]), 2),
                 "edited": (edited, 3),
                 "mid-chain": (list(events[2:]), 0),
                 "spliced": (list(events[:2]) + list(other), 2),
                 "duplicated": ([events[0], events[0]], 1)}
        for name, (value, index) in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(FoldError) as caught:
                    fold(value)
                self.assertTrue(str(caught.exception).startswith(f"event {index}:"), str(caught.exception))

    def test_events_that_cannot_be_reencoded_are_refused(self):
        base = chain(started(R1))[0]
        for value in (dict(base, cost_bps_requested=float("nan")), dict(base, planned={1: "x", "a": "y"}),
                      dict(base, planned={1, 2}), dict(base, planned=b"bytes"), dict(base, seed="\ud800")):
            with self.subTest(value=sorted(set(value) ^ set(base)) or "changed"):
                with self.assertRaises(FoldError) as caught:
                    fold([value])
                self.assertTrue(str(caught.exception).startswith("event 0:"))


class PurityTests(unittest.TestCase):
    def test_determinism_nonmutation_and_frozen_results(self):
        events = chain(*completed_run(R1), started(R2, 10 * SEC), started(R3, 11 * SEC))
        before = copy.deepcopy(events)
        outages = frozenset({R2, R4})
        first = fold(events, as_of=T0 + 7 * HOUR, outage_run_ids=outages)
        second = fold(list(copy.deepcopy(events)), as_of=T0 + 7 * HOUR, outage_run_ids=outages)
        self.assertEqual(first, second)
        self.assertEqual(events, before)
        self.assertEqual(outages, frozenset({R2, R4}))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.runs = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.runs[0].status = "OPEN"
        with self.assertRaises(TypeError):
            first.total_by_family["E1"] = 0
        with self.assertRaises(TypeError):
            first.open_by_family["X"] = 1
        self.assertIsInstance(hash(first.runs), int)
        self.assertTrue(all(type(r.flags) is tuple and type(r.keys) in (tuple, type(None)) for r in first.runs))

    def test_constants_match_the_design_and_the_store(self):
        self.assertEqual(F.STAGES, ("REQUESTED", "COST_RESOLVED", "DATA_LOADED", "PNL_COMPUTED",
                                    "WALK_FORWARD_DONE", "LEDGER_REGISTERED", "SCORED", "DISPLAYED"))
        self.assertEqual(F.FINISHED_STATUSES, {"COMPLETED", "FAILED_BEFORE_STATS", "FAILED_AFTER_STATS", "ABORTED"})
        self.assertEqual(F.EFFECTIVE_STATUSES, {"COMPLETED", "FAILED_BEFORE_STATS", "FAILED_AFTER_STATS", "OPEN"})
        self.assertEqual(F.FOLD_EVENTS, S.MACHINE_EVENTS)
        self.assertEqual(F.ORPHAN_AGE, timedelta(hours=6))
        self.assertEqual(F.FLAGS, {"STAGE_INFERRED", "STAGE_UNKNOWN", "STATUS_STAGE_CONFLICT",
                                   "PROGRESS_MISSING", "REGISTERED_KEYS_MISSING", "KEYS_UNAVAILABLE"})
        self.assertTrue(issubclass(FoldError, ValueError))
        self.assertEqual([f.name for f in dataclasses.fields(F.RunRecord)],
                         ["run_id", "family_id", "started_utc", "status", "status_source", "stage",
                          "effective_status", "flags", "keys", "keys_source", "displayed", "event_count"])

    def test_module_imports_and_names_exclude_io_clock_environment_and_randomness(self):
        tree = ast.parse(Path(F.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add("." * node.level + (node.module or ""))
        self.assertEqual(imported, {"collections.abc", "dataclasses", "datetime", "hashlib", "json",
                                    "re", "types", "."})
        relative = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level]
        self.assertEqual([[a.name for a in n.names] for n in relative], [["run_registry_codec"]])
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        forbidden = {"open", "now", "utcnow", "today", "time", "time_ns", "monotonic", "perf_counter",
                     "getenv", "environ", "putenv", "tzset", "fromtimestamp", "strptime", "system",
                     "popen", "urandom", "random", "token_hex", "print", "input", "eval", "exec",
                     "__import__", "os", "sys", "Path", "socket", "subprocess"}
        self.assertEqual(names & forbidden, set())

    def test_fold_runs_with_io_clock_environment_and_network_refused(self):
        events = chain(*completed_run(R1), started(R2, 10 * SEC), started(R3, 11 * SEC))
        expected = fold(events, as_of=T0 + 7 * HOUR, outage_run_ids=frozenset({R3}))

        def fail(*args, **kwargs):
            raise AssertionError("I/O, clock, environment or network access forbidden")
        with patch.object(builtins, "open", side_effect=fail), patch.object(io, "open", side_effect=fail), \
                patch.object(os, "open", side_effect=fail), patch.object(os, "getenv", side_effect=fail), \
                patch.object(os, "putenv", side_effect=fail), patch.object(time, "time", side_effect=fail), \
                patch.object(time, "time_ns", side_effect=fail), patch.object(time, "monotonic", side_effect=fail), \
                patch.object(time, "perf_counter", side_effect=fail), patch.object(time, "tzset", side_effect=fail), \
                patch.object(time, "localtime", side_effect=fail), \
                patch.object(socket.socket, "connect", side_effect=fail), guarded("no-io"):
            result = F.fold_runs(events, as_of=T0 + 7 * HOUR, outage_run_ids=frozenset({R3}))
        self.assertEqual(result, expected)


class StoreRoundTripTests(unittest.TestCase):
    def test_round_trip_through_single_segment_store_in_a_temporary_directory(self):
        events = completed_run(R1) + [started(R3, 10 * SEC), pnl(R3, 11 * SEC), started(R2, 12 * SEC)]
        with tempfile.TemporaryDirectory(prefix="qg-r3-fold-") as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            with guarded("temp-only", root):
                store = S.SingleSegmentStore(root / "registry.jsonl")
                written = [store.append(event) for event in events]
                stored = store.read()
                raw = (root / "registry.jsonl").read_bytes()
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["registry.jsonl", "registry.lock"])
        self.assertEqual(raw, b"".join(written))
        as_of = T0 + 7 * HOUR
        result = F.fold_runs(stored, as_of=as_of, outage_run_ids=frozenset({R2}))
        self.assertEqual(result, F.fold_runs(chain(*events), as_of=as_of, outage_run_ids=frozenset({R2})))
        self.assertEqual(result.tail_line_md5, hashlib.md5(written[-1], usedforsecurity=False).hexdigest())
        self.assertEqual(result.events_folded, len(written))
        self.assertEqual([(r.run_id, r.effective_status, r.flags) for r in result.runs],
                         [(R1, "COMPLETED", ()), (R3, "FAILED_AFTER_STATS", ()),
                          (R2, "FAILED_AFTER_STATS", ("REGISTERED_KEYS_MISSING", "STAGE_UNKNOWN"))])
        cut = F.fold_runs(stored[:3], as_of=T0 + 2 * SEC)
        self.assertEqual(cut.tail_line_md5, hashlib.md5(written[2], usedforsecurity=False).hexdigest())
        self.assertEqual(cut.open_run_ids, (R1,))


if __name__ == "__main__":
    unittest.main()
