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
minimal updates. Source consistency and exact-head CI/PR receipts follow.
The existing verifier detects source/snapshot inconsistency, not expiry based
on wall-clock age.

No real provider/API call, user Windows/DPI/assistive-technology check, public
release/deployment, legal/license, pilot or frozen-research proof is established.
Optional additional GPT/Gemini specification review remains NOT_PERFORMED.
