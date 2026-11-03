# ⑨-2 Data acquisition and evidence intake

## Result
The inventory covers 73 registered series and 29 distinct CSV dependencies extracted from the recorded QA report. The 121 historical NOT_RUN rows comprise 104 REFDATA, 16 OWNER and 1 OTHER. This is metadata inventory, not proof that those blockers still exist: the old calendar signature reasons are historical and have not been rerun here. No protected cache, actual ledger or holdout was opened.

`DATA_READINESS_2026-10-29.json` supplies each series' source, alternatives, channels, units, calendar, timezone and missing evidence. `python -m tools.status.data_readiness` reproduces it from the two named files. Neither registered provider nor installed API means acquired/licensed data.

## Acquisition order
1. KRX official KOSPI/KOSPI200 closes and 005930/000660 close/market-cap history: original official exports, date coverage and field definitions first. KIS close equivalence remains unverified in the registry; Yahoo is an independent comparison, not a substitute official close. Owner supplies the export and use-right evidence through a private channel.
2. FRED/Treasury/BoK rate, FX and macro series: exact observation dates, publication schedule, vintages and source notices; retain each series' rights attribution. A latest revised series is not point-in-time history.
3. Remaining QF/QX derived and independent reference fixtures: obtain the original specification/version and source authority; do not synthesize expected values from the implementation under test.
4. Resolve OWNER rows against current signed evidence individually. No mass promotion of the old NOT_RUN rows and no changed formal gate.

## Receipt contract
`core.research.intake.validate_data_receipt` validates explicit in-memory observations and metadata: series/provider, retrieval UTC, vintage, adjustment, timezone, calendar, units, rights reference/scope and canonical row SHA256. It rejects missing fields, duplicate/unsorted dates, non-finite values and hash mismatch. A structurally valid receipt still says license authenticity NOT_VERIFIED and gate NOT_RUN.

`compare_observations` requires identical date sets. Missing dates return INCOMPLETE instead of an inner join; the caller supplies the series-specific absolute tolerance from an approved contract. It does not certify source independence, units or licenses. Store acquisition receipts privately; never embed account credentials or licensed raw datasets in the public repo.

## Actual managed-cloud connectivity
On 2026-10-29, bounded probes to `fred.stlouisfed.org` and `query1.finance.yahoo.com` each returned `URLError: Tunnel connection failed: 403 Forbidden`. Existing proxy/network policy was preserved. No live market dataset was acquired in this environment. The UI's production adapters are wired to existing explicit providers, while successful calculations here use clearly marked synthetic fixtures.

Completion boundary: inventory and intake/parity tooling implemented. Official source acquisition, license verification and formal gate runs remain external-data dependent, not completed.
