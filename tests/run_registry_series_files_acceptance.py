"""Temporary-only acceptance for detached verified R3 series files.

Every filesystem effect uses a fresh TemporaryDirectory. No ledger, macro
directory, configuration, environment, provider, network or real series is used.
Windows branches are simulated with a fake msvcrt on other platforms.
"""
import ast
import errno
import multiprocessing
import os
from pathlib import Path
import pickle
import socket
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import numpy as np

from core.quant import run_registry_series_files as M
from core.quant.run_registry_series_format import SeriesFormatError, encode_series
from core.quant.run_registry_series_hash import series_sha256
from core.quant.run_registry_store import IntegrityError, LockTimeout, StoreError

# Literal NPY1 fixtures copied from tests/run_registry_series_format_acceptance.py
# (prepared there with stdlib only). ALT has a different header, same content.
PAYLOAD = bytes.fromhex(
    '934e554d5059010076007b276465736372273a20273c6638272c2027666f727472616e5f6f72646572273a2046616c73652c20277368617065273a2028322c2032292c207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a0000000000000000000000000000f03f00000000000000400000000000000080')
ALT_PAYLOAD = bytes.fromhex(
    '934e554d5059010076007b2027736861706527203a2028322c2032292c2027666f727472616e5f6f7264657227203a2046616c73652c2027646573637227203a20273c663827207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a0000000000000000000000000000f03f00000000000000400000000000000080')
RAW = bytes.fromhex('0000000000000000000000000000f03f00000000000000400000000000000080')
SHA = '428709959da4b04f950606cf66e0d52f48ba4296b605b6d28ecae3135bb0809c'
BUDGET = 4096
REAL_REPLACE = os.replace
REAL_OPEN = os.open
REAL_CLOSE = os.close


def other_series(rows=5, cols=3, start=0.0):
    array = np.arange(start, start + rows * cols, dtype="<f8").reshape(rows, cols)
    return encode_series(array, max_bytes=BUDGET), series_sha256(array)


def _child_guard(root):
    """Spawned children do not inherit audit hooks; install one after imports."""
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
            if write and not path.resolve().is_relative_to(root):
                raise AssertionError("Child file write escaped temporary root")
    sys.addaudithook(guard)


def _hold_lock_child(root, ready, release):
    sys.dont_write_bytecode = True
    _child_guard(root)
    held = M.SeriesFiles(root, max_bytes=BUDGET)._acquire(SHA, create=True)
    try:
        ready.set()
        if not release.wait(30):
            raise SystemExit(3)
    finally:
        errors = M._release(held)
    raise SystemExit(4 if errors else 0)


def _write_child(root, start):
    sys.dont_write_bytecode = True
    _child_guard(root)
    if not start.wait(30):
        raise SystemExit(3)
    digest, created = M.SeriesFiles(root, max_bytes=BUDGET, lock_timeout=10).write(PAYLOAD, SHA)
    raise SystemExit(10 if created and digest == SHA else 11 if digest == SHA else 12)


class FakeTime:
    """Deterministic monotonic clock; sleep advances it without waiting.

    ``overshoot`` is added to every sleep, like a real wake-up that comes late.
    """
    def __init__(self, start=1000.0, interrupt_sleep=False, overshoot=0.0):
        self.now, self.sleeps, self.interrupt_sleep = start, [], interrupt_sleep
        self.overshoot = overshoot

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        if self.interrupt_sleep:
            raise KeyboardInterrupt
        self.sleeps.append(seconds)
        self.now += seconds + self.overshoot


class StatOverride:
    """A stat result with one attribute changed; all others delegate."""
    def __init__(self, result, **changes):
        self._result, self._changes = result, changes

    def __getattr__(self, name):
        if name in self._changes:
            return self._changes[name]
        return getattr(self._result, name)


class FdLog:
    """Labels each descriptor at open time and records closes per label.

    A label stays attached to its descriptor number until that number is
    reopened, so a repeated close of one descriptor is counted twice.
    """
    def __init__(self, fail_close=None):
        self.labels, self.opened, self.closes = {}, [], []
        self.fail_close = fail_close

    @staticmethod
    def kind(path):
        name = Path(os.fsdecode(path)).name
        for suffix, kind in ((".lock", "lock"), (".npy", "npy"), (".tmp", "tmp")):
            if name.endswith(suffix):
                return kind
        return "dir" if os.path.isdir(path) else "other"

    def open(self, path, flags, mode=0o777, *, dir_fd=None):
        fd = REAL_OPEN(path, flags, mode, dir_fd=dir_fd)
        label = (self.kind(path), len(self.opened))
        self.opened.append(label)
        self.labels[fd] = label
        return fd

    def close(self, fd):
        label = self.labels.get(fd)
        self.closes.append(label)
        REAL_CLOSE(fd)
        if label is not None and self.fail_close is not None and self.fail_close(label):
            raise OSError(errno.EIO, "synthetic close report")

    def of(self, kind):
        return [label for label in self.opened if label[0] == kind]

    def close_counts(self, kind):
        return [self.closes.count(label) for label in self.of(kind)]

    def patches(self):
        return [patch.object(M.os, "open", side_effect=self.open),
                patch.object(M.os, "close", side_effect=self.close)]


class Patches:
    def __init__(self, items):
        self.items = items

    def __enter__(self):
        for item in self.items:
            item.start()
        return self

    def __exit__(self, *exc):
        for item in reversed(self.items):
            item.stop()
        return False


class SeriesFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qg-r3-series-files-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / (SHA + ".npy")
        self.sidecar = self.root / (SHA + ".lock")

    def files(self, **kwargs):
        kwargs.setdefault("max_bytes", BUDGET)
        return M.SeriesFiles(self.root, **kwargs)

    def inventory(self):
        return sorted(p.name for p in self.root.iterdir())

    def assert_no_temp(self):
        self.assertEqual([n for n in self.inventory() if n.endswith(".tmp")], [])

    def remove_target(self):
        if self.target.is_symlink() or self.target.is_file():
            self.target.unlink()

    def reset(self):
        for path in (self.target, self.sidecar):
            if path.is_symlink() or path.exists():
                path.unlink()

    def corrupt_after_valid_write(self, data):
        self.files().write(PAYLOAD, SHA)
        self.target.unlink()
        if data is not None:
            self.target.write_bytes(data)

    # --- construction and inputs -------------------------------------------------
    def test_constructor_refusals_create_nothing(self):
        root = self.root
        class BytesPath:
            def __fspath__(self):
                return os.fsencode(str(root))
        (self.root / "plain-file").write_bytes(b"x")
        bad_dirs = ["relative/dir", self.root / "missing", self.root / "missing" / "deeper",
                    os.fsencode(str(self.root)), 7, BytesPath(), self.root / "plain-file",
                    os.path.join(str(self.root), "a\0b")]
        loop = self.root / "loop"
        try:
            os.symlink(loop, loop)
        except (OSError, NotImplementedError):
            pass  # symlinks not permitted here; the loop cases are skipped
        else:
            bad_dirs += [loop, loop / "below"]
        before = self.inventory()
        for value in bad_dirs:
            with self.subTest(directory=repr(value)), self.assertRaises(StoreError):
                M.SeriesFiles(value, max_bytes=BUDGET)
        for value in (0, -1, True, 1.0, "1", None, int(np.iinfo(np.intp).max) + 1):
            with self.subTest(max_bytes=value), self.assertRaises(StoreError):
                M.SeriesFiles(self.root, max_bytes=value)
        for value in (-1, 10.5, 11, 10 ** 1000, float("nan"), float("inf"), True, "1", None):
            with self.subTest(lock_timeout=value), self.assertRaises(StoreError):
                self.files(lock_timeout=value)
        self.assertEqual(self.inventory(), before)
        with self.assertRaises(TypeError):
            M.SeriesFiles(self.root)  # max_bytes is required
        self.assertEqual(self.files(lock_timeout=0).lock_timeout, 0.0)
        self.assertEqual(self.files(lock_timeout=10).lock_timeout, 10.0)
        self.assertEqual(self.files().lock_timeout, 2.0)
        self.assertEqual(self.files().directory, self.root.resolve())
        self.assertEqual(self.inventory(), before)

    def test_input_refusals_happen_before_any_file_effect(self):
        store = self.files(max_bytes=len(PAYLOAD))
        cases = [(bytearray(PAYLOAD), SHA), (memoryview(PAYLOAD), SHA), (PAYLOAD.hex(), SHA),
                 (PAYLOAD, SHA.upper()), (PAYLOAD, SHA[:-1]), (PAYLOAD, "0" * 64),
                 (PAYLOAD, None), (PAYLOAD + b"\0", SHA), (PAYLOAD[:-1], SHA)]
        with patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")), \
                patch.object(M, "_acquire_os", side_effect=AssertionError("no lock")):
            for payload, digest in cases:
                with self.subTest(payload=type(payload), digest=digest), self.assertRaises(SeriesFormatError):
                    store.write(payload, digest)
            for digest in (SHA.upper(), SHA + "0", " " + SHA[1:], None, SHA.encode()):
                with self.subTest(read=digest), self.assertRaises(SeriesFormatError):
                    store.read(digest)
            with self.assertRaises(SeriesFormatError):
                self.files(max_bytes=len(PAYLOAD) - 1).write(PAYLOAD, SHA)
        self.assertEqual(self.inventory(), [])
        self.assertEqual(store.write(PAYLOAD, SHA), (SHA, True))  # exact budget boundary

    # --- publish, read, idempotence -----------------------------------------------
    def test_write_publishes_exact_bytes_and_read_returns_readonly_array(self):
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertEqual(self.sidecar.read_bytes(), b"\0")
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)
        first, second = self.files().read(SHA), self.files().read(SHA)
        self.assertIs(type(first), np.ndarray)
        self.assertEqual(first.tobytes(), RAW)
        self.assertFalse(first.flags.writeable)
        first.setflags(write=True)
        first[0, 0] = 99.0
        self.assertEqual(second.tobytes(), RAW)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def test_temp_is_same_directory_fsynced_and_closed_before_replace(self):
        log, temps = [], []
        real_mkstemp, real_fsync = tempfile.mkstemp, os.fsync
        def mkstemp(*args, **kwargs):
            fd, name = real_mkstemp(*args, **kwargs)
            temps.append((fd, Path(name)))
            log.append("mkstemp")
            return fd, name
        def fsync(fd):
            info = os.fstat(fd)
            if stat.S_ISDIR(info.st_mode):
                kind = "dir"
            elif temps and fd == temps[0][0] and "replace" not in log:
                kind = "temp"
            elif self.sidecar.exists() and os.path.samestat(info, os.stat(self.sidecar)):
                kind = "sidecar"
            else:
                kind = "other"
            log.append("fsync-" + kind)
            return real_fsync(fd)
        def close(fd):
            if temps and fd == temps[0][0] and "replace" not in log:
                log.append("close-temp")
            return REAL_CLOSE(fd)
        def replace(src, dst):
            log.append("replace")
            self.assertEqual(Path(src), temps[0][1])
            self.assertEqual(Path(dst), self.files().directory / (SHA + ".npy"))
            return REAL_REPLACE(src, dst)
        with patch.object(M.tempfile, "mkstemp", side_effect=mkstemp), \
                patch.object(M.os, "fsync", side_effect=fsync), \
                patch.object(M.os, "close", side_effect=close), \
                patch.object(M.os, "replace", side_effect=replace):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        name = temps[0][1]
        self.assertEqual(name.parent, self.files().directory)
        self.assertTrue(name.name.startswith("." + SHA + ".") and name.name.endswith(".tmp"))
        expected = ["fsync-sidecar", "mkstemp", "fsync-temp", "close-temp", "replace"]
        if os.name != "nt":
            expected.append("fsync-dir")
        self.assertEqual(log, expected)
        self.assert_no_temp()

    def test_existing_valid_target_is_validated_then_skipped_without_overwrite(self):
        self.files().write(PAYLOAD, SHA)
        before = self.target.stat()
        calls = []
        real_decode = M.decode_series
        def counted(payload, digest, *, max_bytes):
            calls.append(payload)
            return real_decode(payload, digest, max_bytes=max_bytes)
        with patch.object(M, "decode_series", side_effect=counted), \
                patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")), \
                patch.object(M.os, "replace", side_effect=AssertionError("no replace")):
            self.assertEqual(self.files().write(ALT_PAYLOAD, SHA), (SHA, False))
        self.assertEqual(calls, [ALT_PAYLOAD, PAYLOAD])  # input, then existing target
        after = self.target.stat()
        self.assertEqual((after.st_ino, after.st_mtime_ns, after.st_size),
                         (before.st_ino, before.st_mtime_ns, before.st_size))
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def test_alternate_header_is_stored_verbatim_under_content_name(self):
        self.assertEqual(self.files().write(ALT_PAYLOAD, SHA), (SHA, True))
        self.assertEqual(self.target.read_bytes(), ALT_PAYLOAD)
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
        self.assertEqual(self.target.read_bytes(), ALT_PAYLOAD)

    # --- refusing and preserving bad targets ---------------------------------------
    def test_corrupt_targets_are_refused_and_preserved(self):
        other, _ = other_series()
        variants = {"empty": b"", "truncated": PAYLOAD[:-1], "trailing": PAYLOAD + b"\0",
                    "flipped": PAYLOAD[:-1] + bytes([PAYLOAD[-1] ^ 1]), "magic": b"X" + PAYLOAD[1:],
                    "other_content": other}
        for name, data in variants.items():
            with self.subTest(variant=name):
                self.remove_target()
                self.corrupt_after_valid_write(data)
                with patch.object(M.os, "replace", side_effect=AssertionError("no replace")), \
                        patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")):
                    with self.assertRaises(IntegrityError) as written:
                        self.files().write(PAYLOAD, SHA)
                    with self.assertRaises(IntegrityError):
                        self.files().read(SHA)
                self.assertIsInstance(written.exception.__cause__, SeriesFormatError)
                self.assertEqual(self.target.read_bytes(), data)
                self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def test_oversized_targets_are_refused_and_preserved(self):
        self.corrupt_after_valid_write(PAYLOAD + b"\0" * 64)
        real_read = os.read
        for budget in (len(PAYLOAD), len(PAYLOAD) + 63):
            with self.subTest(budget=budget):
                reads = []
                def bounded(fd, n):
                    reads.append(n)
                    return real_read(fd, n)
                with patch.object(M.os, "read", side_effect=bounded):
                    with self.assertRaisesRegex(IntegrityError, "max_bytes"):
                        self.files(max_bytes=budget).write(PAYLOAD, SHA)
                    with self.assertRaisesRegex(IntegrityError, "max_bytes"):
                        self.files(max_bytes=budget).read(SHA)
                self.assertEqual(reads, [])  # refused from fstat before reading content
        self.assertEqual(self.target.read_bytes(), PAYLOAD + b"\0" * 64)
        self.assert_no_temp()
        self.target.write_bytes(PAYLOAD)
        with self.assertRaises(IntegrityError):  # valid file, smaller reader budget
            self.files(max_bytes=len(PAYLOAD) - 1).read(SHA)
        self.assertEqual(self.files(max_bytes=len(PAYLOAD)).read(SHA).tobytes(), RAW)

    def test_symlink_targets_are_refused_and_preserved(self):
        self.files().write(PAYLOAD, SHA)
        real = self.root / "real.bin"
        real.write_bytes(PAYLOAD)
        self.target.unlink()
        try:
            self.target.symlink_to(real)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted here")
        for label in ("to_valid_file", "dangling"):
            with self.subTest(label=label):
                if label == "dangling":
                    real.unlink()
                with self.assertRaises(IntegrityError):
                    self.files().write(PAYLOAD, SHA)
                with self.assertRaises(IntegrityError):
                    self.files().read(SHA)
                self.assertTrue(self.target.is_symlink())
                self.assert_no_temp()
        self.assertEqual(Path(os.readlink(self.target)).name, real.name)

    def test_non_regular_targets_are_refused_and_preserved(self):
        self.corrupt_after_valid_write(None)
        self.target.mkdir()
        (self.target / "inside").write_bytes(b"keep")
        with self.assertRaises(IntegrityError):
            self.files().write(PAYLOAD, SHA)
        with self.assertRaises(IntegrityError):
            self.files().read(SHA)
        self.assertEqual((self.target / "inside").read_bytes(), b"keep")
        self.assert_no_temp()
        if hasattr(os, "mkfifo"):
            (self.target / "inside").unlink()
            self.target.rmdir()
            os.mkfifo(self.target)
            started = time.monotonic()
            with self.assertRaises(IntegrityError):
                self.files().write(PAYLOAD, SHA)
            with self.assertRaises(IntegrityError):
                self.files().read(SHA)
            self.assertLess(time.monotonic() - started, 5)
            self.assertTrue(stat.S_ISFIFO(self.target.lstat().st_mode))
            self.assert_no_temp()

    def test_existing_target_without_sidecar_is_refused_before_sidecar_creation(self):
        self.target.write_bytes(PAYLOAD)
        opens = []
        real_open_regular = M._open_regular
        def observed(path, flags, error):
            if Path(path).name == self.sidecar.name:
                opens.append(bool(flags & os.O_CREAT))
            return real_open_regular(path, flags, error)
        with patch.object(M, "_open_regular", side_effect=observed):
            for operation in ("write", "read"):
                opens.clear()
                with self.subTest(operation=operation), self.assertRaises(M.SidecarMissing):
                    if operation == "write":
                        self.files().write(PAYLOAD, SHA)
                    else:
                        self.files().read(SHA)
                self.assertEqual(opens, [False, False])  # first open, then the re-check
        self.assertEqual(self.inventory(), [SHA + ".npy"])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.target.unlink()
        try:
            self.target.symlink_to(self.root / "missing")
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(M.SidecarMissing):
            self.files().write(PAYLOAD, SHA)
        self.assertEqual(self.inventory(), [SHA + ".npy"])

    def test_missing_series_read_creates_nothing(self):
        with self.assertRaises(M.SeriesNotFound):
            self.files().read(SHA)
        self.assertEqual(self.inventory(), [])
        self.sidecar.write_bytes(b"")
        with self.assertRaises(M.SeriesNotFound):
            self.files().read(SHA)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        self.assertEqual(self.sidecar.read_bytes(), b"")  # read never initializes it

    def test_non_regular_sidecar_is_refused_before_temp_or_target(self):
        self.sidecar.mkdir()
        with patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")):
            with self.assertRaises(StoreError):
                self.files().write(PAYLOAD, SHA)
            with self.assertRaises(StoreError):
                self.files().read(SHA)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        self.assertEqual(list(self.sidecar.iterdir()), [])

    # --- lock protocol --------------------------------------------------------------
    def test_sidecar_is_initialized_with_nul_only_after_os_lock(self):
        with patch.object(M, "_try_os_lock", side_effect=OSError(errno.EAGAIN, "held")):
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.05).write(PAYLOAD, SHA)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        self.assertEqual(self.sidecar.read_bytes(), b"")
        sizes = []
        real_lock = M._try_os_lock
        def observed(fd):
            sizes.append(os.fstat(fd).st_size)
            return real_lock(fd)
        with patch.object(M, "_try_os_lock", side_effect=observed):
            self.files().write(PAYLOAD, SHA)
            self.files().read(SHA)
        self.assertEqual(sizes, [0, 1])
        self.assertEqual(self.sidecar.read_bytes(), b"\0")

    def test_windows_branch_seeks_byte_zero_before_lock_and_unlock(self):
        events = []
        busy = [True]
        class FakeMsvcrt:
            LK_NBLCK, LK_UNLCK = 2, 0
            @staticmethod
            def locking(fd, mode, nbytes):
                if busy[0]:  # one contended attempt that also moves the offset
                    busy[0] = False
                    os.lseek(fd, 5, os.SEEK_SET)
                    raise OSError(errno.EACCES, "synthetic held byte")
                events.append(("locking", mode, nbytes, os.lseek(fd, 0, os.SEEK_CUR),
                               os.fstat(fd).st_size))
        real_write = os.write
        def logged_write(fd, data):
            if os.fstat(fd).st_size == 0 and bytes(data) == b"\0":
                events.append(("nul",))
            return real_write(fd, data)
        with patch.object(M, "_WINDOWS", True), patch.object(M, "msvcrt", FakeMsvcrt, create=True), \
                patch.object(M.os, "write", side_effect=logged_write), \
                patch.object(M, "_fsync_directory", side_effect=AssertionError("POSIX only")):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
            self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(events, [("locking", 2, 1, 0, 0), ("nul",), ("locking", 0, 1, 0, 1),
                                  ("locking", 2, 1, 0, 1), ("locking", 0, 1, 0, 1)])

    def test_process_lock_timeout_leaves_directory_unchanged(self):
        holder = self.files()
        held = holder._acquire(SHA, create=True)
        try:
            started = time.monotonic()
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.05).write(PAYLOAD, SHA)
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0).read(SHA)
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual(self.inventory(), [SHA + ".lock"])
        finally:
            self.assertEqual(M._release(held), [])
        self.assertEqual(self.files(lock_timeout=0).write(PAYLOAD, SHA), (SHA, True))

    def test_os_lock_from_another_descriptor_times_out_then_releases(self):
        self.files().write(PAYLOAD, SHA)
        fd = os.open(self.sidecar, os.O_RDWR | getattr(os, "O_BINARY", 0))
        try:
            M._try_os_lock(fd)
            started = time.monotonic()
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.1).read(SHA)
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.1).write(PAYLOAD, SHA)
            self.assertLess(time.monotonic() - started, 2)
            M._unlock_os(fd)
        finally:
            os.close(fd)
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_one_deadline_spans_process_and_os_lock_stages(self):
        observed = []
        real_remaining = M._remaining
        def process_stage(deadline):
            observed.append(deadline)  # only the process-lock acquire asks outside _acquire_os
            return real_remaining(deadline)
        def os_stage(fd, deadline):
            observed.append(deadline)
            raise LockTimeout("synthetic remaining-budget timeout")
        with patch.object(M, "_remaining", side_effect=process_stage), \
                patch.object(M, "_acquire_os", side_effect=os_stage):
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.2).write(PAYLOAD, SHA)
        self.assertEqual(len(observed), 2)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(self.files(lock_timeout=0).write(PAYLOAD, SHA), (SHA, True))

    def test_busy_map_guard_does_not_time_out_a_zero_timeout_caller(self):
        # The guard covers one dictionary lookup for every digest in the process;
        # lock_timeout applies to this digest's own locks, not to that lookup.
        payload, digest = other_series()
        guard, done, outcome = M._PROCESS_GUARD, threading.Event(), []
        def worker():
            try:
                outcome.append(self.files(lock_timeout=0).write(payload, digest))
            except BaseException as exc:
                outcome.append(exc)
            finally:
                done.set()
        guard.acquire()
        try:
            thread = threading.Thread(target=worker)
            thread.start()
            finished_while_held = done.wait(0.3)
        finally:
            guard.release()
        thread.join(30)
        self.assertFalse(finished_while_held, outcome)
        self.assertEqual(outcome, [(digest, True)])
        self.assert_no_temp()

    def test_spawned_process_holding_lock_blocks_writer_until_release(self):
        ctx = multiprocessing.get_context("spawn")
        ready, release = ctx.Event(), ctx.Event()
        child = ctx.Process(target=_hold_lock_child, args=(str(self.root), ready, release))
        child.start()
        try:
            self.assertTrue(ready.wait(60), "child did not acquire the temporary lock")
            started = time.monotonic()
            with self.assertRaises(LockTimeout):
                self.files(lock_timeout=0.1).write(PAYLOAD, SHA)
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual(self.inventory(), [SHA + ".lock"])
        finally:
            release.set()
            child.join(60)
            if child.is_alive():
                child.terminate()
                child.join(10)
        self.assertEqual(child.exitcode, 0)
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))

    def test_two_spawned_writers_of_one_digest_create_exactly_once(self):
        # Smoke only: whether the two children actually overlap is probabilistic.
        ctx = multiprocessing.get_context("spawn")
        start = ctx.Event()
        children = [ctx.Process(target=_write_child, args=(str(self.root), start)) for _ in range(2)]
        for child in children:
            child.start()
        try:
            start.set()
            for child in children:
                child.join(60)
        finally:
            for child in children:
                if child.is_alive():
                    child.terminate()
                    child.join(10)
        self.assertEqual(sorted(child.exitcode for child in children), [10, 11])
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_threads_share_process_locks_per_digest(self):
        # Smoke only; the deterministic exclusion evidence is the lock tests above.
        others = [other_series(start=float(10 * n)) for n in range(3)]
        barrier = threading.Barrier(6)
        results, errors = [], []
        def worker(payload, digest):
            try:
                barrier.wait(timeout=10)
                results.append(self.files(lock_timeout=10).write(payload, digest))
            except BaseException as exc:
                errors.append(exc)
        jobs = [(PAYLOAD, SHA)] * 3 + others
        threads = [threading.Thread(target=worker, args=job) for job in jobs]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        self.assertEqual(errors, [])
        self.assertEqual(sorted(created for digest, created in results if digest == SHA), [False, False, True])
        self.assertTrue(all(created for digest, created in results if digest != SHA))
        self.assert_no_temp()
        self.assertEqual(len(self.inventory()), 8)

    @unittest.skipUnless(hasattr(os, "fork") and os.name != "nt", "POSIX fork only")
    def test_fork_resets_python_process_lock_state_only(self):
        key = os.path.normcase(str(self.files().directory / (SHA + ".lock")))
        local = M._process_lock(key)
        self.assertTrue(local.acquire(timeout=1))
        try:
            pid = os.fork()
            if pid == 0:
                code = 1
                try:
                    fresh = M._process_lock(key)
                    code = 0 if fresh is not local and fresh.acquire(timeout=0) else 2
                finally:
                    os._exit(code)
            _, status = os.waitpid(pid, 0)
            self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        finally:
            local.release()

    def test_process_lock_state_resets_on_pid_change(self):
        key = os.path.normcase(str(self.files().directory / (SHA + ".lock")))
        with patch.object(M, "_PROCESS_LOCKS", {}), patch.object(M, "_PROCESS_GUARD", threading.Lock()), \
                patch.object(M, "_LOCK_PID", M._LOCK_PID):
            held = M._process_lock(key)
            self.assertTrue(held.acquire(timeout=1))
            guard = M._PROCESS_GUARD
            self.assertTrue(guard.acquire(timeout=1))  # as if a lost thread kept the old guard
            # In a thread, so a missing reset fails the test instead of hanging it.
            found = []
            lookup = threading.Thread(target=lambda: found.append(M._process_lock(key)))
            try:
                with patch.object(M.os, "getpid", return_value=os.getpid() + 1):
                    lookup.start()
                    lookup.join(2)
                    self.assertFalse(lookup.is_alive(), "lookup waited on the old guard")
                    fresh = found[0]
                    self.assertIsNot(fresh, held)
                    self.assertIsNot(M._PROCESS_GUARD, guard)
                    self.assertTrue(fresh.acquire(timeout=0))
                    fresh.release()
                    self.assertIs(M._process_lock(key), fresh)
            finally:
                guard.release()
                held.release()
                if lookup.ident is not None:
                    lookup.join(10)

    # --- publish retries ------------------------------------------------------------
    def replace_failing(self, failures, effect=None):
        calls = []
        def replace(src, dst):
            calls.append((src, dst))
            if len(calls) <= failures:
                if effect is not None:
                    effect(Path(src), Path(dst))
                raise PermissionError(errno.EACCES, "synthetic sharing violation")
            return REAL_REPLACE(src, dst)
        return calls, replace

    def test_permission_error_is_retried_then_published(self):
        clock = FakeTime()
        calls, replace = self.replace_failing(2)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", clock):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({src for src, _ in calls}), 1)
        self.assertEqual(clock.sleeps, [0.05, 0.1])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assert_no_temp()

    def test_retry_exhaustion_is_ten_attempts_and_leaves_no_temp(self):
        clock = FakeTime()
        calls, replace = self.replace_failing(100)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", clock):
            with self.assertRaises(M.ReplaceRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(len(calls), 10)
        self.assertEqual(caught.exception.attempts, 10)
        self.assertTrue(caught.exception.temp_removed)
        self.assertIsInstance(caught.exception.__cause__, PermissionError)
        self.assertEqual(clock.sleeps, list(M._REPLACE_DELAYS))
        self.assertLessEqual(sum(clock.sleeps), M.REPLACE_BUDGET)
        self.assertEqual(len({src for src, _ in calls}), 1)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        with self.assertRaises(M.SeriesNotFound):
            self.files().read(SHA)
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))

    def test_retry_budget_stops_attempts_before_ten(self):
        clock = FakeTime()
        def slow(src, dst):
            clock.now += 1.5
        calls, replace = self.replace_failing(100, slow)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", clock):
            with self.assertRaises(M.ReplaceRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(caught.exception.attempts, 4)
        self.assertEqual(len(calls), 4)
        self.assertEqual(clock.sleeps, [0.05, 0.1, 0.2])
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_no_attempt_starts_once_the_budget_has_elapsed(self):
        self.assertEqual((M.REPLACE_ATTEMPTS, M.REPLACE_BUDGET), (10, 5.0))
        self.assertEqual(M._REPLACE_DELAYS, (0.05, 0.1, 0.2, 0.4, 0.8, 0.8, 0.8, 0.8, 0.8))
        def run(first_cost, delays=None, overshoot=0.0):
            clock, starts = FakeTime(overshoot=overshoot), []
            def replace(src, dst):
                starts.append(clock.now - 1000.0)
                if len(starts) == 1:
                    clock.now += first_cost
                raise PermissionError(errno.EACCES, "synthetic sharing violation")
            items = [patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", clock)]
            if delays is not None:
                items.append(patch.object(M, "_REPLACE_DELAYS", delays))
            with Patches(items):
                with self.assertRaises(M.ReplaceRetryExhausted) as caught:
                    self.files().write(PAYLOAD, SHA)
            self.assertEqual(caught.exception.attempts, len(starts))
            self.assertTrue(all(start < M.REPLACE_BUDGET for start in starts), starts)
            self.assertEqual(self.inventory(), [SHA + ".lock"])
            return clock.sleeps, len(starts)
        # 4.96875 s used: the 0.05 s wait would reach 5 s, so the store stops without it.
        self.assertEqual(run(4.96875), ([], 1))
        # 4.9375 s used: the full 0.05 s wait fits and one more attempt starts; 0.1 s would not.
        self.assertEqual(run(4.9375), ([0.05], 2))
        # Exact binary values: a wait that would end exactly at 5 s is not taken ...
        self.assertEqual(run(4.9375, delays=(0.0625,) * 9), ([], 1))
        # ... and a late wake-up that reaches 5 s ends the retries before another attempt.
        self.assertEqual(run(4.875, delays=(0.0625,) * 9, overshoot=0.0625), ([0.0625], 1))

    def test_typed_errors_survive_pickling(self):
        # Worker processes (multiprocessing, ProcessPoolExecutor) hand errors back by pickle.
        calls, replace = self.replace_failing(100)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", FakeTime()):
            with self.assertRaises(M.ReplaceRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        back = pickle.loads(pickle.dumps(caught.exception))
        self.assertIs(type(back), M.ReplaceRetryExhausted)
        self.assertEqual((str(back), back.attempts, back.temp_removed),
                         (str(caught.exception), 10, True))
        classes = (M.ReplaceRetryExhausted, M.PublicationUncertain, M.ReleaseError,
                   M.SidecarMissing, M.SeriesNotFound)
        for cls in classes:
            with self.subTest(cls=cls.__name__):
                extra = {"attempts": 3, "temp_removed": False} if cls is M.ReplaceRetryExhausted else {}
                error = M._attach(cls("synthetic", **extra), [OSError(errno.EIO, "cleanup")])
                back = pickle.loads(pickle.dumps(error))
                self.assertIs(type(back), cls)
                self.assertEqual(str(back), "synthetic")
                self.assertEqual([str(e) for e in back.cleanup_errors], ["[Errno 5] cleanup"])
                for name, value in extra.items():
                    self.assertEqual(getattr(back, name), value)

    def test_target_appearing_during_retry_is_uncertain_without_overwrite(self):
        def appear(src, dst):
            dst.write_bytes(b"foreign")
        calls, replace = self.replace_failing(1, appear)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", FakeTime()):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(caught.exception.__cause__, PermissionError)
        self.assertEqual(self.target.read_bytes(), b"foreign")
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def test_target_appearing_on_final_attempt_is_uncertain_not_exhausted(self):
        calls = []
        def replace(src, dst):
            calls.append(src)
            if len(calls) == M.REPLACE_ATTEMPTS:
                Path(dst).write_bytes(b"foreign")
            raise PermissionError(errno.EACCES, "synthetic sharing violation")
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", FakeTime()):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, M.ReplaceRetryExhausted)
        self.assertEqual(len(calls), M.REPLACE_ATTEMPTS)
        self.assertEqual(self.target.read_bytes(), b"foreign")
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def test_changed_or_vanished_temp_during_retry_is_uncertain(self):
        def swap(src, dst):
            # Rename a live file over the temp, so the old inode number cannot be reused.
            other = src.with_name("swap.bin")
            other.write_bytes(PAYLOAD)
            REAL_REPLACE(other, src)
        def vanish(src, dst):
            src.unlink()
        def truncated(src, dst):
            os.truncate(src, 0)  # same identity, different size
        for label, effect in (("swapped", swap), ("vanished", vanish), ("truncated", truncated)):
            with self.subTest(label=label):
                calls, replace = self.replace_failing(1, effect)
                with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", FakeTime()):
                    with self.assertRaises(M.PublicationUncertain):
                        self.files().write(PAYLOAD, SHA)
                self.assertEqual(len(calls), 1)
                self.assertFalse(self.target.exists())
                temps = [n for n in self.inventory() if n.endswith(".tmp")]
                self.assertEqual(len(temps), 1 if label == "swapped" else 0)
                for name in temps:  # foreign file kept by the store, removed by the test
                    self.assertEqual((self.root / name).read_bytes(), PAYLOAD)
                    (self.root / name).unlink()
                self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_other_replace_errors_are_uncertain_and_not_retried(self):
        calls = []
        def replace(src, dst):
            calls.append(src)
            raise OSError(errno.EIO, "synthetic I/O error")
        with patch.object(M.os, "replace", side_effect=replace), \
                patch.object(M.time, "sleep", side_effect=AssertionError("no retry wait")):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(len(calls), 1)
        self.assertEqual(caught.exception.__cause__.errno, errno.EIO)
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_target_appearing_before_first_replace_is_uncertain(self):
        real_mkstemp = tempfile.mkstemp
        def mkstemp(*args, **kwargs):
            result = real_mkstemp(*args, **kwargs)
            self.target.write_bytes(b"foreign")
            return result
        with patch.object(M.tempfile, "mkstemp", side_effect=mkstemp), \
                patch.object(M.os, "replace", side_effect=AssertionError("no replace")):
            with self.assertRaises(M.PublicationUncertain):
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(self.target.read_bytes(), b"foreign")
        self.assert_no_temp()

    # --- temp file failures ---------------------------------------------------------
    def test_short_writes_complete_and_zero_progress_fails_closed(self):
        real_write = os.write
        sizes = []
        def short(fd, data):
            sizes.append(len(data))
            return real_write(fd, bytes(data)[:3])
        with patch.object(M.os, "write", side_effect=short):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertGreater(len(sizes), len(PAYLOAD) // 3)
        self.target.unlink()
        def stalled(fd, data):
            return 0 if len(data) > 1 else real_write(fd, data)
        with patch.object(M.os, "write", side_effect=stalled), \
                patch.object(M.os, "replace", side_effect=AssertionError("no replace")):
            with self.assertRaises(OSError) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(caught.exception.errno, errno.EIO)
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_temp_fsync_or_close_failure_publishes_nothing_and_closes_once(self):
        def failing_fsync(log):
            real_fsync = os.fsync
            def fsync(fd):
                if log.labels.get(fd, ("",))[0] == "tmp":
                    raise OSError(errno.EIO, "synthetic temp fsync failure")
                return real_fsync(fd)
            return fsync
        for label in ("fsync", "close"):
            with self.subTest(label=label):
                log = FdLog(fail_close=(lambda item: item[0] == "tmp") if label == "close" else None)
                extra = [patch.object(M.os, "fsync", side_effect=failing_fsync(log))] if label == "fsync" else []
                with Patches(log.patches() + extra + [
                        patch.object(M.os, "replace", side_effect=AssertionError("no replace"))]):
                    with self.assertRaises(OSError) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertNotIsInstance(caught.exception, M.PublicationUncertain)
                self.assertEqual(caught.exception.errno, errno.EIO)
                self.assertEqual(self.inventory(), [SHA + ".lock"])
                self.assertEqual(log.close_counts("tmp"), [1])
        real_lstat = os.lstat
        seen = []
        def lstat(path, *args, **kwargs):
            result = real_lstat(path, *args, **kwargs)
            if Path(os.fsdecode(path)).name.endswith(".tmp") and not seen:
                seen.append(path)
                return StatOverride(result, st_size=1)
            return result
        log = FdLog()
        with Patches(log.patches() + [patch.object(M.os, "lstat", side_effect=lstat),
                                      patch.object(M.os, "replace", side_effect=AssertionError("no replace"))]):
            with self.assertRaises(StoreError) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, M.PublicationUncertain)
        self.assertEqual(log.close_counts("tmp"), [1])
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)  # ownership unproven, so the store kept it
        (self.root / temps[0]).unlink()
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    # --- post-publication uncertainty -------------------------------------------------
    def test_post_rename_failures_are_publication_uncertain(self):
        state = {}
        def replace(src, dst):
            REAL_REPLACE(src, dst)
            state["replaced"] = True
        def readback_open(path, flags, *args, **kwargs):
            if state.get("replaced") and Path(os.fsdecode(path)).name == self.target.name:
                raise OSError(errno.EIO, "synthetic readback failure")
            return REAL_OPEN(path, flags, *args, **kwargs)
        def tamper_replace(src, dst):
            REAL_REPLACE(src, dst)
            with open(dst, "r+b") as handle:
                handle.seek(-1, os.SEEK_END)
                handle.write(b"\x81")
        def dir_fsync(path):
            raise OSError(errno.EIO, "synthetic directory fsync failure")
        def unlock(fd):
            raise OSError(errno.EIO, "synthetic unlock failure")
        cases = [("readback", lambda: [patch.object(M.os, "replace", side_effect=replace),
                                       patch.object(M.os, "open", side_effect=readback_open)]),
                 ("mismatch", lambda: [patch.object(M.os, "replace", side_effect=tamper_replace)]),
                 ("unlock", lambda: [patch.object(M, "_unlock_os", side_effect=unlock)]),
                 ("sidecar_close", lambda: FdLog(fail_close=lambda item: item[0] == "lock").patches())]
        if os.name != "nt":
            cases.append(("dir_fsync", lambda: [patch.object(M, "_fsync_directory", side_effect=dir_fsync)]))
        for label, patches in cases:
            with self.subTest(label=label):
                self.reset()
                state.clear()
                with Patches(patches()):
                    with self.assertRaises(M.PublicationUncertain) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertIsNotNone(caught.exception.__cause__)
                self.assert_no_temp()
                self.assertTrue(self.target.exists())
                if label == "mismatch":
                    tampered = self.target.read_bytes()
                    with self.assertRaises(IntegrityError):
                        self.files().read(SHA)
                    self.assertNotEqual(tampered, PAYLOAD)
                    self.assertEqual(self.target.read_bytes(), tampered)
                else:
                    self.assertEqual(self.files().read(SHA).tobytes(), RAW)

    def test_read_and_skip_release_failures_are_release_errors(self):
        self.files().write(PAYLOAD, SHA)
        def unlock(fd):
            raise OSError(errno.EIO, "synthetic unlock failure")
        with patch.object(M, "_unlock_os", side_effect=unlock), \
                patch.object(M.os, "replace", side_effect=AssertionError("no replace")):
            with self.assertRaises(M.ReleaseError) as read_error:
                self.files().read(SHA)
            with self.assertRaises(M.ReleaseError) as skip_error:
                self.files().write(PAYLOAD, SHA)
        for caught in (read_error, skip_error):
            self.assertNotIsInstance(caught.exception, M.PublicationUncertain)
            self.assertIsInstance(caught.exception.__cause__, OSError)
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_close_failures_are_typed_and_close_once(self):
        self.files().write(PAYLOAD, SHA)
        for operation in ("read", "skip"):
            with self.subTest(operation=operation):
                log = FdLog(fail_close=lambda item: item[0] == "npy")
                with Patches(log.patches()):
                    with self.assertRaises(M.ReleaseError) as caught:
                        if operation == "read":
                            self.files().read(SHA)
                        else:
                            self.files().write(PAYLOAD, SHA)
                self.assertNotIsInstance(caught.exception, (IntegrityError, M.PublicationUncertain))
                self.assertIsInstance(caught.exception.__cause__, OSError)
                self.assertEqual(log.close_counts("npy"), [1])
                self.assertEqual(log.close_counts("lock"), [1])
                self.assertEqual(self.files().read(SHA).tobytes(), RAW)  # lock released
        self.reset()
        log = FdLog(fail_close=lambda item: item[0] == "npy")
        with Patches(log.patches()):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertIsInstance(caught.exception.__cause__, OSError)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertEqual(log.close_counts("npy"), [1])
        self.assert_no_temp()
        if os.name == "nt":
            return
        for label in ("success", "fsync"):
            with self.subTest(directory=label):
                self.reset()
                log = FdLog()
                real_fsync = os.fsync
                def fsync(fd):
                    if label == "fsync" and log.labels.get(fd, ("",))[0] == "dir":
                        raise OSError(errno.EIO, "synthetic directory fsync failure")
                    return real_fsync(fd)
                with Patches(log.patches() + [patch.object(M.os, "fsync", side_effect=fsync)]):
                    if label == "success":
                        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
                    else:
                        with self.assertRaises(M.PublicationUncertain):
                            self.files().write(PAYLOAD, SHA)
                self.assertEqual(log.close_counts("dir"), [1])
                self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_primary_errors_keep_cleanup_errors(self):
        self.corrupt_after_valid_write(b"corrupt")
        def unlock(fd):
            raise OSError(errno.EIO, "synthetic unlock failure")
        with patch.object(M, "_unlock_os", side_effect=unlock):
            with self.assertRaises(IntegrityError) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual([str(e) for e in caught.exception.cleanup_errors],
                         ["[Errno 5] synthetic unlock failure"])
        self.assertIsInstance(caught.exception.__cause__, SeriesFormatError)
        self.target.unlink()
        calls, replace = self.replace_failing(100)
        with patch.object(M.os, "replace", side_effect=replace), patch.object(M, "time", FakeTime()), \
                patch.object(M.os, "unlink", side_effect=PermissionError(errno.EACCES, "held")):
            with self.assertRaises(M.ReplaceRetryExhausted) as exhausted:
                self.files().write(PAYLOAD, SHA)
        self.assertFalse(exhausted.exception.temp_removed)
        self.assertEqual(len(exhausted.exception.cleanup_errors), 1)
        self.assertIsInstance(exhausted.exception.cleanup_errors[0], PermissionError)
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)
        self.assertTrue(temps[0].startswith("." + SHA + "."))

    def test_interrupts_clean_up_and_propagate_unwrapped(self):
        # (a) interrupt in the retry wait: owned temp removed, interrupt unwrapped.
        calls, replace = self.replace_failing(100)
        with patch.object(M.os, "replace", side_effect=replace), \
                patch.object(M, "time", FakeTime(interrupt_sleep=True)):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, StoreError)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        with self.assertRaises(M.SeriesNotFound):
            self.files().read(SHA)
        # (b) interrupt in unlock: not wrapped, sidecar closed once, lock usable.
        self.files().write(PAYLOAD, SHA)
        def unlock(fd):
            raise KeyboardInterrupt
        for operation in ("read", "skip"):
            with self.subTest(operation=operation):
                log = FdLog()
                with Patches(log.patches() + [patch.object(M, "_unlock_os", side_effect=unlock)]):
                    with self.assertRaises(KeyboardInterrupt) as caught:
                        if operation == "read":
                            self.files().read(SHA)
                        else:
                            self.files().write(PAYLOAD, SHA)
                self.assertNotIsInstance(caught.exception, StoreError)
                self.assertEqual(log.close_counts("lock"), [1])
                self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        # (c) interrupt right after the rename: publication happened, no temp left.
        self.reset()
        def replace_then_interrupt(src, dst):
            REAL_REPLACE(src, dst)
            raise KeyboardInterrupt
        with patch.object(M.os, "replace", side_effect=replace_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assert_no_temp()
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)  # lock released

    def test_interrupts_at_lock_temp_read_and_readback_sites(self):
        # (d) while polling for the OS lock: the process lock and sidecar are released.
        with patch.object(M, "_try_os_lock", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, StoreError)
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        # (e) in the temp fsync: the temp descriptor is closed once and the temp removed.
        log = FdLog()
        real_fsync = os.fsync
        def fsync(fd):
            if log.labels.get(fd, ("",))[0] == "tmp":
                raise KeyboardInterrupt
            return real_fsync(fd)
        with Patches(log.patches() + [patch.object(M.os, "fsync", side_effect=fsync),
                                      patch.object(M.os, "replace", side_effect=AssertionError("no replace"))]):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.files(lock_timeout=0).write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, StoreError)
        self.assertEqual(log.close_counts("tmp"), [1])
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        # (f) during read verification: the lock is released.
        self.assertEqual(self.files(lock_timeout=0).write(PAYLOAD, SHA), (SHA, True))
        with patch.object(M, "decode_series", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.files().read(SHA)
        self.assertNotIsInstance(caught.exception, StoreError)
        self.assertEqual(self.files(lock_timeout=0).read(SHA).tobytes(), RAW)
        # (g) in the post-rename readback: propagated, not wrapped as PublicationUncertain.
        self.reset()
        with patch.object(M.SeriesFiles, "_read_target", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, StoreError)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assert_no_temp()
        self.assertEqual(self.files(lock_timeout=0).read(SHA).tobytes(), RAW)

    def test_sidecar_created_by_racing_writer_is_not_refused(self):
        real_open_regular = M._open_regular
        for operation in ("read", "write"):
            with self.subTest(operation=operation):
                self.reset()
                state = {"raced": False}
                def racing(path, flags, error):
                    if Path(path).name == self.sidecar.name and not state["raced"]:
                        state["raced"] = True  # another writer finishes between our syscalls
                        self.sidecar.write_bytes(b"\0")
                        self.target.write_bytes(PAYLOAD)
                        raise FileNotFoundError(errno.ENOENT, "synthetic race")
                    return real_open_regular(path, flags, error)
                with patch.object(M, "_open_regular", side_effect=racing):
                    if operation == "read":
                        self.assertEqual(self.files().read(SHA).tobytes(), RAW)
                    else:
                        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
                self.assertTrue(state["raced"])
                self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
                self.assertEqual(self.sidecar.read_bytes(), b"\0")

    # --- bounded reads ---------------------------------------------------------------
    def test_chunked_read_extra_byte_probe_and_changes_during_read(self):
        payload, digest = other_series(7, 5)
        real_read = os.read
        with patch.object(M, "_CHUNK", 7):
            self.assertEqual(self.files().write(payload, digest), (digest, True))
            requests = []
            def counted(fd, n):
                requests.append(n)
                return real_read(fd, n)
            with patch.object(M.os, "read", side_effect=counted):
                self.assertEqual(series_sha256(self.files().read(digest)), digest)
            self.assertLessEqual(max(requests), 7)
            self.assertEqual(sum(requests), len(payload) + 1)  # content plus one probe byte
        def grows(fd, n):
            data = real_read(fd, n)
            return data if data else b"\0"
        def shrinks(fd, n):
            return b""
        for label, effect in (("grows", grows), ("shrinks", shrinks)):
            with self.subTest(label=label), patch.object(M.os, "read", side_effect=effect):
                with self.assertRaises(IntegrityError):
                    self.files().read(digest)
        probed = []
        def probe(fd, n):
            if n == 1:
                probed.append(n)
            return real_read(fd, n)
        real_fstat = os.fstat
        def fstat(fd):
            result = real_fstat(fd)
            return StatOverride(result, st_mtime_ns=result.st_mtime_ns + 1) if probed else result
        with self.subTest(label="mtime"), patch.object(M.os, "read", side_effect=probe), \
                patch.object(M.os, "fstat", side_effect=fstat):
            with self.assertRaisesRegex(IntegrityError, "changed during read"):
                self.files().read(digest)
        self.assertEqual(probed, [1])
        self.assertEqual(series_sha256(self.files().read(digest)), digest)

    # --- scope ------------------------------------------------------------------------
    def test_module_has_no_config_env_clock_network_or_recorder(self):
        fail = AssertionError("discovery forbidden")
        with patch.object(socket.socket, "connect", side_effect=fail), \
                patch.object(os, "getenv", side_effect=fail), \
                patch.object(time, "time", side_effect=fail):
            self.files().write(PAYLOAD, SHA)
            self.files().read(SHA)
        tree = ast.parse(Path(M.__file__).read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imports |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {"__future__", "errno", "math", "os", "pathlib", "re", "stat",
                                   "tempfile", "threading", "time", "numpy", "msvcrt", "fcntl",
                                   "core.quant.run_registry_series_format",
                                   "core.quant.run_registry_store"})
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for forbidden in ("environ", "getenv", "macro_dir", "series_error", "mkdir", "makedirs",
                          "rmtree", "datetime", "home", "expanduser", "gettempdir"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
