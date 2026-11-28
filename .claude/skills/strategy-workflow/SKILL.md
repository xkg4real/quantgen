---
name: strategy-workflow
description: >
  Strategy research methodology from hypothesis to out-of-sample validation: features, signals, sizing,
  pre-flight data checks, Optuna search, walk-forward and OOS testing. Use when designing or validating a
  trading strategy. In QUANTGEN, QUANTGEN's own gate (nautilus-portfolio-bridge skill) decides every verdict.
version: "2.0.0-quantgen.1"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Strategy Workflow

> **QUANTGEN audit, 2026-11-23.** Copied from HyperFrequency/skills@7532af7 (MIT per its README). Removed:
> `backtest-optimize.md` (an always-on swarm "doctrine" that tells the agent to kill and relaunch processes and act
> without waiting for direction, plus Vast.ai deploys over `ssh`/`scp` as root and personal paths),
> `references/strategy_generation.md` (the author's own Hyperliquid strategy brief with vendored MPL-2.0 TradingView
> code and Vultr server setup), and this file's swarm entry points, Vast.ai, hardware-watchdog, PAL MCP and
> project-file sections, whose scripts and files never shipped. What remains is methodology. In QUANTGEN, every
> trial is registered in its family ledger before it runs, and the verdict comes from `core/quant/validate.py`'s
> gate (deflated Sharpe with the ledger's trial count, PBO, walk-forward), not from "top K by Sharpe".

Strategy development workflow for quantitative research, from hypothesis to validated out-of-sample result.

## Overview

This skill provides a framework for developing, testing, and validating trading strategies. It supports:

- Hypothesis-driven strategy development
- Bayesian hyperparameter optimization with Optuna
- Walk-forward validation and out-of-sample testing

## Strategy Development

### 1. Hypothesis Formulation

Define your strategy hypothesis in measurable terms:

- What market inefficiency are you exploiting?
- What is the expected holding period?
- What are the entry/exit conditions?
- What is the target risk-adjusted return?

### 2. Feature Selection

Identify relevant features for signal generation:

- Price-based (OHLCV, returns, volatility)
- Technical indicators (EMA, RSI, Bollinger Bands)
- Multi-timeframe features (MTF resampling)
- Volume analysis (PVSRA, VWAP)
- Market microstructure (order flow, spread)

### 3. Signal Generation

Convert features into actionable signals:

- Directional bias (trend following, mean reversion)
- Entry conditions (threshold crossings, pattern recognition)
- Exit conditions (take-profit, stop-loss, trailing stops)
- Position sizing rules

### 4. Position Sizing

Implement risk-aware position sizing:

- Fixed fractional
- Kelly criterion
- Volatility-adjusted
- Regime-dependent scaling

## Backtesting

### Pre-Flight Validation

**MANDATORY** before every optimization run. Upstream's `validation.py` did not ship; the checks are:

- Data >= 90 days with no gaps/NaN
- Min trades >= 30 for statistical significance
- MTF resampling implemented correctly
- No look-ahead bias

QUANTGEN equivalents: `core/quant/validate.py` `data_checks`, and the look-ahead audit in
`docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md`.

### Prescreening with Vectorized Backtests

Phase 0: vectorized parameter screening:

- Generate N random parameter combinations
- Batch evaluate
- Filter by minimum trades (30+)
- Return top K by Sharpe ratio

Every combination screened is a trial: a large screen lowers the deflated Sharpe of whatever survives it.

### Full Backtests with NautilusTrader

Phase 1: Event-driven backtesting for top candidates:

- High-fidelity simulation with realistic execution
- Slippage and commission modeling
- Multi-asset portfolio backtests (not in QUANTGEN's bridge, which takes single-instrument long/flat rules only)

## Parameter Optimization

### Optuna for Hyperparameter Search

Phase 2: Bayesian optimization with warm-start from prescreening:

```python
import optuna

study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner()
)

study.optimize(objective, n_trials=1000)
```

Optuna is not a QUANTGEN dependency; adding it needs the owner's approval.

### Grid Search vs Bayesian Optimization

| Method | Use Case |
|--------|----------|
| Grid Search | Small parameter space, exhaustive coverage needed |
| Random Search | Large space, quick exploration |
| Bayesian (TPE) | Efficient optimization, exploitation/exploration balance |
| CMA-ES | Continuous parameters, smooth objective |

### Pruning Strategies

- **MedianPruner**: Prune if worse than median of completed trials
- **PercentilePruner**: Prune bottom X% of trials
- **HyperbandPruner**: Multi-fidelity optimization
- **SuccessiveHalvingPruner**: Aggressive early stopping

## Walk-Forward Validation

### Rolling Window Validation

Slide the training/test window through time:

```
[Train 1][Test 1]
    [Train 2][Test 2]
        [Train 3][Test 3]
```

Parameters:
- `train_window`: Training period length
- `test_window`: Out-of-sample test length
- `step_size`: Window advancement increment

### Anchored Walk-Forward

Expand training window while sliding test window:

```
[Train 1      ][Test 1]
[Train 1 + 2      ][Test 2]
[Train 1 + 2 + 3      ][Test 3]
```

Use when historical regime diversity improves model robustness. QUANTGEN's implementation:
`core/quant/validate.py` `walk_forward`.

### Epoch Selection Criteria

Intelligent selection of training periods:

- **Regime-aware**: Match training regimes to expected deployment conditions
- **Volatility-adjusted**: Include both high and low volatility periods
- **Event-inclusive**: Ensure major market events are represented
- **Recency-weighted**: Emphasize recent data while maintaining diversity

### Out-of-Sample Testing

Final validation phase:
- Hold out 20-30% of data for final OOS test
- No parameter tuning on OOS data
- Monte Carlo stress testing
- Regime-conditional performance analysis

## Tearsheet Generation

See the `tearsheet-generator` skill for performance reports.

## Resources

- [VectorBT Documentation](https://vectorbt.dev/)
- [NautilusTrader Docs](https://nautilustrader.io/)
- [Optuna Documentation](https://optuna.readthedocs.io/)
- [QuantStats](https://github.com/ranaroussi/quantstats)
