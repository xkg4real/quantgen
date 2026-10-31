# Native market diagnostic language

Scope: 13-8/b2/c/b/a, a child of the unfinished language consistency work.
The Windows PyQt6 ETF, Crypto and Derivatives panes now attach explicit English
and Korean display variants to their existing diagnostic paragraphs:

- ETF premium and Crypto premium/ETH-BTC AR(1) impulse-amplitude decay, including
  unavailable, zero-memory, oscillating and non-decaying cases.
- Crypto funding's retrospective deciles and exploratory circular-phase result,
  including overlapping samples, retired IID bootstrap, unverified market phase
  assumption and unchanged historical cards.
- Option quoted-mid check denominators, true zero violations and NOT_RUN, with
  the limitation that these checks do not prove executable arbitrage or an
  official study verdict.

The canonical paragraph remains in ToolPane.sections and report JSON/HTML.
Switching language changes only the visible label. Numeric precision, signs,
check identifiers, missing-evidence states and provider-supplied diagnostic
reasons remain intact. Unknown diagnostic status/scope uses the original text.
No computation, provider route, data request, model verdict or execution approval
changes. These are local strings; there is no translation service call.

Verification uses injected/synthetic results and offscreen widgets:

```
python -m unittest tests.desktop_market_diagnostics_language_acceptance
```

Tests cover all known decay branches, available/unavailable funding diagnostics,
zero/partial quote coverage, repeated language switches, source/report retention
and result clearing. Native result-level tests do not establish physical Windows
visual/DPI acceptance or browser parity. Other long model narratives, LETF
disclosures, remaining inline labels and actual installation checks are still
separate unfinished scopes. Do not strike the parent language task as complete.
