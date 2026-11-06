# Recorded status display correction

The Native and Flet System pages previously printed public distribution
`NOT_APPROVED` even though the verified project snapshot already recorded
`COMMERCIAL`, `OWNER_APPROVED`, and the 2026-10-30 owner decision. The native
page also printed the fixed summary after snapshot verification failed.

Both pages now use one presentation function on the existing verified snapshot.
The owner decision is explicitly separate from regulatory endorsement, technical
readiness and actual public release. The record has no publication receipt;
the UI therefore says actual public release is not established by this evidence.
Data readiness, formal-gate status/verification and frozen-study status retain
their original codes. Test counts, calendar metadata and dates remain literal.
Recorded test counts are not described as a fresh execution.

Verification still uses the existing snapshot verifier and schema. Missing,
source-inconsistent, tampered or malformed JSON/YAML evidence displays an unavailable message
without an inferred approval summary. The correction does not change approval
rules, research adapters, official verdicts, orders, licensing or release gates.
It is a bounded child of ⑫-1, not completion of the whole status-source roadmap.

The shared presentation supplies authored EN/KO variants directly to both UIs;
original snapshot dictionaries are unchanged. Existing catalog entries remain
for compatibility. A3 critical-content protection remains on the System panel.

Focused isolated validation passed 21 tests: 11 display cases and the existing
10 snapshot-verification tests. The independent review found malformed YAML
could escape the UI exception boundary; both callers now handle that existing
verification failure. Snapshot generation/verification and its original tests
are unchanged. The runtime workflow includes both display/snapshot modules.
Five-module isolated integration passed 43 tests (72.088 seconds, exit 0).
All 20 policies were reviewed; claims policy, FACTS and RELEASE_GAPS received
minimal updates. Source consistency passed for all 20 policies; publication remains BLOCKED.
Exact-head CI/PR receipts follow.
The existing verifier detects source/snapshot inconsistency, not expiry based
on wall-clock age.

No real provider/API call, user Windows/DPI/assistive-technology check, public
release/deployment, legal/license, pilot or frozen-research proof is established.
Optional additional GPT/Gemini specification review remains NOT_PERFORMED.

Five actual native System captures (EN/KO, 1360/1000px, plus 1560px help dock)
show all 11 status lines and their owner/readiness/publication distinctions.
The isolated render diagnostic passed once; a separate baseline comparison
passed once. At 1000px, both pre-change67a8838 and statusb423f0b have EN58px /
KO44px horizontal overflow from the inactive Rules tab. This existing narrow
System limitation remains; the new status panel did not increase it. Wide
views have zero horizontal overflow, vertical scrolling works and A3 help
keeps critical notices uncovered. These runs use verified temporary synthetic
evidence and unchanged raw dictionaries/files, not real-user PC evidence.
The A3 correction was integrated at a99b16b; make_quant matches af782be and
make_system matches b423f0b by AST comparison.
Post-merge isolated status/snapshot/A3 layout validation passed26 tests
(65.732s, exit0); earlier overlapping counts are not added.

The first PR78 runtime run42182875822 at3726dd6 failed the bounded-source
step on all four installed environments. Its older research-home failure test
expected the superseded exact heading and injected raw error. Product behavior
was unchanged: the shared renderer intentionally supplies a bilingual generic
unavailable/no-approval message. That test now exercises KO/EN/KO and rejects
raw error text containing fake READY/OWNER_APPROVED/counts, as well as normal
status codes, recorded counts and evidence dates on the failure path. The
original one-test failure is preserved; research-home, status-display, snapshot
and Flet runtime validation then passed31 tests (3.944s, exit0). Corrected
exact-head Windows/Ubuntu CI is still required.
