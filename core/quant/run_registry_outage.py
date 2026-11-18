"""Explicit-path R3 outage append (ENG-16), outside the registry chain.

The caller supplies an existing trusted local directory and an already stamped
failure record. No default path, directory creation, wall clock, configuration,
network, ledger read, count calculation or repair is provided. A process lock
serialises cooperating threads only; concurrent processes and hostile directory
replacement are unsupported. This is not a filesystem security sandbox.

Use an instance as DetachedRecorder's outage_sink. Errors propagate to that
recorder, which exposes a sink failure in outage_error without retrying it.
There is no application connection or UI notice in this module.
"""
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import stat
import threading
import time

from .run_registry_fold import STAGES


_LOCKS = {}
_LOCKS_GUARD = threading.Lock()
_FIELDS = frozenset(('recorded_utc', 'run_id', 'family_id', 'symbols_typed', 'stage', 'error'))


class OutageError(ValueError):
    """The failure record or explicit destination cannot be used."""


class OutageLockTimeout(OutageError):
    """The process lock budget was exhausted before an append."""


class OutageWriteUncertain(OSError):
    """An append was attempted; do not retry or repair it automatically."""


def _line(record):
    if type(record) is not dict or set(record) != _FIELDS:
        raise OutageError('Supply the complete outage record without extra fields')
    stamp = record['recorded_utc']
    if stamp is not None:
        if type(stamp) is not str or not stamp.endswith('Z'):
            raise OutageError('Outage time must be supplied UTC or None')
        try:
            at = datetime.fromisoformat(stamp[:-1] + '+00:00')
        except ValueError as exc:
            raise OutageError('Invalid supplied outage time') from exc
        if at.utcoffset() != timedelta(0):
            raise OutageError('Outage time must be UTC')
    # None preserves a clock failure or a failure before reserving an ID. Do not
    # invent an ID, family or timestamp to make the failure look complete.
    for name in ('run_id', 'family_id'):
        if record[name] is not None and type(record[name]) is not str:
            raise OutageError('Outage identity must be a string or None')
    symbols = record['symbols_typed']
    if type(symbols) is not list or any(type(x) is not str for x in symbols):
        raise OutageError('Typed symbols must be supplied strings')
    if type(record['stage']) is not str or record['stage'] not in STAGES:
        raise OutageError('Invalid outage stage')
    error = record['error']
    if (type(error) is not dict or set(error) != {'hook', 'type', 'message'}
            or any(type(v) is not str for v in error.values())
            or not error['hook'] or not error['type'] or len(error['message']) > 500):
        raise OutageError('Supply a hook, error type and message of at most 500 characters')
    # Validation and encoding finish before opening a file. This also rejects
    # invalid UTF-8 surrogates. A length bound is not redaction of private text.
    return (json.dumps(record, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def _remaining(deadline):
    return max(0.0, deadline - time.monotonic())


def _path_lock(key, deadline):
    if not _LOCKS_GUARD.acquire(timeout=_remaining(deadline)):
        raise OutageLockTimeout('Outage lock-map timeout')
    try:
        lock = _LOCKS.setdefault((os.getpid(), key), threading.Lock())
    finally:
        _LOCKS_GUARD.release()
    if not lock.acquire(timeout=_remaining(deadline)):
        raise OutageLockTimeout('Outage path-lock timeout')
    return lock


def _open_regular(path):
    try:
        prior = path.lstat()
    except FileNotFoundError:
        prior = None
    if prior is not None and not stat.S_ISREG(prior.st_mode):
        raise OutageError('Outage destination must be a regular file')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND |
                 getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) |
                 getattr(os, 'O_BINARY', 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OutageError('Outage destination must be a regular file')
        return fd
    except BaseException:
        os.close(fd)
        raise


class OutageWriter:
    """Write supplied records to an explicit ``unrecorded.jsonl`` destination.

    The 0..2 second budget bounds process-lock acquisition, not filesystem I/O,
    encoding or fsync. No sidecar/OS lock is used (ENG-16). A non-LF tail is
    refused without modifying it; this is not verification of prior JSON lines
    or a tamper-evident chain. No retry, rotation or deletion is implemented.
    """

    def __init__(self, path, *, lock_timeout=2.0):
        supplied = Path(path)
        if not supplied.is_absolute() or supplied.name != 'unrecorded.jsonl':
            raise OutageError('Supply an absolute unrecorded.jsonl path')
        if (type(lock_timeout) not in (int, float) or not math.isfinite(lock_timeout)
                or not 0 <= lock_timeout <= 2):
            raise OutageError('Process-lock budget must be finite and within 0..2 seconds')
        parent = supplied.parent.resolve(strict=True)
        if not parent.is_dir():
            raise OutageError('The trusted parent directory must already exist')
        self._path = parent / supplied.name
        self.lock_timeout = float(lock_timeout)
        self._key = os.path.normcase(str(self.path))

    @property
    def path(self):
        return self._path

    def __call__(self, record):
        line = _line(record)
        # Properties are public for diagnostics, but changing the budget must
        # not turn this callback into an unbounded lock wait.
        budget = self.lock_timeout
        if type(budget) not in (int, float) or not math.isfinite(budget) or not 0 <= budget <= 2:
            raise OutageError('Invalid process-lock budget')
        lock = _path_lock(self._key, time.monotonic() + budget)
        attempted = False
        fd = None
        try:
            fd = _open_regular(self.path)
            if os.fstat(fd).st_size:
                os.lseek(fd, -1, os.SEEK_END)
                if os.read(fd, 1) != b'\n':
                    raise OutageError('Outage file has an incomplete tail; no repair attempted')
            file = os.fdopen(fd, 'ab', buffering=0)
            fd = None
            with file:
                attempted = True
                if file.write(line) != len(line):
                    raise OSError('Short outage append')
                file.flush()
                os.fsync(file.fileno())
            return line
        except Exception as exc:
            if attempted:
                raise OutageWriteUncertain('Outage append outcome is uncertain; no retry') from exc
            raise
        finally:
            try:
                if fd is not None:
                    os.close(fd)
            finally:
                lock.release()
