"""Detached single-segment R3 envelope storage; no production integration.

The caller supplies an absolute file path in an existing, trusted local directory.
This is not a path-security sandbox. Cooperative writers must use this same
canonical path and sidecar; external replacement, hard-link aliases, sync folders
and hostile directory mutation are not supported. Final symlinks are refused.

Only machine-event envelopes are stored. Payload semantics, lifecycle (beyond
duplicate STARTED/FINISHED), human authority, rollover/recovery, caches, recorders,
keys and Lab/research integration are absent. Reads always verify the entire
segment. The codec's MD5 is not authentication, and a valid unanchored prefix
cannot establish that complete trailing records have not been removed.

Here 32 MB means 32,000,000 bytes. Append preflight refuses crossing that boundary;
this is deliberately stricter than the full design's subsequent-append rollover.
No rotation, truncation, implicit repair or retry of an uncertain write occurs.
"""
from contextlib import contextmanager
import errno
import math
import os
from pathlib import Path
import stat
import threading
import time

from . import run_registry_codec as codec

if os.name == "nt":
    import msvcrt
else:
    import fcntl


MAX_SEGMENT_BYTES = 32_000_000
MAX_LOCK_TIMEOUT = 10.0
MACHINE_EVENTS = frozenset(("STARTED", "PROGRESS", "FINGERPRINT", "SHADOW", "FINISHED"))
_PROCESS_LOCKS = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


class StoreError(ValueError):
    """The detached store refused the operation."""


class LockTimeout(StoreError):
    """The combined process/OS lock budget was exhausted before writing."""


class IntegrityError(StoreError):
    """Existing bytes are invalid; they have not been repaired."""


class DuplicateEvent(StoreError):
    """A verified STARTED/FINISHED event already uses this run ID."""


class UnsupportedEvent(StoreError):
    """The event requires an unimplemented authority or segment capability."""


class RolloverRequired(StoreError):
    """This bounded store cannot admit the segment size without rollover."""


class AppendOutcomeUncertain(StoreError):
    """Writing was attempted: bytes may be absent, partial, or fully persisted.

    Do not blindly retry. A subsequent verified read can establish current bytes,
    but cannot establish that an unsuccessful fsync was durable at failure time.
    """


def _remaining(deadline):
    return max(0.0, deadline - time.monotonic())


def _process_lock(key, deadline):
    if not _PROCESS_LOCKS_GUARD.acquire(timeout=_remaining(deadline)):
        raise LockTimeout("Process lock-map timeout")
    try:
        # A child created through fork must not reuse a parent's held path lock.
        return _PROCESS_LOCKS.setdefault((os.getpid(), key), threading.Lock())
    finally:
        _PROCESS_LOCKS_GUARD.release()


def _open_regular(path, flags):
    try:
        prior = path.lstat()
    except FileNotFoundError:
        prior = None
    if prior is not None and not stat.S_ISREG(prior.st_mode):
        raise StoreError("Store files must be regular files, not links or devices")
    # Nonblocking open also avoids a FIFO-open hang if an unsupported external
    # writer replaces a regular file between lstat and open (POSIX).
    fd = os.open(path, flags | getattr(os, "O_NOFOLLOW", 0) |
                 getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise StoreError("Store files must be regular files")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _try_os_lock(fd):
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_os(fd):
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


def _acquire_os(fd, deadline):
    while True:
        try:
            _try_os_lock(fd)
            return
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise
            left = _remaining(deadline)
            if left <= 0:
                raise LockTimeout("OS sidecar lock timeout") from exc
            time.sleep(min(0.01, left))


class SingleSegmentStore:
    """An explicit-path envelope store with one bounded lock-acquisition budget.

    ``lock_timeout`` is 0–10 elapsed seconds, shared across process and OS locks.
    It bounds lock waits, not filesystem reads, verification, writes or fsync.
    The caller supplies recorded_utc in each event; no timestamp is generated.
    Creating this object does not create the directory, segment or sidecar.
    """

    def __init__(self, path, *, lock_timeout=2.0):
        if type(lock_timeout) not in (int, float):
            raise StoreError("Lock timeout must be a finite number")
        if not 0 <= lock_timeout <= MAX_LOCK_TIMEOUT:
            raise StoreError("Lock timeout must be between 0 and 10 seconds")
        if not math.isfinite(lock_timeout):
            raise StoreError("Lock timeout must be a finite number")
        supplied = Path(path)
        if not supplied.is_absolute() or supplied.suffix != ".jsonl":
            raise StoreError("Supply an absolute .jsonl segment path")
        parent = supplied.parent.resolve(strict=True)
        if not parent.is_dir():
            raise StoreError("The supplied parent must be an existing directory")
        self.path = parent / supplied.name
        self.lock_path = self.path.with_suffix(".lock")
        self.lock_timeout = float(lock_timeout)
        self._key = os.path.normcase(str(self.path))

    @contextmanager
    def _locked(self, *, create):
        deadline = time.monotonic() + self.lock_timeout
        local = _process_lock(self._key, deadline)
        if not local.acquire(timeout=_remaining(deadline)):
            raise LockTimeout("Process path lock timeout")
        fd = None
        acquired = False
        try:
            try:
                fd = _open_regular(self.lock_path, os.O_RDWR | (os.O_CREAT if create else 0))
            except FileNotFoundError:
                if create:
                    raise
                yield False
                return
            _acquire_os(fd, deadline)
            acquired = True
            if create and os.fstat(fd).st_size == 0:
                # Windows permits a byte-range lock beyond EOF. Initialize only
                # after acquisition, avoiding writes to another writer's lock.
                os.lseek(fd, 0, os.SEEK_SET)
                if os.write(fd, b"\0") != 1:
                    raise OSError("Short sidecar initialization")
                os.fsync(fd)
            yield True
        finally:
            try:
                if fd is not None:
                    try:
                        if acquired:
                            _unlock_os(fd)
                    finally:
                        os.close(fd)
            finally:
                local.release()

    def _read_verified(self):
        try:
            fd = _open_regular(self.path, os.O_RDONLY)
        except FileNotFoundError:
            return b"", (), None
        with os.fdopen(fd, "rb", buffering=0) as stream:
            before = os.fstat(stream.fileno())
            if before.st_size > MAX_SEGMENT_BYTES:
                raise RolloverRequired("Existing segment exceeds the single-segment limit")
            data = stream.read(MAX_SEGMENT_BYTES + 1)
            after = os.fstat(stream.fileno())
        if len(data) != before.st_size or after.st_size != before.st_size:
            raise IntegrityError("Segment changed during read")
        try:
            events = codec.verify_event_lines(data.splitlines(keepends=True))
        except codec.CodecError as exc:
            raise IntegrityError("Invalid event chain; repair is not performed") from exc
        seen = set()
        for event in events:
            if event["event"] not in MACHINE_EVENTS:
                raise UnsupportedEvent("Stored human/segment events require another implementation")
            if event["event"] in ("STARTED", "FINISHED"):
                key = (event["event"], event["run_id"])
                if key in seen:
                    raise IntegrityError("Existing chain contains duplicate STARTED/FINISHED")
                seen.add(key)
        return data, events, before

    def read(self):
        """Return freshly decoded envelopes without creating missing files.

        Existing data without its sidecar refuses. A missing store may return
        empty just before a concurrent first writer creates it, a valid snapshot.
        """
        with self._locked(create=False) as locked:
            if not locked:
                if self.path.exists() or self.path.is_symlink():
                    raise StoreError("Existing segment has no lock sidecar")
                return ()
            return self._read_verified()[1]

    def append(self, event):
        """Append one detached machine envelope and return its exact stored bytes.

        A write/flush/fsync/close or later unlock error has an uncertain outcome;
        it is surfaced without retry, truncation or an implicit repair.
        """
        if (type(event) is not dict or type(event.get("event")) is not str or
                event["event"] not in MACHINE_EVENTS):
            raise UnsupportedEvent("Only machine-event envelopes are supported")
        # Freeze caller input before waiting, using the existing codec rather
        # than retaining a mutable mapping during lock contention.
        prepared = codec.decode_event_line(codec.encode_event_line(event))
        del prepared["row_md5"], prepared["prev_row_md5"]
        attempted = False
        try:
            with self._locked(create=True):
                data, events, snapshot = self._read_verified()
                if prepared["event"] in ("STARTED", "FINISHED") and any(
                        item["event"] == prepared["event"] and
                        item["run_id"] == prepared["run_id"] for item in events):
                    raise DuplicateEvent("STARTED/FINISHED already recorded for this run ID")
                previous = data.splitlines(keepends=True)[-1] if data else None
                line = codec.encode_event_line(prepared, previous_line=previous)
                if len(data) + len(line) > MAX_SEGMENT_BYTES:
                    raise RolloverRequired("Append requires unimplemented rollover")
                fd = _open_regular(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
                with os.fdopen(fd, "ab", buffering=0) as stream:
                    current = os.fstat(stream.fileno())
                    if current.st_size != len(data) or (snapshot is not None and
                            (current.st_dev, current.st_ino) != (snapshot.st_dev, snapshot.st_ino)):
                        raise IntegrityError("Segment was replaced or resized before append")
                    attempted = True
                    if stream.write(line) != len(line):
                        raise OSError("Short event append")
                    stream.flush()
                    os.fsync(stream.fileno())
                return line
        except (OSError, StoreError) as exc:
            if attempted:
                raise AppendOutcomeUncertain("Append outcome uncertain; inspect before any retry") from exc
            raise
