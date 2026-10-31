# Native chart text rendering fixes

The UI session follows the owner's 2026-10-31 instruction to fix display defects
independently and report completed code changes. Product redesign awaits the
owner's specific directions. The separate main session's research queue and
handoff ownership are unchanged.

## Reproduced defects and behavior

- Monte Carlo fans and line charts clipped the leading digits of large price
  ticks because the y-axis label area was fixed at 53/58 logical pixels.
- At a 350-pixel chart width, portfolio objective legends overlapped. Long line
  series names also ran into adjacent legends, and the frontier footer clipped.
- Many line series consumed the chart's plotting height without increasing the
  widget's minimum height.

Chart text now uses the actual Qt font metrics. Axis margins accommodate the
tick strings, legends flow onto additional rows, long individual names elide
with full names available in the tooltip, and footers wrap. Minimum height
reserves room for the legend, axes, footer and plot after resize/font changes.
Horizontal ticks reduce density when their labels would collide. Qt continues
to handle device scaling; the chart data, formulas and result objects are
unchanged.

## Validation

- All four new Qt painting regressions fail on the unmodified main baseline and
  pass with the fix. They inspect the actual text paint bounds for clipping and
  overlap, including large prices, narrow charts, long names, font changes and
  twelve series.
- The four regressions pass at `QT_SCALE_FACTOR=1`, `1.25` and `1.5` on Linux
  offscreen Qt, including light/dark large-price fixtures.
- Existing `tests.desktop_acceptance`: 22 tests pass; market and portfolio
  scope fixtures: 13 tests pass (39 distinct tests total with the regressions).
- The runtime packaging CI runs the new regressions with the existing desktop
  fixtures on Windows and Linux.

```text
python -m unittest tests.desktop_chart_rendering_acceptance tests.desktop_acceptance tests.desktop_market_acceptance tests.desktop_portfolio_scope_acceptance -v
```

These are synthetic/offscreen rendering checks. Physical Windows monitor/font/
DPI inspection and live-provider acceptance remain pending.
