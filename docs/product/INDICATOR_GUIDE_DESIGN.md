# QUANTGEN indicator guide and shared chart rules

The guide teaches indicator interpretation on one attributed historical
series. Opening it shows an introduction and a baseline chart. In the native
app (2026-11-03, owner request UI-13) the guide is search-first: a box titled
“Search what you want to explore” (“궁금한 내용을 검색해 보세요”) suggests up to
eight matching terms while typing, like a browser search box, and the chosen
term’s explanation appears directly below it. The glossary
(`core/education/glossary.py`) covers the five indicators and 27 market, risk,
rates, derivatives, FX and QUANTGEN terms in Korean and English; names,
abbreviations, aliases, Hangul initial consonants and finally definition words
match. Choosing an indicator also draws it on the chart; chosen indicators show
as removable chips and can be combined or cleared. The Flet guide keeps its A–E
buttons.
The existing Signals workspace uses the same guide with its actual loaded
`History`, so its dates and prices are never replaced with an educational sample.

The owner selected [C format](CHART_C_DESIGN_2026-10-31.md): chart left and
interpretation right when wide; stack when narrow. Both app themes use the
QUANTGEN ivory/forest palette.

## Screen and interaction

Order: introduction → choices and sample → selection reason/source → chart and
same-date cursor → interpretation → four-part explanations → counterexamples
→ explicit report save. Keep provenance, period and data type near the chart.

Each indicator has a stable letter and colour, shared by the button or chip,
chart and explanation. A Flet checked button adds a checkmark and a native chip
shows the letter and abbreviation (reopening its explanation) beside a remove
button; colour is not the only
selection signal. Native keyboard path: Tab to the search box, type, Down into
the suggestions (Up returns), Enter chooses, Escape closes the list. Clear preserves the underlying historical example policy. The guide can
be collapsed and reopened without losing selections. Changing language preserves
selections, the cursor date when available, financial inputs and research results.

Single SMA/EMA selections use the 2022 trend/pullback example. Other singles and
multiple selections use the 2020 disruption/trend-change example. An explicit
sample choice overrides this policy for **every** selected indicator. No chart
combines indicators computed on different instruments or intervals.

The native Qt view supports mouse crosshair, slider, Left/Right/Home/End and
counterexample buttons. The Flet application supports the same choices, slider
and counterexample buttons; a browser hover crosshair is not claimed. Cursor
readings report observations, including warmup gaps, rather than trade decisions.
The explanatory text identifies the selected-date relationships and their limits.

## Rendering contract

`core.education.chart` produces self-contained SVG for Qt, Flet and exported HTML.
Qt paints the moving crosshair separately; cached, read-only calculations avoid
recomputing every indicator on every mouse move. There are no remote scripts,
chart vendors or embedded provider credentials.

| Element | Rule |
| --- | --- |
| Colour/identity | SMA A `#358C73`; EMA B `#477DC2`; RSI C `#9666B8`; MACD D `#B27628`; BB E `#258895` |
| Price | Neutral line; overlays share the price scale |
| Multiple curves | Fast average/centre/MACD solid; slow average/band edges/signal dashed; explanation names this convention |
| RSI | Own 0–100 axis with 30/50/70 references |
| MACD | Own zero-centred scale, two distinguishable lines and histogram |
| Time | Every panel maps the same observation index to the same x coordinate |
| Candles | Require real aligned `(open, high, low, close)` data; hollow rising / filled falling bodies |
| Volume | Separate panel only when actual aligned nonnegative observations exist |
| Axes | Regional formatting; width reserved for large values; fewer date labels in narrow charts |
| Legend | Wrap rows as width decreases; abbreviations match the glossary; complete values in cursor readout |
| Background | Explicit SVG dimensions, avoiding Qt's incorrect percentage-rectangle rendering |
| Fonts/scaling | Bundled QG Interface; vector chart at device scale; native logical minimum window 1000×700 |
| Theme | Existing QUANTGEN light/dark tokens; stable indicator colours |

`ChartSeries` validates positive finite closes, ordered unique aligned dates,
OHLC bounds and matching closes, and volume lengths. Current `History` supplies
closes only: neither candles nor volume is fabricated. Candle rendering is a
supported component contract, not a claim that the bundled sample contains OHLCV.

## Historical evidence and educational limits

The bundle includes 1,247 daily USD/EUR reference observations, 2018–2022, from a
pinned `datasets/exchange-rates` mirror of Federal Reserve H.10 data. The mirror
inverts DEXUSEU and rounds to four decimals: the displayed unit is **EUR per USD**.
The source URL, pinned revision, transformation and byte checksum are in
`core/education/samples/usdeur_provenance.json`. The CSV checksum is verified on
load. No runtime provider request is needed to open the educational guide.

Each explanation follows meaning → where to look → interpretation → limits.
The example-selection reason explicitly identifies hindsight selection. Selected
counterexamples show instances where a common directional reading disagreed with
the next five observations. These are hindsight annotations, not a backtest,
representative performance estimate, validation verdict or execution permission.

The ZIP contains localized `report.html`, canonical `education.json`, and a
checksum `MANIFEST.json`. Its explicit `education_only` and `NOT_RUN` fields keep
it distinct from the research run ledger. Save is user initiated; cancellation
writes nothing. Existing research exports retain canonical JSON and add a readable
localized HTML layer without changing IDs, verdicts or stored calculations.

## Verification and remaining acceptance

Offline fixtures cover formula parity and prefix invariance, common dates,
warmup, sample orientation/checksum, counterexamples, read-only calculation cache,
native/Flet callbacks, locale persistence, original financial inputs/reports,
explicit saves and chart painting. Installed-wheel smoke verifies the educational
CSV/provenance, rights inventory, Babel formatting and native shell outside checkout.

Native screenshots were inspected at 1100×820 light and 1000×700 dark with
150% scaling. Physical Windows display/input/installer acceptance remains a
separate check. The Flet guide has callback tests and local Linux Chromium visual checks at
1600×1100 and 390×1000, including C layout, dark mode and Korean glyphs.
The actual `quantgeneration.com` source/deployment remains separate AWS work.
