# R3 detached outage writer — 2026-11-14

Scope: **⑨-3a/recorder/1/outage only**, following the
[lifecycle child](R3_DETACHED_RECORDER_2026-11-14.md). The recorder parent and R3
remain incomplete. Owner P4 permits headless work before Step 10 integration;
ENG-16 in design 5.2 requires an outage file outside the registry chain. This
module does not connect the recorder to Lab or either UI.

`OutageWriter(absolute_path, lock_timeout=2.0)` is a callable suitable for the
lifecycle recorder's `outage_sink`. The path must end in `unrecorded.jsonl` and
its trusted local parent must already exist. No default directory, configuration,
environment, wall clock, provider or real ledger is consulted. The path property
cannot be reassigned. Sync-folder screening still belongs to a future adapter.

The supplied record contains `recorded_utc`, `run_id`, `family_id`,
`symbols_typed`, `stage` and `error` (`hook`, `type`, `message`). An unavailable
time or identity stays `null`; the writer does not invent evidence. The error
message limit is 500 characters and is **not** a secret/PII redaction filter.
Other fields are refused before a file is created. Valid input is encoded as one
sorted, compact UTF-8 JSON line with LF, flushed and fsynced after append.

A process lock shared by instances for the same canonical path serialises
cooperating threads. Its 0..2 second acquisition budget is shared with the lock
map acquisition. As required by ENG-16, there is **no OS sidecar lock**. This does
not support concurrent processes, hostile directory replacement or hard-link
aliases. The budget does not bound encoding, filesystem I/O or fsync. This is
not a filesystem sandbox, encryption or an owner-PC latency guarantee.

An existing non-LF tail, final symlink, directory or FIFO is refused without
repair. The boundary check does not validate older JSON records or provide a
tamper-evident chain. No reader, count computation, retention, rotation or
deletion is added. Once an append is attempted, write/flush/fsync/close failures
raise `OutageWriteUncertain`; no retry or truncation occurs. The lifecycle
recorder catches an ordinary callback failure and exposes `outage_error`, leaving
the existing calculation exception and verdict alone. `BaseException` still
propagates. A future UI must display the failed-outage notice distinctly.

## Evidence and reproduction

Local Linux synthetic tests: **27 outage tests PASS**. Combined with the prior
47 lifecycle and 80 store/codec/fold cases: **154 tests PASS**. These totals
overlap and must not be added together. Tests use temporary files only, including
two-instance thread contention, real fsync calls, injected fsync failure, short
writes, an unchanged torn tail, lock refusal, unknown time, and lifecycle callback
integration preserving an original exception. The runtime smoke matrix includes
this suite. The FIFO fixture is POSIX-only; the symlink case reports a skip on a
host without symlink permission. CI skips must not be relabelled as passes.

```text
python -B -m unittest tests.run_registry_outage_acceptance tests.run_registry_recorder_acceptance tests.run_registry_store_acceptance tests.run_registry_codec_acceptance tests.run_registry_fold_acceptance -q
```

The full PR's CI and remote readback remain the merge gate. The source-review
manifest uses CI-verified base `ed92dc90b2b32fd6bd2a9254e7a568e45e3e553e`
(document consistency PASS/749 sources), overlaid with this exact tree's changes.
This is not a full local scan of a partial checkout.

Production storage selection, source/metadata collection, scientific payload
checks, outage reporting/UI notice, sync-folder screening, ledger linkage,
fingerprint/shadow computation, registry recovery/rotation and Lab connection
remain open. No actual account, provider, frozen study, protected cache or owner
PC was used. Step 10, F, publication, legal and licensing evidence are separate.
