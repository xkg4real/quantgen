"""Temporary-only acceptance for a partial single-segment R3 envelope store."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from core.quant import run_registry_codec as C
from core.quant import run_registry_store as S


RUN = "LAB-20261106T080910Z-FAM-0123abcd"
BODY = (b'{"event":"STARTED","recorded_utc":"2026-11-06T08:09:10.123456Z",'
        b'"run_id":"LAB-20261106T080910Z-FAM-0123abcd","schema":"qg-run-registry/1",'
        b'"writer":"ui/strategy_lab_page.py"}')
ROW = hashlib.md5(BODY, usedforsecurity=False).hexdigest().encode("ascii")
GOLDEN = (b'{"event":"STARTED","prev_row_md5":null,'
          b'"recorded_utc":"2026-11-06T08:09:10.123456Z","row_md5":"' + ROW +
          b'","run_id":"LAB-20261106T080910Z-FAM-0123abcd",'
          b'"schema":"qg-run-registry/1","writer":"ui/strategy_lab_page.py"}\n')


def event(kind="STARTED", **extra):
    result = json.loads(BODY)
    result["event"] = kind
    result.update(extra)
    return result


def _child_guard(root):
    """Spawn does not inherit the parent's Python audit hooks."""
    root = Path(root).resolve()
    def guard(name, args):
        if name == "socket.connect":
            raise AssertionError("Child network forbidden")
        if name == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0]))
            if any(part.startswith(".env") or part in
                   ("holdout", "frozen", "paper_live", "grokteam", ".nextgen", "_backup")
                   for part in path.parts):
                raise AssertionError("Child protected path forbidden")
            if "asset_expansion" in path.parts and "cache" in path.parts:
                raise AssertionError("Child protected cache forbidden")
            mode, flags = args[1], args[2]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if (write or path.suffix == ".jsonl") and not path.resolve().is_relative_to(root):
                raise AssertionError("Child file access escaped temporary root")
    sys.addaudithook(guard)


def _hold_sidecar(root):
    _child_guard(root)
    root = Path(root)
    with S.SingleSegmentStore(root / "registry.jsonl")._locked(create=False) as held:
        if not held:
            raise AssertionError("Temporary sidecar missing")
        (root / "child_ready").write_text("locked", encoding="utf-8")
        deadline = time.monotonic() + 15
        while not (root / "child_release").exists():
            if time.monotonic() >= deadline:
                raise AssertionError("Parent did not release temporary lock probe")
            time.sleep(0.01)


class RunRegistryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qg-r3-store-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "registry.jsonl"

    def store(self, **kwargs):
        return S.SingleSegmentStore(self.path, **kwargs)

    def test_missing_read_creates_neither_file_nor_sidecar(self):
        store = self.store()
        self.assertEqual(store.read(), ())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_golden_append_reopen_input_preserved_and_exact_prior_lf(self):
        source = event()
        old = copy.deepcopy(source)
        store = self.store()
        self.assertEqual(store.append(source), GOLDEN)
        self.assertEqual(source, old)
        self.assertEqual(self.path.read_bytes(), GOLDEN)
        second = store.append(event("PROGRESS", stage="PNL_COMPUTED"))
        rows = self.store().read()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["prev_row_md5"], hashlib.md5(GOLDEN, usedforsecurity=False).hexdigest())
        self.assertEqual(self.path.read_bytes(), GOLDEN + second)
        rows[0]["writer"] = "mutated-return"
        self.assertEqual(self.store().read()[0]["writer"], "ui/strategy_lab_page.py")

    def test_corruption_torn_reformat_drop_reorder_preserved(self):
        store = self.store()
        lines = [store.append(event())]
        lines.append(store.append(event("PROGRESS", stage="PNL_COMPUTED")))
        lines.append(store.append(event("FINISHED", status="COMPLETED")))
        variants = [lines[0] + lines[2], lines[1] + lines[0] + lines[2],
                    b"".join(lines)[:-5], b"".join(lines).replace(b":", b": ", 1),
                    b"".join(lines).replace(b"PNL_COMPUTED", b"DATA_LOADED")]
        for damaged in variants:
            with self.subTest(damaged=damaged):
                self.path.write_bytes(damaged)
                with self.assertRaises(S.IntegrityError):
                    store.read()
                with self.assertRaises(S.IntegrityError):
                    store.append(event("PROGRESS"))
                self.assertEqual(self.path.read_bytes(), damaged)

    def test_full_verification_and_consistent_prefix_limit(self):
        store = self.store()
        first = store.append(event())
        store.append(event("PROGRESS"))
        self.assertEqual(len(store.read()), 2)
        # A complete valid prefix is not proof that its previous suffix never existed.
        self.path.write_bytes(first)
        self.assertEqual(len(store.read()), 1)
        self.path.write_bytes(first.replace(b"FAM", b"BAD"))
        with self.assertRaises(S.IntegrityError):
            store.read()

    def test_duplicate_started_finished_refused_without_change(self):
        store = self.store()
        store.append(event())
        for kind in ("STARTED", "FINISHED"):
            if kind == "FINISHED":
                store.append(event(kind, status="COMPLETED"))
            before = self.path.read_bytes()
            with self.assertRaises(S.DuplicateEvent):
                self.store().append(event(kind))
            self.assertEqual(self.path.read_bytes(), before)
        # Even a byte-valid preexisting duplicate chain is not accepted.
        self.path.write_bytes(GOLDEN + C.encode_event_line(event(), previous_line=GOLDEN))
        with self.assertRaises(S.IntegrityError):
            self.store().read()

    def test_five_threads_ten_appends_each_share_locks_across_instances(self):
        self.store().append(event())
        barrier = threading.Barrier(5)
        errors = []
        def worker(number):
            try:
                store = self.store(lock_timeout=10)
                barrier.wait(timeout=10)
                for index in range(10):
                    store.append(event("PROGRESS", stats={"worker": number, "index": index}))
            except BaseException as exc:
                errors.append(exc)
        threads = [threading.Thread(target=worker, args=(n,)) for n in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        rows = self.store().read()
        self.assertEqual(len(rows), 51)
        self.assertEqual({(r["stats"]["worker"], r["stats"]["index"]) for r in rows[1:]},
                         {(n, i) for n in range(5) for i in range(10)})
        self.assertEqual(len(C.verify_event_lines(self.path.read_bytes().splitlines(keepends=True))), 51)

    def test_duplicate_collision_race_has_exactly_one_winner(self):
        barrier = threading.Barrier(2)
        outcomes = []
        def append():
            barrier.wait(timeout=10)
            try:
                self.store().append(event())
                outcomes.append("written")
            except S.DuplicateEvent:
                outcomes.append("duplicate")
        threads = [threading.Thread(target=append) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(sorted(outcomes), ["duplicate", "written"])
        self.assertEqual(len(self.store().read()), 1)

    def test_process_path_lock_timeout_and_release(self):
        self.store().append(event())
        with self.store()._locked(create=False):
            start = time.monotonic()
            with self.assertRaises(S.LockTimeout):
                self.store(lock_timeout=0.05).read()
            self.assertLess(time.monotonic() - start, 2)
        self.assertEqual(len(self.store().read()), 1)
        self.store().append(event("PROGRESS"))

    def test_real_competing_process_os_lock_timeout_then_release(self):
        self.store().append(event())
        # A fresh interpreter avoids replaying the guarded harness's main module.
        # The helper installs its own guard before opening any store/probe files.
        script = ("import sys; sys.path.insert(0, sys.argv[1]); "
                  "from tests.run_registry_store_acceptance import _hold_sidecar; "
                  "_hold_sidecar(sys.argv[2])")
        process = subprocess.Popen([sys.executable, "-B", "-c", script,
                                    str(Path(__file__).resolve().parents[1]), str(self.root)],
                                   cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 15
            while not (self.root / "child_ready").exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.root / "child_ready").exists(), "child failed to acquire temporary OS lock")
            before = self.path.read_bytes()
            start = time.monotonic()
            with self.assertRaises(S.LockTimeout):
                self.store(lock_timeout=0.1).append(event("PROGRESS"))
            self.assertLess(time.monotonic() - start, 2)
            self.assertEqual(self.path.read_bytes(), before)
        finally:
            (self.root / "child_release").write_text("release", encoding="utf-8")
            try:
                stdout, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, (stdout, stderr))
        self.store().append(event("PROGRESS"))
        self.assertEqual(len(self.store().read()), 2)

    def test_timeout_uses_one_deadline_across_lock_stages(self):
        self.store().append(event())
        # Simulate elapsed time while an acquired path lock consumed the first
        # portion. The OS stage must receive only the remainder, not a reset.
        real_process_lock = S._process_lock
        observed = []
        def get_lock(key, deadline):
            observed.append(deadline)
            return real_process_lock(key, deadline)
        def os_stage(fd, deadline):
            observed.append(deadline)
            raise S.LockTimeout("synthetic remaining-budget timeout")
        with patch.object(S, "_process_lock", side_effect=get_lock), patch.object(S, "_acquire_os", side_effect=os_stage):
            with self.assertRaises(S.LockTimeout):
                self.store(lock_timeout=0.2).read()
        self.assertEqual(len(observed), 2)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(len(self.store().read()), 1)

    def test_human_segment_unknown_events_and_existing_payload_refused(self):
        for kind in ("SUPERSEDED", "DECLARATION", "ANNOTATION", "BACKFILL", "SEGMENT_START", "UNKNOWN", []):
            with self.subTest(kind=kind):
                with self.assertRaises(S.UnsupportedEvent):
                    self.store().append(event(kind))
        self.assertEqual(list(self.root.iterdir()), [])
        store = self.store()
        store.append(event())
        self.path.write_bytes(C.encode_event_line(event("ANNOTATION", person=None, owner_ruling=None)))
        before = self.path.read_bytes()
        with self.assertRaises(S.UnsupportedEvent):
            store.read()
        with self.assertRaises(S.UnsupportedEvent):
            store.append(event("PROGRESS"))
        self.assertEqual(self.path.read_bytes(), before)

    def test_explicit_paths_timeouts_and_missing_sidecar(self):
        for value in (-1, 11, 10 ** 1000, float("nan"), float("inf"), True, "1"):
            with self.assertRaises(S.StoreError):
                self.store(lock_timeout=value)
        for path in ("registry.jsonl", self.root / "other.txt"):
            with self.assertRaises(S.StoreError):
                S.SingleSegmentStore(path)
        self.path.write_bytes(GOLDEN)
        with self.assertRaises(S.StoreError):
            self.store().read()
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["registry.jsonl"])
        self.assertEqual(self.path.read_bytes(), GOLDEN)

    def test_size_boundary_refuses_without_rotation_or_partial_append(self):
        self.assertEqual(S.MAX_SEGMENT_BYTES, 32_000_000)
        with patch.object(S, "MAX_SEGMENT_BYTES", len(GOLDEN)):
            self.assertEqual(self.store().append(event()), GOLDEN)
            with self.assertRaises(S.RolloverRequired):
                self.store().append(event("PROGRESS"))
            self.assertEqual(self.path.read_bytes(), GOLDEN)
            self.assertEqual(len(self.store().read()), 1)
        with patch.object(S, "MAX_SEGMENT_BYTES", len(GOLDEN) - 1):
            with self.assertRaises(S.RolloverRequired):
                self.store().read()
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["registry.jsonl", "registry.lock"])

    def test_fsync_failure_exposes_uncertain_complete_bytes_without_retry(self):
        self.store().append(event())
        calls = []
        def fail(fd):
            calls.append(fd)
            raise OSError("synthetic fsync failure")
        with patch.object(S.os, "fsync", side_effect=fail):
            with self.assertRaises(S.AppendOutcomeUncertain):
                self.store().append(event("PROGRESS"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(self.store().read()), 2)

    def test_short_write_keeps_torn_bytes_and_releases_lock(self):
        self.store().append(event())
        before = self.path.read_bytes()
        real_fdopen = os.fdopen
        class ShortWriter:
            def __init__(self, wrapped): self.wrapped = wrapped
            def __enter__(self): self.wrapped.__enter__(); return self
            def __exit__(self, *args): return self.wrapped.__exit__(*args)
            def fileno(self): return self.wrapped.fileno()
            def write(self, data): return self.wrapped.write(data[:len(data) // 2])
            def flush(self): return self.wrapped.flush()
        def opened(fd, mode, **kwargs):
            stream = real_fdopen(fd, mode, **kwargs)
            return ShortWriter(stream) if mode == "ab" else stream
        with patch.object(S.os, "fdopen", side_effect=opened):
            with self.assertRaises(S.AppendOutcomeUncertain):
                self.store().append(event("PROGRESS"))
        damaged = self.path.read_bytes()
        self.assertTrue(damaged.startswith(before))
        self.assertGreater(len(damaged), len(before))
        self.assertFalse(damaged.endswith(b"\n"))
        with self.assertRaises(S.IntegrityError):
            self.store().read()
        with self.assertRaises(S.IntegrityError):
            self.store().append(event("PROGRESS"))
        self.assertEqual(self.path.read_bytes(), damaged)

    def test_special_file_or_final_symlink_refusal(self):
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.path)
            try:
                with self.assertRaises(S.StoreError):
                    self.store().append(event())
                self.assertTrue(stat.S_ISFIFO(self.path.lstat().st_mode))
            finally:
                self.path.unlink()
        target = self.root / "target.jsonl"
        target.write_bytes(GOLDEN)
        try:
            self.path.symlink_to(target)
        except (OSError, NotImplementedError):
            return  # Windows privilege-dependent; OS lock tests still run.
        with self.assertRaises(S.StoreError):
            self.store().append(event())
        self.assertEqual(target.read_bytes(), GOLDEN)


if __name__ == "__main__":
    unittest.main()
