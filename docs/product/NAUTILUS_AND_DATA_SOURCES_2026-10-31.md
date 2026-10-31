# Nautilus and market-data sources are separate layers

FMP, KIS, Yahoo, FRED and other sources supply market observations or reference
data. NautilusTrader is a backtesting/trading framework; it consumes historical
data and can connect to data providers/venues through adapters. It is not itself
a replacement database for every price, financial statement or macro series.
Adapter availability does not remove provider credentials, entitlements or rights.
See the [official Nautilus overview](https://github.com/nautechsystems/nautilus_trader#readme).

QUANTGEN's current bridge is narrower than Nautilus's overall capabilities:
an **independent event-driven BacktestEngine leg for the research gate**, compared
against the existing vectorised simulator. QUANTGEN's bridge excludes live clients,
network adapters and API credentials. Therefore the request to replace the earlier
QuantConnect engine direction with Nautilus did not implement a universal data-feed
replacement, nor make every app calculation use Nautilus.

| Layer | Current role |
| --- | --- |
| `core/quant/history.py` | Product historical input routing: auto/FMP/KIS/yfinance/crypto; synthetic only when explicitly selected. |
| Existing product calculation modules | Monte Carlo, analytics, pricing and other app calculations; not all are backtest engines. |
| Nautilus research bridge | Independent historical backtest/parity leg, using constrained research input and execution rules. |
| Anthropic API | Optional commentary about computed results; unrelated to historical price providers or Nautilus. |

Verified repository state on 2026-10-31: [PR #21](https://github.com/xkg4real/quantgen/pull/21)
was merged into `claude/amazing-gauss-tdiguu` at 16:19:56 Asia/Seoul, merge
`0510719995e0ec3dfda8f113f826f43ca1821c6b`. This is **research branch integration**,
not product main integration. Product main checked here was
`c3a0613eaa6d26620d871b28f28e5ba349ff1ac9`.
The [bridge spec at that research commit](https://github.com/xkg4real/quantgen/blob/0510719995e0ec3dfda8f113f826f43ca1821c6b/docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md)
is the scope evidence; older paused task briefs are historical.

Still outstanding: actual Windows registration/validation, provider comparison,
separately authorized pilots and the specified parity/integration requirements.
O8 extra GPT/Gemini reviews remain optional and NOT_PERFORMED; their absence alone
does not block handoff. O11 A2's twelve settings registered before price reads,
`n_trials = 12 + U`, `U <= 24`, and actual execution approval remain unchanged.
This explanation grants no `owner_confirmed` and does not run a pilot or ledger.

Removing a particular provider would require mapping its actual datasets and app
consumers to another licensed source and checking coverage, adjustments, timestamps
and failure behavior. Renaming the existing source selector to Nautilus would hide
provenance without accomplishing that migration. No source was removed or silently
replaced as part of this clarification.
