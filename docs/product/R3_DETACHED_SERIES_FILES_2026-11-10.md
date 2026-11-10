# R3 detached series files

This is bounded child **⑨-3a/series-files/1** of the approved R3 implementation
(owner rulings: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:302` and `:320`, which
approve R3 design revision 2 and the 10.2 A build questions). It adds
`core/quant/run_registry_series_files.py`: a store for caller-supplied NPY1
series payloads, verified before they are published under their content
SHA-256 in a directory the caller names. It is not connected to the Lab, the
recorder, any actual ledger, configuration, provider or owner-decision effect.
The R3 parent remains open.

Child **⑨-3a/series-files/2** (2026-11-11) changed the publish step: it no
longer calls `os.replace` and can no longer overwrite an existing target (owner
ruling 10 of 2026-11-11, section "No-clobber publish"). Two things follow for a
caller. A target that appears while a write is in progress is now verified
(`created=False`, or `IntegrityError`) where child 1 raised
`PublicationUncertain`. A POSIX filesystem without hard links raises the new
`NoClobberUnsupported`. The locks, the temp file handling, the retry limits, the
bounded reads and the other typed errors are as child 1 left them. The sections
below describe the current behaviour; the child 1 verification record is kept as
written.

## Design reference and deltas

The contract is R3 design revision 2 at `fa280591b9915b213a00e231a55bbe8d33b0d9d7`
(`docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`), §5.7
"Series store", with ENG-15 (a), and the Nautilus bridge rule it cites
(`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:794-797`): same-folder
`mkstemp`, `fsync`, then `os.replace`, retried up to 10 times over 5 s on
`PermissionError`. The revision 2 header still reads "Owner approval: not given";
that is the text from before the rulings above.

Deliberate deltas from §5.7:

- **No-clobber publish instead of `os.replace`** (owner ruling 10, 2026-11-11;
  child 2). §5.7 and the bridge rule name `os.replace`, which overwrites. The
  store gives the temp its final name with a call that fails when that name
  exists, and verifies an existing target instead of replacing it. See
  "No-clobber publish".

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
  bounds this digest's lock waits only, not filesystem calls, hashing, the
  process-wide map lookup or the publish retries.

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
   from a guarded map. The map guard is held for one dictionary lookup only and is
   taken without a timeout, so even `lock_timeout=0` never fails because another
   thread is looking up an unrelated digest; the deadline applies to this
   digest's process lock and OS lock. If the process ID differs from the one
   that built the map, the map, its guard and the recorded PID are rebound before
   use; the same reset runs as an `os.register_at_fork` child handler where
   available. This fixes Python lock state only, not inherited descriptors or OS
   locks held through them.
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
   `created=False` with no temp and no publish call; an invalid one raises
   `IntegrityError` and is never repaired, adopted, deleted or overwritten.
4. Otherwise `tempfile.mkstemp` in the same directory (prefix `.<digest>.`,
   suffix `.tmp`). Its `lstat` identity `(st_dev, st_ino)` is recorded and it must
   be an empty regular file, else `StoreError` (the temp is then kept, because
   its ownership is unproven). Short writes continue; a zero-progress write is
   `OSError(EIO)`. Then `fsync` and a single `close`. Any failure here removes
   only the identity-matching temp; the publish call is never made.
5. The temp is given the target name by a call that fails when that name exists
   ("No-clobber publish"), with the bounded retry below.
6. After the publish call: on POSIX the temp name is unlinked and the directory
   is fsynced; then, on both platforms, a bounded readback whose bytes must equal
   the verified payload exactly. Any failure is `PublicationUncertain`.
7. `(sha256, created)` is returned only after a clean unlock and close.

| Retried | Not retried |
| --- | --- |
| `PermissionError` from the publish call only (a Windows access or sharing violation; POSIX EACCES): at most 10 attempts within a 5 s monotonic budget, with waits 0.05, 0.1, 0.2, 0.4 and then 0.8 s (nine waits, 4.75 s in total). No attempt starts once 5 s have elapsed: a wait that would reach 5 s is not taken, and the clock is read again after each wait, so a late wake-up also ends the retries | `mkstemp`, a zero-progress write, the temp fsync or close, `FileExistsError` from the publish call (the target is verified instead), the POSIX errors that say the filesystem cannot make the hard link (EPERM included, although Python raises it as a `PermissionError`), other publish errors, the state checks, unlink, the directory fsync, readback (including a Windows `PermissionError` on readback), unlock and close. OS-lock contention is a lock wait, bounded by `lock_timeout` |

Before every attempt and again at exhaustion, the store requires the original
temp (same identity, regular, same size); a vanished or changed temp raises
`PublicationUncertain`. A target name found at those checks is verified as
"No-clobber publish" describes and is never overwritten. Exhaustion with the
original temp and an absent target confirmed raises `ReplaceRetryExhausted` with
`attempts` and `temp_removed`. That class name, `REPLACE_ATTEMPTS` and
`REPLACE_BUDGET` are kept from child 1 so the typed errors and limits of the
contract do not change; nothing is replaced. No time limit applies to a single
filesystem call, so the last attempt, started before 5 s, can end later. The lock
stays held during the retry window, so another caller of the same digest with the
default 2 s timeout can get `LockTimeout`; other digests are unaffected.

## No-clobber publish

Owner ruling 10 of 2026-11-11 (see "Owner question" below) approved a publish
that cannot overwrite. No call in the module can replace an existing name:
`os.replace` and POSIX `os.rename` are not used, and a test checks the source
for them.

| Platform | Call | Why this call |
| --- | --- | --- |
| POSIX | `os.link(temp, target)`, then the temp name is unlinked | `link(2)` fails with `FileExistsError` when the target name exists in any form (a dangling symlink or a directory included), and it gives the name its full, already fsynced content in one step. POSIX `rename` replaces silently. A rename that refuses (`renameat2` with `RENAME_NOREPLACE` on Linux, `renamex_np` on macOS) is not in the standard library. An exclusive create followed by a copy would not overwrite either, but a crash would leave a partial file under the final name, which the store never repairs. |
| Windows | `os.rename(temp, target)` | It is `MoveFileExW` without `MOVEFILE_REPLACE_EXISTING`: any existing target is a `FileExistsError`, the name moves in one step, and no hard-link support is needed, so FAT and exFAT volumes work. |

A target name that exists at publish time was created outside the cooperating
lock, after this call's absence check. It is found by the check before an
attempt, by the publish call itself (`FileExistsError`) or by the check at
exhaustion, and all three are handled alike: this call's temp is removed and
the existing target is validated as in Read.

- Valid bytes: the call returns `created=False`, and the file is kept byte for
  byte (the other writer's container wins, as for any existing target).
- Anything else (wrong or partial bytes, a link, a directory): `IntegrityError`;
  the target is left untouched.
- The name vanished again before it could be validated: `PublicationUncertain`.

A POSIX filesystem that cannot make the hard link (FAT, exFAT, some FUSE and
network mounts) fails `os.link` with EPERM, ENOTSUP, EOPNOTSUPP, ENOSYS, EMLINK
or EXDEV. These errors are permanent, so they are not retried, EPERM included.
After confirming the original temp and an absent target, the call removes the
temp and raises the typed `NoClobberUnsupported` at once. There is no fallback
to a call that can overwrite, and no second primitive is tried: on POSIX such a
directory cannot hold series files. Windows is not affected. A filesystem that
reports the same condition with another error ends in `ReplaceRetryExhausted`
(EACCES, after the bounded retries) or `PublicationUncertain` (any other error);
in no case is an overwriting call made.

Durability is not weaker than before. The temp is fsynced and closed before the
publish call on both platforms. POSIX fsyncs the directory once, after the link
and the unlink of the temp name, where child 1 fsynced it after the rename.
Windows has no directory fsync, as before. If a POSIX process dies between the
link and the unlink, the temp name stays next to the published file; both names
are then the same fsynced file.

The typed errors survive pickling, so a parent receives the same type,
`attempts`, `temp_removed` and `cleanup_errors` from a worker process; as for any
pickled exception, the traceback and `__cause__` are not carried.

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
| `IntegrityError` | Target untouched; no temp. Also raised for a target name that appeared during the publish and does not verify |
| `ReleaseError` | A read or an existing-target check (the idempotent skip, or a valid target that appeared during the publish) verified its result, but unlock, a close or the removal of this call's temp failed; no publication by this call; the result is not returned |
| Raw `OSError` from `mkstemp`, the temp write, fsync or close | No publish call; the identity-matching temp is removed unless `cleanup_errors` says otherwise; a new sidecar may stay empty if its NUL initialization failed |
| Temp `StoreError`, or an `lstat` failure right after `mkstemp` | No publish call; the temp is kept, because its ownership is unproven; a new sidecar may stay empty if its NUL initialization failed |
| `ReplaceRetryExhausted` | Target absent at the final check; temp removed if `temp_removed` |
| `NoClobberUnsupported` | POSIX only: the filesystem cannot make the hard link. Nothing published and nothing overwritten; the original temp and an absent target were confirmed; the temp is removed unless `cleanup_errors` says otherwise |
| `PublicationUncertain` | Never overwrote a target; the target may be absent, foreign, or published without completed checks (on POSIX this includes a published file whose temp name could not be unlinked and is still a hard link to it). Do not blindly retry; a later `read()` verifies current bytes but not durability |
| `KeyboardInterrupt`, `SystemExit` | Propagated unwrapped after cleanup (identity-checked temp removal, unlock, a single close, process-lock release). Before the publish call the owned temp is removed unless `cleanup_errors` says otherwise; during or after it publication is unknown, so verify with `read()` |

Any raised exception may carry `cleanup_errors`, a tuple of cleanup failures.
Typed wrappers keep their trigger as `__cause__`. Only `Exception` is collected or
wrapped; asynchronous interrupts arriving between cleanup steps are best effort.

## Platform notes

- POSIX publishes with `os.link`, unlinks the temp name and then fsyncs the
  directory. A filesystem that rejects directory fsync (EINVAL) turns every publish
  into `PublicationUncertain`; one that cannot hard-link raises
  `NoClobberUnsupported` for every new file. Files are created with mode 0600 by
  `mkstemp`.
- Windows publishes with `os.rename` and has no directory fsync here; only the temp
  file is fsynced before the rename. `msvcrt` locks are byte-range locks on byte 0,
  which may lie beyond end of file; the NUL byte is written only after locking. If
  unlock fails, Windows releases the lock when the handle closes, asynchronously,
  so an immediate zero-timeout retry may still time out.
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
- Trust model excludes hostile path changes, hard-link aliases made by others,
  sync folders and network mounts, fork during active I/O and inherited
  descriptors. A non-cooperating writer that creates the target name while a
  write is in progress is no longer excluded: its file is verified and never
  overwritten (ruling 10). One that changes or removes a file after the store
  verified it still is. On a network mount a link can report failure after it
  succeeded; the store then verifies the file it just made and reports
  `created=False`.
- One `.lock` per digest persists. Dot-prefixed `.<digest>.*.tmp` files can remain
  after a kill or a cleanup failure; they are hidden only on POSIX and are visible
  on Windows, where a leading dot sets no hidden attribute and the store sets
  none. On POSIX a temp left between the link and its unlink is a hard link to
  the published file: the same content under a second name, to be removed with
  the other leftovers. There is no automatic cleanup, retention,
  TTL or tombstone. The process-lock map grows by one entry per digest.
- Deleting or omitting the `.lock` of an existing `.npy` (including restoring only
  the `.npy` from a backup) makes that digest permanently refused with
  `SidecarMissing`. Delete the `.npy` first or together with its `.lock`; back
  them up as a pair. Re-running the same input re-creates a deleted `.npy`, and
  one file may be shared by several runs.
- Matrix semantics (day column, P&L versus prices, configuration order) are
  opaque and not enforced; the caller must not put prices, account or personal
  data in the matrix.

## Owner question (closed by ruling 10, 2026-11-11)

The question, as child 1 recorded it on 2026-11-10. The approved design and the
claimed contract name `os.replace`. With it, a target created by a
non-cooperating writer after the last absence check and before `os.replace` was
overwritten on both platforms; the readback then matched the payload and
`write()` returned `(sha256, True)`. On Windows, `os.replace` is `MoveFileExW` with
`MOVEFILE_REPLACE_EXISTING`, which replaces a foreign target that is closed or
open with delete sharing. Only while that target was held open without delete
sharing did it fail with `PermissionError`, and the next pre-attempt check then
refused. A no-clobber publish (Windows `os.rename`, or POSIX `os.link` plus
`unlink`) would refuse to overwrite in that window on both platforms. Child 1
recorded this as a question and did not implement it.

The answer. The decision table of 2026-11-11 carried it as item 10, "시계열 파일
덮어쓰기 금지(no-clobber)", with the recommendation "덮어쓰기 금지로 변경. 파일
이름이 내용 해시라서 이미 있으면 검증만 하면 되고, 덮어쓰기는 증거 손실 위험만
남깁니다." The owner answered "10-승인"
(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, section "2026-11-11, Claude Code
채팅: 남은 결정 14건에 대한 답 (원문)", reflection 10: "이미 있는 대상은 덮어쓰지
않고 검증만 합니다"). Child ⑨-3a/series-files/2 implements it as "No-clobber
publish" describes. The departure from the literal `os.replace` of design §5.7 is
therefore owner-approved, and the question is closed.

## Boundaries

No recorder, `series_error` event, `series_ref`, retention, Lab, ledger,
counting, verdict or prices check is implemented. The seven existing helpers
(codec, store, keys, data hash, source hash, series hash, series format) are
unchanged. Dependency: PR87 (series hash) and PR88 (series format) must merge
first; base `e7ed793` is PR88's head. Child 2 changes only
`core/quant/run_registry_series_files.py`, its test and this record; no 01-20
policy row names the publish call, so none changed.

## Verification

The first part is the child 1 record of 2026-11-10, kept as written (it names
`os.replace`, which the module no longer calls). The child 2 record follows it.

All local checks ran on Linux with Python 3.13 (`-B`, no bytecode), in fresh
temporary directories only, with no network, real series, ledger or
configuration.

- `tests.run_registry_series_files_acceptance`: **45 tests** after the review
  fixes below, run three times as a flake check: 1.400 s, 1.450 s and 1.435 s,
  exit 0 each. Before them, the first 41 tests passed three times (2.177 s,
  2.196 s, 2.342 s) and once in development (2.124 s); no run failed.
- Combined R3 run (series files 45 + series format 22 + series hash 15 + source
  hash 8 + data hash 15 + keys 13 + store 16 + codec 17): **151 tests in 3.519 s,
  exit 0** (first round: 147 tests in 5.144 s). These overlap and are not added
  together.
- Mutation run on scratch copies: **41 of 41 mutants killed**: the first round's
  28 (two retry mutants rewritten for the new retry code) plus 13 for the review
  round (reverts of the three code fixes, six budget value and boundary mutants,
  four interrupt sites). The first round killed 28 of 28 (18 clause mutants, 6
  found in review, 4 specific to the revision 2 fixes); its first launch stopped
  before any mutant ran (a relative interpreter path) and was rerun with absolute
  paths.
- `tests.runtime_syntax_acceptance` passed; the module and its test compiled on
  Python 3.11 and 3.12, and `ast.parse(feature_version=(3, 10))` accepted them. A
  real 3.10 compile is the CI syntax job.
- Cross-process exclusion is covered deterministically by a spawned child holding
  the lock, a second descriptor's OS lock, the shared deadline and the sidecar
  race; two spawned writers of one digest and six threads are smoke checks only.

Review round (same day). Three defects were reproduced on the first commit and
fixed: an attempt started at exactly 5 s after the last wait was cut to the
remaining budget (5.0002 s on the real clock); `ReplaceRetryExhausted` raised
`TypeError` when unpickled; and with `lock_timeout=0` a busy map guard raised
`LockTimeout` for an unrelated digest (664 of 3,200 reads in one stress probe
with a 1 µs thread switch interval).
After the fixes the same probes show no attempt at or after 5 s, a clean pickle
round trip and no spurious `LockTimeout`. New tests also pin the 5 s value and
four interrupt sites (the OS-lock wait, the temp phase, read verification and the
post-rename readback). The owner question, the temp-file outcome rows and the
dot-prefixed temp wording were corrected.

The Windows branch was exercised on Linux only through a fake `msvcrt` that
checks call order and offsets. Real `msvcrt`, `os.replace` under Defender,
OneDrive or the indexer, `lstat` file-ID behavior, deferred unlock on handle
close, spawn on Windows and `MAX_PATH` were not executed locally; the first real
execution is the Windows Runtime CI matrix (3.11, 3.12, 3.14).

### Child 2: no-clobber publish (2026-11-11)

Local checks on Linux (ext4) with Python 3.13 (`-B`), fresh temporary directories
only, no network, real series, ledger or configuration.

- `tests.run_registry_series_files_acceptance`: **53 tests** (45 before; of the
  three tests of the old `PublicationUncertain` reading one was removed and two
  were rewritten for the new reading, and nine were added), three runs of
  1.502 s, 1.401 s and 1.581 s, exit 0 each, and once more with
  `-W error::ResourceWarning` (1.455 s). No run failed.
- The race is tested on both branches. POSIX: a hook inside the publish call
  creates the target (valid bytes, wrong bytes, a dangling symlink, a directory)
  after the store's last absence check and then calls the real `os.link`, so the
  kernel itself refuses. Windows branch: selected on Linux with a stand-in
  `msvcrt`, and `os.rename` replaced by a stand-in that refuses an existing
  destination as Windows does; on Windows the same tests use the real
  `os.rename`. Each test's `setUp` makes `os.replace` (and, on POSIX, `os.rename`)
  raise, so no test passes through a call that can overwrite. Other new tests: a
  target that appears before the first attempt, during a retry and on the final
  attempt; the six no-hard-link errors (one attempt, no wait, typed error,
  nothing left); every `PermissionError` retried on the Windows branch; a failed
  temp unlink after the link; a blocking name that vanishes; a verified existing
  target whose temp could not be removed; and a source check that `os.link` and
  `os.rename` are each called once, inside `_no_clobber`, and `os.replace` never.
- Combined run with the fold, the adoption checks and the seven other R3
  modules: **238 tests in 6.426 s, exit 0** (230 before this child; overlapping,
  not added together). `tests.runtime_syntax_acceptance` passed; the module and
  its test compiled on Python 3.11, 3.12 and 3.13 and
  `ast.parse(feature_version=(3, 10))` accepted them.
- Mutation run on scratch copies: **26 of 26 mutants killed** (the publish call
  swapped for `os.replace` or POSIX `os.rename` on either branch; each of the
  three target checks removed; verification, temp removal, the typed errors and
  their state checks removed; the EPERM carve-out removed or applied to Windows;
  the directory fsync removed; retry count and budget changed).
- Real-thread probe, scratch only: a second thread creates the target with an
  exclusive create while `write()` runs, 20,000 fresh directories per run. With
  child 1's module the foreign file was overwritten 1, 8 and 6 times in three
  runs (15 of 60,000); with this child 0 times in two runs (0 of 40,000), and
  the foreign file's bytes were intact in every case. The probe shows the old
  window was reachable; a count of zero is not a proof.

Not executed locally: Windows itself (real `os.rename`, `msvcrt`, Defender,
OneDrive, the indexer), macOS, and any filesystem without hard links (no FAT or
exFAT support in this environment), so `NoClobberUnsupported` was exercised only
with injected errors. That EPERM is what `link(2)` returns there is taken from
its manual page. The first real Windows execution is the Runtime CI matrix.

Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
