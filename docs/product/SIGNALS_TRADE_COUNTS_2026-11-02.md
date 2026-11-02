# N11: executed sides and completed round trips

The descriptive Signals backtest counted a signal change at the final close as
an executed trade, although that change has no subsequent return observation and
is excluded from the existing cost path. It also counted a pending final-close
exit as a completed winning/losing trade. This change corrects those statistics
without changing positions, costs, equity, returns, drawdowns or risk metrics.

## Meaning of the current fields

- `n_trades` retains its integer name for existing consumers, but now counts
  **executed entry/exit sides**, aligned exactly to the existing cost window.
  An entry and an exit are two sides, not two completed round trips.
- `completed_round_trips` counts executed entry/exit pairs. An initial long
  position is recognized as an entry from the initial flat state.
- `pending_last_signal` is `entry`, `exit` or `none`. Final-close changes are
  preserved in the signal/position array but excluded from executed statistics.
  No terminal liquidation or extra fee is introduced.
- `win_rate` is the fraction of completed round trips whose exit price exceeds
  their entry price, **before costs**. A gross-price winner can lose money after
  costs. Zero closed round trips yields `None`, not a zero win rate.
- New calculations carry `statistics_version="signals-executed-sides/1"`.
  Additive dataclass defaults use `legacy_unverified`, `None` and `NOT_RECORDED`
  rather than inventing missing statistics for old manually constructed objects.
  Legacy/unknown versions display a recorded count and win rate with an
  explicitly unverified basis; they are not relabeled as current executions.
  Existing saved reports are not migrated or reclassified.

The native and Flet views show executed sides, completed round trips, pending
signals and the gross-price win-rate basis separately. English/Korean labels,
local narrative, native JSON/ZIP reports and both AI payload paths retain the
same meaning. The analysis report version and its official `NOT_RUN` verdict
are unchanged. These statistics do not feed a book, gate or research ledger.

## Reproduction and validation

`python -m unittest tests.signals_trade_count_acceptance -v` covers:

- `[100]*59+[101]`: no executed side or closed trade; pending entry; equity 1.
- `[100]*56+[101,102,103,102]`: one executed entry; pending exit; no closed-trade
  win rate. The last return still belongs to the held position.
- A completed round trip: two sides and one completed trade.
- No trades, an open position with no pending change, and an initial-position
  fixture; no forced liquidation.
- A positive gross-price trade with negative costed equity: the win basis stays
  explicitly gross, not silently redefined as a net-cost win.
- Legacy/unknown version objects remain visibly unverified in English/Korean,
  native/Flet and metadata; missing completed/pending values remain unknown.
- Native locale switching, unchanged report/numeric state, JSON and AI metadata;
  actual Flet worker execution on injected synthetic history with intercepted AI,
  and Flet English/Korean control translation.

An additional direct comparison loaded the original `core/quant/backtest.py`
from local commit `5c7acbb` in memory. All 36 combinations of three strategies,
four 120-observation synthetic paths (100 flat, linear 100→130,
`100 + 4*sin(arange(120)*.4)`, and `100*exp(cumsum(N(.0005,.015)))`
with RNG seed 60811), and costs 0/10/175 bp passed **108 exact array comparisons** (equity, benchmark,
position) and **504 exact existing scalar/metadata comparisons**. The intended
count/win-rate changes were excluded from that invariance comparison.
Strategy parameters were momentum lookback 1, MA fast 5/slow 20, and RSI
period 14/buy below 30/exit above 55.

All checks disable dotenv and network access; no real data, API keys, cached
prices, frozen studies or actual ledgers were used. This is source/synthetic
acceptance, not Windows hardware or live-provider acceptance.

## Website impact

The Flet Signals view and its AI payload require the same corrected wording and
metadata as native Signals; this source patch implements both. Actual website
application, deployment and destination-chat delivery are separate and unverified.
The coordinating root agent owns the UI website update record and dispatch.

An independent review grouped consecutive held intervals instead of reproducing
this implementation's transition loop. Across 2,048 synthetic combinations
(256 binary signal patterns × two positions in the observation window × four
price shapes), all 8,192 comparisons of side count, completed round trips,
gross win rate and pending signal passed. The review caught and prompted the
legacy/unknown-version display safeguard described above.
