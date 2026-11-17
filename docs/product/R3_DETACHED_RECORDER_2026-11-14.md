# R3 detached lifecycle recorder — 2026-11-14

Completion unit: **⑨-3a/recorder/1/lifecycle only**. The recorder parent and R3
remain incomplete. This module is not connected to Strategy Lab or either UI.

The owner approved headless R3 work before Step 10 integration in P4 and supplied
the seven source-identity paths in C-Q12. Owner ruling 9 permits only
`PNL_COMPUTED` progress inside `run_family`; earlier stages remain in memory.
See [owner rulings](../nautilus_bridge/OWNER_RULINGS_LOG.md). This child does not
modify the seven identified strategy/research files or consume their contents.

## Implemented contract

`core/quant/run_registry_recorder.py` supplies `DetachedRecorder`. A caller must
provide two `SingleSegmentStore` instances for the same trusted absolute path,
an aware UTC clock, a monotonic clock, a token source, an outage callback and a
writer identity. Construction does not read a clock, discover configuration or
create a file. Each instance belongs to one run and one calling thread.

| Hook | Behavior |
| --- | --- |
| `started(metadata)` | Accepts the complete supplied STARTED field set, planned key shape and the exact seven Q12 paths with LF/raw digests. Appends STARTED with its own envelope. |
| `advance(stage)` | Remembers an allowed stage without writing progress. |
| `pnl_computed(payload)` | Writes the single in-run PNL_COMPUTED progress and supplied registered keys. |
| `after_run(payload, displayed=..., error=...)` | Writes closing progress after calculation or failure, including the display state. |
| `fingerprint(payload)` / `shadow(payload)` | Writes caller-supplied post-run events only after closing progress; does not compute either payload. |
| `finish(...)` | Attempts a missing closing progress and FINISHED. Distinguishes completion, pre/post-statistics failure and abort. Repeated terminal calls are no-ops. |

Ordinary hook exceptions disable further recording and call the supplied outage
callback once. A callback failure is exposed separately in `outage_error`.
`KeyboardInterrupt`/`SystemExit` are not swallowed. Hook boolean results are
diagnostics: an adapter must never use them to decide a research verdict or to
skip calculation. Calling `finish` from `finally` preserves an ordinary original
exception. Constructor failures must also be contained by a future adapter.

A colliding STARTED ID draws another token, up to five attempts. All attempts
share one two-second lock-acquisition budget. A candidate ID is retained only
after a successful append or an append whose outcome is uncertain; a pre-write
failure does not assign someone else's colliding ID to an outage. An uncertain
write is never retried. The ten-second post-run budget is shared by both appends
when `finish` must add closing progress first.

`SingleSegmentStore.append(..., lock_timeout=remaining)` now accepts a smaller
per-call budget. This is the necessary extension to the already completed store
child: retries must not reset its full default wait. Omitting the keyword keeps
the previous behavior and the instance's budget is never changed. These limits
bound lock acquisition, **not** filesystem I/O, hashing, callbacks or fsync.

Inputs are copied through the existing codec before storage. The caller's
payload and existing verdict are unchanged; nonfinite values use codec markers.
No implicit repair, truncation, rotation or retry after uncertainty is added.

## Validation and limits

Local synthetic tests: **47 recorder + 80 existing store/codec/fold = 127 PASS**.
They use only temporary stores and supplied metadata. Cases include success,
failure before/after statistics, display followed by rendering failure, abort,
the owner's no-early-progress rule, original exception preservation, collisions,
shared lock budgets, real temporary-store fsync failure, corrupt-chain refusal,
outage callback failure, backward clocks and phase/envelope violations. The
runtime smoke workflow includes the recorder suite for Linux/Windows CI.
Local tests alone are not owner-PC or production-path validation.

Remaining work includes the Lab adapter and source/metadata collection,
scientific payload semantic validation, durable outage files and UI notices,
sync-folder screening, ledger linkage, fingerprint/shadow computation, rotation,
recovery and the R3 user interface. Callback errors are bounded to 500 characters
but are **not** a secret/PII redaction system. Supplied source hashes are metadata,
not proof that this module collected or authenticated the source. The integration
must enforce those contracts before production use. It must also implement the
disabled/no-op path and safe construction failure handling.

No real ledger, protected cache, provider API, frozen study or owner-PC resource
was accessed by these tests. Windows E and Pilot evidence remain separate; this
change does not close Step 10, authorize F/main research integration or approve
commercial publication. Existing legal, licensing and operating-evidence gaps
remain open.

## Reproduce with synthetic data

```text
python -B -m unittest tests.run_registry_recorder_acceptance tests.run_registry_store_acceptance tests.run_registry_codec_acceptance tests.run_registry_fold_acceptance -q
```

Source-review inventory provenance: the unchanged entries come from main
`e01e1526be28b8a6374583ce3802510e07819598`, whose full consistency CI passed.
Only this change's reviewed paths are overlaid on that manifest and on that Git
tree. This is not a full scan of the partial local checkout. The target PR's
ordinary full consistency CI must validate the resulting tree before merge.
