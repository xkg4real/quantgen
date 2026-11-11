"""Temporary-only acceptance for detached verified R3 series files.

Every filesystem effect uses a fresh TemporaryDirectory. No ledger, macro
directory, configuration, environment, provider, network or real series is used.
Windows branches are simulated with a fake msvcrt on other platforms, and with
a stand-in os.rename that refuses an existing destination as Windows does.
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
REAL_RENAME = os.rename
REAL_OPEN = os.open
REAL_CLOSE = os.close
# The no-clobber call this platform's branch makes (owner ruling 10, 2026-11-11).
PUBLISH = "rename" if os.name == "nt" else "link"
REAL_PUBLISH = getattr(os, PUBLISH)
NO_PUBLISH = AssertionError("no publish")
# Calls that can replace an existing name; the store must never reach them.
OVERWRITING = ("replace",) if os.name == "nt" else ("replace", "rename")


def windows_rename(src, dst):
    """os.rename as Windows performs it: an existing destination is never replaced."""
    if os.path.lexists(dst):
        raise FileExistsError(errno.EEXIST, "synthetic ERROR_ALREADY_EXISTS", os.fspath(dst))
    return REAL_RENAME(src, dst)


def deny_target_open(path, flags, mode=0o777, *, dir_fd=None):
    """os.open that refuses the series target only, like a file its writer still holds open."""
    if os.fsdecode(path).endswith(".npy"):
        raise PermissionError(errno.EACCES, "synthetic sharing violation", os.fspath(path))
    return REAL_OPEN(path, flags, mode, dir_fd=dir_fd)


class QuietMsvcrt:
    """A stand-in msvcrt whose byte lock always succeeds (single-caller tests only)."""
    LK_NBLCK, LK_UNLCK = 2, 0

    @staticmethod
    def locking(fd, mode, nbytes):
        return None


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
    ``during(n)`` runs inside the n-th wait (1-based), as another program would.
    """
    def __init__(self, start=1000.0, interrupt_sleep=False, overshoot=0.0, during=None):
        self.now, self.sleeps, self.interrupt_sleep = start, [], interrupt_sleep
        self.overshoot, self.during = overshoot, during

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        if self.interrupt_sleep:
            raise KeyboardInterrupt
        self.sleeps.append(seconds)
        if self.during is not None:
            self.during(len(self.sleeps))
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
        for name in OVERWRITING:  # os.replace, and POSIX os.rename, replace an existing name
            guard = patch.object(M.os, name, side_effect=AssertionError(f"os.{name} can overwrite"))
            guard.start()
            self.addCleanup(guard.stop)

    def files(self, **kwargs):
        kwargs.setdefault("max_bytes", BUDGET)
        return M.SeriesFiles(self.root, **kwargs)

    def inventory(self):
        return sorted(p.name for p in self.root.iterdir())

    def temps(self):
        return [n for n in self.inventory() if n.endswith(".tmp")]

    def assert_no_temp(self):
        self.assertEqual(self.temps(), [])

    def remove_target(self):
        if self.target.is_symlink() or self.target.is_file():
            self.target.unlink()

    def reset(self):
        for path in (self.target, self.sidecar):
            if path.is_dir() and not path.is_symlink():
                path.rmdir()
            elif path.is_symlink() or path.exists():
                path.unlink()

    def windows_branch(self, before=None):
        """Patches that run the store's Windows branch, and the os.rename calls it makes.

        On Windows the real os.rename and msvcrt are used. Elsewhere the branch
        is selected with a stand-in msvcrt, and os.rename is the stand-in that
        refuses an existing destination, because POSIX rename would replace it.
        ``before(src, dst)`` runs inside each call, before the rename itself.
        """
        calls = []
        real = REAL_RENAME if os.name == "nt" else windows_rename
        def rename(src, dst):
            calls.append((Path(src), Path(dst)))
            if before is not None:
                before(Path(src), Path(dst))
            return real(src, dst)
        items = [patch.object(M.os, "rename", side_effect=rename),
                 patch.object(M.os, "link", side_effect=AssertionError("POSIX branch only"))]
        if os.name != "nt":
            items += [patch.object(M, "_WINDOWS", True),
                      patch.object(M, "msvcrt", QuietMsvcrt, create=True),
                      patch.object(M, "_fsync_directory", side_effect=AssertionError("POSIX only"))]
        return calls, items

    BRANCHES = ("native", "windows")

    def branch(self, name, before=None):
        """(calls, patches) for one publish branch; ``before(src, dst)`` runs inside each call.

        "native" is this platform's own call (os.link on POSIX, os.rename on Windows) and
        "windows" the Windows branch (windows_branch), so both are run on every platform.
        """
        if name == "windows":
            return self.windows_branch(before)
        calls = []
        def publish(src, dst):
            calls.append((Path(src), Path(dst)))
            if before is not None:
                before(Path(src), Path(dst))
            return REAL_PUBLISH(src, dst)
        return calls, [patch.object(M.os, PUBLISH, side_effect=publish)]

    def refused_rename(self, failures, effect=None):
        """The Windows branch with os.rename refused ``failures`` times, then performed.

        The refusal is a PermissionError, as for a sharing violation while another program
        holds the new file open; ``effect(src, dst)`` runs before each one. Only this branch
        retries a refused publish call: a POSIX os.link error is never retried.
        """
        seen = []
        def before(src, dst):
            seen.append(src)
            if len(seen) <= failures:
                if effect is not None:
                    effect(src, dst)
                raise PermissionError(errno.EACCES, "synthetic sharing violation")
        return self.windows_branch(before)

    def target_opens(self, refuse=0, seen=None):
        """os.open that counts opens of the series target and refuses the first ``refuse``."""
        opens = [] if seen is None else seen
        def opened(path, flags, mode=0o777, *, dir_fd=None):
            if os.fsdecode(path).endswith(".npy"):
                opens.append(len(self.temps()))  # this call's temp files at the time of the look
                if len(opens) <= refuse:
                    raise PermissionError(errno.EACCES, "synthetic sharing violation", os.fspath(path))
            return REAL_OPEN(path, flags, mode, dir_fd=dir_fd)
        return opens, patch.object(M.os, "open", side_effect=opened)

    def sync_log(self):
        """(log, patches): fsyncs by kind of descriptor, and the temp's unlink, in order."""
        log, fds = [], {}
        real_fsync, real_unlink = os.fsync, os.unlink
        def opened(path, flags, mode=0o777, *, dir_fd=None):
            fd = REAL_OPEN(path, flags, mode, dir_fd=dir_fd)
            writable = flags & (os.O_WRONLY | os.O_RDWR)
            fds[fd] = FdLog.kind(path) + ("" if writable or os.path.isdir(path) else "-readonly")
            return fd
        def fsync(fd):
            log.append("fsync-" + fds.get(fd, "unknown"))
            return real_fsync(fd)
        def unlink(path, *args, **kwargs):
            log.append("unlink-" + FdLog.kind(path))
            return real_unlink(path, *args, **kwargs)
        return log, [patch.object(M.os, "open", side_effect=opened),
                     patch.object(M.os, "fsync", side_effect=fsync),
                     patch.object(M.os, "unlink", side_effect=unlink)]

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

    def test_temp_is_same_directory_fsynced_and_closed_before_publish(self):
        log, temps = [], []
        real_mkstemp, real_fsync, real_unlink = tempfile.mkstemp, os.fsync, os.unlink
        def mkstemp(*args, **kwargs):
            fd, name = real_mkstemp(*args, **kwargs)
            temps.append((fd, Path(name)))
            log.append("mkstemp")
            return fd, name
        def fsync(fd):
            info = os.fstat(fd)
            if stat.S_ISDIR(info.st_mode):
                kind = "dir"
            elif temps and fd == temps[0][0] and "publish" not in log:
                kind = "temp"
            elif self.sidecar.exists() and os.path.samestat(info, os.stat(self.sidecar)):
                kind = "sidecar"
            else:
                kind = "other"
            log.append("fsync-" + kind)
            return real_fsync(fd)
        def close(fd):
            if temps and fd == temps[0][0] and "publish" not in log:
                log.append("close-temp")
            return REAL_CLOSE(fd)
        def publish(src, dst):
            log.append("publish")
            self.assertEqual(Path(src), temps[0][1])
            self.assertEqual(Path(dst), self.files().directory / (SHA + ".npy"))
            return REAL_PUBLISH(src, dst)
        def unlink(path, *args, **kwargs):
            if temps and Path(os.fsdecode(path)) == temps[0][1]:
                log.append("unlink-temp")
            return real_unlink(path, *args, **kwargs)
        with patch.object(M.tempfile, "mkstemp", side_effect=mkstemp), \
                patch.object(M.os, "fsync", side_effect=fsync), \
                patch.object(M.os, "close", side_effect=close), \
                patch.object(M.os, "unlink", side_effect=unlink), \
                patch.object(M.os, PUBLISH, side_effect=publish):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        name = temps[0][1]
        self.assertEqual(name.parent, self.files().directory)
        self.assertTrue(name.name.startswith("." + SHA + ".") and name.name.endswith(".tmp"))
        expected = ["fsync-sidecar", "mkstemp", "fsync-temp", "close-temp", "publish"]
        if os.name != "nt":
            # POSIX: the link, then the temp name's unlink, then one directory fsync for both.
            expected += ["unlink-temp", "fsync-dir"]
        self.assertEqual(log, expected)
        self.assert_no_temp()
        self.assertEqual(self.target.stat().st_nlink, 1)

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
                patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH):
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
                with patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH), \
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
        renames = []
        def rename(src, dst):
            renames.append((Path(src).name.endswith(".tmp"), Path(dst).name))
            return windows_rename(src, dst)
        with patch.object(M, "_WINDOWS", True), patch.object(M, "msvcrt", FakeMsvcrt, create=True), \
                patch.object(M.os, "write", side_effect=logged_write), \
                patch.object(M.os, "rename", side_effect=rename), \
                patch.object(M.os, "link", side_effect=AssertionError("POSIX branch only")), \
                patch.object(M, "_fsync_directory", side_effect=AssertionError("POSIX only")):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
            self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(renames, [(True, SHA + ".npy")])  # one os.rename, no link, no directory fsync
        self.assert_no_temp()
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

    # --- publish retries: the Windows branch only (/code-review F9) -------------------
    def test_permission_error_is_retried_then_published(self):
        clock = FakeTime()
        calls, items = self.refused_rename(2)
        with Patches(items + [patch.object(M, "time", clock)]):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({src for src, _ in calls}), 1)
        self.assertEqual(clock.sleeps, [0.05, 0.1])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assert_no_temp()

    def test_retry_exhaustion_is_ten_attempts_and_leaves_no_temp(self):
        clock = FakeTime()
        calls, items = self.refused_rename(100)
        with Patches(items + [patch.object(M, "time", clock)]):
            with self.assertRaises(M.PublishRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(len(calls), 10)
        self.assertEqual(caught.exception.attempts, 10)
        self.assertTrue(caught.exception.temp_removed)
        self.assertIsInstance(caught.exception.__cause__, PermissionError)
        self.assertEqual(clock.sleeps, list(M._PUBLISH_DELAYS))
        self.assertLessEqual(sum(clock.sleeps), M.PUBLISH_BUDGET)
        self.assertEqual(len({src for src, _ in calls}), 1)
        self.assertIn("still raised PermissionError", str(caught.exception))
        self.assertIn("nothing was published", str(caught.exception))
        self.assertEqual(self.inventory(), [SHA + ".lock"])  # no target was made by another route
        with self.assertRaises(M.SeriesNotFound):
            self.files().read(SHA)
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))

    def test_retry_budget_stops_attempts_before_ten(self):
        clock = FakeTime()
        def slow(src, dst):
            clock.now += 1.5
        calls, items = self.refused_rename(100, slow)
        with Patches(items + [patch.object(M, "time", clock)]):
            with self.assertRaises(M.PublishRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(caught.exception.attempts, 4)
        self.assertEqual(len(calls), 4)
        self.assertEqual(clock.sleeps, [0.05, 0.1, 0.2])
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_no_attempt_starts_once_the_budget_has_elapsed(self):
        self.assertEqual((M.PUBLISH_ATTEMPTS, M.PUBLISH_BUDGET), (10, 5.0))
        self.assertEqual(M._PUBLISH_DELAYS, (0.05, 0.1, 0.2, 0.4, 0.8, 0.8, 0.8, 0.8, 0.8))
        def run(first_cost, delays=None, overshoot=0.0):
            clock, starts = FakeTime(overshoot=overshoot), []
            def before(src, dst):
                starts.append(clock.now - 1000.0)
                if len(starts) == 1:
                    clock.now += first_cost
                raise PermissionError(errno.EACCES, "synthetic sharing violation")
            items = self.windows_branch(before)[1] + [patch.object(M, "time", clock)]
            if delays is not None:
                items.append(patch.object(M, "_PUBLISH_DELAYS", delays))
            with Patches(items):
                with self.assertRaises(M.PublishRetryExhausted) as caught:
                    self.files().write(PAYLOAD, SHA)
            self.assertEqual(caught.exception.attempts, len(starts))
            self.assertTrue(all(start < M.PUBLISH_BUDGET for start in starts), starts)
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

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link")
    def test_posix_link_permission_error_ends_at_once_and_is_never_retried(self):
        # /code-review F9. link(2) returns EACCES for a directory that may not be written or
        # searched; waiting does not change that, and the old ten attempts held both locks
        # for 4.75 s. The retry exists for Windows sharing violations only.
        self.assertIsInstance(OSError(errno.EACCES, "x"), PermissionError)
        self.assertNotIn(errno.EACCES, M._NO_HARD_LINK)
        calls = []
        def link(src, dst):
            calls.append(src)
            raise OSError(errno.EACCES, "synthetic: the directory may not be written")
        with patch.object(M.os, "link", side_effect=link), \
                patch.object(M.time, "sleep", side_effect=AssertionError("no retry wait")):
            with self.assertRaises(M.NoClobberUnsupported) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(len(calls), 1)  # setUp's guards: no os.replace or os.rename either
        self.assertIs(type(caught.exception), M.NoClobberUnsupported)
        self.assertIs(type(caught.exception.__cause__), PermissionError)
        self.assertEqual(caught.exception.__cause__.errno, errno.EACCES)
        message = str(caught.exception)
        self.assertIn("os.link refused the hard link (EACCES)", message)
        self.assertIn("nothing was published", message)
        for claim in ("filesystem", "transient", "retr", "attempt", "again"):
            self.assertNotIn(claim, message)  # names the error; claims no cause and no retry
        self.assertEqual(self.inventory(), [SHA + ".lock"])
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))  # both locks released

    def test_retry_names_say_publish_and_the_old_names_are_gone(self):
        # /code-review F8: nothing is replaced any more, so no name says so; no aliases.
        self.assertTrue(issubclass(M.PublishRetryExhausted, StoreError))
        self.assertEqual(len(M._PUBLISH_DELAYS), M.PUBLISH_ATTEMPTS - 1)
        for old in ("REPLACE_ATTEMPTS", "REPLACE_BUDGET", "_REPLACE_DELAYS", "ReplaceRetryExhausted"):
            self.assertFalse(hasattr(M, old), old)

    def test_typed_errors_survive_pickling(self):
        # Worker processes (multiprocessing, ProcessPoolExecutor) hand errors back by pickle.
        calls, items = self.refused_rename(100)
        with Patches(items + [patch.object(M, "time", FakeTime())]):
            with self.assertRaises(M.PublishRetryExhausted) as caught:
                self.files().write(PAYLOAD, SHA)
        back = pickle.loads(pickle.dumps(caught.exception))
        self.assertIs(type(back), M.PublishRetryExhausted)
        self.assertEqual((str(back), back.attempts, back.temp_removed),
                         (str(caught.exception), 10, True))
        classes = (M.PublishRetryExhausted, M.PublicationUncertain, M.ReleaseError,
                   M.SidecarMissing, M.SeriesNotFound, M.NoClobberUnsupported)
        for cls in classes:
            with self.subTest(cls=cls.__name__):
                extra = {"attempts": 3, "temp_removed": False} if cls is M.PublishRetryExhausted else {}
                error = M._attach(cls("synthetic", **extra), [OSError(errno.EIO, "cleanup")])
                back = pickle.loads(pickle.dumps(error))
                self.assertIs(type(back), cls)
                self.assertEqual(str(back), "synthetic")
                self.assertEqual([str(e) for e in back.cleanup_errors], ["[Errno 5] cleanup"])
                for name, value in extra.items():
                    self.assertEqual(getattr(back, name), value)

    # --- no-clobber publish (owner ruling 10, 2026-11-11) -----------------------------
    # A target name that appears after the absence check, created by a writer outside the
    # cooperating lock, is never overwritten: valid bytes are reported as already present
    # (created False, the foreign container kept), anything else is refused and preserved.
    # A regular file that does not verify is looked at again until the attempts or the 5 s
    # are used (/code-review F1), so these tests run on a FakeTime clock and check its waits.
    # A name that is not a regular file is refused at once (⑨-3a/series-files/3).
    # "same_size" has the size of this call's temp and one wrong data byte: a store that
    # compared sizes and not content would adopt it.
    SAME_SIZE = PAYLOAD[:-1] + bytes([PAYLOAD[-1] ^ 1])
    FOREIGN = (("valid", ALT_PAYLOAD), ("invalid", b"foreign"), ("same_size", SAME_SIZE))
    NOT_REGULAR = ("dangling_symlink", "directory", "fifo")

    def write_meets_foreign(self, label, clock=None, waits=None):
        """write() meets a foreign target; ``waits`` are the waits expected on ``clock``.

        Default: none for a valid target and for a name that is not a regular file, and
        every wait of the budget for a regular file that never verifies.
        """
        if label == "valid":
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
        else:
            with self.assertRaises(IntegrityError) as caught:
                self.files().write(PAYLOAD, SHA)
            self.assertIs(type(caught.exception), IntegrityError)
        if clock is not None:
            if waits is None:
                waits = [] if label == "valid" or label in self.NOT_REGULAR else list(M._PUBLISH_DELAYS)
            self.assertEqual(clock.sleeps, waits)

    def assert_foreign_kept(self, data):
        self.assertEqual(self.target.read_bytes(), data)
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    def foreign_makers(self, fifo=False):
        """Ways a non-cooperating writer can occupy the target name (label, make(dst)).

        Regular files first, then the names that are not regular files. A kind this platform
        or this account cannot create (a symlink on Windows without the privilege, a FIFO
        where there is none) is left out.
        """
        def symlink(dst):
            os.symlink(self.root / "missing", dst)
        makers = [(label, lambda dst, data=data: dst.write_bytes(data)) for label, data in self.FOREIGN]
        probe = self.root / "probe-link"
        try:
            symlink(probe)
        except (OSError, NotImplementedError):
            pass
        else:
            probe.unlink()
            makers.append(("dangling_symlink", symlink))
        makers.append(("directory", lambda dst: dst.mkdir()))
        if fifo and hasattr(os, "mkfifo"):
            makers.append(("fifo", lambda dst: os.mkfifo(dst)))
        return tuple(makers)

    def assert_made_kept(self, label):
        """The name a maker occupied is exactly as it was made, and no temp is left."""
        self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
        files = dict(self.FOREIGN)
        if label in files:
            self.assertEqual(self.target.read_bytes(), files[label])
            if os.name != "nt":
                self.assertEqual(self.target.stat().st_nlink, 1)  # and no second name was given to it
            if label == "valid":
                self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        elif label == "directory":
            self.assertTrue(self.target.is_dir() and not self.target.is_symlink())
            self.assertEqual(list(self.target.iterdir()), [])
        elif label == "fifo":
            self.assertTrue(stat.S_ISFIFO(os.lstat(self.target).st_mode))
        else:
            self.assertEqual(Path(os.readlink(self.target)).name, "missing")

    def test_target_created_before_the_first_attempt_is_verified_never_overwritten(self):
        real_mkstemp = tempfile.mkstemp
        for label, data in self.FOREIGN:
            with self.subTest(label=label):
                self.reset()
                clock = FakeTime()
                def mkstemp(*args, **kwargs):
                    result = real_mkstemp(*args, **kwargs)
                    self.target.write_bytes(data)  # after the store's absence check
                    return result
                with patch.object(M.tempfile, "mkstemp", side_effect=mkstemp), \
                        patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH), patch.object(M, "time", clock):
                    self.write_meets_foreign(label, clock)
                self.assert_foreign_kept(data)

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link")
    def test_posix_link_never_overwrites_a_target_created_between_check_and_publish(self):
        # The hook runs inside the publish call, after the store's last absence check, and
        # then calls the real os.link: the kernel itself refuses the existing name.
        for label, make in self.foreign_makers():
            with self.subTest(label=label):
                self.reset()
                clock, calls, synced = FakeTime(), [], []
                def link(src, dst):
                    calls.append((Path(src), Path(dst)))
                    make(Path(dst))
                    return REAL_PUBLISH(src, dst)
                with patch.object(M.os, "link", side_effect=link), patch.object(M, "time", clock), \
                        patch.object(M, "_fsync_directory", side_effect=synced.append):
                    self.write_meets_foreign(label, clock)
                self.assertEqual(calls, [(calls[0][0], self.files().directory / (SHA + ".npy"))])
                self.assertTrue(calls[0][0].name.endswith(".tmp"))
                # The directory is fsynced for a verified existing target only (/code-review F4).
                self.assertEqual(len(synced), 1 if label == "valid" else 0)
                self.assert_no_temp()
                self.assert_made_kept(label)

    def test_target_made_right_after_the_absence_check_is_never_removed_before_the_publish_call(self):
        # The tests around this one create the foreign file inside the publish call. Here it is
        # made one step earlier, right after the store's last absence check and before the
        # call: a store that cleared the name before os.link or os.rename would remove the
        # file and publish over it. Until this test only the source check caught that.
        real_present = M._target_present
        self.assertEqual(len(self.SAME_SIZE), len(PAYLOAD))
        for name in self.BRANCHES:
            for label, make in self.foreign_makers():
                with self.subTest(branch=name, label=label):
                    self.reset()
                    clock, made = FakeTime(), []
                    def present(temp, target, identity, size, cause):
                        found = real_present(temp, target, identity, size, cause)
                        if not found and not made:
                            made.append(label)
                            make(Path(target))  # the other writer takes the name right here
                        return found
                    calls, items = self.branch(name)
                    with Patches(items + [patch.object(M, "_target_present", side_effect=present),
                                          patch.object(M, "time", clock)]):
                        self.write_meets_foreign(label, clock)
                    self.assertEqual((len(calls), made), (1, [label]))  # the call met the name
                    self.assert_made_kept(label)

    def test_windows_rename_never_overwrites_a_target_created_between_check_and_publish(self):
        for label, data in self.FOREIGN:
            with self.subTest(label=label):
                self.reset()
                clock = FakeTime()
                calls, items = self.windows_branch(lambda src, dst: dst.write_bytes(data))
                with Patches(items + [patch.object(M, "time", clock)]):
                    self.write_meets_foreign(label, clock)
                self.assertEqual(calls, [(calls[0][0], self.files().directory / (SHA + ".npy"))])
                self.assertTrue(calls[0][0].name.endswith(".tmp"))
                self.assert_foreign_kept(data)

    def test_windows_branch_publishes_with_one_rename_and_retries_every_permission_error(self):
        # The "cannot hard-link" errors are a POSIX os.link matter; on Windows os.rename
        # needs no hard link, and every PermissionError (EPERM included) is retried.
        clock = FakeTime()
        failures = [PermissionError(errno.EPERM, "synthetic"), PermissionError(errno.EACCES, "synthetic")]
        def before(src, dst):
            if failures:
                raise failures.pop(0)
        calls, items = self.windows_branch(before)
        with Patches(items + [patch.object(M, "time", clock)]):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
        self.assertEqual(len(calls), 3)
        self.assertEqual(clock.sleeps, [0.05, 0.1])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assert_no_temp()

    def test_windows_branch_verifies_a_foreign_target_at_every_check(self):
        # The three checks around os.rename, on the Windows branch: before the first
        # attempt, before the attempt that follows a PermissionError, and at exhaustion.
        # (The retry of a refused publish call exists on this branch only.)
        real_mkstemp = tempfile.mkstemp
        for label, data in self.FOREIGN:
            with self.subTest(where="before the first attempt", label=label):
                self.reset()
                clock = FakeTime()
                def mkstemp(*args, **kwargs):
                    result = real_mkstemp(*args, **kwargs)
                    self.target.write_bytes(data)  # after the store's absence check
                    return result
                calls, items = self.windows_branch()
                with Patches(items + [patch.object(M.tempfile, "mkstemp", side_effect=mkstemp),
                                      patch.object(M, "time", clock)]):
                    self.write_meets_foreign(label, clock)
                self.assertEqual(calls, [])
                self.assert_foreign_kept(data)
            for appears_on in (1, 3, M.PUBLISH_ATTEMPTS):
                with self.subTest(where="attempt %d" % appears_on, label=label):
                    self.reset()
                    clock, opens = FakeTime(), []
                    calls, items = self.refused_rename(
                        100, lambda src, dst: dst.write_bytes(data) if len(calls) == appears_on else None)
                    with Patches(items + [patch.object(M, "time", clock), self.target_opens(seen=opens)[1]]):
                        # The target is found after the wait that follows the refused call. One
                        # that never verifies is looked at in each round that is left; one found
                        # only when the rounds are used up is looked at once.
                        rounds_left = M.PUBLISH_ATTEMPTS - appears_on
                        self.write_meets_foreign(
                            label, clock, list(M._PUBLISH_DELAYS[:appears_on if label == "valid"
                                                                 else M.PUBLISH_ATTEMPTS - 1]))
                    self.assertEqual(len(calls), appears_on)  # no publish call while the name exists
                    self.assertEqual(len(opens), 1 if label == "valid" else max(rounds_left, 1))
                    self.assert_foreign_kept(data)

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link")
    def test_filesystem_without_hard_links_is_a_typed_error_with_no_overwriting_fallback(self):
        # Six names; five values on Linux, where ENOTSUP and EOPNOTSUPP are the same number.
        codes = {errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS, errno.EMLINK, errno.EXDEV}
        self.assertEqual(M._NO_HARD_LINK, frozenset(codes))
        self.assertIsInstance(OSError(errno.EPERM, "x"), PermissionError)  # and still not retried
        for code in sorted(codes):
            with self.subTest(errno=errno.errorcode[code]):
                self.reset()
                calls = []
                def link(src, dst):
                    calls.append(src)
                    raise OSError(code, "synthetic: this filesystem has no hard links")
                with patch.object(M.os, "link", side_effect=link), \
                        patch.object(M.time, "sleep", side_effect=AssertionError("no retry wait")):
                    with self.assertRaises(M.NoClobberUnsupported) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertEqual(len(calls), 1)  # setUp's guards: no os.replace or os.rename either
                self.assertEqual(caught.exception.__cause__.errno, code)
                self.assertNotIsInstance(caught.exception, (M.PublicationUncertain, M.PublishRetryExhausted))
                self.assertEqual(self.inventory(), [SHA + ".lock"])
                # The message names the error and does not blame the filesystem: link(2) also
                # returns EPERM for a kernel hard-link restriction or an immutable file.
                message = str(caught.exception)
                self.assertIn("os.link refused the hard link (%s)" % errno.errorcode[code], message)
                self.assertIn("does not fall back to an overwriting call", message)
                self.assertNotIn("filesystem", message)

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link")
    def test_target_appearing_in_the_no_hard_link_window_is_verified_or_refused(self):
        # The fourth place a foreign target is found: after os.link refused, with a
        # no-hard-link error or EACCES. It is verified or refused like the other three,
        # never overwritten, removed or reported as an unsupported filesystem.
        for code in sorted(M._NO_HARD_LINK | {errno.EACCES}):
            for label, make in self.foreign_makers():
                with self.subTest(errno=errno.errorcode[code], label=label):
                    self.reset()
                    clock, calls, synced = FakeTime(), [], []
                    def link(src, dst):
                        calls.append(src)
                        make(Path(dst))
                        raise OSError(code, "synthetic: no hard link was made")
                    with patch.object(M.os, "link", side_effect=link), patch.object(M, "time", clock), \
                            patch.object(M, "_fsync_directory", side_effect=synced.append):
                        self.write_meets_foreign(label, clock)
                    self.assertEqual(len(calls), 1)  # the refused call is not made again
                    self.assertEqual(len(synced), 1 if label == "valid" else 0)
                    self.assert_made_kept(label)

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link")
    def test_refused_link_is_made_again_only_when_a_foreign_name_is_gone_again(self):
        # No os.link error is retried. One case still has a second os.link call after a
        # refused one: a foreign name that does not verify was found at the check after the
        # refusal and is gone again at the next round. That is the rule for a name that
        # vanished (/code-review F1), inside the same rounds and budget; the call is made with
        # the same temp, and the second refusal, with no name in the way, ends the write.
        for code in (errno.EPERM, errno.EACCES):
            with self.subTest(errno=errno.errorcode[code]):
                self.reset()
                calls = []
                def link(src, dst):
                    calls.append(Path(src))
                    if len(calls) == 1:
                        Path(dst).write_bytes(b"foreign")
                    raise OSError(code, "synthetic: no hard link was made")
                clock = FakeTime(during=lambda n: self.target.unlink())
                with patch.object(M.os, "link", side_effect=link), patch.object(M, "time", clock):
                    with self.assertRaises(M.NoClobberUnsupported) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertEqual(caught.exception.__cause__.errno, code)
                self.assertEqual((len(calls), clock.sleeps), (2, [0.05]))
                self.assertEqual(calls[0], calls[1])
                self.assertEqual(self.inventory(), [SHA + ".lock"])

    @unittest.skipIf(os.name == "nt", "POSIX branch: os.link, then the temp name's unlink")
    def test_posix_temp_unlink_failure_after_link_is_publication_uncertain(self):
        with patch.object(M.os, "unlink", side_effect=PermissionError(errno.EACCES, "held")), \
                patch.object(M, "_fsync_directory", side_effect=AssertionError("after the unlink only")):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertIsInstance(caught.exception.__cause__, PermissionError)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)  # published; the temp name is its hard link
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)
        self.assertTrue(os.path.samestat(os.lstat(self.root / temps[0]), os.lstat(self.target)))
        (self.root / temps[0]).unlink()
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)  # lock released
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))

    def test_blocking_name_that_keeps_vanishing_is_uncertain_at_the_end_of_the_budget(self):
        # The publish call reports an existing name in every round, and the name is gone at
        # every look: the call is made again in each round and nothing is ever published.
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                clock = FakeTime()
                def before(src, dst):
                    raise FileExistsError(errno.EEXIST, "synthetic: a name that is gone again")
                calls, items = self.branch(name, before)
                with Patches(items + [patch.object(M, "time", clock)]):
                    with self.assertRaises(M.PublicationUncertain) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertIsInstance(caught.exception.__cause__, FileNotFoundError)
                self.assertIn("vanished before it could be verified", str(caught.exception))
                self.assertEqual(len(calls), M.PUBLISH_ATTEMPTS)
                self.assertEqual(clock.sleeps, list(M._PUBLISH_DELAYS))
                self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_blocking_target_that_cannot_be_opened_or_read_is_uncertain_and_untouched(self):
        # A file another program has just created is often still held open by it: on
        # Windows the open is then a sharing violation, on POSIX the file may be unreadable
        # to this process. A refused open is looked at again until the budget is used
        # (/code-review F1); any other read failure ends the call at once. The typed error
        # keeps the OS error as its cause.
        failures = (("open", lambda: patch.object(M.os, "open", side_effect=deny_target_open),
                     PermissionError, errno.EACCES, list(M._PUBLISH_DELAYS)),
                    ("read", lambda: patch.object(M.os, "read", side_effect=OSError(errno.EIO, "synthetic")),
                     OSError, errno.EIO, []))
        for name in self.BRANCHES:
            for label, data in self.FOREIGN:
                for step, failure, kind, code, waits in failures:
                    with self.subTest(branch=name, label=label, step=step):
                        self.reset()
                        clock = FakeTime()
                        # inside the publish call, after the last absence check
                        calls, items = self.branch(name, lambda src, dst: dst.write_bytes(data))
                        with Patches(items + [failure(), patch.object(M, "time", clock)]):
                            with self.assertRaises(M.PublicationUncertain) as caught:
                                self.files().write(PAYLOAD, SHA)
                        self.assertIs(type(caught.exception), M.PublicationUncertain)
                        self.assertIsInstance(caught.exception.__cause__, kind)
                        self.assertEqual(caught.exception.__cause__.errno, code)
                        self.assertIn("could not be opened or read", str(caught.exception))
                        self.assertFalse(hasattr(caught.exception, "cleanup_errors"))
                        self.assertEqual((len(calls), clock.sleeps), (1, waits))
                        self.assert_foreign_kept(data)       # untouched, and this call's temp is gone
                        self.write_meets_foreign(label)      # lock released; a later call verifies it
                        self.assert_foreign_kept(data)

    def test_unopenable_blocking_target_keeps_the_temp_removal_error(self):
        def publish(src, dst):
            Path(dst).write_bytes(ALT_PAYLOAD)
            return REAL_PUBLISH(src, dst)
        with patch.object(M.os, PUBLISH, side_effect=publish), patch.object(M, "time", FakeTime()), \
                patch.object(M.os, "open", side_effect=deny_target_open), \
                patch.object(M.os, "unlink", side_effect=OSError(errno.EBUSY, "held")):
            with self.assertRaises(M.PublicationUncertain) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(caught.exception.__cause__.errno, errno.EACCES)
        self.assertEqual([error.errno for error in caught.exception.cleanup_errors], [errno.EBUSY])
        self.assertEqual(self.target.read_bytes(), ALT_PAYLOAD)
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)
        (self.root / temps[0]).unlink()
        self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))  # lock released

    def test_unopenable_target_present_before_the_call_is_a_raw_os_error(self):
        # Unchanged from child 1: a target that was there before the call, in write() and in
        # read(), raises the OS error itself. No temp exists yet and no publish is attempted.
        self.files().write(PAYLOAD, SHA)
        for label, call in (("write", lambda: self.files().write(PAYLOAD, SHA)),
                            ("read", lambda: self.files().read(SHA))):
            with self.subTest(call=label):
                with patch.object(M.os, "open", side_effect=deny_target_open), \
                        patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")), \
                        patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH):
                    with self.assertRaises(PermissionError) as caught:
                        call()
                self.assertIs(type(caught.exception), PermissionError)
                self.assertEqual(self.target.read_bytes(), PAYLOAD)
                self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)  # lock released

    def test_verified_existing_target_with_an_unremoved_temp_is_a_release_error(self):
        real_mkstemp = tempfile.mkstemp
        def mkstemp(*args, **kwargs):
            result = real_mkstemp(*args, **kwargs)
            self.target.write_bytes(ALT_PAYLOAD)
            return result
        with patch.object(M.tempfile, "mkstemp", side_effect=mkstemp), \
                patch.object(M.os, "unlink", side_effect=PermissionError(errno.EACCES, "held")), \
                patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH):
            with self.assertRaises(M.ReleaseError) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, M.PublicationUncertain)
        self.assertIsInstance(caught.exception.__cause__, PermissionError)
        self.assertEqual(self.target.read_bytes(), ALT_PAYLOAD)
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)
        (self.root / temps[0]).unlink()
        self.assertEqual(self.files().read(SHA).tobytes(), RAW)  # lock released

    # --- a blocking target is looked at with this call's temp still in hand (/code-review F1) ---
    # Before the fix the temp was deleted first and the target looked at once, so a state that
    # passes (half written, still held open, gone again) ended the call with the verified
    # payload already discarded.
    def test_half_written_blocking_target_is_looked_at_again_until_it_verifies(self):
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                seen = []
                def other_writer(n):  # still writing during the first wait, finished in the second
                    seen.append((self.target.read_bytes(), len(self.temps())))
                    if n == 2:
                        with open(self.target, "ab") as handle:
                            handle.write(ALT_PAYLOAD[60:])
                clock = FakeTime(during=other_writer)
                calls, items = self.branch(name, lambda src, dst: dst.write_bytes(ALT_PAYLOAD[:60]))
                with Patches(items + [patch.object(M, "time", clock)]):
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
                self.assertEqual((len(calls), clock.sleeps), (1, [0.05, 0.1]))
                self.assertEqual(seen, [(ALT_PAYLOAD[:60], 1)] * 2)  # this call's temp was kept meanwhile
                self.assert_foreign_kept(ALT_PAYLOAD)  # the other writer's container; the temp is gone
                self.assertEqual(self.files().read(SHA).tobytes(), RAW)

    def test_blocking_target_still_held_open_is_looked_at_again_until_it_opens(self):
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                clock = FakeTime()
                opens, refusing = self.target_opens(refuse=3)
                calls, items = self.branch(name, lambda src, dst: dst.write_bytes(ALT_PAYLOAD))
                with Patches(items + [refusing, patch.object(M, "time", clock)]):
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
                self.assertEqual((len(calls), clock.sleeps), (1, [0.05, 0.1, 0.2]))
                self.assertEqual(opens, [1, 1, 1, 1])  # four looks, this call's temp in hand at each
                self.assert_foreign_kept(ALT_PAYLOAD)

    def test_blocking_name_that_is_gone_again_is_published_from_the_kept_temp(self):
        real_open_regular = M._open_regular
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                clock, gone = FakeTime(), []
                def vanishing(path, flags, error):
                    if Path(path).name == self.target.name and not gone:
                        gone.append(self.temps())
                        self.target.unlink()  # the other program removes its file before the look
                    return real_open_regular(path, flags, error)
                calls, items = self.branch(
                    name, lambda src, dst: dst.write_bytes(b"gone soon") if len(calls) == 1 else None)
                with Patches(items + [patch.object(M, "_open_regular", side_effect=vanishing),
                                      patch.object(M, "time", clock)]):
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
                self.assertEqual((len(calls), clock.sleeps), (2, [0.05]))
                self.assertEqual(len(gone[0]), 1)  # the temp was still there when the name vanished
                self.assertEqual(calls[0][0], calls[1][0])  # and the second call published it
                self.assertEqual(self.target.read_bytes(), PAYLOAD)
                self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])
                self.assertEqual(self.files().read(SHA).tobytes(), RAW)

    def test_blocking_target_that_never_verifies_is_refused_only_when_the_budget_is_used(self):
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                held, made = [], []
                clock = FakeTime(during=lambda n: held.append(len(self.temps())))
                opens, counting = self.target_opens()
                def before(src, dst):
                    dst.write_bytes(b"foreign")
                    info = os.lstat(dst)
                    made.append((info.st_ino, info.st_mtime_ns, info.st_size))
                calls, items = self.branch(name, before)
                with Patches(items + [counting, patch.object(M, "time", clock)]):
                    with self.assertRaises(IntegrityError) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertIs(type(caught.exception), IntegrityError)
                self.assertIsInstance(caught.exception.__cause__, SeriesFormatError)
                self.assertFalse(hasattr(caught.exception, "cleanup_errors"))
                self.assertEqual(len(calls), 1)                         # never published over it
                self.assertEqual(len(opens), M.PUBLISH_ATTEMPTS)        # one look in each round
                self.assertEqual(clock.sleeps, list(M._PUBLISH_DELAYS))
                self.assertEqual(held, [1] * len(M._PUBLISH_DELAYS))    # the temp was kept through every wait
                after = os.lstat(self.target)
                self.assertEqual((after.st_ino, after.st_mtime_ns, after.st_size), made[0])
                self.assert_foreign_kept(b"foreign")                    # not repaired or removed; no temp left

    def test_looks_at_a_blocking_target_share_the_time_budget(self):
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                clock, starts = FakeTime(), []
                def opened(path, flags, mode=0o777, *, dir_fd=None):
                    if os.fsdecode(path).endswith(".npy"):
                        starts.append(clock.now - 1000.0)
                        clock.now += 1.5  # a slow look
                    return REAL_OPEN(path, flags, mode, dir_fd=dir_fd)
                calls, items = self.branch(name, lambda src, dst: dst.write_bytes(b"foreign"))
                with Patches(items + [patch.object(M.os, "open", side_effect=opened),
                                      patch.object(M, "time", clock)]):
                    with self.assertRaises(IntegrityError):
                        self.files().write(PAYLOAD, SHA)
                # Looks start at about 0, 1.55, 3.15 and 4.85 s; the 0.4 s wait would pass 5 s.
                self.assertEqual((clock.sleeps, len(starts)), ([0.05, 0.1, 0.2], 4))
                self.assertTrue(all(start < M.PUBLISH_BUDGET for start in starts), starts)
                self.assert_foreign_kept(b"foreign")

    # --- verification of the /code-review fixes (⑨-3a/series-files/3) ---------------------------
    def test_late_wake_up_discards_the_look_made_before_that_wait(self):
        # Every wake-up comes 0.3 s late. Six waits end at 4.15 s; the seventh (0.8 s) is
        # taken because 4.95 s is inside the budget, and it ends at 5.25 s. The rounds are
        # over, but the look made before that wait is 1.1 s old. Before the fix it decided the
        # outcome: IntegrityError for a target that had become valid, or for a name that was
        # gone. Now the name is looked at once more, and no publish call follows the budget.
        late_wait = 7
        def complete():
            with open(self.target, "ab") as handle:
                handle.write(ALT_PAYLOAD[60:])
        cases = (("completed", ALT_PAYLOAD[:60], complete, ALT_PAYLOAD),
                 ("removed", b"foreign", lambda: self.target.unlink(), None),
                 ("unchanged", b"foreign", lambda: None, b"foreign"))
        for name in self.BRANCHES:
            for label, first, change, left in cases:
                with self.subTest(branch=name, during_the_last_wait=label):
                    self.reset()
                    clock = FakeTime(overshoot=0.3, during=lambda n: change() if n == late_wait else None)
                    opens, counting = self.target_opens()
                    calls, items = self.branch(name, lambda src, dst: dst.write_bytes(first))
                    with Patches(items + [counting, patch.object(M, "time", clock)]):
                        if label == "completed":
                            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
                        elif label == "removed":
                            with self.assertRaises(M.PublicationUncertain) as caught:
                                self.files().write(PAYLOAD, SHA)
                            self.assertIn("vanished before it could be verified", str(caught.exception))
                            self.assertIsInstance(caught.exception.__cause__, FileNotFoundError)
                        else:
                            with self.assertRaises(IntegrityError) as caught:
                                self.files().write(PAYLOAD, SHA)
                            self.assertIs(type(caught.exception), IntegrityError)
                    self.assertEqual(clock.sleeps, list(M._PUBLISH_DELAYS[:late_wait]))
                    self.assertGreaterEqual(clock.now - 1000.0, M.PUBLISH_BUDGET)
                    self.assertEqual(len(calls), 1)  # no publish call once the budget is used
                    # One look in each of the seven rounds, and one more after the late wake-up
                    # when the name is still there.
                    self.assertEqual(len(opens), late_wait + (0 if left is None else 1))
                    if left is None:
                        self.assertEqual(self.inventory(), [SHA + ".lock"])  # nothing stored; temp removed
                    else:
                        self.assert_foreign_kept(left)

    def test_blocking_name_that_is_not_a_regular_file_is_refused_at_once(self):
        # A link, a directory or a FIFO is not a file somebody is still writing, and waiting
        # cannot make it verify. Before the fix the call looked at it in all ten rounds and
        # held both locks for 4.75 s; now it ends at the first look, as it did before the
        # /code-review round. The name is refused from lstat and is never opened.
        makers = [(label, make) for label, make in self.foreign_makers(fifo=True)
                  if label in self.NOT_REGULAR]
        self.assertGreaterEqual(len(makers), 1)
        for name in self.BRANCHES:
            for label, make in makers:
                with self.subTest(branch=name, label=label):
                    self.reset()
                    clock = FakeTime()
                    opens, counting = self.target_opens()
                    calls, items = self.branch(name, lambda src, dst: make(dst))
                    with Patches(items + [counting, patch.object(M, "time", clock)]):
                        with self.assertRaises(IntegrityError) as caught:
                            self.files().write(PAYLOAD, SHA)
                    self.assertIs(type(caught.exception), IntegrityError)
                    self.assertIn("must be regular files", str(caught.exception))
                    self.assertFalse(hasattr(caught.exception, "cleanup_errors"))
                    self.assertEqual((len(calls), clock.sleeps, opens), (1, [], []))
                    self.assert_made_kept(label)  # as it was made, and this call's temp is gone
                    with self.assertRaises(IntegrityError):  # both locks were released
                        self.files().read(SHA)

    def test_name_that_fails_verification_and_is_gone_a_moment_later_is_waited_on(self):
        # The check that ends the call for a link or a directory reads the name once more.
        # When the name is gone by then, nothing says it was not a regular file: the call
        # waits, and the next round publishes from the kept temp, as for any vanished name.
        real_confirm = M.SeriesFiles._confirm_existing
        def confirm(store, target, digest):
            try:
                return real_confirm(store, target, digest)
            except IntegrityError:
                Path(target).unlink()  # its writer removes it right after the look
                raise
        for name in self.BRANCHES:
            with self.subTest(branch=name):
                self.reset()
                clock = FakeTime()
                calls, items = self.branch(
                    name, lambda src, dst: dst.write_bytes(b"foreign") if len(calls) == 1 else None)
                with Patches(items + [patch.object(M.SeriesFiles, "_confirm_existing", confirm),
                                      patch.object(M, "time", clock)]):
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, True))
                self.assertEqual((len(calls), clock.sleeps), (2, [0.05]))
                self.assertEqual(calls[0][0], calls[1][0])  # the kept temp was published
                self.assertEqual(self.target.read_bytes(), PAYLOAD)
                self.assertEqual(self.inventory(), [SHA + ".lock", SHA + ".npy"])

    # --- an existing target is synced before it is reported as stored (/code-review F4) ---------
    # A writer outside the lock may have synced neither its file nor the directory entry. Before
    # the fix this call deleted its own fsynced temp and reported the series as stored.
    @unittest.skipIf(os.name == "nt", "POSIX: fsync through a read-only descriptor, and a directory fsync")
    def test_existing_target_and_directory_are_fsynced_before_created_false_is_returned(self):
        log, items = self.sync_log()
        def link(src, dst):
            Path(dst).write_bytes(ALT_PAYLOAD)  # after the last absence check; never fsynced
            log.append("publish")
            return REAL_PUBLISH(src, dst)
        with Patches(items + [patch.object(M.os, "link", side_effect=link)]):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
        self.assertEqual(log, ["fsync-lock", "fsync-tmp", "publish",
                               "fsync-npy-readonly", "fsync-dir", "unlink-tmp"])
        self.assert_foreign_kept(ALT_PAYLOAD)
        # The same for a target that was there when the call began: no temp, and both fsyncs.
        log, items = self.sync_log()
        with Patches(items + [patch.object(M.tempfile, "mkstemp", side_effect=AssertionError("no temp")),
                              patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH)]):
            self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
        self.assertEqual(log, ["fsync-npy-readonly", "fsync-dir"])
        # read() returns an array, not a statement that the series is stored: it syncs nothing.
        log, items = self.sync_log()
        with Patches(items):
            self.assertEqual(self.files().read(SHA).tobytes(), RAW)
        self.assertEqual(log, [])
        self.assert_foreign_kept(ALT_PAYLOAD)

    @unittest.skipIf(os.name == "nt", "POSIX: fsync through a read-only descriptor, and a directory fsync")
    def test_target_that_does_not_verify_is_never_fsynced(self):
        log, items = self.sync_log()
        def link(src, dst):
            Path(dst).write_bytes(b"foreign")
            log.append("publish")
            return REAL_PUBLISH(src, dst)
        with Patches(items + [patch.object(M.os, "link", side_effect=link), patch.object(M, "time", FakeTime())]):
            with self.assertRaises(IntegrityError):
                self.files().write(PAYLOAD, SHA)
        self.assertEqual(log[log.index("publish"):], ["publish", "unlink-tmp"])  # ten looks, no fsync
        self.assert_foreign_kept(b"foreign")

    @unittest.skipIf(os.name == "nt", "POSIX: fsync through a read-only descriptor, and a directory fsync")
    def test_failed_fsync_of_an_existing_target_is_publication_uncertain_and_changes_nothing(self):
        real_fsync = os.fsync
        def failing(kind):
            fds = {}
            def opened(path, flags, mode=0o777, *, dir_fd=None):
                fd = REAL_OPEN(path, flags, mode, dir_fd=dir_fd)
                fds[fd] = FdLog.kind(path)
                return fd
            def fsync(fd):
                if fds.get(fd) == kind:
                    raise OSError(errno.EIO, "synthetic fsync failure")
                return real_fsync(fd)
            return [patch.object(M.os, "open", side_effect=opened), patch.object(M.os, "fsync", side_effect=fsync)]
        def appears(src, dst):
            Path(dst).write_bytes(ALT_PAYLOAD)
            return REAL_PUBLISH(src, dst)
        for kind, words in (("npy", "its fsync failed"), ("dir", "the directory fsync failed")):
            for when in ("appears during the publish", "there before the call"):
                with self.subTest(fsync=kind, when=when):
                    self.reset()
                    if when == "there before the call":
                        self.files().write(ALT_PAYLOAD, SHA)
                        publish = patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH)
                    else:
                        publish = patch.object(M.os, PUBLISH, side_effect=appears)
                    with Patches(failing(kind) + [publish, patch.object(
                            M.time, "sleep", side_effect=AssertionError("a failed fsync is not retried"))]):
                        with self.assertRaises(M.PublicationUncertain) as caught:
                            self.files().write(PAYLOAD, SHA)
                    self.assertIs(type(caught.exception), M.PublicationUncertain)
                    self.assertEqual(caught.exception.__cause__.errno, errno.EIO)
                    self.assertIn("An existing series was verified, but " + words, str(caught.exception))
                    self.assertFalse(hasattr(caught.exception, "cleanup_errors"))
                    self.assert_foreign_kept(ALT_PAYLOAD)  # unchanged, and this call's temp is gone
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))  # lock released

    def test_windows_branch_reports_an_existing_target_without_an_fsync_of_it(self):
        # FlushFileBuffers needs a handle opened for writing, and the store never opens a target
        # for writing; Windows has no directory fsync. Nothing is synced on that branch.
        for when in ("appears during the publish", "there before the call"):
            with self.subTest(when=when):
                self.reset()
                log, items = self.sync_log()
                if when == "there before the call":
                    self.target.write_bytes(ALT_PAYLOAD)
                    self.sidecar.write_bytes(b"\0")
                    calls, branch = self.windows_branch()
                else:
                    calls, branch = self.windows_branch(lambda src, dst: dst.write_bytes(ALT_PAYLOAD))
                with Patches(items + branch):  # off Windows, windows_branch makes a directory fsync an error
                    self.assertEqual(self.files().write(PAYLOAD, SHA), (SHA, False))
                self.assertEqual([entry for entry in log if "npy" in entry or "dir" in entry], [])
                self.assertEqual(len(calls), 0 if when == "there before the call" else 1)
                self.assert_foreign_kept(ALT_PAYLOAD)

    def test_only_the_no_clobber_calls_can_give_a_file_the_target_name(self):
        tree = ast.parse(Path(M.__file__).read_text(encoding="utf-8"))
        os_calls = [node.func.attr for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "os"]
        self.assertEqual((os_calls.count("link"), os_calls.count("rename"), os_calls.count("unlink")),
                         (1, 1, 1))
        attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
        for overwriting in ("replace", "renames", "copyfile", "copy", "copy2", "move", "symlink",
                            "truncate", "ftruncate", "remove", "rmdir"):
            self.assertNotIn(overwriting, attributes)
        # No other way to write, create or remove a name, whatever object it is called on:
        # os.open twice (the regular-file open and the directory fsync), one rename, one
        # link, one unlink, one mkstemp; no pathlib writer and no builtin open().
        for name, allowed in (("open", 2), ("rename", 1), ("link", 1), ("unlink", 1), ("mkstemp", 1),
                              ("write_bytes", 0), ("write_text", 0), ("touch", 0), ("fdopen", 0),
                              ("mkdir", 0), ("makedirs", 0), ("hardlink_to", 0), ("symlink_to", 0)):
            self.assertEqual(attributes.count(name), allowed, name)
        # Only the sidecar is opened read-write (three places in _open_sidecar, one of them
        # creating it). A target is opened read-only, also for the fsync of an existing one.
        for name, allowed in (("O_RDWR", 3), ("O_CREAT", 1), ("O_WRONLY", 0), ("O_TRUNC", 0),
                              ("O_APPEND", 0), ("O_EXCL", 0)):
            self.assertEqual(attributes.count(name), allowed, name)
        builtin_calls = {node.func.id for node in ast.walk(tree)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("open", builtin_calls)
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and node.name == "_no_clobber")
        self.assertEqual([ast.unparse(node) for node in function.body[1:]],
                         ["if _WINDOWS:\n    os.rename(temp, target)\nelse:\n    os.link(temp, target)"])

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
        # The temp is checked again before every round. A second round follows a refused
        # publish call (Windows branch; the temp changes inside that call) or a blocking
        # target that does not verify yet (either branch; the temp changes during the wait).
        for label, effect in (("swapped", swap), ("vanished", vanish), ("truncated", truncated)):
            for why in ("refused publish call", "blocking target"):
                with self.subTest(label=label, why=why):
                    self.reset()
                    if why == "refused publish call":
                        clock = FakeTime()
                        calls, items = self.refused_rename(1, effect)
                    else:
                        clock = FakeTime(during=lambda n: effect(calls[0][0], self.target))
                        calls, items = self.branch("native", lambda src, dst: dst.write_bytes(b"foreign"))
                    with Patches(items + [patch.object(M, "time", clock)]):
                        with self.assertRaises(M.PublicationUncertain):
                            self.files().write(PAYLOAD, SHA)
                    self.assertEqual((len(calls), clock.sleeps), (1, [0.05]))  # found before round two
                    if why == "blocking target":
                        self.assertEqual(self.target.read_bytes(), b"foreign")
                        self.target.unlink()
                    self.assertFalse(self.target.exists())
                    temps = self.temps()
                    self.assertEqual(len(temps), 1 if label == "swapped" else 0)
                    for name in temps:  # foreign file kept by the store, removed by the test
                        self.assertEqual((self.root / name).read_bytes(), PAYLOAD)
                        (self.root / name).unlink()
                    self.assertEqual(self.inventory(), [SHA + ".lock"])

    def test_other_publish_errors_are_uncertain_and_not_retried(self):
        # On the Windows branch this includes the errors that mean "no hard link" to POSIX
        # os.link: os.rename makes no hard link, and NoClobberUnsupported is POSIX only.
        cases = [("native", errno.EIO), ("windows", errno.EIO), ("windows", errno.EXDEV),
                 ("windows", errno.ENOSYS)]
        for name, code in cases:
            with self.subTest(branch=name, errno=errno.errorcode[code]):
                self.reset()
                def before(src, dst):
                    raise OSError(code, "synthetic publish failure")
                calls, items = self.branch(name, before)
                with Patches(items + [patch.object(
                        M.time, "sleep", side_effect=AssertionError("no retry wait"))]):
                    with self.assertRaises(M.PublicationUncertain) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertIs(type(caught.exception), M.PublicationUncertain)
                self.assertEqual(len(calls), 1)
                self.assertEqual(caught.exception.__cause__.errno, code)
                self.assertEqual(self.inventory(), [SHA + ".lock"])

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
                patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH):
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
                        patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH)]):
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
                                      patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH)]):
            with self.assertRaises(StoreError) as caught:
                self.files().write(PAYLOAD, SHA)
        self.assertNotIsInstance(caught.exception, M.PublicationUncertain)
        self.assertEqual(log.close_counts("tmp"), [1])
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)  # ownership unproven, so the store kept it
        (self.root / temps[0]).unlink()
        self.assertEqual(self.inventory(), [SHA + ".lock"])

    # --- post-publication uncertainty -------------------------------------------------
    def test_post_publish_failures_are_publication_uncertain(self):
        state = {}
        def publish(src, dst):
            REAL_PUBLISH(src, dst)
            state["published"] = True
        def readback_open(path, flags, *args, **kwargs):
            if state.get("published") and Path(os.fsdecode(path)).name == self.target.name:
                raise OSError(errno.EIO, "synthetic readback failure")
            return REAL_OPEN(path, flags, *args, **kwargs)
        def tamper_publish(src, dst):
            REAL_PUBLISH(src, dst)
            with open(dst, "r+b") as handle:
                handle.seek(-1, os.SEEK_END)
                handle.write(b"\x81")
        def dir_fsync(path):
            raise OSError(errno.EIO, "synthetic directory fsync failure")
        def unlock(fd):
            raise OSError(errno.EIO, "synthetic unlock failure")
        cases = [("readback", lambda: [patch.object(M.os, PUBLISH, side_effect=publish),
                                       patch.object(M.os, "open", side_effect=readback_open)]),
                 ("mismatch", lambda: [patch.object(M.os, PUBLISH, side_effect=tamper_publish)]),
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
                patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH):
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
        calls, items = self.refused_rename(100)
        with Patches(items + [patch.object(M, "time", FakeTime()),
                              patch.object(M.os, "unlink", side_effect=PermissionError(errno.EACCES, "held"))]):
            with self.assertRaises(M.PublishRetryExhausted) as exhausted:
                self.files().write(PAYLOAD, SHA)
        self.assertFalse(exhausted.exception.temp_removed)
        self.assertEqual(len(exhausted.exception.cleanup_errors), 1)
        self.assertIsInstance(exhausted.exception.cleanup_errors[0], PermissionError)
        temps = [n for n in self.inventory() if n.endswith(".tmp")]
        self.assertEqual(len(temps), 1)
        self.assertTrue(temps[0].startswith("." + SHA + "."))

    def test_interrupts_clean_up_and_propagate_unwrapped(self):
        # (a) interrupt in the retry wait: owned temp removed, interrupt unwrapped. The wait
        # follows a refused publish call (Windows branch) or a blocking target that does not
        # verify yet (either branch); that target is left as it is.
        waits = (("refused publish call", lambda: self.refused_rename(100), None),
                 ("blocking target", lambda: self.branch("native", lambda src, dst: dst.write_bytes(b"foreign")),
                  b"foreign"))
        for why, patches_for, left in waits:
            with self.subTest(wait=why):
                self.reset()
                calls, items = patches_for()
                with Patches(items + [patch.object(M, "time", FakeTime(interrupt_sleep=True))]):
                    with self.assertRaises(KeyboardInterrupt) as caught:
                        self.files().write(PAYLOAD, SHA)
                self.assertNotIsInstance(caught.exception, StoreError)
                self.assertEqual(len(calls), 1)
                self.assert_no_temp()
                if left is None:
                    self.assertEqual(self.inventory(), [SHA + ".lock"])
                    with self.assertRaises(M.SeriesNotFound):
                        self.files().read(SHA)
                else:
                    self.assert_foreign_kept(left)
                    with self.assertRaises(IntegrityError):  # lock released
                        self.files().read(SHA)
        self.reset()
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
        # (c) interrupt right after the publish call: publication happened, no temp left.
        self.reset()
        def publish_then_interrupt(src, dst):
            REAL_PUBLISH(src, dst)
            raise KeyboardInterrupt
        with patch.object(M.os, PUBLISH, side_effect=publish_then_interrupt):
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
                                      patch.object(M.os, PUBLISH, side_effect=NO_PUBLISH)]):
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
        # (g) in the post-publish readback: propagated, not wrapped as PublicationUncertain.
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
                          "rmtree", "datetime", "home", "expanduser", "gettempdir", "replace"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
