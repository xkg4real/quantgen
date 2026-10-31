# QUANTGEN C chart format and themes

The owner selected concept C on 2026-10-31. This replaces the earlier A-default
proposal. C combines the chart and its interpretation in one reading area.
The existing QUANTGEN ivory/forest palette supplies the app colours. The deployed
quantgeneration.com CSS was not retrievable (403); AWS must compare its actual
tokens before describing an exact site/app match.

## Shared presentation

- Wide: chart and related data on the left, interpretation on the right, 2:1.
  Narrow: chart first, interpretation below. Native switches at an available
  study width of 820 px; Flet uses its md grid breakpoint.
- Guide: selected-date relationships and the four-part indicator explanation
  live beside the chart; tabs (Qt) or a detail selector (Flet) prevent multiple
  full explanations from making a very tall empty chart column. All selected
  indicators remain on the same instrument, interval and time axis.
- Keep actual chart types: fan distribution, line, bars, scatter and heatmap
  remain appropriate to their data. Do not convert all plots into candles or
  fabricate OHLCV for reference-rate/close-only data.
- Keep indicator A–E letters, stable colours and line styles, source, units,
  selected date, warmup gaps and limitations visible.
- Light: background #F7F5F0, surface #FFFEFB, accent #194C40.
  Dark: background #101915, surface #17231D, accent #91C5AC.
- Theme switches repaint existing results and preserve financial inputs, model
  outputs, axis limits, selection and cursor. Qt persists ui/theme in QSettings;
  Flet holds the choice in its page session. No theme-triggered provider request.

## Implementation coverage

| Surface | Shared implementation |
| --- | --- |
| Qt Home/Signals guide | indicator_guide.py and chart_study.ChartStudy |
| Qt Quant, Portfolio, Bonds | existing chart + canonical narrative in ChartStudy |
| Qt common analysis tools | ToolPane result and narrative in ChartStudy |
| Flet Home/Signals | indicator_guide.py and study_row |
| Flet equity (7), FICC (15), extended (6) factories | qcharts._to_image → FigureStudy, shared C reading area |

Existing model calculations, chart data, legend labels and exported research
records retain their source values. A chart title/axis/legend summary is a reading
aid, not a complete accessible data table or newly generated financial advice.

## Verification and boundaries

230 bounded runtime checks passed before the final Home/font refinement; the
final 16 focused Home/theme/Flet checks passed afterward, including two new Home
regressions. All 28 chart factories rendered through the common frame and changed
theme. Native C light/dark captures at 1600×1050 and actual local Chromium/Flet
captures at 1600×1100 and 390×1000 were inspected. The latter found and fixed a
Flutter SVG font-family issue, duplicate guide intro and Home refresh translation
loss. Fixture provider/engine hooks are inert; this is not a live market test.

Physical Windows taskbar, installer, DPI and full keyboard/screenreader acceptance
remain separate. CI and installed-wheel checks must be consulted for the final
PR head. Website source changes/deployment belong to 웹사이트 작업공간(AWS).
Shared handoff: [AWS continuation](https://github.com/xkg4real/quantgen/blob/handoff/WEBSITE_AWS_HANDOFF.md).
No cross-chat messaging receipt or website deployment is claimed.
