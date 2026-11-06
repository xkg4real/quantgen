# Detached instrument identity resolver

This is the bounded implementation child **⑫-2/b/1** of the PR-B identity
contract. It provides a pure resolver and synthetic acceptance tests. It does
not complete PR-B, production cost classification or the frozen-harness work.
The earlier ⑫-2/a design, 17-alias proposal and characterization remain history.

`core.research.instrument_identity.resolve_instrument(provider, provider_symbol,
*, registry, metadata=None)` accepts an explicitly supplied `IdentityRegistry`
and optional request-bound `InstrumentMetadata`. It returns an immutable
`InstrumentIdentity` with the original request strings, caller-supplied registry
version, asset class, base, quote currency, nullable venue, status and reason.
`resolve_many` preserves input order and every refusal; it performs no aggregation.

There is no default registry, provider request, credential lookup, filesystem
read or cache scan. Alias matching ignores boundary whitespace and ASCII case
only; returned request strings remain exact. A suffix or alphabetic spelling
cannot establish an asset. A metadata record must bind to both the provider and
the requested symbol. Conflicting records, including null versus concrete
evidence, do not merge. Duplicate matching aliases refuse even if identical.
Malformed registry records refuse the whole supplied registry. These conservative
choices are explicit implementation decisions for unspecified contract details.

Statuses are `RESOLVED`, `UNKNOWN`, `AMBIGUOUS` and `UNSUPPORTED_COST`, with typed
reasons. An unsupported cost result can retain the known identity while omitting
the cost row. Crypto USD, USDT and KRW quotes remain distinct, and a missing
venue remains missing. Continuous futures series are explicitly non-orderable;
other identities have no orderability evidence. No security or execution ID is
invented. A resolved record does not authorize a trade.

The optional cost-row output is one of the existing names `us`, `krx_stock`,
`krx_etf`, `crypto`, `fx` or `futures`. The caller must supply that typed label.
The module checks bounded asset/quote/MIC combinations for equities, ETFs and
futures and rejects FX self-pairs, including ASCII-case-equivalent currencies.
Crypto/FX rows require explicit asset/row evidence but do not establish venue
support. This small compatibility table is a detached implementation choice,
not verified vendor policy, production cost approval or an exchange directory.
It contains no basis-point values or cost arithmetic. Known London identity
cannot inherit the US row, and a registered ETF remains an ETF.

## Observed verification

The 17 historical proposal requests are exercised against a deliberately
synthetic registry. The proposal's `required_evidence` strings are requirements,
not metadata or proof of live provider mappings. Further cases cover missing
evidence, malformed input, provider binding, duplicate aliases, quote/venue
conflicts, mixed universes and immutable results.

Independent review found that case-different FX self-pairs were initially
accepted. Two failing subcases were preserved, then corrected without changing
the returned identity strings. The final guarded suite passed **19 tests**
(0.014s, exit0); the root independently reran the same suite, **19 passed**
(0.012s, exit0). These are overlapping runs, not 38 distinct tests. Both used
synthetic inputs, denied network/protected stores, disabled dotenv and isolated
mutable state. The runtime workflow includes this module in bounded fixtures
and its test path in pull-request triggers.

Pure acceptance can be reproduced with:

```sh
python -B -m unittest tests.instrument_identity_acceptance -v
```

Exact-head Windows/Ubuntu CI and PR merge are separate required results. The
existing production lookup, data-routing identity, `validate.py`, instrument
registry, cost numbers, maximum floor, frozen harness, gates, cards, ledgers,
past studies and actual order paths are unchanged. Adapter integration, provider
identity confirmation, frozen-package authorization and prospective studies are
still incomplete. No actual API, user-PC, legal/license, pilot or publication
evidence is supplied. Optional additional GPT/Gemini spec review remains
`NOT_PERFORMED`.

## A1 test-process cleanup follow-up

The integrated source `b79d56d5aedd0a7d854421c933d87b31338e5177` passed
the final detached identity rerun (19 tests, 0.013s, exit0) and source consistency
(20 policies, 591 files, publication BLOCKED). Its Runtime run42191579626
Ubuntu3.12 job127804645117 later failed after the separate A1 step printed
18 tests OK in11.710s: the process segfaulted with exit139. The complete job
failure is retained; successful assertions do not establish successful exit.

A guarded natural-shutdown probe of those same three A1 modules passed18 tests
in14.055s with exit0 locally, but retained four owned ResearchWindows and five
owned status hosts, including four reading-help controllers. Only the two native
A1 test modules now reuse the existing `delete_owned_widget` helper for their
owned fixture cleanup. All18 methods and82 assertion AST nodes are unchanged;
the helper, Flet test module and production implementation are unchanged.

The same guarded after-probe passed18 tests in12.249s with exit0. All nine owned
C++ widgets emitted destruction and were deleted; no ResearchWindow or reading
controller remained. Natural shutdown produced no exception, unraisable event
or fatal trace. The original segfault was not reproduced locally, and its precise
cause is not established. These lifecycle measurements and independent source
review justify the narrow test fix; fresh exact-head full CI is still required.
No test is skipped, weakened, retried into a passing claim or made to exit early.
