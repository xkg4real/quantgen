# PR-A bounded status source — ⑫-1/a

Base: main `950f25edd196189eac50a2ca39d5ff952656f353`.

The recorded QA file contains 749 PASS / 0 FAIL / 121 NOT_RUN, total 870.
Its run time and commit are absent; generation time is never substituted for them.
README's 743/864 table is retained as dated 2026-10-23 history, while a generated
current recorded-evidence block supplies the latest file aggregate. Stale unsigned-calendar
wording is corrected to signed MANIFEST metadata (17 rows, set 1.0.0).

`python -m tools.status.snapshot --check` verifies the generated JSON, README block,
explicit input hashes and declared policy. A source change or contradictory summary fails.
`python -m unittest tests.status_snapshot_acceptance -v`: 8/8 PASS (synthetic fixtures).
The source QA file is unchanged; this is not a rerun of its 870 tests.

Scope remains bounded: formal gate NOT_FROZEN is the README declaration, protected
package verification is NOT_INSPECTED; paper studies and actual ledgers NOT_INSPECTED;
data readiness NOT_VERIFIED; public release NOT_APPROVED. No global readiness Boolean.
Full PR-A's protected evidence adapters and PR-F CI/Windows packaging are not implemented.
The tool does not import runtime configuration, traverse directories or use the network.

Rollback: revert this branch's commit; no models, signatures, gates, ledgers or source QA
were changed. Regeneration is explicit (`--write`), never performed by the UI.
