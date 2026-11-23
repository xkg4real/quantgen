---
name: nautilus-trader
description: >
  NautilusTrader reference for strategy development and backtesting (BacktestEngine, Strategy,
  indicators, bars, Parquet data catalog, API docs). Use when writing or debugging NautilusTrader
  backtest code or looking up its API. Inside QUANTGEN, the nautilus-portfolio-bridge skill wins over this one.
version: "2.0.0-quantgen.1"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Nautilus Trader Skill

> **QUANTGEN audit, 2026-11-23.** Copied from HyperFrequency/skills@7532af7 (MIT per its README). Removed:
> the Hyperliquid mainnet adapter monkey-patch (`hyperliquid_patch.py`), the live runner (`live_trading.py`),
> the leverage setter (`set_leverage.py`), the hyperfix README, CHANGELOG and requirements, `references/hyperliquid.md`,
> and this file's live-node, leverage, private-key and patch sections. From `references/`, the venue-integration,
> adapter, live-node, developer-guide and installation pages were dropped. Fixed for the pinned 1.231.0 wheel:
> the `Indicator` import and the `BacktestEngineConfig` logging argument (checked against the installed source).
> The reference docs are a v1.222.0 scrape with code blocks collapsed onto one line: before relying on an API,
> check it in `%LOCALAPPDATA%\quantgen\ntvenv\Lib\site-packages\nautilus_trader`.
> Inside QUANTGEN, Nautilus runs only in `tools/nautilus/sandbox.py` under its spec: read `nautilus-portfolio-bridge`.

Comprehensive assistance with NautilusTrader development for research backtests.

---

## Overview

This skill covers:

- Strategy development with NautilusTrader
- Backtesting using the Parquet data catalog

### When to Use

- Building trading strategies with NautilusTrader
- Running backtests with historical data
- Working with multi-timeframe (MTF) indicators

---

## Prerequisites

QUANTGEN installs NautilusTrader only into its hash-pinned venv from `requirements-nautilus.txt`
(`nautilus-trader==1.231.0`), never into the global interpreter. Install nothing else for this skill.

### Verify Installation

```python
import nautilus_trader
print(f"Nautilus Trader: {nautilus_trader.__version__}")
# QUANTGEN pins 1.231.0; the upstream skill was tested with v1.222.0
```

---

## Quick Start

### Basic Strategy Template

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from decimal import Decimal

class MyStrategyConfig(StrategyConfig):
    instrument_id: str
    bar_type: str
    trade_size: Decimal = Decimal("0.1")

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.trade_size = config.trade_size

    def on_start(self):
        self.instrument = self.cache.instrument(self.instrument_id)
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar):
        # Your strategy logic here
        pass

    def on_stop(self):
        # Upstream called self.close_all_positions(...) here. In QUANTGEN that verb and six others
        # (modify_order, cancel_orders, cancel_all_orders, close_position, market_exit, submit_order_list)
        # fail the T-RO-01 scan, and the bridge never liquidates at the end.
        pass
```

---

## Strategy Development

### Heiken Ashi Indicator

```python
from nautilus_trader.indicators.base import Indicator  # 1.231.0 path; upstream's indicators.base.indicator does not exist
from nautilus_trader.model.data import Bar

class HeikenAshi(Indicator):
    """Heiken Ashi candle smoothing indicator."""

    def __init__(self):
        super().__init__([])
        self.ha_open = 0.0
        self.ha_close = 0.0
        self.ha_high = 0.0
        self.ha_low = 0.0
        self._prev_ha_open = None
        self._prev_ha_close = None
        self.initialized = False

    def handle_bar(self, bar: Bar) -> None:
        o, h, l, c = float(bar.open), float(bar.high), float(bar.low), float(bar.close)

        self.ha_close = (o + h + l + c) / 4

        if self._prev_ha_open is None:
            self.ha_open = (o + c) / 2
        else:
            self.ha_open = (self._prev_ha_open + self._prev_ha_close) / 2

        self.ha_high = max(h, self.ha_open, self.ha_close)
        self.ha_low = min(l, self.ha_open, self.ha_close)

        self._prev_ha_open = self.ha_open
        self._prev_ha_close = self.ha_close
        self.initialized = True

    @property
    def is_bullish(self) -> bool:
        return self.ha_close > self.ha_open

    @property
    def is_bearish(self) -> bool:
        return self.ha_close < self.ha_open

    def reset(self) -> None:
        self._prev_ha_open = None
        self._prev_ha_close = None
        self.initialized = False
```

### Multi-Timeframe EMA Strategy

Key concepts:

- HTF (Higher Timeframe): Determines trend direction via EMA crossover
- LTF (Lower Timeframe): Entry timing via Heiken Ashi confirmation
- Entry: HA color change in trend direction
- Exit: HA color reversal

---

## Backtesting

### Engine Setup

```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from decimal import Decimal

def run_backtest():
    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(log_level="INFO"),  # 1.231.0 has no logging_level field
    )
    engine = BacktestEngine(config=config)

    # Add venue
    engine.add_venue(
        venue=Venue("HYPERLIQUID"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(100_000, USD)],
    )

    # Load data from catalog
    catalog = ParquetDataCatalog("./data_catalog")

    instruments = catalog.instruments()
    for instrument in instruments:
        engine.add_instrument(instrument)

    bars = catalog.bars()
    engine.add_data(bars)

    # Add strategy
    strategy = MyStrategy(config=MyStrategyConfig(
        instrument_id="SOL-USD.HYPERLIQUID",
        bar_type="SOL-USD.HYPERLIQUID-5-MINUTE-LAST-EXTERNAL",
        trade_size=Decimal("1.0"),
    ))
    engine.add_strategy(strategy)

    # Run
    engine.run()

    # Results
    print(engine.trader.generate_account_report(Venue("HYPERLIQUID")))
    print(engine.trader.generate_order_fills_report())
    print(engine.trader.generate_positions_report())

    engine.dispose()
```

The venue name here is only a label for the simulated exchange. QUANTGEN's sandbox builds its engine, venue
(`SIM`, CASH, NETTING) and instruments exactly as spec 2026-10-26 section 5.2.3 says, not like this template.

### Data Catalog

See `references/backtesting.md` and `references/data.md` for detailed catalog operations:

- `ParquetDataCatalog` - Query and manage Parquet data files
- `BarDataWrangler` - Convert pandas DataFrames to Nautilus Bar objects
- `write_data()` - Persist data to catalog
- `query()` - Retrieve data with time filters

QUANTGEN's bridge uses no catalog: the parent writes `bars.csv` into a temp dir and the child builds each `Bar`
with the wrangler's own constructor calls (spec section 5.2.4).

---

## Configuration

### Bar Type Format

```
{symbol}.{venue}-{step}-{aggregation}-{price_type}-{source}

Examples:
SOL-USD.HYPERLIQUID-1-HOUR-LAST-EXTERNAL
SOL-USD.HYPERLIQUID-5-MINUTE-LAST-EXTERNAL
BTC-USD.HYPERLIQUID-15-MINUTE-LAST-EXTERNAL
SPY.SIM-1-DAY-LAST-EXTERNAL          (QUANTGEN pilot 1)
BTC/USD.SIM-1-DAY-LAST-EXTERNAL      (QUANTGEN pilot 2)
```

---

## Troubleshooting

### Missing Data in Backtest

1. Verify data catalog path exists
2. Check instrument IDs match between data and strategy config
3. Ensure bar types are correctly formatted

### Position Not Closing

Check that `reduce_only=True` is set on exit orders for netting accounts.

---

## Reference Files

Detailed documentation is available in `references/` (official nautilustrader.io pages, scraped at v1.222.0):

| File | Description |
|------|-------------|
| `strategies.md` | Trading, analysis, position and risk API pages, docs home |
| `backtesting.md` | Data catalog and persistence API |
| `data.md` | Cache and data API, `model/data` |
| `getting_started.md` | Quickstart, low- and high-level backtest tutorials |
| `concepts.md` | Core concepts and architecture (live and adapter pages removed) |
| `api.md` | API reference (adapter pages removed) |

Use `Read` with an offset, or `Grep`, on the large files; `api.md` is about 430 KB.
