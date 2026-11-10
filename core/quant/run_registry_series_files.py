"""Detached verified immutable NPY series files for R3 §5.7; no Lab integration.

``SeriesFiles`` stores caller-supplied NPY1 payloads, already verified by the
existing in-memory format decoder and content SHA-256, as ``<digest>.npy`` in
an existing absolute directory the caller names. A ``<digest>.lock`` sidecar
serializes cooperating writers and readers through a process lock plus an OS
byte lock. There is no default path, configuration, environment lookup,
provider, recorder, error event, retention or cleanup of stored files.

Publishing never overwrites (owner ruling 10 of 2026-11-11). The verified temp
file is given the target name by a call that fails when that name exists:
``os.link`` on POSIX, after which the temp name is unlinked, and ``os.rename``
on Windows. ``os.replace`` and POSIX ``os.rename`` are never called. A target
name that exists at publish time is verified against the digest and reported
as already present, or refused and left untouched; one that cannot be opened
or read is ``PublicationUncertain``. When ``os.link`` cannot make the hard
link at all (a filesystem without hard links, or a kernel refusal) the write
raises ``NoClobberUnsupported``; there is no overwriting fallback.

This is not a path-security sandbox. Hostile path changes, hard-link aliases
made by others, sync folders, network mounts, fork during active I/O and
inherited descriptors are outside the trust model. No power-loss durability is
promised: POSIX fsyncs the directory after the link and the temp unlink;
Windows fsyncs only the file before the rename.
"""
from __future__ import annotations

import errno
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time

import numpy as np

from core.quant.run_registry_series_format import SeriesFormatError, decode_series
from core.quant.run_registry_store import IntegrityError, LockTimeout, StoreError

_WINDOWS = os.name == "nt"
if _WINDOWS:
    import msvcrt
else:
    import fcntl


MAX_LOCK_TIMEOUT = 10.0
REPLACE_ATTEMPTS = 10
REPLACE_BUDGET = 5.0
# Nine waits between ten attempts; their sum (4.75 s) fits the 5 s budget.
# The REPLACE_* names date from the first version, which published with
# os.replace; they now bound the no-clobber publish call.
_REPLACE_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8, 0.8, 0.8, 0.8, 0.8)
# os.link errors that say the hard link cannot be made at all. Most name a
# filesystem without hard links (link(2): EPERM "does not support the creation
# of hard links"). EPERM is also what the kernel returns when its
# protected-hardlinks policy refuses (the temp's owner is not the caller, as
# on some uid-mapped mounts) or the file is immutable or append-only. A retry
# helps in none of these, so they are never retried and never answered with an
# overwriting call. Six names; ENOTSUP and EOPNOTSUPP are one value on Linux.
_NO_HARD_LINK = frozenset(getattr(errno, name) for name in (
    "EPERM", "ENOTSUP", "EOPNOTSUPP", "ENOSYS", "EMLINK", "EXDEV") if hasattr(errno, name))
_CHUNK = 1 << 20
_INTP_MAX = int(np.iinfo(np.intp).max)
_DIGEST = re.compile(r"[0-9a-f]{64}")
_OPEN_FLAGS = (getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) |
               getattr(os, "O_BINARY", 0))
_PROCESS_LOCKS = {}
_PROCESS_GUARD = threading.Lock()
_LOCK_PID = os.getpid()


class SidecarMissing(StoreError):
    """An existing target name has no lock sidecar; nothing was created or changed."""


class SeriesNotFound(StoreError):
    """No stored series exists for this digest; nothing was created."""


class ReleaseError(StoreError):
    """A verified read or existing-target check could not release its lock or file.

    Nothing was published by this call; the verified result is not returned.
    """


class ReplaceRetryExhausted(StoreError):
    """Every bounded publish attempt raised PermissionError; nothing was published.

    The original temp identity and target absence were confirmed after the last
    attempt. ``temp_removed`` says whether the owned temp file was deleted.
    The keyword defaults exist only so that unpickling, which rebuilds the
    exception from its message and then restores its attributes, works in a
    worker process's parent. The class name dates from the first version, which
    published with os.replace; the publish call no longer replaces anything.
    """

    def __init__(self, message, *, attempts=None, temp_removed=None):
        super().__init__(message)
        self.attempts = attempts
        self.temp_removed = temp_removed


class PublicationUncertain(StoreError):
    """Publication state is not established; do not blindly retry.

    The target may be absent, foreign or published without the post-publish
    checks completing. A later read() verifies the bytes present now but does
    not prove durability at the time of failure.
    """


class NoClobberUnsupported(StoreError):
    """os.link could not make the hard link, so nothing was published.

    POSIX only. The usual cause is a filesystem without hard links (for example
    FAT or exFAT): use a directory on a filesystem that has them. link(2) also
    returns EPERM when the kernel's protected-hardlinks policy refuses (the
    temp file's owner is not the caller, as on some uid-mapped mounts) and when
    the file is immutable or append-only, so the message names the errno and
    not a cause; the OS error is ``__cause__``. In every case nothing was
    overwritten, the original temp and an absent target were confirmed, and the
    store does not fall back to a call that replaces.
    """


def _reset_process_locks():
    """Rebind Python lock state for a new process (fork child or PID change).

    It fixes Python lock state only, not inherited OS descriptors or OS locks
    held through them; the OS lock is the cross-process guarantee.
    """
    global _PROCESS_LOCKS, _PROCESS_GUARD, _LOCK_PID
    _PROCESS_LOCKS = {}
    _PROCESS_GUARD = threading.Lock()
    _LOCK_PID = os.getpid()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_process_locks)


def _attach(primary, errors):
    if errors:
        primary.cleanup_errors = tuple(getattr(primary, "cleanup_errors", ())) + tuple(errors)
    return primary


def _remaining(deadline):
    return max(0.0, deadline - time.monotonic())


def _process_lock(key):
    """Return the process lock for ``key``; the caller applies its deadline to it.

    The map guard is held only for one dictionary lookup, so it is taken
    without a timeout: a zero lock_timeout must not fail because another
    thread is looking up an unrelated digest.
    """
    # A PID check also covers forks that bypass at-fork handlers.
    if _LOCK_PID != os.getpid():
        _reset_process_locks()
    guard, locks = _PROCESS_GUARD, _PROCESS_LOCKS
    with guard:
        return locks.setdefault(key, threading.Lock())


def _close_once(fd):
    """Close a descriptor whose ownership the caller has already given up.

    The close is attempted once and never retried. An Exception is returned
    for the caller to report; an interrupt propagates.
    """
    try:
        os.close(fd)
    except Exception as exc:
        return [exc]
    return []


def _lexists(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def _open_regular(path, flags, error):
    try:
        prior = os.lstat(path)
    except FileNotFoundError:
        prior = None
    if prior is not None and not stat.S_ISREG(prior.st_mode):
        raise error("Series store names must be regular files, not links, directories or devices")
    # Nonblocking open also avoids a FIFO-open hang if a regular file is swapped
    # between lstat and open by an unsupported external writer (POSIX).
    fd = os.open(path, flags | _OPEN_FLAGS, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise error("Series store names must be regular files")
    except BaseException as primary:
        raise _attach(primary, _close_once(fd))
    return fd


def _try_os_lock(fd):
    if _WINDOWS:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_os(fd):
    if _WINDOWS:
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


class _Held:
    __slots__ = ("local", "fd", "locked")

    def __init__(self, local):
        self.local, self.fd, self.locked = local, None, False


def _release(held):
    """Unlock, close once and release the process lock; return collected errors.

    Exceptions are collected. An interrupt is remembered, the remaining steps
    still run, and it is then raised unwrapped with the collected errors.
    """
    errors, interrupt = [], None
    try:
        if held.locked:
            held.locked = False
            try:
                _unlock_os(held.fd)
            except Exception as exc:
                errors.append(exc)
            except BaseException as exc:
                interrupt = exc
        if held.fd is not None:
            owned, held.fd = held.fd, None
            try:
                os.close(owned)
            except Exception as exc:
                errors.append(exc)
            except BaseException as exc:
                interrupt = interrupt or exc
    finally:
        held.local.release()
    if interrupt is not None:
        raise _attach(interrupt, errors)
    return errors


def _identity(info):
    return info.st_dev, info.st_ino


def _read_bounded(fd, limit):
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode):
        raise IntegrityError("Stored series is not a regular file")
    if before.st_size > limit:
        raise IntegrityError("Stored series exceeds max_bytes; it was not changed")
    chunks, total = [], 0
    while total < before.st_size:
        chunk = os.read(fd, min(_CHUNK, before.st_size - total))
        if not chunk:
            raise IntegrityError("Stored series shrank during read")
        chunks.append(chunk)
        total += len(chunk)
    if os.read(fd, 1):
        raise IntegrityError("Stored series grew during read")
    after = os.fstat(fd)
    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        raise IntegrityError("Stored series changed during read")
    return b"".join(chunks)


def _remove_owned_temp(temp, identity):
    """Unlink the temp only if it is still this call's regular file.

    Return ``(removed, errors)``. The target, sidecar and other files are never
    touched.
    """
    try:
        info = os.lstat(temp)
    except FileNotFoundError:
        return False, []
    except OSError as exc:
        return False, [exc]
    if not stat.S_ISREG(info.st_mode) or _identity(info) != identity:
        return False, []
    try:
        os.unlink(temp)
    except OSError as exc:
        return False, [exc]
    return True, []


def _temp_problem(temp, identity, size):
    """Return why the temp is no longer this call's file, or None."""
    try:
        info = os.lstat(temp)
    except FileNotFoundError:
        return "the owned temp file vanished"
    if not stat.S_ISREG(info.st_mode) or _identity(info) != identity or info.st_size != size:
        return "the owned temp file changed identity or size"
    return None


def _target_present(temp, target, identity, size, cause):
    """Confirm the original temp, then say whether the target name exists.

    A vanished or changed temp, or state that cannot be read, is
    PublicationUncertain. A present target name (created outside the
    cooperating lock) is the caller's to verify, never to overwrite.
    """
    try:
        problem = _temp_problem(temp, identity, size)
        present = problem is None and _lexists(target)
    except Exception as exc:
        errors = _remove_owned_temp(temp, identity)[1]
        raise _attach(PublicationUncertain(
            "Temp or target state could not be confirmed; nothing was overwritten"), errors) from exc
    if problem is not None:
        errors = _remove_owned_temp(temp, identity)[1]
        raise _attach(PublicationUncertain(
            "Not published: " + problem + "; nothing was overwritten"), errors) from cause
    return present


def _no_clobber(temp, target):
    """Give the temp file the target name; fail if that name exists.

    Windows: os.rename (MoveFileExW without MOVEFILE_REPLACE_EXISTING) raises
    FileExistsError for any existing target and moves the temp name in one
    step. POSIX: os.link raises FileExistsError for any existing target name,
    links included, where rename(2) would replace it; the caller then unlinks
    the temp name. Neither call can replace an existing name.
    """
    if _WINDOWS:
        os.rename(temp, target)
    else:
        os.link(temp, target)


def _fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    except BaseException as primary:
        raise _attach(primary, _close_once(fd))
    errors = _close_once(fd)
    if errors:
        raise errors[0]


class SeriesFiles:
    """Verified immutable NPY1 series files named by content SHA-256 (R3 §5.7).

    ``directory`` must be an existing absolute directory; nothing is created on
    construction. ``max_bytes`` bounds payload and stored-file bytes, not peak
    memory. ``lock_timeout`` (0-10 s, default 2) bounds lock waits only.
    Cooperating instances on one directory must share one ``max_bytes``.
    """

    def __init__(self, directory, *, max_bytes, lock_timeout=2.0):
        if type(max_bytes) is not int or not 0 < max_bytes <= _INTP_MAX:
            raise StoreError("max_bytes must be a plain positive int within np.intp")
        if type(lock_timeout) not in (int, float):
            raise StoreError("Lock timeout must be a finite number")
        if not 0 <= lock_timeout <= MAX_LOCK_TIMEOUT or not math.isfinite(lock_timeout):
            raise StoreError("Lock timeout must be between 0 and 10 seconds")
        try:
            raw = os.fspath(directory)
        except TypeError as exc:
            raise StoreError("Supply an existing absolute directory path") from exc
        if type(raw) is not str or not Path(raw).is_absolute():
            raise StoreError("Supply an existing absolute directory path as text")
        try:
            resolved = Path(raw).resolve(strict=True)
            is_dir = resolved.is_dir()
        except (OSError, ValueError, RuntimeError) as exc:
            raise StoreError("The series directory must already exist and be resolvable") from exc
        if not is_dir:
            raise StoreError("The series directory must already exist")
        self.directory = resolved
        self.max_bytes = max_bytes
        self.lock_timeout = float(lock_timeout)

    def _paths(self, digest):
        return self.directory / (digest + ".lock"), self.directory / (digest + ".npy")

    @staticmethod
    def _open_sidecar(sidecar, target, create):
        try:
            return _open_regular(sidecar, os.O_RDWR, StoreError)
        except FileNotFoundError:
            pass
        if _lexists(target):
            # A cooperating writer may have created the sidecar and published
            # between the failed open and this lstat; look again before refusing.
            try:
                return _open_regular(sidecar, os.O_RDWR, StoreError)
            except FileNotFoundError:
                raise SidecarMissing("Existing series target has no lock sidecar") from None
        if not create:
            raise SeriesNotFound("No stored series for this digest")
        return _open_regular(sidecar, os.O_RDWR | os.O_CREAT, StoreError)

    def _acquire(self, digest, *, create):
        sidecar, target = self._paths(digest)
        deadline = time.monotonic() + self.lock_timeout
        local = _process_lock(os.path.normcase(str(sidecar)))
        if not local.acquire(timeout=_remaining(deadline)):
            raise LockTimeout("Process sidecar lock timeout")
        held = _Held(local)
        try:
            held.fd = self._open_sidecar(sidecar, target, create)
            _acquire_os(held.fd, deadline)
            held.locked = True
            if create and os.fstat(held.fd).st_size == 0:
                # Windows permits a byte lock beyond EOF; initialize only after
                # acquisition so no other writer's locked byte is written to.
                os.lseek(held.fd, 0, os.SEEK_SET)
                if os.write(held.fd, b"\0") != 1:
                    raise OSError(errno.EIO, "Short sidecar initialization")
                os.fsync(held.fd)
        except BaseException as primary:
            raise _attach(primary, _release(held))
        return held

    def _read_target(self, target):
        """Bounded read of a target; return ``(data, close_errors)``."""
        fd = _open_regular(target, os.O_RDONLY, IntegrityError)
        try:
            data = _read_bounded(fd, self.max_bytes)
        except BaseException as primary:
            raise _attach(primary, _close_once(fd))
        return data, _close_once(fd)

    def _load_verified(self, target, digest):
        """Bounded read, extra-byte probe and exact content rehash of a target."""
        data, close_errors = self._read_target(target)
        try:
            array = decode_series(data, digest, max_bytes=self.max_bytes)
        except SeriesFormatError as exc:
            raise _attach(IntegrityError(
                "Stored series failed format or content verification; it was not repaired"),
                close_errors) from exc
        if close_errors:
            raise _attach(ReleaseError(
                "Stored series was verified but its file did not close cleanly"),
                close_errors[1:]) from close_errors[0]
        return array

    def read(self, sha256):
        """Return the verified read-only array stored under ``sha256``.

        Nothing is created or written, but the sidecar is opened for writing.
        """
        if type(sha256) is not str or _DIGEST.fullmatch(sha256) is None:
            raise SeriesFormatError("sha256 must be a plain lowercase 64-hex string")
        held = self._acquire(sha256, create=False)
        try:
            target = self._paths(sha256)[1]
            if not _lexists(target):
                raise SeriesNotFound("No stored series for this digest")
            array = self._load_verified(target, sha256)
        except BaseException as primary:
            raise _attach(primary, _release(held))
        errors = _release(held)
        if errors:
            raise _attach(ReleaseError(
                "Series was verified but its lock was not released cleanly"),
                errors[1:]) from errors[0]
        return array

    def write(self, payload, expected_sha256):
        """Verify and publish an NPY1 payload; return ``(sha256, created)``.

        The result is returned only after verification and a clean release.
        An existing valid target is kept byte for byte (``created`` False),
        also when it appears while this call is publishing: no existing
        target name is ever overwritten.
        """
        decode_series(payload, expected_sha256, max_bytes=self.max_bytes)
        held = self._acquire(expected_sha256, create=True)
        try:
            created = self._write_locked(payload, expected_sha256)
        except BaseException as primary:
            raise _attach(primary, _release(held))
        errors = _release(held)
        if errors:
            if created:
                raise _attach(PublicationUncertain(
                    "Series was published and verified, but its lock was not released cleanly"),
                    errors[1:]) from errors[0]
            raise _attach(ReleaseError(
                "Existing series was verified, but its lock was not released cleanly"),
                errors[1:]) from errors[0]
        return expected_sha256, created

    def _write_locked(self, payload, digest):
        target = self._paths(digest)[1]
        if _lexists(target):
            self._load_verified(target, digest)
            return False
        fd, name = tempfile.mkstemp(prefix="." + digest + ".", suffix=".tmp",
                                    dir=str(self.directory))
        temp, owned, identity = Path(name), fd, None
        try:
            info = os.lstat(temp)
            if not stat.S_ISREG(info.st_mode) or info.st_size != 0:
                raise StoreError("New temp file is not an empty regular file; it was kept")
            identity = _identity(info)
            view, offset = memoryview(payload), 0
            while offset < len(view):
                written = os.write(fd, view[offset:offset + _CHUNK])
                if written <= 0:
                    raise OSError(errno.EIO, "Series temp write made no progress")
                offset += written
            os.fsync(fd)
            owned = None
            errors = _close_once(fd)
            if errors:
                raise errors[0]
        except BaseException as primary:
            errors = []
            try:
                if owned is not None:
                    closing, owned = owned, None
                    errors += _close_once(closing)
            finally:
                if identity is not None:
                    errors += _remove_owned_temp(temp, identity)[1]
            raise _attach(primary, errors)
        if not self._publish(temp, target, identity, len(payload), digest):
            return False
        try:
            if not _WINDOWS:
                _fsync_directory(self.directory)
            data, close_errors = self._read_target(target)
            if close_errors:
                raise close_errors[0]
            if data != payload:
                raise IntegrityError("Published bytes differ from the verified payload")
        except Exception as exc:
            raise PublicationUncertain(
                "The publish call returned, but post-publication fsync, readback or close "
                "failed") from exc
        return True

    def _keep_existing(self, temp, target, identity, digest):
        """A target name exists at publish time: verify it, never overwrite it.

        The owned temp is removed first. A target that verifies against the
        digest is reported as already present (False). One that does not is
        refused with IntegrityError and left untouched. One that vanished
        again, or that could not be opened or read (for example while its
        writer still holds it open on Windows), is PublicationUncertain with
        the OS error as its cause; it is left untouched as well.
        """
        errors = _remove_owned_temp(temp, identity)[1]
        try:
            self._load_verified(target, digest)
        except OSError as exc:
            reason = ("vanished before it could be verified" if isinstance(exc, FileNotFoundError)
                      else "could not be opened or read for verification")
            raise _attach(PublicationUncertain(
                "A target name blocked the publish and " + reason + "; nothing was overwritten"),
                errors) from exc
        except BaseException as primary:
            raise _attach(primary, errors)
        if errors:
            raise _attach(ReleaseError(
                "Existing series was verified, but this call's temp file was not removed"),
                errors[1:]) from errors[0]
        return False

    def _publish(self, temp, target, identity, size, digest):
        """Publish without overwriting; return whether this call created the target.

        The only retry: the publish call on PermissionError, at most 10
        attempts in 5 s. No attempt starts once 5 s have elapsed: a wait that
        would reach the budget is not taken, and the clock is read again after
        each wait. A target name found before an attempt, by the call itself
        (FileExistsError), after a no-hard-link error or at exhaustion is
        verified instead (False).
        """
        start, attempts, last = time.monotonic(), 0, None
        try:
            while True:
                if _target_present(temp, target, identity, size, last):
                    return self._keep_existing(temp, target, identity, digest)
                attempts += 1
                try:
                    _no_clobber(temp, target)
                except FileExistsError:
                    return self._keep_existing(temp, target, identity, digest)
                except Exception as exc:
                    if not _WINDOWS and isinstance(exc, OSError) and exc.errno in _NO_HARD_LINK:
                        if _target_present(temp, target, identity, size, exc):
                            return self._keep_existing(temp, target, identity, digest)
                        errors = _remove_owned_temp(temp, identity)[1]
                        raise _attach(NoClobberUnsupported(
                            "os.link refused the hard link (%s), so nothing was published; "
                            "the store does not fall back to an overwriting call"
                            % errno.errorcode.get(exc.errno, exc.errno)), errors) from exc
                    if not isinstance(exc, PermissionError):
                        errors = _remove_owned_temp(temp, identity)[1]
                        raise _attach(PublicationUncertain(
                            "The publish call failed without PermissionError; publication is "
                            "uncertain"), errors) from exc
                    last = exc
                else:
                    if not _WINDOWS:
                        # The target is published; the temp name is now its hard link.
                        errors = _remove_owned_temp(temp, identity)[1]
                        if errors:
                            raise PublicationUncertain(
                                "Published without overwrite, but the temp name, a hard link "
                                "to the published file, was not removed") from errors[0]
                    return True
                if attempts < REPLACE_ATTEMPTS:
                    wait = _REPLACE_DELAYS[attempts - 1]
                    if time.monotonic() - start + wait < REPLACE_BUDGET:
                        time.sleep(wait)
                        if time.monotonic() - start < REPLACE_BUDGET:
                            continue
                if _target_present(temp, target, identity, size, last):
                    return self._keep_existing(temp, target, identity, digest)
                removed, errors = _remove_owned_temp(temp, identity)
                raise _attach(ReplaceRetryExhausted(
                    "The publish call raised PermissionError on every bounded attempt; "
                    "nothing was published", attempts=attempts, temp_removed=removed),
                    errors) from last
        except BaseException as primary:
            if isinstance(primary, Exception):
                raise
            # Interrupt: identity-checked cleanup, then propagate unwrapped.
            raise _attach(primary, _remove_owned_temp(temp, identity)[1])
