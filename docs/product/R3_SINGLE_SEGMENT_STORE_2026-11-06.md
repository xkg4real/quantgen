# Detached R3 single-segment store

This is bounded child **⑨-3a/store/1** of the approved R3 implementation.
It adds explicit-path storage around the separately reviewed event codec. It
is not connected to the existing Lab, actual research ledger, counts, verdicts,
provider data or owner-ruling effects. The R3 parent and full T-RUNREG-02 remain
incomplete.

The contract is the recorded R3 revision 2 design, sections 5.2 and 9.1. The
current implementation deliberately stops before rollover, recovery, prefix
caching, full lifecycle/payload validation, human events and recorder integration.
Those omissions must not be interpreted as an operational registry approval.

## Behavior and limits

`SingleSegmentStore` requires an absolute `.jsonl` file path in an existing,
trusted local directory. It has no default macro directory, configuration or
environment lookup, provider call or recorded-time clock. Every event supplies
its own timestamp. Elapsed monotonic time bounds only lock acquisition; filesystem
operations, decoding, append and fsync are outside that timeout.

Each read and append verifies the whole segment through the existing codec.
A process lock shared by canonical path and an OS sidecar lock serialize
cooperating access. The caller may choose a combined lock wait from 0 to 10 seconds;
the default is 2. Reads do not create absent files and refuse an existing segment
without its sidecar. Creating a store object creates neither file nor directory.

Only STARTED, PROGRESS, FINGERPRINT, SHADOW and FINISHED envelopes are supported.
Duplicate STARTED or FINISHED for the same run ID is refused under the lock.
This does not establish complete event ordering, payload semantics, identity
provenance or human authority. Unsupported human and segment events are refused.

Appending writes canonical UTF-8 JSON plus LF in binary append mode, then flushes
and fsyncs. A partial write or fsync failure is an uncertain outcome: the operation
does not retry, truncate or repair. A later read verifies the bytes currently
present; it cannot prove durability at the time of the failed fsync.

The single-segment limit interprets 32 MB as 32,000,000 bytes. Preflight refuses
crossing that limit, which is stricter than the full design's later-append
rollover. There is no rotation or owner-approved recovery command in this child.

The supplied path is not a security sandbox. Final symlinks are refused;
hard-link aliases, hostile directory changes, external replacement and sync
folders are unsupported. Cooperative writers must use the same canonical path
and sidecar. MD5 checks consistency, not authenticity; without an independent
tail anchor a valid prefix cannot reveal removal of its complete suffix.

## Verification and remaining work

The guarded combined acceptance run passed **33 tests in 0.401 seconds, exit 0**:
16 new store tests plus the existing 17 codec tests. It covered literal golden
bytes/reopen, nonmutation, malformed/torn/reformatted/reordered/interior-drop
refusal, duplicate races, five threads appending ten events each, a real competing
process OS lock, bounded timeouts, lock release and uncertain failed writes.

An independent implementation review passed **8 private overlapping probes in
0.141 seconds, exit 0**, including actual partial writes, fsync/unlock failures,
path-alias coordination and input snapshot behavior. These are not added to the
33 acceptance count. Source and test hashes stayed fixed through review.
Linux evidence for the OS lock does not prove Windows byte-lock behavior.

All local checks used isolated temporary synthetic files with network and
protected-data access denied and dotenv disabled. The child-process probe also
installs a guard because a new interpreter does not inherit Python audit hooks.
The Runtime workflow adds the new source/test triggers and acceptance module;
every earlier test-module count and timeout budget is preserved. Final-head
Windows/Ubuntu Runtime and Compliance results must pass before merge.

Only this detached implementation is covered. Actual
user Windows acceptance, real ledgers, live APIs/providers, legal/license,
pilot and frozen-research evidence remain separate. No preregistration,
holdout, verdict criterion or existing owner approval rule is changed.
Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
