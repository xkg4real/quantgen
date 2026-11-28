---
name: tearsheet-generator
description: >
  Tearsheet layout, MAE (max adverse excursion) analysis and leverage/liquidation math for strategy
  performance reports (QuantStats-style HTML/SVG, trade lists, metrics JSON). Use when presenting or
  stress-reading a backtest's results. QUANTGEN numbers come from QUANTGEN's own engine and gate.
version: "1.1.0-quantgen.1"
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Tearsheet Generator Skill

> **QUANTGEN audit, 2026-11-23.** Copied from HyperFrequency/skills@7532af7 (MIT per its README). Kept whole:
> `tearsheet_helpers.py` (numpy/scipy only, no network, no file I/O) and `references/`. Changed: the Installation
> section (it pointed at the author's machine), the import in `commands/generate-tearsheet.md`, and the Hyperliquid
> "apply leverage via SDK patch" row in `references/index.md`. Caveats for the helpers: `simulate_leveraged_equity`
> annualises **per-trade** returns with sqrt(252), so its Sharpe and Sortino are not daily-return ratios; the
> liquidation threshold `100 / leverage` ignores maintenance margin and fees; leverage up to 50x is a crypto-perp
> framing. QUANTGEN does research and paper trading only: a leverage "recommendation" here is analysis, never an
> instruction to any venue.

## About

This skill generates custom tearsheets using the [QuantStats library](https://github.com/ranaroussi/quantstats) - a Python library for portfolio analytics.

**Key Features:**
- Custom SVG visualizations (returns, drawdowns, monthly heatmaps)
- Professional HTML tearsheets
- MAE (Maximum Adverse Excursion) analysis
- Leverage recommendations based on risk metrics
- Copyable strategy configurations

Generate comprehensive trading strategy tearsheets with:
- IBM Plex Mono font styling (QuantStats format)
- MAE (Max Adverse Excursion) percentile analysis (p90-p99)
- Optimal leverage recommendations with stop-loss levels
- Fixed Position (Static) vs Full Position (Dynamic) analysis
- 10%, 20%, 30% liquidation buffer calculations
- Full trade list with entry/exit details and MAE stats
- Copyable strategy config text boxes
- Multiple leverage scenario comparisons (1x, 10x, 15x, 20x)

## Quick Start

The three procedures below live in `commands/`. They are reference procedures, not registered slash commands.

```bash
# Generate tearsheet from trades CSV
/generate-tearsheet SOL_MTF_EMA_001 --trades ./trades.csv --capital 10000

# Verify backtest with Nautilus Trader
/verify-backtest SOL_MTF_EMA_001 --trades ./trades.csv

# Test optimal leverage configuration
/verify-mae-lev SOL_MTF_EMA_001 --leverage p95
```

## Commands

### /generate-tearsheet
Generate a complete tearsheet with all analysis sections.

### /verify-backtest
Verify tearsheet results against Nautilus Trader for accuracy validation. In QUANTGEN, engine-vs-engine parity
is `tools/nautilus/parity.py` (checks P0b to P13); use that, not this procedure's tolerances, for any verdict.

### /verify-mae-lev
Run backtest with optimal leverage config derived from MAE analysis.

## Output Files

Each tearsheet generation produces:
- `{strategy}_comparison.html` - Full HTML tearsheet
- `{strategy}_comparison_metrics.json` - JSON metrics for programmatic access

## Key Sections

### 1. Key Performance Metrics
- B&H, Fix1x, Dyn1x, Fix10x, Dyn10x columns
- Cumulative Return, CAGR, Sharpe, Sortino, Max DD, Calmar
- Intratrade risk metrics with liquidation distance

### 2. MAE Analysis & Optimal Leverage
- MAE distribution table (min, mean, p50, p75, p90-p99, max)
- Safe leverage recommendations per percentile
- Stop loss table with % PRICE movement (not position cost)

### 3. Fixed Position (Static) Analysis
- Leverage table: 5x, 10x, 15x, 20x, 25x, 30x
- Columns: Liq @ %Price, Rec. SL, Max Loss, +10% Buffer, +20% Buffer, Risk Level

### 4. Full Position (Dynamic) Analysis
- Warning about compounding risk
- Leverage table: 1x, 2x, 3x, 5x, 10x
- Recommendation per leverage level

### 5. Buffer Analysis Summary
- +10%, +20%, +30% buffers above worst MAE
- Safety check for 10x, 15x, 20x leverage

### 6. Full Trade List
- All trades with entry/exit times, prices, side, PnL, MAE, MFE, duration
- Scrollable table with sticky headers
- Summary row with averages

### 7. Strategy Configuration
- Original config text box (copyable JSON)
- MAE-optimized config text box (copyable JSON)
- Backtest methodology description

## Dependencies

- Python 3.10+
- pandas, numpy, matplotlib (scipy for `tearsheet_helpers.py`)

## Installation

Upstream's `StrategyComparisonTearsheet` (`backtesting.tearsheets.strategy_comparison_tearsheet`) never shipped and
is not in QUANTGEN. Import the helpers from this folder by path, and build the HTML from `references/html_templates.md`.
QuantStats is not a QUANTGEN dependency; adding it needs the owner's approval. The templates load IBM Plex Mono from
Google Fonts; QUANTGEN's UI font is QG Interface (`quantgen_desktop/typography.py`), and offline reports should
drop the `@import`.
