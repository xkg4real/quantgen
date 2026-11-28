---
name: nautilus-authoring
description: >
  NautilusTrader 1.231 strategy-authoring pitfalls (indicator scale and import paths, frozen StrategyConfig,
  bar-close decisions, string money columns in reports, Actor.log in tests), each checked against the installed
  1.231.0 source. Use before writing or reviewing a Nautilus Strategy, indicator, or test of one.
---

# Authoring NautilusTrader strategies: pitfalls

Extracted 2026-11-23 from cajias/nautilus-trading@998a4ae (MIT, (c) 2026 Raul Cajias):
`skills/nautilus-strategy-authoring/SKILL.md` and `agents/strategy-author.md`. Upstream targets NautilusTrader 1.224
and its own `nt` CLI. Each item was checked against QUANTGEN's pinned 1.231.0 wheel at
`%LOCALAPPDATA%\quantgen\ntvenv\Lib\site-packages\nautilus_trader` (the `.pyx` sources ship with it).

Not taken: the `nt` registry contract (`StrategySpec`, `ConfigBuilder`, entry points, `uv`, `make`), which QUANTGEN
does not use; the Binance Spot MARKET+IOC rule, the `BarFanoutActor` for several strategies on one `TradingNode`,
and signal handlers around a `TradingNode`, all live/paper-node matters outside QUANTGEN; the `strategy-author` agent,
whose orient-author-verify loop is folded in below. In QUANTGEN, the `nautilus-portfolio-bridge` skill and spec
2026-10-26 win over anything here.

## Pitfalls

1. **`RelativeStrengthIndex.value` is in [0, 1], not [0, 100].** Verified: `indicators/momentum.pyx` sets
   `_rsi_max = 1` and `value = _rsi_max - _rsi_max / (1 + rs)`. Write `rsi.value > 0.55`, not `> 55`. `RateOfChange`
   also returns a fraction. Check an indicator's scale in its source before using a threshold.

2. **Import indicators from the package root.** Verified: `nautilus_trader.indicators` re-exports
   `ExponentialMovingAverage`, `RelativeStrengthIndex`, `BollingerBands`, `AverageTrueRange` and the rest. The
   1.231.0 submodules are `averages`, `momentum`, `trend`, `volatility`, `volume`, `spread_analyzer`,
   `fuzzy_candlesticks`, `base`: `nautilus_trader.indicators.rsi` and `.average` do not exist, and neither does
   `indicators.base.indicator` (the base class is `from nautilus_trader.indicators.base import Indicator`).
   A wrong path compiles and fails with `ModuleNotFoundError` at import.

3. **Decide on the bar's close, not its wicks.** Testing `bar.high >= take_profit or bar.low <= stop_loss` inside
   `on_bar` acts on prices the strategy could not have traded at decision time. Decide on `bar.close`; for a real
   intra-bar trigger, rest a stop order in advance. Fill timing depends on the venue config: upstream says a MARKET
   order from `on_bar` fills at the next bar's open, while spec 2026-10-26 section 5.2.3 measured a fill at the same
   bar's close with `bar_execution=True` and `bar_adaptive_high_low_ordering=False` on 1.231.0. Measure it for your
   config; do not assume either.

4. **`StrategyConfig` is a frozen msgspec struct.** Verified: `trading/config.py` declares
   `class StrategyConfig(NautilusConfig, kw_only=True, frozen=True)`. Subclasses inherit the frozen config; writing
   `frozen=True` on the subclass, as QUANTGEN's `PortConfig` does, is harmless and explicit. Keep every parameter in
   the config (QUANTGEN's sandbox has no `__init__` in its ports, rule F3). If configs are built from a dict that
   supplies defaults, that dict's default always wins over the class default: keep one source of defaults.

5. **Report money columns are strings.** Verified: `model/position.pyx` writes `"realized_pnl": str(self.realized_pnl)`,
   so the positions report holds `"-9.48 USD"`, not a float. Strip the currency before arithmetic:
   `df["realized_pnl"].str.replace(r"\s+\w+$", "", regex=True).astype(float)`. Check the dtype of any money column
   (`commissions`, balances) before summing or sorting it.

6. **`Actor.log` cannot be replaced in tests.** Verified: `common/actor.pxd` declares `cdef readonly Logger log`, so
   `actor.log = MagicMock()` raises `TypeError`. Put the logic in a module-level pure function that takes what it
   needs and test that; do not build an `Actor` outside an engine.

7. **A passing `--help` or import proves little.** Exercise the real path: run the backtest on a fixture and check
   fills. In QUANTGEN that means the bridge's own checks (`tools/nautilus/runner.py --check-env`, `--fixtures` against
   `tools/nautilus/golden/`) and the layer-1 tests, as `nautilus-portfolio-bridge` lists.

## Orient, author, verify (adapted from the `strategy-author` agent)

1. Orient: read `CLAUDE.md`, the `nautilus-portfolio-bridge` skill, spec 2026-10-26 sections 3 and 5.2, and the
   existing ports in `tools/nautilus/sandbox.py` (`Port`, `TrendSwitchPort`, `CryptoTrendPort`).
2. Author: config fields on a frozen `StrategyConfig` subclass; subscribe and register in `on_start`; decide in
   `on_bar`; the pitfalls above.
3. Verify: run the real path, not `--help`; leave the suite's pass count no lower than before.
