# O11 A2 — pilot-1 configuration registration only

Owner decision received 2026-10-30. This is an addendum to revision 6's O11,
not a change to gate thresholds, the frozen row-set key or the ordinary runner.

## Scope and result

The owner's Windows PC may initialize missing/empty E1 with the twelve approved
pilot-1 configurations **before reading any price or risk-free series**. Each
configuration uses SPY, US cost 50 bp, the 2004-12-01–2026-09-25 span and
`rule × lookback × step = (sma, tsmom) × (126, 210, 252) × (21, 42)`.
The normal runner's configuration IDs are reused. No strategy, engine, gate,
stored card, frozen study or C3 ledger is executed/read by registration.

Initial `family_n_raw=12`; `n_trials=12+U`, with `0 <= U <= 24`. For the current
documented 24 US/KRX study configurations, the temporary-ledger test yields
`U=24`, `n_trials=36`. This is a trial-count result, not a performance result.

Successful output is **REGISTERED_ONLY**, never PASS or CARD_WRITTEN. The tool
does not write either `owner_confirmed` or the registration table. Owner Windows
registration, a reviewed host fingerprint, independent review, Step 7A and an
actual of-record pilot still need their own evidence. Do not count the cloud
tests as Windows pilot acceptance or as cumulative research-main merge approval.

## Owner Windows procedure (not executed by cloud automation)

Use the reviewed, committed research checkout and its existing interpreter and
directory convention. Stop all other QUANTGEN research writers first. Do not
remove or reset an existing ledger to make this command pass.

```powershell
python -B -m tools.nautilus.register_e1 --owner-windows --table docs\nautilus_bridge\registration\pilot1_E1_spy.json
```

Owner mode accepts no output/ledger/repository override. It checks Windows and
a clean anchored repository, uses `config.macro_dir()/ledgers/E1.jsonl`, and
writes an atomic receipt under `docs/nautilus_bridge/runs/A2-E1-<table-prefix>.json`.
The application keeps its existing configuration loading convention; cloud
tests disable dotenv loading only inside the isolated test process.

Inspect the receipt's 12 IDs, verified ledger hash, source anchor, table hash,
host fingerprint and four trial counts. Keep this host/ledger receipt private.
Then follow the existing reviewed fingerprint / owner-confirmed procedure;
registration alone is not permission to run the pilot. The normal runner's
600-second ledger freshness guard remains in force after the append.

## Retry and refusal behavior

- One durable intent is saved before the first row. Same-table OS locking is
  shared with the normal runner; each append also uses the existing ledger lock.
- After interruption, rerunning the same source/table/host resumes only the
  validated prefix. A crash after append but before receipt update is recoverable.
- A completed retry leaves the ledger bytes unchanged. Missing rows relative
  to the receipt, a different source/table/host, a broken chain, an unrelated
  pre-existing ledger or an interleaved writer causes refusal. No rollback,
  history deletion or automatic reset is performed.
- Preserve the original receipt/ledger if a refusal needs investigation. A
  receipt cannot be used to approve an engine run or replace owner confirmation.

## Synthetic verification

```text
python -B -m unittest tests.nautilus_registration_acceptance -v
```

This bounded suite imports neither the full Nautilus suite nor the engine. It
uses temporary ledgers and table metadata, blocks provider connections and
protected-data/.env opens, and compares IDs with the existing runner. Fourteen
tests cover unique registration and counts, byte-idempotent retry, recovery
after append, malformed grid/study configs, prior history, broken chain,
receipt/row loss, invalid receipts, competing writers, table locking, Windows
mode refusal on non-Windows, temp-directory enforcement and unchanged ordinary
owner/freshness guards. Local Linux result: 14 PASS. Windows CI is separate
from the owner's Windows acceptance; consult the exact commit's check result.

The original private approval remains private. Public scope summaries are in
OWNER_RULINGS_LOG.md and the spec Status / Appendix B. The subsequent 2026-10-30 O8 decision
makes additional GPT/Gemini reviews optional / NOT_PERFORMED. Missing optional reports do not block
Windows hand-off. Existing technical/Windows acceptance and separately recorded actual pilot
`owner_confirmed` remain mandatory; this documentation does not perform real registration or a pilot.
