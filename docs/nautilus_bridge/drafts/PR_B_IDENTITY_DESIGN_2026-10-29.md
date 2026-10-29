# PR-B instrument identity / regression contract — ⑫-2/a

Status: design and characterization only. No frozen implementation or cost is changed.
Source: HANDOFF_MANUAL section 4, step 2; validate.py cost_class / cost_floor_bp;
instruments.py registry; history.py _looks_crypto; gate_package.py HARNESS_SOURCES.

## Reproduced current defect

BTCUSD and EURUSD resolve to US shares (50 bp); BTC-USD and EURUSD=X resolve to
crypto and FX (10 bp). Arbitrary alphabetic UNKNOWN also resolves to US shares.
`tests/fixtures/instrument_identity/pr_b_proposal.json` records 17 concrete aliases
with observed current and proposed target classes. The tests characterize the bug;
a passing characterization is NOT a fixed cost resolver or approval of these costs.

## Proposed contract

Resolve provider symbol -> canonical instrument identity -> existing cost-table row.
Identity fields: asset_class, base, quote_currency, venue (nullable), provider,
provider_symbol, registry_version and resolution_status/reason. Preserve original
symbol. A global security identity and a venue-specific tradable instrument are
separate; absence of venue never silently means Nasdaq or a crypto exchange.

Explicit aliases may map BTCUSD and BTC-USD to BTC/USD with unknown venue;
BTCUSDT is BTC/USDT and KRW-BTC is BTC/KRW, never the same price series. Bare
alphabetic strings require known-asset registry/provider evidence; suffix alone
cannot prove every instrument. AAPL/SPY examples require confirmed equity metadata;
ES=F is a provider continuous futures series, not an orderable futures contract.
252670.KS preserves the existing registered ETF identity. VOD.L identity may be
known, but unsupported cost venue must still refuse rather than inherit US costs.

The proposal preserves COST_BP_PER_SIDE values, mixed-universe maximum floor and
unsupported-asset refusal. A corrected identity may select a different *existing*
row. That changes research results and therefore needs explicit frozen-harness
approval, even if the bug fix looks obvious. Never lower an override to make a
strategy pass. Keep cards/ledgers/results immutable and never retrospectively rescore.

## Implementation after approval

1. Owner decisions: audit 12.8, K-f priority and exact frozen-harness scope. Proposed
   touched files: core/quant/instruments.py and validate.py; a bounded adapter for
   history/UI aliases only if required. Confirm expected source hashes first.
2. Implement pure resolver with explicit metadata/alias table. No provider request,
   cache scan or credential lookup during identity resolution. Return typed UNKNOWN,
   AMBIGUOUS or UNSUPPORTED_COST instead of guessing. Conflicting metadata refuses.
3. Convert the proposal rows to resolver acceptance tests. Add whitespace/case,
   ambiguous alias, venue conflict, unknown asset, quote mismatch and mixed universe
   cases. Ensure identity used for data retrieval equals identity used for costs.
4. Run old/new mapping in shadow on synthetic inputs, recording both identities,
   row, cost, reason, code and registry versions. No actual ledger or frozen study.
5. Separately approve any new frozen package/version and prospective reruns. Research
   gates, owners' approvals and old results remain unchanged by this PR.

## Validation evidence

Linux: 3 characterization tests PASS, covering 17 symbols and mixed cost refusal.
Proposed resolver: NOT_IMPLEMENTED / NOT_RUN. Actual provider routing: NOT_RUN.
No model, frozen source, threshold, ledger, protected cache or .env was changed/read.
