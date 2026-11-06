# Detached R3 event codec and LAB IDs

This is bounded child **⑨-3a/codec/1** of the approved R3 implementation. It
provides deterministic primitives for a future registry without connecting to
the existing Lab, research ledger, cost keys, counts, verdicts or owner rulings.
It does not complete R3, its first storage step, or T-RUNREG-02/09.

The implementation follows the envelope and byte conventions in sections
5.2–5.5 of the [recorded R3 design](https://github.com/xkg4real/quantgen/blob/fa280591b9915b213a00e231a55bbe8d33b0d9d7/docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md).
The later R3 implementation approval does not remove the current protections
around actual ledgers, frozen research, preregistration, holdout or criteria.

## Implemented boundary

[`core/quant/run_registry_codec.py`](../../core/quant/run_registry_codec.py)
accepts explicitly supplied objects and bytes. It has no storage, configuration,
provider access, wall clock, default randomness or automatic recovery.

- `validate_envelope` checks schema, event names, allowed top-level fields and
  basic identity types. Event-specific payload fields are optional at this layer:
  complete request/result semantics, event ordering and human authority are not
  validated. The design does not name segment payload keys, so SEGMENT_START
  supports only an envelope here.
- `encode_event_line` copies JSON values, replaces nonfinite floats with null,
  records deterministic RFC 6901 JSON Pointer paths, and emits sorted compact
  UTF-8 JSON followed by one LF. Existing markers are structurally checked
  against null; they do not prove a value's historical origin. Original strings
  are preserved; this is not a privacy filter or redaction feature.
- `row_md5` excludes both chain fields. `prev_row_md5` hashes the exact supplied
  preceding line, including LF. `decode_event_line` refuses duplicate JSON keys,
  malformed encoding, noncanonical bytes, invalid hashes and incomplete lines.
- `verify_event_lines` checks linkage only among supplied lines and an optional
  supplied predecessor. MD5 provides byte-consistency checks, not authentication.
  A valid complete prefix cannot reveal removal of its final records without an
  independent tail anchor. No file is repaired or implicitly trusted.
- `make_run_id` requires an explicit aware UTC datetime and injected token
  callback, called once. It validates the ASCII LAB format, calendar instant,
  family bounds and eight lowercase hex characters. It provides no entropy
  guarantee, collision reservation or retry protocol. The callback's external
  behavior is the caller's responsibility.

## Verification

[`tests/run_registry_codec_acceptance.py`](../../tests/run_registry_codec_acceptance.py)
passed **17 synthetic tests in 0.010 seconds, exit 0** using guarded execution:
network denied, dotenv disabled, protected payload access denied, and temporary
mutable state. Tests include independent literal JSON/MD5 fixtures, exact LF
linkage, malformed and duplicate JSON, UTF-8 refusal, nonfinite pointer escaping,
input preservation, altered/reordered/dropped interior records and the explicitly
undetectable consistent suffix case. ID cases cover ASCII bounds, calendar dates
and injected time/token behavior. Oversized integer conversion failures are
reported without changing the interpreter's conversion limit.

An independent implementation review found no blocking issue, and **nine private
synthetic probes passed in 0.010 seconds, exit 0**. These overlap the 17 acceptance
tests and are not summed. An initially incorrect expected pointer sort order in
the private probe was corrected without changing product source; that failed
probe remains in the private evidence history.

The Runtime workflow adds this module to the existing bounded fixture command
and adds its source/test triggers. Every pre-existing test command remains.
Exact-head Windows/Ubuntu Runtime and Compliance results belong to the PR and
must be successful before merge. Local synthetic success is not a claim of
physical Windows acceptance or a completed registry.

## Remaining work and evidence

Storage locking/read-verify-append, duplicate lifecycle refusal, fsync, rollover,
owner-approved recovery, cached-prefix verification, canonical panel generation,
writer-compatible keys, Lab hooks, human ruling validation, counts and reports
remain separate. No actual ledger, protected cache, live provider/API, frozen
study or holdout was read or run for this child. Full T-RUNREG-02/09 and the R3
parent remain open. Legal/license, pilot, physical Windows/DPI/AT and actual
publication/deployment evidence remain separate. Publication readiness remains
BLOCKED; optional additional GPT/Gemini specification review is NOT_PERFORMED.
