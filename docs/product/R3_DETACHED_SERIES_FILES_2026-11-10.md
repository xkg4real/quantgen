# R3 detached series files

This is bounded child **⑨-3a/series-files/1** of the approved R3 implementation
(owner rulings: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:302` and `:320`, which
approve R3 design revision 2 and the 10.2 A build questions). It adds
`core/quant/run_registry_series_files.py`: a store for caller-supplied NPY1
series payloads, verified before they are published under their content
SHA-256 in a directory the caller names. It is not connected to the Lab, the
recorder, any actual ledger, configuration, provider or owner-decision effect.
The R3 parent remains open.

## Design reference and deltas

The contract is R3 design revision 2 at `fa280591b9915b213a00e231a55bbe8d33b0d9d7`
(`docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`), §5.7
"Series store", with ENG-15 (a), and the Nautilus bridge rule it cites
(`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:794-797`): same-folder
`mkstemp`, `fsync`, then `os.replace`, retried up to 10 times over 5 s on
`PermissionError`. The revision 2 header still reads "Owner approval: not given";
that is the text from before the rulings above.

Deliberate deltas from §5.7:

- **Stricter skip.** §5.7 says the writer "skips a name that exists" and records
  `series_error`. Here an existing target is fully validated (bounded read and
  exact content rehash) before the skip, and an invalid one is refused with a
  typed error and left untouched. Recording `series_error` belongs to the future
  recorder; this module only raises typed errors.
- **Skip by content identity; stored verbatim.** An existing valid target is kept
  byte for byte even when the caller's container bytes differ (for example an
  alternate NPY header with the same content); the call returns `created=False`.
  New payloads are stored exactly as supplied after verification. §5.7 says the
  file is "written with `numpy.save`"; here any NPY1 container that the existing
  `decode_series` accepts is stored as supplied, the first writer's container
  wins, and stored bytes need not be `numpy.save` output. Nothing is re-encoded.

## API and limits

`SeriesFiles(directory, *, max_bytes, lock_timeout=2.0)`:

- `directory`: an existing absolute directory as `str` or a `PathLike` that yields
  `str`. It is resolved strictly; a missing path, a file, bytes, an embedded NUL
  or a symlink loop is refused with `StoreError`. Nothing is created: no `mkdir`,
  no default path, no environment or configuration lookup.
- `max_bytes`: required plain `int`, `0 < max_bytes <= np.iinfo(np.intp).max`.
  It bounds the payload and the bytes read from a stored file. Cooperating
  instances on one directory must share one `max_bytes`: a smaller reader
  refuses valid larger files with `IntegrityError`.
- `lock_timeout`: plain `int` or `float`, finite, 0 to 10 seconds, default 2. It
  bounds lock waits only, not filesystem calls, hashing or the replace retries.

`write(payload, expected_sha256) -> (sha256, created)` and
`read(sha256) -> numpy.ndarray` (read-only flag set, as a convenience only).

Peak memory is not bounded by `max_bytes`. One Linux `tracemalloc` measurement
on a 5,000 x 13 series (520,128 bytes) gave about 3.0x the file size on read
(chunks, joined bytes, decoded array, hash serialization) and about 2.0x the
payload on write, in addition to the caller's payload. This is a measurement,
not a bound.

## Lock protocol

Names are fixed: `<digest>.npy` and `<digest>.lock` in the directory, where the
digest is the lowercase 64-hex content SHA-256 already validated by the format
decoder (write) or by an exact pattern check (read), so no other path is formed.

1. One monotonic deadline covers both lock stages.
2. A process lock per sidecar path (normalized with `os.path.normcase`) comes
   from a guarded map. If the process ID differs from the one that built the map,
   the map, its guard and the recorded PID are rebound before use; the same
   reset runs as an `os.register_at_fork` child handler where available. This
   fixes Python lock state only, not inherited descriptors or OS locks held
   through them.
3. The sidecar is opened read-write without following links (`O_NOFOLLOW`,
   `O_NONBLOCK`, `O_BINARY` where defined); an existing non-regular sidecar is
   refused with `StoreError`.
4. If the sidecar is absent and the target name exists in any form (links
   included), the sidecar is opened again without `O_CREAT`. A cooperating writer
   may have created it and published between the two system calls; that case
   continues normally. If it is still absent, `SidecarMissing` is raised and
   nothing is created. Otherwise a read raises `SeriesNotFound`, and only a write
   creates the sidecar.
5. The OS lock is polled until the deadline: POSIX `flock(LOCK_EX | LOCK_NB)`;
   Windows seeks to byte 0, then `msvcrt.locking(fd, LK_NBLCK, 1)`. Unlock seeks
   to byte 0 again before `LK_UNLCK`. Contention errors (EACCES, EAGAIN, EDEADLK)
   are retried until the deadline, then `LockTimeout`.
6. Only after the lock, and only for a write that finds an empty sidecar, one NUL
   byte is written and fsynced. Reads never write the sidecar.

## Write

1. `decode_series(payload, expected_sha256, max_bytes=...)` runs before any
   filesystem effect; a refusal is `SeriesFormatError` and creates nothing.
2. Lock as above.
3. If the target name exists, it is validated as in Read. A valid target returns
   `created=False` with no temp and no replace; an invalid one raises
   `IntegrityError` and is never repaired, adopted, deleted or overwritten.
4. Otherwise `tempfile.mkstemp` in the same directory (prefix `.<digest>.`,
   suffix `.tmp`). Its `lstat` identity `(st_dev, st_ino)` is recorded and it must
   be an empty regular file, else `StoreError` (the temp is then kept, because
   its ownership is unproven). Short writes continue; a zero-progress write is
   `OSError(EIO)`. Then `fsync` and a single `close`. Any failure here removes
   only the identity-matching temp; `os.replace` is never called.
5. `os.replace(temp, target)` with the bounded retry below.
6. After the rename: POSIX directory fsync, then a bounded readback whose bytes
   must equal the verified payload exactly. Any failure is `PublicationUncertain`.
7. `(sha256, created)` is returned only after a clean unlock and close.

| Retried | Not retried |
| --- | --- |
| `PermissionError` from `os.replace` only (EACCES, or a Windows access or sharing violation): at most 10 attempts within a 5 s monotonic budget, with waits 0.05, 0.1, 0.2, 0.4 and then 0.8 s (nine waits, 4.75 s in total), each cut to the remaining budget | `mkstemp`, a zero-progress write, the temp fsync or close, other `os.replace` errors, the state checks, unlink, the directory fsync, readback (including a Windows `PermissionError` on readback), unlock and close. OS-lock contention is a lock wait, bounded by `lock_timeout` |

Before every attempt and again at exhaustion, the store requires the original
temp (same identity, regular, same size) and an absent target name. A vanished or
changed temp, or a target that appeared, raises `PublicationUncertain` and is never
overwritten. Exhaustion with those conditions confirmed raises
`ReplaceRetryExhausted` with `attempts` and `temp_removed`. No time limit applies
to a single filesystem call. The lock stays held during the retry window, so
another caller of the same digest with the default 2 s timeout can get
`LockTimeout`; other digests are unaffected.

## Read

`read(sha256)` checks the digest pattern before any filesystem access, takes the
lock without creating anything, raises `SeriesNotFound` for an absent target, and
then validates: links and non-regular files are refused from `lstat` (a FIFO
cannot hang the open), `fstat` must show a regular file no larger than
`max_bytes`, chunks of at most 1 MiB are read up to the size, a one-byte probe
must find end of file, and size plus `st_mtime_ns` must be unchanged. File bytes
read are at most `max_bytes + 1`. The existing `decode_series` then re-hashes the
content exactly; a format or content mismatch is `IntegrityError`.

The sidecar is opened read-write even for a read, so read-only media or backups
cannot be read through this module.

## Outcomes

| Outcome | State guaranteed |
| --- | --- |
| `SeriesFormatError`, constructor `StoreError` | Nothing created |
| `LockTimeout` | No temp created; an existing target untouched; a newly created empty sidecar may remain |
| `SidecarMissing`, `SeriesNotFound` | Nothing created or changed |
| `IntegrityError` | Target untouched; no temp |
| `ReleaseError` | A read or idempotent skip verified its result but unlock or a close failed; no publication by this call; the result is not returned |
| Raw `OSError` or temp `StoreError` from write | No replace call; the owned temp is removed unless `cleanup_errors` says otherwise; a new sidecar may stay empty if its NUL initialization failed |
| `ReplaceRetryExhausted` | Target absent at the final check; temp removed if `temp_removed` |
| `PublicationUncertain` | Never overwrote a target it observed; the target may be absent, foreign, or published without completed checks. Do not blindly retry; a later `read()` verifies current bytes but not durability |
| `KeyboardInterrupt`, `SystemExit` | Propagated unwrapped after cleanup (identity-checked temp removal, unlock, a single close, process-lock release). Before `os.replace` the owned temp is removed unless `cleanup_errors` says otherwise; during or after `os.replace` publication is unknown, so verify with `read()` |

Any raised exception may carry `cleanup_errors`, a tuple of cleanup failures.
Typed wrappers keep their trigger as `__cause__`. Only `Exception` is collected or
wrapped; asynchronous interrupts arriving between cleanup steps are best effort.

## Platform notes

- POSIX fsyncs the directory after the rename. A filesystem that rejects directory
  fsync (EINVAL) turns every publish into `PublicationUncertain`. Files are created
  with mode 0600 by `mkstemp`.
- Windows has no directory fsync here; only the temp file is fsynced before the
  rename. `msvcrt` locks are byte-range locks on byte 0, which may lie beyond end of
  file; the NUL byte is written only after locking. If unlock fails, Windows
  releases the lock when the handle closes, asynchronously, so an immediate
  zero-timeout retry may still time out.
- Without long-path support, a directory longer than about 180 characters fails,
  because temp names are about 78 characters.
- Identity checks compare `lstat` with `lstat`, never `fstat` with `lstat`. Where
  `lstat` reports no file ID (`st_ino` 0, for example some SMB or FAT volumes),
  the check degrades to name plus size. Inode reuse after delete and recreate is
  outside the trust model.

## Non-guarantees and trust boundaries

- No power-loss durability (macOS `fsync` without `F_FULLFSYNC` included). No
  OneDrive, Defender, indexer or network-drive guarantee. The OneDrive refusal of
  design §5.1 (ENG-15 (d)) belongs to the future recorder; this module makes no
  environment lookup.
- Trust model excludes hostile path changes, hard-link aliases, sync folders and
  network mounts, fork during active I/O, inherited descriptors, and a
  non-cooperating writer creating the target after the absence check (see the
  owner question below).
- One `.lock` per digest persists. Hidden `.<digest>.*.tmp` files can remain
  after a kill or a cleanup failure. There is no automatic cleanup, retention,
  TTL or tombstone. The process-lock map grows by one entry per digest.
- Deleting or omitting the `.lock` of an existing `.npy` (including restoring only
  the `.npy` from a backup) makes that digest permanently refused with
  `SidecarMissing`. Delete the `.npy` first or together with its `.lock`; back
  them up as a pair. Re-running the same input re-creates a deleted `.npy`, and
  one file may be shared by several runs.
- Matrix semantics (day column, P&L versus prices, configuration order) are
  opaque and not enforced; the caller must not put prices, account or personal
  data in the matrix.

## Owner question

The approved design and the claimed contract name `os.replace`. On POSIX, a
target created by a non-cooperating writer after the absence check would be
overwritten; on Windows, `MoveFileEx` fails with `PermissionError` while that
target is open, and the next pre-attempt check then refuses. A no-clobber publish
(Windows `os.rename`, or POSIX `os.link` plus `unlink`) would refuse to overwrite
in that window. It is recorded here as a question, not implemented.

## Boundaries

No recorder, `series_error` event, `series_ref`, retention, Lab, ledger,
counting, verdict or prices check is implemented. The seven existing helpers
(codec, store, keys, data hash, source hash, series hash, series format) are
unchanged. Dependency: PR87 (series hash) and PR88 (series format) must merge
first; base `e7ed793` is PR88's head.

## Verification

All local checks ran on Linux with Python 3.13 (`-B`, no bytecode), in fresh
temporary directories only, with no network, real series, ledger or
configuration.

- `tests.run_registry_series_files_acceptance`: **41 tests**, run three times as a
  flake check: 2.177 s, 2.196 s and 2.342 s, exit 0 each. An earlier development
  run of the same 41 tests also passed (2.124 s); no run failed.
- Combined R3 run (series files 41 + series format 22 + series hash 15 + source
  hash 8 + data hash 15 + keys 13 + store 16 + codec 17): **147 tests in 5.144 s,
  exit 0**. These overlap and are not added together.
- Mutation run on scratch copies: **28 of 28 mutants killed** (18 clause mutants,
  6 found in review, 4 specific to the revision 2 fixes). The first launch of
  the mutation script stopped before any mutant ran (a relative interpreter path);
  it was rerun with absolute paths.
- `tests.runtime_syntax_acceptance` passed; the module compiled on Python 3.11 and
  3.12, and `ast.parse(feature_version=(3, 10))` accepted it. A real 3.10 compile
  is the CI syntax job.
- Cross-process exclusion is covered deterministically by a spawned child holding
  the lock, a second descriptor's OS lock, the shared deadline and the sidecar
  race; two spawned writers of one digest and six threads are smoke checks only.

The Windows branch was exercised on Linux only through a fake `msvcrt` that
checks call order and offsets. Real `msvcrt`, `os.replace` under Defender,
OneDrive or the indexer, `lstat` file-ID behavior, deferred unlock on handle
close, spawn on Windows and `MAX_PATH` were not executed locally; the first real
execution is the Windows Runtime CI matrix (3.11, 3.12, 3.14).

Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
