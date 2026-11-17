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
`PublicationUncertain`; one that cannot be opened or read still is
`PublicationUncertain`. A POSIX `os.link` that cannot make the hard link at all
(usually a filesystem without hard links) raises the new
`NoClobberUnsupported`. Child 2 left the locks, the temp file handling, the retry
limits, the bounded reads and the other typed errors as child 1 had them.

Child **⑨-3a/series-files/3** (2026-11-11) is the `/code-review` round on
child 2 and the verification of its fixes (sections "Child 3: /code-review
fixes" and "Child 3: verification of the fixes"). It changed four things a
caller can see. A target that blocks the publish is no longer judged on a
single look taken after this call's temp was deleted: the temp is kept, and a
regular file that does not verify yet is looked at again within the 10 attempts
and 5 s. On POSIX an existing target is fsynced, together with the directory,
before `created=False` is returned. No POSIX `os.link` error is retried: a
`PermissionError` from it (EACCES), with no target name in the way, is
`NoClobberUnsupported` at once, and only the Windows publish call is retried on
`PermissionError`. `ReplaceRetryExhausted`, `REPLACE_ATTEMPTS` and
`REPLACE_BUDGET` are now `PublishRetryExhausted`, `PUBLISH_ATTEMPTS` and
`PUBLISH_BUDGET`, with no aliases.

The sections below describe the current behaviour; the earlier verification
records are kept as written.

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
- **The publish call is retried on Windows only** (/code-review round,
  2026-11-11). §5.7 says the writer "retries up to 10 times over 5 seconds on
  `PermissionError`, because OneDrive, Defender and the indexer open new files".
  That reason exists on Windows. On POSIX the publish call is `os.link`, whose
  `PermissionError`s (EPERM, EACCES) do not pass by waiting, so they end the
  write at once with `NoClobberUnsupported`. A refused `os.link` is not
  repeated because of its error; it is made again only when a foreign name
  found at the check after the refusal is gone again, within the same rounds
  and budget ("When os.link refuses"). The limits (10 and 5 s) are
  unchanged and also bound the looks at a blocking target. No sentence of §5.7,
  of the bridge rule or of the child 1 claim asks for the retry on POSIX; the
  child 2 text of this record listed "POSIX EACCES" as retried, which described
  the code of that day and is corrected below.
- **An existing target is fsynced before it is skipped** (POSIX; /code-review
  round). §5.7 says only that the writer "skips a name that exists". See "Sync
  of an existing target".
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
  process-wide map lookup or the publish rounds (at most 5 s more, with the
  lock held).

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
3. If the target name exists, it is validated as in Read, once. A valid target is
   synced on POSIX ("Sync of an existing target") and the call returns
   `created=False` with no temp and no publish call; an invalid one raises
   `IntegrityError` and is never repaired, adopted, deleted or overwritten.
4. Otherwise `tempfile.mkstemp` in the same directory (prefix `.<digest>.`,
   suffix `.tmp`). Its `lstat` identity `(st_dev, st_ino)` is recorded and it must
   be an empty regular file, else `StoreError` (the temp is then kept, because
   its ownership is unproven). Short writes continue; a zero-progress write is
   `OSError(EIO)`. Then `fsync` and a single `close`. Any failure here removes
   only the identity-matching temp; the publish call is never made.
5. The temp is given the target name by a call that fails when that name exists
   ("No-clobber publish"), in the bounded rounds below.
6. After the publish call: on POSIX the temp name is unlinked and the directory
   is fsynced; then, on both platforms, a bounded readback whose bytes must equal
   the verified payload exactly. Any failure is `PublicationUncertain`.
7. `(sha256, created)` is returned only after a clean unlock and close.

A publish takes at most 10 rounds (`PUBLISH_ATTEMPTS`) within a 5 s monotonic
budget (`PUBLISH_BUDGET`), with waits of 0.05, 0.1, 0.2, 0.4 and then 0.8 s
between rounds (nine waits, 4.75 s in total). A round is one publish call, one
look at a target name that blocks it, or both. No round starts once 5 s have
elapsed: a wait that would reach 5 s is not taken, and the clock is read again
after each wait, so a late wake-up also ends the rounds. What a look found
before a wait that ended late is then not used: the name is looked at once
more, and no publish call is made after the 5 s ("No-clobber publish").

| Repeated in the next round | Not repeated |
| --- | --- |
| The Windows publish call (`os.rename`) after a `PermissionError` (an access or sharing violation while another program holds the new file open). On both platforms, the look at a target name that blocks the publish, while that target is a regular file that does not verify (`IntegrityError`), cannot be opened or read (`PermissionError`) or is gone again (`FileNotFoundError`; the publish call is then made again) | `mkstemp`, a zero-progress write, the temp fsync or close, every error of POSIX `os.link` (`FileExistsError` leads to a look; a `PermissionError` or a no-hard-link error with no target name in the way ends the write at once; `os.link` is made again only by the rule for a name that is gone again, see "When os.link refuses"), other publish errors, the look at a blocking name that is not a regular file (`IntegrityError` at once), any other failure to read a blocking target, the fsync of an existing target or of its directory, the state checks, unlink, the directory fsync, readback (including a Windows `PermissionError` on readback), unlock and close. A target that is already there when the call begins (step 3) is looked at once. OS-lock contention is a lock wait, bounded by `lock_timeout` |

Before every round, and again when the rounds are used up after a refused
publish call or after a late wake-up, the store requires the original temp (same
identity, regular, same size); a vanished or changed temp raises
`PublicationUncertain`. When the rounds end with a look made in the last round,
that look decides and the temp is not checked again. A target name found at
those checks is looked at as "No-clobber publish" describes and is never
overwritten. When the
rounds are used up with the original temp and an absent target confirmed, the
Windows branch raises `PublishRetryExhausted` with `attempts` (the publish calls
made) and `temp_removed`. The POSIX branch cannot end that way: a refused
`os.link` with no target name in the way ends the call at once, and a name that
was in the way and is gone when the rounds are used up ends it in
`PublicationUncertain`. Until the /code-review round the three
names were `REPLACE_ATTEMPTS`, `REPLACE_BUDGET` and `ReplaceRetryExhausted`; the
values (10 and 5.0) are unchanged, and the old names are gone without aliases,
because nothing is replaced any more and only this module's own test imports it.
No time limit applies to a single filesystem call, so the last round, started
before 5 s, can end later. The lock stays held during the rounds, so another
caller of the same digest with the default 2 s timeout can get `LockTimeout`;
other digests are unaffected. How long that is for a name that never passes
(Linux, real clock, child 3 verification): a regular file that does not verify
holds both locks for 4.76 s and is opened ten times; a 64 MiB file with one
wrong byte for 4.81 s, read and hashed in each of eight rounds; in both cases a
reader of the same digest that started 0.3 s in got `LockTimeout` after 2.0 s.
A name that is not a regular file is refused at the first look, in 0.003 to
0.008 s, and the reader gets its `IntegrityError` at once.

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
lock, after this call's absence check. It is found in one of four places: the
check before a round, the publish call itself (`FileExistsError`), the check
when the rounds are used up (after a refused publish call or a late wake-up)
and, on POSIX, the check that follows a refused `os.link` (below). All four
are handled alike. This call's verified temp is
kept, and the target is looked at: validated as in Read, and never written,
repaired or removed.

- Valid bytes: the target is synced on POSIX ("Sync of an existing target"),
  then this call's temp is removed and the call returns `created=False`. The
  file is kept byte for byte (the other writer's container wins, as for any
  existing target).
- A regular file that does not verify (wrong or partial bytes): the store
  cannot tell a file that is still being written from one that is wrong, so it
  waits and looks again in the next round. If the target still does not verify
  when the rounds are used up, the temp is removed and the call raises
  `IntegrityError`; the target is left untouched.
- Not a regular file (a link, a directory, a FIFO or another special file):
  nobody is still writing one into a series, and waiting cannot make it verify.
  The temp is removed and the call raises `IntegrityError` at the first look,
  so the locks are not held for the rest of the 5 s. The name is refused from
  `lstat`, never opened, and left untouched. The store reads the name once more
  to decide this; if it is gone by then, the call waits as for any name that
  is gone again. Between the /code-review round and its verification such a
  name was looked at in all ten rounds (4.75 s with both locks held).
- It cannot be opened or read because of a `PermissionError` (a Windows sharing
  violation while the program that created it still holds it open; on POSIX a
  file this process may not read yet): the store waits and looks again. If that
  is still so when the rounds are used up, the call raises
  `PublicationUncertain` with the OS error as `__cause__`.
- The name is gone again: the store waits, and the next round makes the publish
  call again with the temp it kept. If a name still blocks the call and is gone
  again at the look when the rounds are used up, the call raises
  `PublicationUncertain` ("vanished before it could be verified").
- The wake-up from a wait comes late and the 5 s are used: what the look before
  that wait found may no longer be so, and it is not used. The name is looked
  at once more and that look decides as above: `created=False` for a target
  that verifies now, `IntegrityError` for one that still does not. No publish
  call is made after the 5 s, so a name that is gone at that look ends the call
  in `PublicationUncertain` ("vanished before it could be verified") with
  nothing stored. Between the /code-review round and its verification the look
  from before the wait decided: a target completed during that wait, or a name
  removed during it, gave `IntegrityError`.
- Any other failure to open or read it (an I/O error): `PublicationUncertain`
  at once, with the OS error as `__cause__`.

In each of these outcomes the target is left as it was found, and this call's
temp is removed at the end, not before. Until the /code-review round the temp
was removed first and the target looked at once, so a file that was half
written, still held open or gone again ended the call although the state would
have passed.

A target that was already there when the call began (step 3 of Write), and any
target in `read()`, is looked at once. No temp exists yet, so nothing of this
call is lost by answering at once. Such a target raises `IntegrityError` when it
does not verify, also when another program is still writing it, and the OS
error itself when it cannot be opened or read, as in child 1 (see Outcomes);
that includes `FileNotFoundError` when the name is gone between the existence
check and the open.

Why the waits stop at step 3. A name found after this call's own absence check
is known to be new, so it may well still be written. A target found at step 3
can be of any age: waiting on each one would hold both locks for 4.75 s in
every write that meets a damaged file, and a reader of that digest would get
`LockTimeout` where it now gets `IntegrityError`. The price is that the states
the rounds wait for are answered at once when they are met a moment earlier.
Measured in the child 3 verification with real threads and the real clock: on
the POSIX branch (10,000 calls against a writer outside the lock) 709 calls
raised `IntegrityError` at step 3, 173 of them for a file that its writer
completed within 0.3 s and 271 for one that it removed within 0.3 s, and 6
raised `FileNotFoundError` for a name that was removed between the existence
check and the open; on the simulated Windows branch (4,500 calls) 478 calls
raised `PermissionError` at step 3 for a file its writer still held open.
The caller still has the payload and nothing was changed, so calling again is
safe. Whether step 3 should wait as well was raised in the verification and is
not decided ("Child 3: verification of the fixes").

### Sync of an existing target

`created=False` says that the series is stored. On POSIX it is therefore
returned only after two fsyncs: of the existing file, through the read-only
descriptor that read and verified it (a target is never opened for writing), and
of the directory. This applies to a target that appeared during the publish, to
one found before the first attempt, and equally to one that was already there
when the call began. A writer outside the lock may have synced neither its file
nor the directory entry; until the /code-review round the call removed its own
fsynced temp and reported such a file as stored. If either fsync fails the call
raises `PublicationUncertain`; nothing is changed, and this call's temp, if
there is one, is removed. A target that does not verify is not fsynced, and
`read()` syncs nothing.

On Windows neither fsync is made. `os.fsync` is `FlushFileBuffers` there, which
needs a handle opened for writing, and the store never opens a target for
writing; and Windows has no directory fsync here. On Windows an existing target
is therefore reported on verification alone, as before, and its durability rests
on the program that wrote it. That `FlushFileBuffers` refuses a read-only handle
is taken from its documentation; it was not executed here.

### When os.link refuses

No POSIX `os.link` error is retried: the call is not made again because of the
error it raised. A filesystem that cannot make the hard
link (FAT, exFAT, some FUSE and network mounts) fails `os.link` with EPERM,
ENOTSUP, EOPNOTSUPP, ENOSYS, EMLINK or EXDEV (six names; five values on Linux,
where ENOTSUP and EOPNOTSUPP are the same number). EPERM does not always mean
the filesystem: `link(2)` also returns it when the kernel's protected-hardlinks
policy refuses (the temp file's owner is not the caller, as on some uid-mapped
mounts) and when the file is immutable or append-only. Every other
`PermissionError` from `os.link` is handled the same way: `link(2)` returns
EACCES when the directory may not be written or a directory of either path may
not be searched, and waiting does not change that. Until the /code-review round
EACCES was retried ten times over 4.75 s with the process lock and the sidecar
lock held.

The store cannot tell these causes apart, so the error message names the errno,
"os.link refused the hard link (EPERM), so nothing was published; the store does
not fall back to an overwriting call", and not a cause; the OS error is
`__cause__`. Nothing is overwritten in any of these cases. After confirming the
original temp and an absent target, the call removes the temp and raises the
typed `NoClobberUnsupported` at once; a target name that exists at that check is
looked at as above. One case has a second `os.link` call after a refused one:
the name found at that check does not verify yet and is gone again at the next
round. The publish call is then made again with the same temp, as for any name
that is gone again, within the same 10 rounds and 5 s; refused again with no
name in the way, it raises `NoClobberUnsupported` (run in the child 3
verification: EPERM and EACCES, two calls, one wait of 0.05 s). There is no
fallback to a call that can overwrite, and no
second primitive is tried: on POSIX a directory without hard links cannot hold
series files (see "Platform notes"). Windows is not affected: `os.rename` makes
no hard link,
and every `PermissionError` from it is retried. A filesystem that reports the
same condition with yet another error ends in `PublicationUncertain`; in no case
is an overwriting call made.

Durability is not weaker than before. The temp is fsynced and closed before the
publish call on both platforms. POSIX fsyncs the directory once, after the link
and the unlink of the temp name, where child 1 fsynced it after the rename, and
since the /code-review round it also syncs an existing target before
`created=False`. Windows has no directory fsync, as before. If a POSIX process
dies between the link and the unlink, the temp name stays next to the published
file; both names are then the same fsynced file (see "Non-guarantees and trust
boundaries").

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
| `IntegrityError` | Target untouched. Raised at once, with no temp made, for a target that was there before the call. For a target name that appeared during the publish it is raised at the first look when the name is not a regular file, and for a regular file only when the rounds are used up and the target still does not verify; this call's temp is then removed unless `cleanup_errors` says otherwise |
| `ReleaseError` | A read or an existing-target check (the idempotent skip, or a valid target that appeared during the publish) verified its result, and on POSIX synced it, but unlock, a close or the removal of this call's temp failed; no publication by this call; the result is not returned |
| Raw `OSError` while opening or reading a target that was there before the call (`read()`, or step 3 of Write), `FileNotFoundError` included when the name is gone between the existence check and the open | No temp and no publish call; the target is untouched |
| Raw `OSError` from `mkstemp`, the temp write, fsync or close | No publish call; the identity-matching temp is removed unless `cleanup_errors` says otherwise; a new sidecar may stay empty if its NUL initialization failed |
| Temp `StoreError`, or an `lstat` failure right after `mkstemp` | No publish call; the temp is kept, because its ownership is unproven; a new sidecar may stay empty if its NUL initialization failed |
| `PublishRetryExhausted` | Windows only: `os.rename` still raised `PermissionError` when the rounds were used up. Target absent at the final check; temp removed if `temp_removed`; `attempts` is the number of publish calls made |
| `NoClobberUnsupported` | POSIX only: `os.link` refused the hard link (a filesystem without hard links, an EPERM refusal for another reason, or EACCES; the message names the errno) while no target name exists. It is raised right after that call, with no wait and no retry of the error; the call is the first one unless a foreign name that was in the way after an earlier refusal is gone again ("When os.link refuses"). Nothing published and nothing overwritten; the original temp and an absent target were confirmed; the temp is removed unless `cleanup_errors` says otherwise. The digest's `.lock` stays |
| `PublicationUncertain` | Never overwrote a target; the target may be absent, foreign, or published without completed checks. Foreign includes a target that appeared during the publish and, when the rounds were used up or a wake-up came after the 5 s, had vanished again or still could not be opened; one that could not be read for another reason; and an existing target that verified but whose fsync or directory fsync failed (POSIX). Published without completed checks includes, on POSIX, a published file whose temp name could not be unlinked and is still a hard link to it. Do not blindly retry; a later `read()` verifies current bytes but not durability |
| `KeyboardInterrupt`, `SystemExit` | Propagated unwrapped after cleanup (identity-checked temp removal, unlock, a single close, process-lock release). Before the publish call, and in a wait between rounds, the owned temp is removed unless `cleanup_errors` says otherwise; during or after the publish call publication is unknown, so verify with `read()` |

Any raised exception may carry `cleanup_errors`, a tuple of cleanup failures.
Typed wrappers keep their trigger as `__cause__`. Only `Exception` is collected or
wrapped; asynchronous interrupts arriving between cleanup steps are best effort.

## Platform notes

- POSIX publishes with `os.link`, unlinks the temp name and then fsyncs the
  directory. A filesystem that rejects directory fsync (EINVAL) turns every
  publish, and every `created=False`, into `PublicationUncertain`. Files are
  created with mode 0600 by `mkstemp`.
- A POSIX directory without hard-link support cannot hold series files, and the
  store finds that out late. The constructor accepts such a directory: it checks
  that the path is an existing directory and probes nothing. Every write of a new
  digest then does all its work first: the sidecar is created and initialized,
  the payload is written to a temp file and fsynced, and only then does `os.link`
  fail and the call raise `NoClobberUnsupported`. The temp is removed, one
  `.lock` per attempted digest stays behind, and nothing is ever stored.
  Affected: FAT and exFAT volumes (USB sticks, SD cards) mounted on Linux or
  macOS, and FUSE or network mounts whose driver or server does not implement
  `link` (for example an SMB share without hard-link support). Not affected:
  Windows on any volume, because `os.rename` needs no hard link. Two remedies
  are possible and neither is implemented: a one-time probe when the store is
  constructed, or a rename that refuses an existing name and needs no hard link
  (`renameat2` with `RENAME_NOREPLACE` on Linux). Which of them, if either, is
  left for the recorder unit to decide. No such mount was available here; the
  behaviour was run with an injected `os.link` error only.
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
  succeeded. If the link reports `FileExistsError`, `PermissionError` or a
  no-hard-link error after it succeeded, the store verifies the file it just
  made, fsyncs it and the directory, removes the temp name and reports
  `created=False`; any other reported error is `PublicationUncertain`, and the
  published file stays.
- One `.lock` per digest persists. Dot-prefixed `.<digest>.*.tmp` files can remain
  after a kill or a cleanup failure; they are hidden only on POSIX and are visible
  on Windows, where a leading dot sets no hidden attribute and the store sets
  none. There is no automatic cleanup, retention, TTL or tombstone. The
  process-lock map grows by one entry per digest.
- On POSIX a process killed between `os.link` and the unlink of the temp name
  leaves that temp name as a second hard link to the published file, and it
  stays for good: the store never looks for such a name and never removes one.
  The published file is complete, and later calls work (`read()` returns it,
  `write()` returns `created=False`). The alias is a second way to the same
  bytes: whatever changes the file in place through the temp name changes the
  published file. `read()` and the existing-target check verify the content on
  every call, so such damage is detected as `IntegrityError`; it is not
  prevented and not repaired. Removing these names belongs to the retention
  unit (design Q14).
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
`core/quant/run_registry_series_files.py`, its test and this record, plus the
series-files section of `docs/compliance/FACTS.md` and the compliance baseline
(`docs/compliance/source-review.json`); no 01-20 policy row names the publish
call, so none changed. The /code-review round and its verification (child 3)
changed the same files for this unit. No 01-20 policy row names the retry
constants or the typed error either, and the stored file kinds, the leftovers
and the deletion order are as before, so again none changed. The module is
still detached: only its own test imports it.

## Verification

The first part is the child 1 record of 2026-11-10, kept as written (it names
`os.replace`, which the module no longer calls, and `ReplaceRetryExhausted`,
which is now `PublishRetryExhausted`). The child 2 records and the two child 3
records (the /code-review round and its verification) follow it; each is kept
as written when a later round adds to it.

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
  attempt; the six named no-hard-link errors (five distinct values on Linux,
  where ENOTSUP equals EOPNOTSUPP; one attempt, no wait, typed error, nothing
  left); every `PermissionError` retried on the Windows branch; a failed
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

### Child 2 review round (2026-11-11)

A review of the child 2 commit (`7fabb4a`) found no case in which the committed
module overwrites, removes or adopts a foreign target. It found two gaps in the
tests, one untyped error, one misleading message and five inexact statements in
the records. Each was reproduced before it was changed. The numbers in the
child 2 record above are kept as written; the corrections to its wording are
listed here.

- **Test gaps, no product defect.** Six scratch mutants passed all 53 tests.
  Three were in the no-hard-link window, where the tests created only a valid
  foreign target: no verification there, an invalid foreign file overwritten,
  and one deleted. Three acted only on the Windows branch: a truncating copy over
  the target at the check before an attempt, the same at exhaustion, and no
  verification at the check before an attempt. New tests: every kind of foreign
  target (valid, invalid, dangling symlink, directory) created inside a failing
  `os.link`, for each no-hard-link error; the Windows branch at its three checks
  and at retry exhaustion; and the source check now counts every `open`,
  `rename`, `link`, `unlink` and `mkstemp` attribute and refuses pathlib writers
  and the builtin `open()`.
- **One behaviour change.** A target that appeared during the publish and could
  not be opened or read made `write()` raise the bare `PermissionError` or
  `OSError`, where child 1 raised a typed error in that window. It was
  reproduced with a real mode-000 file in a process without
  `CAP_DAC_OVERRIDE`, and on the simulated Windows branch with the open
  refused. It is now `PublicationUncertain` with the OS error as `__cause__`.
  The state was safe before and is unchanged: target untouched, temp removed,
  lock released. A target present before the call still raises the OS error
  itself, in `write()` and in `read()`; a test now pins that too.
- **Message.** `NoClobberUnsupported` said "This filesystem cannot hard-link"
  for every EPERM. Two other causes were reproduced on ext4, which has hard
  links: through the store, the kernel's protected-hardlinks policy
  (`fs.protected_hardlinks=1`, the temp owned by another uid and unreadable to
  the caller, no `CAP_FOWNER`), and with `ln`, an immutable file. The message
  now names the errno and no cause. A uid-mapped mount itself was not
  available.
- **Record corrections.** A foreign target is found in four places, not three.
  The network-mount sentence now says which reported errors end in
  `created=False` (one probe: `FileExistsError`, EACCES, EPERM, ENOTSUP and
  EXDEV, each with no directory fsync) and which in `PublicationUncertain` (EIO,
  ETIMEDOUT; the published file stays). "The six no-hard-link errors" are six
  names and five values on Linux, and the test ran five cases. Child 2 also
  changed the FACTS section and the compliance baseline, which the Boundaries
  sentence omitted. The FACTS lock row listed all hard links as unsupported,
  although the POSIX publish makes one; it now says hard-link aliases made by
  others.

Checks after the fixes, on Linux (ext4) with Python 3.13 (`-B`), fresh temporary
directories only:

- `tests.run_registry_series_files_acceptance`: **59 tests** (53 before; six
  added, three changed), three runs of 1.662 s, 1.634 s and 1.671 s, exit 0
  each, and once more with `-W error::ResourceWarning` (1.763 s). Against the
  module as child 2 committed it, the same 59 tests give 9 errors (the two new
  tests of the untyped error) and 5 failures (the message assertions); the
  tests for the two gaps pass there, as they should on a module that does not
  overwrite.
- Combined run with the fold, the adoption checks and the seven other R3
  modules: **245 tests in 6.693 s, exit 0** (239 before this round; overlapping,
  not added together). `tests.runtime_syntax_acceptance` passed; the module and
  its test compiled on Python 3.11, 3.12 and 3.13 and
  `ast.parse(feature_version=(3, 10))` accepted them.
- Mutation run on scratch copies: **47 of 47 mutants killed**, each by at least
  one behavioural test and not only by the source check: the review's 34 (28 of
  them killed before this round, the six above not), three further variants of
  those six, and ten mutants of this round's two code changes. This run is
  separate from child 2's 26.

Still not executed locally: Windows, macOS, a filesystem without hard links and
a uid-mapped mount.

### Child 3: /code-review fixes (2026-11-11)

Roadmap ID ⑨-3a/series-files/3. Child 2 (⑨-3a/series-files/2) was closed when
pull request #100 merged, so this round and its verification below are a new
child and not more work under the closed ID.

A `/code-review` of pull request #100 at `e4b0772` (the child 2 commits merged
with main `7ddb568`) reported findings on this module. Four were accepted as
code changes and two as limits to state; each code finding was reproduced on
`e4b0772` with a scratch probe before anything was changed. The numbers of the
earlier rounds above are kept as written.

- **The temp was deleted before a single look (F1).** `_keep_existing` removed
  this call's verified temp first and then looked at the blocking target once.
  Reproduced three ways. POSIX, real clock: a foreign file was half written
  when `os.link` was refused and complete 0.3 s later; the call had raised
  `IntegrityError` after 0.03 s, with the unlink of the temp before the first
  open of the target. Windows branch (simulated): a valid foreign file whose
  first two opens were sharing violations gave `PublicationUncertain` after
  one open. POSIX: a name that blocked one publish call and was gone again
  gave `PublicationUncertain` with nothing stored. After the fix the same
  three probes return `created=False` (0.36 s, the temp kept meanwhile),
  `created=False` (waits 0.05 and 0.1 s) and `created=True` (second publish
  call after 0.05 s). The temp is now kept until the outcome is known, and the
  look is repeated within the existing 10 attempts and 5 s ("No-clobber
  publish"). What a target that never verifies ends in is unchanged
  (`IntegrityError`, target preserved); it now comes when the rounds are used
  up, up to 4.75 s later, with the lock held. A foreign target is never
  overwritten, repaired or removed in any branch.
- **An existing target was reported as stored without a sync (F4).**
  Reproduced on POSIX: a valid foreign target created inside `os.link`, with no
  fsync of the file or the directory, gave `(sha, False)` after the call had
  unlinked its own fsynced temp; no fsync of the target or the directory was
  made. A target present before the call was not synced either. Now the steps
  after the refused `os.link` are: fsync of the target through its read-only
  descriptor, fsync of the directory, unlink of the temp. The decision for a
  target found before the first attempt, and for one already there when the
  call began: the same sync applies ("Sync of an existing target"). Windows
  makes neither fsync and says so.
- **Names that had become false (F8).** `REPLACE_ATTEMPTS`, `REPLACE_BUDGET`,
  `_REPLACE_DELAYS` and `ReplaceRetryExhausted` are `PUBLISH_ATTEMPTS`,
  `PUBLISH_BUDGET`, `_PUBLISH_DELAYS` and `PublishRetryExhausted`, without
  aliases. `git grep` over the repository (the protected cache directory
  excluded) finds no importer of the module other than its own test, and the
  old names only in this record and in FACTS, both updated.
- **POSIX EACCES was retried for the whole budget (F9).** Reproduced with a
  real `link(2)` EACCES (the directory lost its write bit after `mkstemp`, in a
  process without `CAP_DAC_OVERRIDE`): ten `os.link` calls, nine waits, 4.77 s
  with both locks held, `ReplaceRetryExhausted`, and a second caller of the same
  digest got `LockTimeout` after its 2 s. Now: one call, no wait,
  `NoClobberUnsupported` naming EACCES. Before the change this record and the
  claimed contract were read for a sentence that requires the retry on POSIX.
  None was found: §5.7 and the bridge rule give the retry with the reason
  "OneDrive, Defender and the indexer open new files", the child 1 claim says
  "retry only os.replace PermissionError", and the child 2 text here listed
  "POSIX EACCES" as retried, which described that day's code. The change is
  recorded as a delta from §5.7 above.
- **Limits stated, no code change (F3, F5).** A POSIX directory without
  hard-link support fails every new write after the payload was written and
  fsynced ("Platform notes"). A process killed between `os.link` and the unlink
  of the temp name leaves a second hard link for good ("Non-guarantees and
  trust boundaries"). Both were run on the fixed module: an injected EPERM gave
  `NoClobberUnsupported` on each of two writes, with one fsynced temp written
  and removed per call and only the `.lock` left; a child killed with SIGKILL
  inside the temp's unlink left the temp name as a hard link (`st_nlink` 2),
  after which `read()` returned the array and `write()` returned
  `created=False`, and one byte changed through the alias made both raise
  `IntegrityError`.
- **Not changed.** A target that is already there when the call begins is still
  looked at once (step 3): a half-written one raises `IntegrityError` at once.
  The finding was about the target met while a temp is in hand.

Checks after the fixes, on Linux (ext4) with Python 3.13.17 (`-B`), fresh
temporary directories only, no network:

- `tests.run_registry_series_files_acceptance`: **67 tests** (59 before; three
  that would have become exact copies of Windows-branch tests were merged into
  them, one was rewritten, eleven were added), three runs of 1.976 s, 1.845 s
  and 1.753 s, exit 0 each, and once more with `-W error::ResourceWarning`
  (1.913 s). The retry tests now run on the Windows branch, the only one that
  retries a refused publish call. The foreign-target tests run on a fake clock
  and check the waits.
- Fail before, pass after. Against the old behaviour (the `e4b0772` module with
  only the four names changed) the same 67 tests give 50 failures and 10 errors
  in 18 test methods. Nine of the eleven new tests fail before the fix: five
  for F1, two for F4 and the one for F9 against that old behaviour, and the F8
  name test against `e4b0772` itself. The other two pass before and after and
  guard the limits of the fix: a target that does not verify is never fsynced,
  and the Windows branch fsyncs no target.
- Combined run with the fold, the adoption checks and the seven other R3
  modules: **255 tests in 10.129 s, exit 0** (245 before this round;
  overlapping, not added together). `tests.runtime_syntax_acceptance` passed;
  the module and its test compiled on Python 3.11.17, 3.12.3 and 3.13.17 and
  `ast.parse(feature_version=(3, 10))` accepted them.
- Mutation run on scratch copies: **76 of 76 mutants killed**, each by at least
  one behavioural test and not only by the source check. 33 attack the
  no-clobber guarantee itself with the anchors of the earlier rounds moved to
  the new code: the publish call swapped for `os.replace` or POSIX `os.rename`,
  an overwriting or deleting call at each place a blocking target is met or
  given up on, and the verification dropped at each of those places and at
  step 3. The others are 3 for the fsyncs of a fresh publish, 16 for F1, 12
  for F4, 9 for F9 and 3 for the budget values. This run is separate from the
  47 and the 26 above.
- Real-thread probe, scratch only: a second thread creates the target with an
  exclusive create while `write()` runs and writes it in two halves, 20,000
  fresh directories per run, two runs per module with different delays. No
  foreign file was overwritten by either module (0 of 40,000 each). With the
  fixed module 3 and 6 calls met the half-written file during the publish,
  waited and returned `created=False`; 41 and 166 calls met it at step 3 and
  raised `IntegrityError` at once, as before. A count of zero is not a proof.
- The source check additionally counts the open flags: `O_RDWR` three times
  and `O_CREAT` once (the sidecar), and no `O_WRONLY`, `O_TRUNC`, `O_APPEND`
  or `O_EXCL`, so no target is opened for writing.

Still not executed locally: Windows (real `os.rename`, `msvcrt`, and
`os.fsync` on a read-only handle), macOS, a filesystem without hard links, a
uid-mapped mount and a real power loss. The first real Windows execution is the
Runtime CI matrix.

### Child 3: verification of the fixes (2026-11-11)

Roadmap ID ⑨-3a/series-files/3, the same child as the round above. A
verification pass over the /code-review commit (`51bd45c`) found no case in
which the module overwrites, removes or adopts a foreign target, and no false
success. It reported six findings on this unit and one on the adoption checks
(recorded in `ADOPTION_STRATEGY_CHECKS_2026-11-10.md`). Each was reproduced on
`51bd45c` before anything was changed. Two became code changes, one added
tests, two corrected records, and one was left as it is, with the reason given.
The numbers of the rounds above are kept as written.

- **A late wake-up let a stale look decide (code).** When the sleep itself
  carried the elapsed time past 5 s, the rounds ended on the result of the look
  made before that sleep, and the look at exhaustion was skipped. Reproduced
  with a fake clock: a half-written foreign target completed during the ninth
  wait, with a wake-up 0.3 s late, gave `IntegrityError` although the target
  was a valid series when the call ended (last look at 3.95 s, end at 5.05 s);
  an invalid target removed during that wait gave `IntegrityError` for a name
  that was absent; with looks of 28 ms a wake-up 1 ms late was enough. On time,
  the same cases gave `created=False` and `created=True`. The `e4b0772` code
  always looked again at exhaustion, so the corner came in with the
  /code-review round. Nothing was overwritten and no success was reported.
  Now the result from before the wait is set aside and the name is looked at
  once more. The same three probes return `created=False`,
  `PublicationUncertain` ("vanished", nothing stored, no publish call after the
  5 s) and `created=False`.
- **A name that is not a regular file was waited on for the whole budget
  (code).** The verification asked whether the lock hold is wanted for states
  that cannot pass. For a link, a directory or a FIFO it is not: nobody is
  still writing one, and `e4b0772` answered at once. Reproduced with the real
  clock: each of the three took 4.755 or 4.756 s before `IntegrityError`, with
  both locks held, and a reader of the same digest that started 0.3 s in got
  `LockTimeout` after 2.0 s. Now: 0.008 s, 0.004 s and 0.003 s, and the reader
  gets `IntegrityError`. Not changed, because it is what keeping the temp for
  a file that may still be written costs: a regular file that never verifies
  holds both locks for 4.76 s (ten opens), and a 64 MiB file with one wrong
  byte for 4.81 s (read and hashed in each of eight rounds); the reader got
  `LockTimeout` after 2.0 s in both.
- **Three test gaps (tests only).** Of the verification's 53 scratch mutants,
  48 were killed by behavioural tests, 3 by the source check only and 2
  survived. (a) A store that unlinked an existing target just before the
  publish call was caught by the source check only, because every test
  created the foreign file inside the publish call. A new test creates it
  right after the store's last absence check, on both branches and for every
  kind of foreign name. (b) A store that adopted a blocking target of the
  temp's size without checking its content survived: no mid-publish fixture
  had that size and wrong bytes. `FOREIGN` now has one (the payload with one
  data byte flipped), and it runs through every foreign-target test. (c) The
  late wake-up with a blocking target had no test; see the first item.
- **Sentences that were too absolute (records and docstrings; no code).**
  "POSIX `os.link` errors are never retried", "never repeats a refused publish
  call" and "raised at once" do not hold in one corner: `os.link` is refused
  (EPERM or EACCES) while a foreign file that does not verify sits on the
  target name, and that name is gone at the next round. Probe on `51bd45c`:
  two `os.link` calls, one wait of 0.05 s, then `NoClobberUnsupported`. The
  second call is the rule for a name that is gone again and stays inside the
  10 rounds and 5 s, so the behaviour is kept; the sentences now say it, here,
  in FACTS and in the module's docstrings, and a new test pins the two calls.
  FACTS also said the temp is checked again "at exhaustion"; that is done only
  after a refused publish call (and, since this round, after a late wake-up).
  Probe: a temp removed during the tenth look gives `IntegrityError` for the
  target, not `PublicationUncertain`.
- **Step 3 still answers at once (not changed).** The states the rounds wait
  for are still answered at once when the target is already there when the
  call begins. In the real-thread races below: 709 `IntegrityError` and 6
  `FileNotFoundError` at step 3 on the POSIX branch (173 of the 709 for a file
  completed within 0.3 s, 271 for one removed within 0.3 s), and 478
  `PermissionError` at step 3 on the simulated Windows branch, for a file its
  writer still held open. The reason for stopping the waits there is in
  "No-clobber publish": a target found at step 3 can be of any age, and
  waiting on each one would hold both locks for 4.75 s in every write that
  meets a damaged file, which is the hold the second item removes where it
  can. The /code-review finding was about a temp in hand, and here none
  exists: the caller still has the payload and nothing was changed. If step 3
  is to wait as well, the change is: on `IntegrityError`, `PermissionError` or
  `FileNotFoundError` there, look again within the same 10 rounds and 5 s,
  and go on to `mkstemp` and the publish when the name is gone. That is a
  decision about the contract child 1 pinned (a raw `OSError` and an immediate
  `IntegrityError` at step 3), and it is left open here.
- **Roadmap ID.** The /code-review commit was titled with the IDs of child 2
  and of ⑨-4/2/b, which the ledger has as finished at `1a8b29f`. The round and
  this verification are ⑨-3a/series-files/3; the headings above and the FACTS
  rows now carry it.

Checks after the changes, on Linux (ext4) with Python 3.13.17 (`-B`), fresh
temporary directories only, no network:

- `tests.run_registry_series_files_acceptance`: **72 tests** (67 before; five
  added, and the same-size fixture and the non-regular names added to
  existing ones), three runs of 1.907 s, 1.826 s and 1.882 s, exit 0 each, and
  once more with `-W error::ResourceWarning` (1.671 s).
- Fail before, pass after. Against the `51bd45c` module the same 72 tests give
  26 failures and 4 errors in 5 test methods. The two tests for the code
  changes fail there in every sub-case (the late wake-up: 6; a name that
  is not a regular file: 6), and two existing foreign-target tests and the new
  gap test fail in their link and directory sub-cases, which now expect no
  wait. The rest of the new tests pass before and after: the gap test in its
  regular-file sub-cases, the test of a name that is gone right after a failed
  look, and the pin of the second `os.link` call. With only one of the two
  code changes undone, the test of that change fails (mutants V1a and V4a
  below).
- Combined run with the fold, the adoption checks and the seven other R3
  modules: **260 tests in 6.370 s, exit 0** (255 before this round;
  overlapping, not added together). `tests.runtime_syntax_acceptance` passed;
  the module and its test compiled on Python 3.11.17, 3.12.3 and 3.13.17 and
  `ast.parse(feature_version=(3, 10))` accepted them.
- Mutation run on scratch copies: **70 of 70 mutants killed**, each by at
  least one behavioural test and not only by the source check: the
  verification's 53, re-anchored to the new code (the 3 and the 2 above are
  now killed by the gap test, the same-size fixture and the late wake-up
  test), and 17 for this round's two code changes (8 for the late wake-up, 9
  for the names that are not regular files, among them a publish call after
  the budget, a removed link or directory and a stale look kept). This run is
  separate from the 76, the 47 and the 26 above.
- Model fuzz, fake clock, scratch only: 80,000 schedules in which a foreign
  actor creates, completes, removes or replaces the target at the points where
  the store looks at or touches the name. On each branch 20,000 schedules keep
  that actor quiet during the last sync and cleanup steps, so the end state is
  checked exactly, and 20,000 let it act at every step. No store-made change
  to a foreign file and no unverified `created=False` in any schedule. Four of
  the mutants above, run through the same model on the POSIX branch, were each
  reported as violations.
- Real-thread races, real clock, scratch only: POSIX branch 10,000 calls (4
  runs of 2,500 fresh directories), simulated Windows branch 4,500 calls (3
  runs of 1,500; `os.rename` as `renameat2` with `RENAME_NOREPLACE`, and the
  open of a file its writer holds refused). In no call was a foreign file
  changed or removed by the store, `created=True` returned while a foreign
  file held the name, or `created=False` returned without a valid foreign
  file. 402 POSIX and 1,285 Windows-branch calls met a foreign file during the
  publish and returned `created=False`. A count of zero is not a proof.

Still not executed locally: Windows (real `os.rename` onto a directory or a
link, `msvcrt`, `os.fsync` on a read-only handle), macOS, a filesystem without
hard links, a uid-mapped mount and a real power loss. The new tests run both
branches on every platform; their first real Windows execution is the Runtime
CI matrix.

Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
