# 01. NautilusTrader backtest API, as the QUANTGEN bridge would use it

Scope: the engine side of the NautilusTrader bridge. It maps the low-level `BacktestEngine` flow for one US
equity on daily bars, the fee and fill models, the reports, the daily equity series, the live/order surface
that QUANTGEN must refuse, and the packaging facts. QUANTGEN's gate, ledger and Lab inputs are in the sibling
map `02_quantgen_gate_ledger_lab.md`.

Method. I installed `nautilus_trader==1.231.0` into a separate venv (Python 3.13.17, numpy 2.3.5,
pandas 2.3.3; no scipy). I did not touch the global interpreter. I read the installed source, the docs at the
`v1.231.0` git tag (backtesting pages, orders, execution, data, reports, accounting, live), the release notes and
PyPI metadata. The API reference pages are only on the blocked docs site, so the installed source served as the
API reference. I ran three probe scripts on synthetic,
seeded data only. No real SPY or BTC data was used, so no pilot number exists here. I wrote no ledger row.
The probe scripts live outside the repo, in the session scratchpad (`.../scratchpad/nt_probe/`). Their full
text and output are in the appendices.

Citation keys.

- `file:line` with no prefix is a QUANTGEN path at commit `f5742ab` (Linux clone).
- `nt:<path>:<line>` is the installed wheel source, `site-packages/nautilus_trader/<path>`, version 1.231.0.
  The same file is at `https://github.com/nautechsystems/nautilus_trader/blob/v1.231.0/nautilus_trader/<path>`.
  I compared four files byte for byte with the tag (`backtest/engine.pyx`, `backtest/models/fee.pyx`,
  `analysis/analyzer.py`, `risk/engine.pyx`). They are identical, so the line numbers match the tag.
- `docs:<page>` is `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/docs/concepts/<page>`.
  The site `https://nautilustrader.io/docs/latest/` was blocked by this session's proxy (HTTP 403), so I read
  the same docs from the git tag instead.
- `probe:<key>` is a measured line in the probe output (Appendix D).

---

## 0. Fourteen findings that shape the bridge

1. **It runs, it is fast, and it is deterministic.** A 600-bar run takes 0.06 to 0.09 s. Twelve runs on 5,600
   bars (about 2004 to 2026) take 10.9 to 11.8 s with a fresh engine per run (`probe:timing_12_fresh_engines_5600_bars_s`).
   The fills report hashes the same across two runs in one process and across two separate processes, once
   the random UUID columns are dropped (`probe:hash_fills_nouuid_A_B` = `4443e95f46b89f8d` every time).
2. **A MARKET order sent from `on_bar` fills at the close of that same bar.** 21 of 21 fills did
   (`probe:A_fill_px`). The engine moves the market through the bar's O, H, L, C first, then calls the strategy,
   then settles the queued order against the book left at the close (`nt:backtest/engine.pyx:1716, 1724, 1727`;
   `docs:backtesting/bar-execution.md`, "Order submission timing"). This is QUANTGEN's own convention:
   decide at close t, trade at close t, earn t to t+1 (`core/quant/backtest.py:116-119`).
3. **`AT_THE_CLOSE` and `AT_THE_OPEN` are rejected in backtest.** The reason is "time in force AT_THE_CLOSE is
   not currently supported" (`nt:backtest/engine.pyx:5333-5339` for MARKET, `:5431-5437` for LIMIT;
   `probe:F_at_the_close_rejected_first`). There is no `MARKET_ON_CLOSE` order type at all. A plain GTC MARKET
   order from `on_bar` already behaves like a market-on-close order on daily bars.
4. **There is no native next-bar-open fill.** The docs say so (`docs:backtesting/bar-execution.md`, note under
   "Order submission timing"). A latency model on bars alone fills at the next bar's close, not its open
   (`probe:G_latency_fill_px`). I built a working next-open recipe: one synthetic trade print per day at the
   open, plus a latency model, plus a strategy that waits while an order is in flight. All 20 fills landed on
   the next open (`probe:nextopen_fill_px`).
5. **The PortfolioAnalyzer returns are wrong for this use.** On a CASH account the account balance is cash only.
   Buying SPY drops the balance to $6.60 (`probe:acct_report_first3_after_start`). The analyzer builds returns
   from that balance and resamples to calendar days (`nt:analysis/analyzer.py:816-869`, `:856`). The result runs
   from -99.99% to +19,252% per day, with 172 weekend rows (`probe:analyzer_returns_min_max`,
   `probe:analyzer_returns_weekend_rows`). It printed a Sharpe of +1.94 for a run whose true Sharpe is -1.90
   (`probe:A_analyzer_stats`, `probe:A_parity_1x`). The bridge must build its own equity series: cash plus
   quantity times the bar close, recorded in `on_bar`.
6. **A CASH account can kill the run silently.** The risk engine checks notional against free cash but ignores
   the fee (`nt:risk/engine.pyx:942-955`; `nt:accounting/accounts/cash.pyx:482-493`). An order sized to 100% of
   cash passes, fills, pushes cash below zero, and raises `AccountBalanceNegative`. The engine then stops the
   whole backtest and returns normally (`nt:backtest/engine.pyx:1742-1745`). In the probe it stopped after 343
   of 600 bars (`probe:nohead_bars_seen_vs_loaded`). The bridge must size with headroom and fail closed on a
   forced stop.
7. **QUANTGEN's bp-of-notional cost is exact as a custom `FeeModel`.** A 10-line Python subclass charges
   `qty x price x bp / 1e4` per fill, rounded to the cent (`probe:A_fee_vs_bp_formula`). It gives identical
   commissions to the built-in `MakerTakerFeeModel` with `taker_fee=0.005` (`probe:D_maker_taker_vs_custom_commissions_equal`).
   The 2x-cost rerun is the same model with `stress=2.0` in a fresh engine.
8. **Parity on synthetic data passes with a wide margin.** Signal agreement 100%, daily-return correlation
   0.999999, Sharpe difference 0.002 at 1x and 0.006 at 2x (`probe:A_parity_1x`, `probe:C_2x_parity`). The
   next-open variant is much closer to the limit: correlation 0.9914 and Sharpe difference 0.028
   (`probe:nextopen_vs_local_close_convention`). On real SPY, with real overnight gaps, a next-open run could
   fail the 0.99 correlation bar for reasons that are execution timing, not code error. Parity should compare
   like with like (close fills). Next-open should be a separate, labelled realism delta.
9. **`Equity` cannot hold fractional shares.** It hard-codes `size_precision=0` and `size_increment=1`
   (`nt:model/instruments/equity.pyx:115-117`). A `Cfd` with `asset_class=EQUITY` and 4 size decimals works as a
   fractional stand-in on a CASH account (`probe:E_fractional_first_qty` = 458.0302). Whole shares already pass
   parity at $100,000 (`probe:A_parity_1x`).
10. **QUANTGEN's T-RO-01 scan would fail the bridge's strategy file, and it would miss the real danger.** The
    strategy must call `self.submit_order(...)`. `submit_order` is a forbidden text token and a forbidden call
    (`tests/macro_m0_harness.py:29, 45`; also `tests/acceptance.py:64`). I ran the repo's own scanner on a copy
    of the probe placed at `core/bridge/nautilus_sandbox.py`. It reported two hits. I also ran it on a file that
    imports `nautilus_trader.live.node.TradingNode`, `nautilus_trader.adapters.binance` and `nautilus_pyo3`, then
    calls `node.run()`. It reported nothing. The import check only looks at the top-level package name
    (`tests/macro_m0_harness.py:92, 95`). The owner must rule on a narrow T-RO-01 amendment before any bridge
    code lands (section 9).
11. **A runtime import block on `nautilus_trader.live` would break the backtest.** The kernel that every
    `BacktestEngine` builds imports `nautilus_trader.live.data_engine`, `.execution_engine` and `.risk_engine`
    (`nt:system/kernel.py:75-77`). `nautilus_trader.config` re-exports `TradingNodeConfig` and the live client
    configs (`nt:config/__init__.py:67-76`). After a backtest, seven `nautilus_trader.live.*` modules plus
    `asyncio`, `socket`, `ssl` and `uvloop` are loaded (`probe:live_or_adapters_loaded`, `probe:third_party_net_loaded`).
    No `nautilus_trader.adapters.*` or `nautilus_trader.network` module is loaded. The guard must be a static
    allow-list on QUANTGEN's own source, plus a runtime check that no adapter or network module was imported.
12. **1.231.0 is the last 1.x release.** The release notes call it "the final NautilusTrader `1.x` release with
    support for the legacy Cython v1 core". `develop` moves to v2 (Rust + PyO3). The v1 line gets critical
    security backports for about three months after the cutover
    (`https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/RELEASES.md`, lines 5-24).
    PyPI already lists `2.0.0rc2` to `2.0.0rc7` (2 Aug to 15 Oct 2026) (`https://pypi.org/pypi/nautilus_trader/json`).
    The docs at the `v1.231.0` tag already show v2 import paths that fail on the 1.231.0 wheel (section 10.4).
13. **The trial ledger will not double-count the second engine.** `config_id` hashes only the row-set key
    (`core/quant/gate_ledger.py:60-61, 168-171`). The key has no engine, cost or source field. A Nautilus
    replica of a local variant gets the same `config_id`, and `append` returns the existing row
    (`core/quant/gate_ledger.py:337-346`). This is right for the DSR count. The bridge must fill the key fields
    exactly as the local run does.
14. **`FillModel` reseeds Python's global `random` module.** With a seed it calls `random.seed(seed)`; without
    one it calls `random.seed()` from OS entropy (`nt:backtest/models/fill.pyx:75, 77`;
    `probe:fillmodel_reseeds_global_random`). Running Nautilus in its own subprocess keeps this away from any
    QUANTGEN code that uses `random`.

---

## 1. Install and environment facts

| Item | Value | Source |
|---|---|---|
| Venv | `scratchpad/ntvenv`, Python 3.13.17 | this session |
| Installed | nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3, pyarrow 26.0.0, fsspec 2026.2.0, msgspec 0.22.0, click 8.5.0, portion 2.6.3, pytz 2026.5, tqdm 4.70.1, tzdata 2026.5, uvloop 0.22.1, python-dateutil 3.0.0, six, sortedcontainers | `pip list` in the venv |
| scipy | not installed, not required | `Requires-Dist` in wheel METADATA |
| Global interpreter | untouched: numpy 2.3.5, pandas 2.3.3, scipy 1.18.0, and no `nautilus_trader` (checked after all probes) | `python3 -I -c ...` in this session |
| Install wall time | 5 min 47 s wall, 15 s CPU; the rest was network wait through the proxy. Not a useful Windows estimate. | `time` in this session |

The QUANTGEN pins are compatible with Nautilus 1.231.0. Nautilus needs `numpy>=1.26.4` and
`pandas>=2.3.3,<4.0.0` (wheel METADATA). pandas 2.3.3 is exactly the floor, so the pin cannot move down. Two
Nautilus pins are exact: `fsspec==2026.2.0` and, off Windows, `uvloop==0.22.1`. I did not check whether they
conflict with QUANTGEN's other dependencies (gs-quant, yfinance, flet) in one environment. UNVERIFIED. This is a
second reason, after the frozen-study rule, to keep Nautilus in its own venv and call it as a subprocess.

Frozen guard clause (d) reads the versions of the interpreter that runs the tests
(`tests/frozen_guard.py:39, 85-91`). A separate venv used only as a subprocess does not change that interpreter.

---

## 2. The low-level flow, step by step

All names below are from the 1.231.0 wheel. Import paths matter: see section 10.4.

### 2.1 Engine

```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig
engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGPROBE-001"),
                                             logging=LoggingConfig(log_level="ERROR")))
```

`BacktestEngineConfig` defaults: `trader_id="BACKTESTER-001"`, a `CacheConfig(drop_instruments_on_reset=False)`,
default data, risk and exec engine configs, `run_analysis=True` (`nt:backtest/config.py:386-392`).
`log_level="ERROR"` keeps the console quiet. Errors such as a forced stop still print.

### 2.2 Venue

```python
engine.add_venue(
    venue=Venue("ARCA"), oms_type=OmsType.NETTING, account_type=AccountType.CASH,
    base_currency=USD, starting_balances=[Money(100_000, USD)],
    fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=42),
    fee_model=BpsNotionalFeeModel(50.0),         # section 5
    latency_model=None,                           # zero latency: same-bar-close fills
    bar_execution=True, bar_adaptive_high_low_ordering=False,
    allow_cash_borrowing=False)
```

Full signature: `nt:backtest/engine.pyx:502-536`. Parameters that matter for the bridge:

| Parameter | Default | Bridge setting and reason |
|---|---|---|
| `oms_type` | required | `NETTING`: one net position per instrument, like a weight. |
| `account_type` | required | `CASH` for SPY. No leverage, no shorting needed for a long/flat rule. |
| `base_currency` | `None` | `USD` for SPY. Must be `None` for BTC/USD (section 11). |
| `starting_balances` | required | One `Money` per currency. |
| `fill_model` | `FillModel()` (`nt:backtest/engine.pyx:640-641`) | Pass one with an explicit `random_seed`. The low-level engine type-checks it as a `FillModel` (`:650`). |
| `fee_model` | `MakerTakerFeeModel()` (`nt:backtest/engine.pyx:643-644`) | A custom bp-of-notional model (section 5). |
| `latency_model` | `None` | `None` for parity runs. |
| `book_type` | `L1_MBP` | Keep. Bars only update an L1 book (`docs:backtesting/data-and-venues.md`). |
| `bar_execution` | `True` | Keep. Bars move the matching engine (`nt:backtest/engine.pyx:596-597`). |
| `bar_adaptive_high_low_ordering` | `False` | Irrelevant for MARKET orders sent at the close. Matters only for resting stops and limits inside a bar (`nt:backtest/engine.pyx:598-604`). |
| `allow_cash_borrowing` | `False` | Keep `False`. Size with headroom instead (section 4). |
| `use_random_ids` | `False` | Keep. Venue order IDs then stay deterministic (`nt:backtest/engine.pyx:584-586`). |
| `trade_execution` | `True` | Needed only by the next-open recipe (open prints are trade ticks). |

`engine.change_fill_model(venue, model)` exists (`nt:backtest/engine.pyx:715`). There is no
`change_fee_model`. A different cost level therefore needs a new engine (section 5.3).

### 2.3 Instrument

```python
spy = Equity(instrument_id=InstrumentId(Symbol("SPY"), Venue("ARCA")), raw_symbol=Symbol("SPY"),
             currency=USD, price_precision=2, price_increment=Price.from_str("0.01"),
             lot_size=Quantity.from_int(1), ts_event=0, ts_init=0,
             maker_fee=Decimal("0"), taker_fee=Decimal("0"))
engine.add_instrument(spy)
```

Constructor: `nt:model/instruments/equity.pyx:85-104`. `size_precision` is fixed at 0 and `size_increment` at 1
(`:115-117`). The probe used `lot_size=1`. I did not test whether a larger `lot_size` restricts order sizes.
UNVERIFIED. `maker_fee` and `taker_fee` are read only by
`MakerTakerFeeModel`. `TestInstrumentProvider.equity()` exists (`nt:test_kit/providers.py:615-627`) but sets
`lot_size=100` and a hard-coded AAPL ISIN. It lives in `test_kit`. The bridge should build its own `Equity`.

Price precision. Adjusted prices have more than two decimals. The wrangler rounds every price to the
instrument's precision (`nt:persistence/wranglers.pyx:779-791`; `probe:wrangler_rounds_to_price_precision`,
300.0049 became 300.00). Use `price_precision=4` and `price_increment=0.0001` for adjusted SPY. I ran that: 13
fills, all at the same-bar close, at 4-decimal prices.

Corporate actions. The 1.231.0 package has no dividend or split cash-flow logic (a search for "dividend" finds
only `model/greeks.pyx` and the IB adapter). Feed total-return-adjusted prices, as QUANTGEN's local backtest does.

### 2.4 Bar type and bars

```python
bar_type = BarType.from_str("SPY.ARCA-1-DAY-LAST-EXTERNAL")
bars = BarDataWrangler(bar_type, spy).process(df)    # df: open, high, low, close, volume; UTC index
engine.add_data(bars)
```

- `EXTERNAL` matters. Internally aggregated bars do not move the matching engine
  (`nt:backtest/engine.pyx:4757-4758`).
- `LAST` (or `MID`) turns each bar into four synthetic trades, O, H, L, C (`nt:backtest/engine.pyx:4804-4805,
  4850-4880`). The volume is split into quarters, with the remainder on the close.
- Timestamps. `ts_init` must be the bar's close (`docs:backtesting/bar-execution.md`, "Bar timestamp
  convention"). The probe stamps each daily bar at 21:00 UTC. For real data, stamp each bar at its session
  close. `process(df, ts_init_delta=0)` sets `ts_event = ts_init = index` (`nt:persistence/wranglers.pyx:727-776`).
- The wrangler reads columns **by position**: `values[0]` is open, `[1]` high, `[2]` low, `[3]` close, `[4]`
  volume (`nt:persistence/wranglers.pyx:779-791`). Reorder the frame explicitly. A wrong order raised
  `ValueError: high was < open` in the probe (`probe:wrangler_wrong_column_order`). `Bar` checks only that the
  high and low bound the open and close (`nt:model/data.pyx:1522-1526`). A swap of open and close alone passes
  those checks, so it would build wrong bars silently (inferred from the checks; not run). The bridge should
  assert the column order.
- Volume. If the frame has no `volume` column, the wrangler uses 1,000,000 (`:730, 766-767`). Use real volume
  in instrument units. With L1 books, a MARKET order larger than the displayed size at the close fills the
  rest one tick worse (`docs:backtesting/fill-prices-and-matching.md`, "L1 books"). The displayed size at the
  close is about one quarter of the bar volume. For SPY this never binds. For thin BTC bars it might.

### 2.5 Strategy

```python
class SmaTargetConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    sma_window: int = 200
    weight_on: float = 1.0
    headroom_bp: float = 0.0

class SmaTargetWeight(Strategy):
    def on_start(self):
        self.instrument = self.cache.instrument(self.config.instrument_id)
        self.subscribe_bars(self.config.bar_type)
    def on_bar(self, bar):
        # 1. pre-trade mark-to-market at this close: cash + qty x close
        # 2. signal from closes up to and including this bar
        # 3. target qty = floor(w x equity / (close x (1 + headroom)))  -> one MARKET order for the difference
        ...
        self.submit_order(self.order_factory.market(instrument_id, side, qty, time_in_force=TimeInForce.GTC))
```

The full class is in Appendix A. Notes:

- `self.portfolio.account(venue).balance_total(USD)` is cash. `self.portfolio.net_position(instrument_id)`
  is the signed quantity (`nt:portfolio/portfolio.pyx:816, 1735`).
- `self.portfolio.equity(venue)` returns cash plus mark value for cash accounts
  (`nt:portfolio/portfolio.pyx:1176-1182`). With bars only it matched my own `cash + qty x close` to 1.5e-11
  (`probe:A_parity_1x`, field `nt_equity_vs_portfolio_equity_maxdiff`). With open prints mixed in, it marks at
  the latest print (the open), not the close. The gap reached $2,405 (`probe:nextopen_vs_local_close_convention`).
  I confirmed that the marked value equals `cash + qty x open` to 3e-11 on all 53 differing days. Use the bar
  close directly.
- `order_factory.market(instrument_id, order_side, quantity, time_in_force=GTC, reduce_only=False,
  quote_quantity=False, ...)` (`nt:common/factories.pyx:236-248`).
- Floor the target quantity to the size increment. `instrument.make_qty(value)` uses banker's rounding by
  default; `make_qty(value, round_down=True)` floors (`nt:model/instruments/base.pyx:753-784`). Rounding up can
  overdraw a CASH account. The probe floors with `Decimal` before calling `make_qty`.
- Trade only when needed. A loop that re-targets the exact weight every bar trades small drift amounts. With
  fractional sizes the probe made 60 fills, 46 of them under $1,000 notional, against 14 signal switches. With
  whole shares it made 21 fills, 7 under $1,000. QUANTGEN charges cost only when the position changes
  (`core/quant/backtest.py:117-118`). For parity, the bridge strategy should trade only on a target-weight
  change (or a drift band the owner sets). I did not implement that in the probe.

### 2.6 Run

```python
engine.add_strategy(strategy)
engine.run()                 # run(start=None, end=None, run_config_id=None, streaming=False)
result = engine.get_result() # iterations, total_orders, total_positions, backtest_end, stats_returns ...
engine.dispose()
```

`run()` calls `end()` unless streaming (`nt:backtest/engine.pyx:1313-1380`). Repeated runs: `engine.reset()`
keeps data, instruments, venues and strategies, and clears orders, positions and balances
(`docs:backtesting/apis-and-runs.md`, "Repeated runs"). A reset rerun gave the same fills hash
(`probe:reset_rerun_same_fills_hash`). Use `clear_strategies()` before adding a new strategy instance.

### 2.7 Reports

Call them on `engine.trader` (`nt:trading/trader.py:843-891`); they wrap `ReportProvider`
(`nt:analysis/reporter.py:33-218`).

| Call | Rows | Key columns (from the probe) | Deterministic? |
|---|---|---|---|
| `generate_orders_report()` | one per order | order fields, `init_id` (UUID) | yes, after dropping `init_id` |
| `generate_order_fills_report()` | one per filled order | `side, quantity, filled_qty, avg_px, slippage, commissions, status, time_in_force, ts_last` | yes, after dropping `init_id` |
| `generate_fills_report()` | one per fill event | `order_side, last_qty, last_px, commission, liquidity_side, trade_id, venue_order_id, position_id, ts_event, event_id` (UUID) | yes, after dropping `event_id` |
| `generate_positions_report()` | one per position (plus snapshots) | `side, quantity, peak_qty, avg_px_open, avg_px_close, realized_pnl, realized_return, commissions, ts_opened, ts_closed` | **no**: closed NETTING snapshots carry a random UUID suffix in `position_id` (two runs gave `...-000-1f1346a3-...` and `...-000-ead810ea-...`). Strip the suffix before hashing. |
| `generate_account_report(venue)` | one per account state | `total, free, locked, currency` as strings | yes |

Full column lists: `probe:fills_report_columns`, `probe:order_fills_columns`, `probe:positions_report_columns`,
`probe:account_report_columns`.

### 2.8 The daily equity and return series

Do not use `engine.portfolio.analyzer.returns()` or its statistics for this case (finding 5). Do not use the
account report as equity: on a CASH account it is cash only. Use the strategy's own record:

- In `on_bar(t)`, before any order, record `equity_t = cash + qty x close_t`. The cash already includes every
  fill up to the close of t-1.
- Daily return `r_t = equity_t / equity_{t-1} - 1`. This is the return from close t-1 to close t, net of the fee
  paid at close t-1. It lines up with QUANTGEN's `strat_daily[t-1] = held[t-1] x daily[t-1] - costs[t-1]`
  (`core/quant/backtest.py:116-119`).
- The last bar's own trade is not reflected. That matches the local backtest, which drops the last day too.
- Turnover per session, for `walk_forward(..., turnover=...)` (`core/quant/validate.py:345-352`): the sum of
  fill notionals at close t divided by `equity_t`. I did not compute it in the probe.

---

## 3. Which price a daily-bar order fills at

| Mode | Setup | Fill price | Measured |
|---|---|---|---|
| Parity (default) | MARKET, GTC, zero latency, bars only | close of the decision bar | 21 of 21 (`probe:A_fill_px`) |
| AT_THE_CLOSE | MARKET, `TimeInForce.AT_THE_CLOSE` | rejected, never fills | 0 fills, 53 rejections (`probe:F_at_the_close_*`) |
| Latency on bars | `LatencyModel(base_latency_nanos=3.6e12)`, bars only | close of the **next** bar | `probe:G_latency_fill_px` (fill stamped at the next bar, at its close) |
| Next open | latency + one trade print per day at 14:30 UTC + in-flight-aware strategy | open of the next bar | 20 of 20 (`probe:nextopen_fill_px`) |
| Slippage | `FillModel(prob_slippage=1.0, random_seed=42)` | close plus one tick against the order | BUY +0.01, SELL -0.01 (`probe:slip1_px_minus_close`) |

Two traps in the latency modes:

- The strategy must not send a second order while the first is in flight. My first latency run double-bought,
  went negative and was force-stopped (`err` lines in Appendix D). The fix checks
  `self.cache.orders_inflight(instrument_id=...)` and `self.cache.orders_open(...)` (Appendix B, `InflightAware`).
- Sizing at close t and filling at open t+1 can overdraw cash on a gap up. The first next-open run stopped at
  -$99.27 (Appendix D). I used 100 bp headroom in the working run.

`LatencyModel()` with no arguments has a 1 ms base latency (`nt:backtest/models/latency.pyx:61-84`). Passing
`latency_model=None` to `add_venue` means zero latency. Keep it `None` for parity runs.

---

## 4. Cash, fees and forced stops on a CASH account

- **Where the fee goes.** Each fill's commission is a `Money` in USD (2 decimals) and is taken from cash at the
  fill. The first fill: BUY 458 at 217.24, commission 497.48 USD; the bp formula gives 497.4796
  (`probe:A_first_fill`, `probe:A_fee_vs_bp_formula`).
- **What the account balance is.** Cash only. It went 100,000.00, then 6.60 after the first buy, then 653.72
  after a small sale, then 96,595.20 after the exit (`probe:acct_report_first3_after_start`).
- **The pre-trade check ignores the fee.** `NOTIONAL_EXCEEDS_FREE_BALANCE` compares free cash with the
  order's balance impact (`nt:risk/engine.pyx:942-955`). For a cash account that impact is the notional alone
  (`nt:accounting/accounts/cash.pyx:482-493`).
- **What happens when cash goes negative.** `AccountBalanceNegative` is an `AccountError`. The main loop catches
  it, sets the global force-stop flag, logs `Stopping backtest from AccountBalanceNegative(...)`, and returns
  (`nt:backtest/engine.pyx:1742-1745`). `run()` then calls `end()` (`:1378-1380`). No exception reaches the
  caller.
- **How to detect a forced stop.** Any one of these works; the bridge should check all three:
  `nautilus_trader.common.component.is_backtest_force_stop()` is `True` (`nt:common/component.pyx:619-620`;
  `probe:nohead_force_stop_flag`); bars seen by the strategy fewer than bars loaded (343 of 600); and
  `get_result().backtest_end` before the last bar's timestamp (2021-04-26 against 2022-04-20).
- **Two ways to avoid it.** Size with headroom: `qty = floor(w x equity / (close x (1 + cost_bp/1e4)))`.
  The probe used headroom equal to the cost (50 bp at 1x, 100 bp at 2x) and never stopped. Or set
  `allow_cash_borrowing=True`. That run completed, but cash reached -$439.52
  (`probe:borrow_min_cash`). That is a small implicit loan, which changes the economics. I recommend headroom
  plus a fail-closed check. A MARGIN account with leverage 1 is another option. UNVERIFIED: I did not run it.

---

## 5. Fees, fills and the 2x-cost rerun

### 5.1 Fee models in 1.231.0

| Model | Charge | Source |
|---|---|---|
| `FeeModel` | abstract; `get_commission(order, fill_qty, fill_px, instrument) -> Money` | `nt:backtest/models/fee.pyx:33-64` |
| `MakerTakerFeeModel()` | notional x `instrument.maker_fee` or `taker_fee`, by liquidity side; Decimal arithmetic | `nt:backtest/models/fee.pyx:67-112` |
| `FixedFeeModel(commission, charge_commission_once=True)` | a fixed `Money` per order (or per fill) | `nt:backtest/models/fee.pyx:115-165` |
| `PerContractFeeModel(commission)` | `commission x fill_qty x legs` | `nt:backtest/models/fee.pyx:168-207` |
| custom subclass | anything; the probe's `BpsNotionalFeeModel` | Appendix A |

A Python subclass of the Cython `FeeModel` works: the matching engine calls the Python override. The custom
model and `MakerTakerFeeModel` with `taker_fee=0.005` gave identical commission strings on every fill
(`probe:D_maker_taker_vs_custom_commissions_equal`). All MARKET fills are TAKER (`probe:A_first_fill`).

Exactness. Nautilus charges `|qty| x price x bp` in dollars at each fill, rounded to the cent. QUANTGEN charges
`|dw| x bp` as a fraction of NAV (`core/quant/backtest.py:117-118`; `core/quant/costed.py:157-158`). For a 0/1
weight these agree, up to share rounding and the cent. One convention differs and the bridge must decide it:
`costed_path` leaves the **initial entry uncosted** (`core/quant/costed.py:134, 155-157`); `run_backtest` costs it
(`core/quant/backtest.py:117`); Nautilus always costs it. The probe's local reference used the `run_backtest`
convention. If the gate uses `costed_path`, the first Nautilus day differs by one cost charge.

### 5.2 Fill models in 1.231.0

`FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=None)` (`nt:backtest/models/fill.pyx:34-79`).
On an L1 book `prob_slippage` moves a fill one tick against the order; `prob_fill_on_limit` is the chance a
touched limit fills (`docs:backtesting/fill-models.md`). Other classes in the same file: `BestPriceFillModel`
(`:170`), `OneTickSlippageFillModel` (`:244`), `TwoTierFillModel` (`:296`), `ProbabilisticFillModel` (`:364`),
`SizeAwareFillModel` (`:431`), `LimitOrderPartialFillModel` (`:527`), `ThreeTierFillModel` (`:596`),
`MarketHoursFillModel` (`:686`), `VolumeSensitiveFillModel` (`:776`), `CompetitionAwareFillModel` (`:862`).
Their tier sizes are fixed unit counts (for example 10, or 50/30/20 units), so check scale before using one
(`docs:backtesting/fill-models.md`, "Available models").

For SPY one tick is $0.01, about 0.5 bp at $200. QUANTGEN's 50 bp cost row (`core/quant/validate.py:78`)
dwarfs it. The bridge should keep `prob_slippage=0` and carry all cost in the fee model, so the 2x rule doubles
one number. Always pass `random_seed` (finding 14).

### 5.3 Running 1x and 2x

- Build one engine per cost level. The fee model is fixed at `add_venue`, and there is no `change_fee_model`.
- Use `BpsNotionalFeeModel(bp, stress=1.0)` and `BpsNotionalFeeModel(bp, stress=2.0)`. QUANTGEN's own rule is
  "every result is rerun at 2x (`stress=2.0`)" (`core/quant/costed.py:8`, `:145`).
- Raise the headroom with the cost, or the 2x run can force-stop.
- Measured: total commission 6,276.22 at 1x and 12,136.90 at 2x; final equity 80,066.35 and 74,716.61
  (`probe:A_1x_total_commission`, `probe:C_2x_*`). The 2x total is not exactly double: the 2x run holds
  slightly fewer shares because of the larger headroom.

---

## 6. Determinism

- Fills report: identical hashes for runs A and B in one process, and again in a second process, once
  `event_id` (and `init_id` in the order-fills report) are dropped (`probe:hash_fills_nouuid_A_B`,
  `probe:hash_order_fills_nouuid_A_B`). With those UUID columns the hashes differ every run
  (`probe:hash_fills_raw_A_B`).
- Trade IDs are deterministic by design: an FNV-1a hash of venue, raw id and `ts_init`
  (`docs:backtesting/execution-flow.md`, "Deterministic trade IDs"). Venue order IDs are deterministic with
  `use_random_ids=False`.
- The strategy's equity series was identical across runs (`probe:equity_identical_A_B`).
- The positions report is not hash-stable as is (section 2.7).
- Run ids, `run_started` and `run_finished` are wall-clock values. Keep them out of any hash.
- Sources of nondeterminism to keep out: a `FillModel` without `random_seed`; Python `random` used elsewhere in
  the same process; set or dict iteration over unordered keys in strategy code.

Recommended manifest hash: SHA-256 of the fills report with `event_id` dropped, plus SHA-256 of the daily
equity series, plus the Nautilus version and the input data hash.

---

## 7. Parity preview on synthetic data

Synthetic data: 600 business days, seeded random walk, 200-day SMA switch, 14 switches over 401 signal days.
The local reference re-implements `core/quant/backtest.py:113-119` inside the probe; it does not import the
repo. Thresholds are the task defaults.

| Run | Signal agree (>= 0.98) | Corr of daily returns (>= 0.99) | Sharpe NT | Sharpe local | Diff (<= 0.05) | Max daily diff |
|---|---|---|---|---|---|---|
| A: whole shares, 50 bp | 1.000 | 0.9999993 | -1.8975 | -1.8954 | 0.0021 | 1.7e-4 |
| C: whole shares, 100 bp (2x) | 1.000 | 0.9999938 | -2.3275 | -2.3219 | 0.0056 | 3.5e-4 |
| E: fractional (Cfd), 50 bp | 1.000 | 0.9999996 | -1.8970 | -1.8954 | 0.0015 | 1.2e-4 |
| Next open, 50 bp cost, 100 bp headroom, against the close reference | 1.000 | 0.9914 | -1.9231 | -1.8954 | 0.0276 | 6.6e-3 |

Sources: `probe:A_parity_1x`, `probe:C_2x_parity`, `probe:E_fractional_parity_1x`,
`probe:nextopen_vs_local_close_convention`.

What this shows and what it does not:

- It shows the plumbing agrees when both sides use the same rule, data and timing.
- Signal agreement is 100% by construction: both sides compute the same SMA on the same closes. On real data
  the check will catch only bar-construction errors (rounding, column order, timestamps, missing days).
- The remaining gap at close fills comes from whole-share rounding, the headroom (exposure is 1/(1.005) of
  equity, not 1.0) and cent-rounded fees.
- Synthetic overnight gaps are small (sigma 0.3%). Real SPY gaps are larger in stress periods. The next-open
  row is therefore an optimistic preview of the timing gap. UNVERIFIED on real data.
- No real SPY number exists in this map. Running the pilot grid before ledger registration would itself be an
  unregistered trial.

---

## 8. Strategy methods that place, change or cancel orders

These must appear only inside the bridge's sandbox module. Line numbers are `nt:trading/strategy.pyx`.

| Method | Line | Effect |
|---|---|---|
| `submit_order` | 805 | sends an order |
| `submit_order_list` | 899 | sends a bracket / OCO list |
| `modify_order` | 1011 | changes an open order |
| `cancel_order` | 1089 | cancels one order |
| `cancel_orders` | 1134 | cancels a list |
| `cancel_all_orders` | 1215 | cancels all for an instrument |
| `close_position` | 1351 | sends a closing MARKET order |
| `close_all_positions` | 1418 | sends closing MARKET orders |
| `market_exit` | 1750 | cancels all and closes all, on a timer |
| `query_account`, `query_order` | 1492, 1527 | ask the venue (no order, but a venue round trip) |

Other order paths: `self.order_factory.*` builds orders (`nt:common/factories.pyx:236` and siblings) but sends
nothing by itself. `ExecAlgorithm.spawn_market / spawn_limit / spawn_market_to_limit` create child orders
(`nt:execution/algorithm.pyx:853, 934, 1040`). The bridge needs none of these except `order_factory.market` and
`submit_order`.

---

## 9. Live and order-path surface to refuse

### 9.1 What can reach a real venue

| Surface | What it is | Source |
|---|---|---|
| `nautilus_trader.live.node.TradingNode`, `live.node_builder.TradingNodeBuilder`, `live.config.TradingNodeConfig` | the live runtime | `nt:live/node.py:39`, `nt:live/node_builder.py:34`, `nt:live/config.py:284` |
| `nautilus_trader.live.execution_client.LiveExecutionClient`, `live.data_client.LiveDataClient`, `LiveMarketDataClient` | base classes of every live client | `nt:live/execution_client.py:66`, `nt:live/data_client.py:82, 320` |
| `nautilus_trader.adapters.*`: `architect_ax, betfair, binance, bitmex, bybit, databento, deribit, dydx, hyperliquid, interactive_brokers, interactive_brokers_pyo3, kraken, okx, polymarket, tardis` | venue and data-vendor clients, API-key configs | `nt:adapters/` listing |
| `nautilus_trader.adapters.sandbox` (`SandboxExecutionClient(LiveExecutionClient)`) | simulated fills on **live** data inside a `TradingNode` | `nt:adapters/sandbox/execution.py:58` |
| `nautilus_trader.adapters._template` | a skeleton for writing a new adapter | `nt:adapters/_template/` |
| `nautilus_trader.adapters.env.get_env_key / get_env_key_or` | reads API keys from environment variables | `nt:adapters/env.py:19-30` |
| `nautilus_trader.network` | re-exports `HttpClient` and friends from the Rust runtime | `nt:network/__init__.py` |
| `nautilus_trader.core.nautilus_pyo3` | the Rust extension; exposes `HttpClient`, `WebSocketClient`, `SocketClient` and adapter clients such as `BybitHttpClient`, `OKXWebSocketClient`, `KrakenSpotHttpClient`, `DatabentoLiveClient`, `TardisMachineClient` | `nt:core/nautilus_pyo3.pyi` (355 classes) |

54 Python files under `adapters/` mention `api_key`, `api_secret` or `private_key` (grep count). The sandbox and
template adapters are no safer than the others for QUANTGEN's purpose: both exist to run inside the live node.
Block all of `adapters`.

### 9.2 Why the current T-RO-01 is not enough, and why it also blocks the bridge

- The text scan forbids the substring `submit_order` in code (`tests/macro_m0_harness.py:28-29`) and the call
  names `submit_order` and `cancel_order` (`:44-45`). Its scope is `core/`, `data/`, `ui/`, `main.py`,
  `config.py`, `docs/*.py`, `tools/` and `papers/` (`tests/macro_m0_harness.py:63-70`; `tests/acceptance.py:50-56`).
  The older `test_08` scans the same runtime files as raw text, comments included (`tests/acceptance.py:62-68`).
  Any bridge strategy file in scope fails both. Measured: two hits on the probe copied to
  `core/bridge/nautilus_sandbox.py`.
- The import check compares only the first dotted name with a set that includes `binance`, `okx` and `bybit`
  (`tests/macro_m0_harness.py:38-42, 92, 95`). `nautilus_trader.adapters.binance` starts with `nautilus_trader`,
  so it passes. Measured: zero hits on a file that imports `TradingNode`, a Binance adapter and `nautilus_pyo3`,
  then calls `node.run()`.
- Placing the bridge outside the scanned trees to avoid the scan would be evasion. It needs the same owner ruling.

### 9.3 A guard that works (proposal for the owner)

Static part, added to T-RO-01 (this is a test change; the owner rules on it):

1. **One allow-listed sandbox path**, for example `core/bridge/nautilus_sandbox.py`. Only there may
   `submit_order` appear, and only as `self.submit_order(...)` inside a class that subclasses
   `nautilus_trader.trading.strategy.Strategy`. `cancel_order`, `modify_order`, `close_position`,
   `close_all_positions`, `market_exit`, `submit_order_list` and `cancel_all_orders` stay forbidden everywhere,
   unless a later rule needs one.
2. **An import allow-list for that file** (and every other QUANTGEN file): `nautilus_trader.backtest.engine`,
   `nautilus_trader.backtest.models`, `nautilus_trader.config` (only the names `BacktestEngineConfig`,
   `LoggingConfig`, `StrategyConfig`), `nautilus_trader.model.*`, `nautilus_trader.persistence.wranglers`,
   `nautilus_trader.trading.strategy`, `nautilus_trader.common.component` (only `is_backtest_force_stop`), and
   the bare `nautilus_trader` (only `__version__`). Anything else under `nautilus_trader` fails the scan. (The
   probe also imports `nautilus_trader.analysis.analyzer`; the bridge does not need it.)
3. **A deny-list by dotted prefix**, checked on every scanned file: `nautilus_trader.live`,
   `nautilus_trader.adapters`, `nautilus_trader.network`, `nautilus_trader.core.nautilus_pyo3`,
   `nautilus_trader.backtest.node` (the high-level node is not needed), and the bare names `TradingNode`,
   `TradingNodeBuilder`, `TradingNodeConfig`, `LiveNode`, `LiveExecClientConfig`, `LiveDataClientConfig`,
   `SandboxExecutionClient`, `get_env_key`, `nautilus_pyo3`, `HttpClient`, `WebSocketClient`, `SocketClient`.
   The check must compare full dotted names, not the first component.
4. **No other venue I/O in the sandbox file**: no `requests`, `socket`, `asyncio`, `subprocess`, `os.environ`.

Runtime part, inside the bridge subprocess after `engine.run()`:

- Assert that no key of `sys.modules` starts with `nautilus_trader.adapters` or `nautilus_trader.network`.
  This held in the probe (`probe:live_or_adapters_loaded` lists only `nautilus_trader.live.*`).
- Do **not** block `nautilus_trader.live` at import time. The kernel imports it (finding 11).
- Assert `engine.trader` has no live clients: the run used `BacktestEngine`, never `TradingNode`. The static
  scan already covers this; a type check on the engine object is a cheap second line.
- A `sys.addaudithook` that refuses `socket.connect` would catch Python-level sockets only. Rust code inside
  `nautilus_pyo3` opens sockets without Python audit events. Treat the audit hook as a partial check. UNVERIFIED:
  I did not test an audit hook.

Orders inside a Nautilus backtest are simulated, like QUANTGEN's paper engine, which already routes every fill
through `OrderBook.fill` (`core/engine/orders.py:90, 169, 253-257`). The amendment should say so in its rationale.

---

## 10. Packaging facts

### 10.1 License

- PyPI: `LGPL-3.0-or-later` (`https://pypi.org/pypi/nautilus_trader/json`, `info.license`). The wheel METADATA
  says the same.
- LGPL-3.0 section 4, "Combined Works", lists what applies when you **convey** a combined work: a prominent
  notice, copies of the GPL and LGPL texts, and either a shared-library mechanism that lets the user swap the
  library or the source to relink (`https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/LICENSE`,
  lines 78-125).
- A private research repo that imports the package and does not distribute it conveys nothing. GPLv3 section 2
  lets you "make, run and propagate covered works that you do not convey, without conditions"
  (`https://www.gnu.org/licenses/gpl-3.0.html`). I could not fetch gnu.org from this session (proxy 403), so
  that quote is from the standard text and is UNVERIFIED here.
- If QUANTGEN is ever shipped with Nautilus inside (for example a packaged Flet build), section 4 applies.
  Importing an unmodified package from `site-packages` should count as a "suitable shared library mechanism".
  That is my reading, not legal advice.
- Conveying a modified copy of Nautilus would bring in section 2 ("Conveying Modified Versions"). The bridge
  only subclasses `Strategy` and `FeeModel` in QUANTGEN's own files. It does not edit the library.

### 10.2 Wheels, size, import time, Python versions

| Item | Value | Source |
|---|---|---|
| Python | `>=3.12,<3.15`; classifiers 3.12, 3.13, 3.14 | PyPI JSON |
| cp313 wheels | win_amd64, manylinux_2_35 x86_64 and aarch64, macOS 26 arm64 | PyPI JSON `releases["1.231.0"]` |
| Windows cp313 wheel | 112,708,191 bytes download; 332.6 MB unpacked (765 files); largest file `core/nautilus_pyo3.cp313-win_amd64.pyd` 141.9 MB | zip listing of the downloaded wheel |
| Linux cp313 wheel | 188,980,188 bytes; 608.7 MB unpacked | zip listing |
| Installed on Linux | `nautilus_trader/` 589 MB; whole venv `site-packages` 940 MB with dependencies | `du -sh` |
| Windows dependency difference | `uvloop` is skipped on `win32` | METADATA `Requires-Dist` |
| Import time (Linux container, warm) | `import nautilus_trader` 0.09 s; `from nautilus_trader.backtest.engine import BacktestEngine` 1.03 to 1.08 s | `time` in this session |
| Windows import and run times | not measured | UNVERIFIED |

### 10.3 Release cadence and API stability

- Recent 1.x releases (`RELEASES.md` at the tag): 1.221.0 on 26 Oct 2025, 1.222.0 on 1 Jan 2026, 1.223.0 on
  21 Feb, 1.224.0 on 3 Mar, 1.225.0 on 6 Apr, 1.226.0 on 29 Apr, 1.227.0 on 18 May, 1.228.0 on 8 Jun,
  1.229.0 on 25 Jun, 1.230.0 on 29 Jun, 1.231.0 on 2 Aug 2026. That is ten minor releases in about nine months.
- Each release section from 1.220.0 to 1.231.0 has a "Breaking Changes" heading (`RELEASES.md` headers at
  lines 136, 583, 686, 958, 1172, 1459, 1779, 2061, 2179, 2433, 2703, 2939).
- The project is still marked "Development Status :: 4 - Beta" on PyPI.
- Conclusion: pin `nautilus_trader==1.231.0` exactly, with a hash, in a bridge-only requirements file. Keep all
  Nautilus calls in one module so a later upgrade touches one file.

### 10.4 The v2 transition

- 1.231.0 is "intended to be the final NautilusTrader `1.x` release". `develop` moves to v2-only, v1 moves to a
  `develop_v1` branch, and critical security backports continue "for approximately three months after the v2
  cutover" (`RELEASES.md` lines 5-24 at the tag).
- PyPI has `2.0.0rc2` (2 Aug 2026) through `2.0.0rc7` (15 Oct 2026). `2.0.0rc7` requires Python `>=3.13`, ships
  cp313 and cp314 wheels including win_amd64 (66.5 MB), and lists no hard numpy or pandas dependency
  (`https://pypi.org/pypi/nautilus_trader/2.0.0rc7/json`). I did not install or run any 2.0 release. UNVERIFIED
  whether the bridge code would run on it.
- The docs at the `v1.231.0` tag already use v2 import paths. On the 1.231.0 wheel these fail:
  `from nautilus_trader.backtest import BacktestEngine` (ImportError) and
  `from nautilus_trader.execution import DefaultFillModel` (ImportError). These work:
  `from nautilus_trader.backtest.engine import BacktestEngine`,
  `from nautilus_trader.config import BacktestEngineConfig`,
  `from nautilus_trader.backtest.models import FillModel, MakerTakerFeeModel, FixedFeeModel, PerContractFeeModel, LatencyModel`,
  `from nautilus_trader.persistence.wranglers import BarDataWrangler`. Read the installed source, not the
  published docs, for 1.231.0 behaviour.
- Owner decision: build the pilot on 1.231.0 (stable now, frozen soon) or on a 2.0 release candidate (current,
  still moving). My recommendation is 1.231.0 for pilot 1, with one adapter module and a planned v2 migration
  task once 2.0.0 is final.

---

## 11. Pilot 2 shape: BTC/USD smoke check

Synthetic data only, 600 calendar days, 10 bp cost (QUANTGEN's crypto row, `core/quant/validate.py:78`).

- A `CurrencyPair` cannot be added to a single-currency CASH venue. `add_instrument` raises
  `InvalidConfiguration` (`nt:backtest/engine.pyx:762-770`; `probe_btc:base=USD`). Use `base_currency=None` with
  starting balances in USD and BTC.
- That run completed: 600 bars, fills to 6 decimals (first 279.268981), cash and BTC balances both tracked
  (`probe_btc:base=None`).
- The analyzer returned an empty series, because the account has two currencies (`nt:analysis/analyzer.py:818-844`).
  The strategy-side equity series still works.
- The re-target-every-bar loop made 401 fills for zero signal switches. This is the drift problem of section 2.5,
  worse with fine size increments.
- Crypto bars need a 7-day calendar and a close timestamp convention (for example 00:00 UTC). Thin volume can
  bind the L1 quarter-volume rule (section 2.4).

---

## 12. Integration points with QUANTGEN

| Point | QUANTGEN side | Contract for the bridge |
|---|---|---|
| Register before run | `register_trial(ledger, row, script=...)` (`core/quant/gate_ledger.py:379-386`); required row fields (`:63`); row-set key (`:60-61`) | Register every variant before its first engine run, with the same row-set key fields as the local run. Expect `appended=False` for a replica. |
| Ledger hash check | `assert_hash_at_run` (`core/quant/gate_ledger.py:389-397`) | Record the ledger hash at run start in the run manifest. |
| Cost table | `COST_BP_PER_SIDE` (`core/quant/validate.py:78`): us 50, crypto 10 bp | Read the rate from QUANTGEN, pass it to the subprocess; never hard-code it in the sandbox. |
| 2x rule | `costed_path(..., stress)` (`core/quant/costed.py:130, 145`) | Second engine with `stress=2.0`; refuse `stress < 1`. |
| Gate input | `walk_forward(pnl, dates, *, turnover, pnl_stress, ...)`, T x G arrays (`core/quant/validate.py:345-352`) | Output one daily net-return column per variant, a 2x twin, a turnover column, on QUANTGEN's session dates. |
| Local reference | `run_backtest` (`core/quant/backtest.py:108-119`) and `costed_path` (`core/quant/costed.py:130-159`) | Choose one convention for the initial entry (section 5.1). |
| Read-only scan | T-RO-01 (`tests/macro_m0_harness.py:25-146`), `test_08` (`tests/acceptance.py:62-68`) | Needs an owner-approved amendment (section 9.3). |
| Frozen studies | `tests/frozen_guard.py:39, 85-91` | Run Nautilus only in its own venv, as a subprocess. Never install into the global interpreter. |

Suggested subprocess contract (a proposal, not built):

- Input: an OHLCV file with an explicit column order and close timestamps; the variant parameters; `cost_bp`;
  `stress`; the starting cash; the data hash; the ledger hash at run start.
- Output: the fills report (UUID columns dropped), the daily equity and return series, daily turnover, and a
  manifest with the Nautilus version, Python version, the input hashes, the fills and equity hashes, bars seen,
  bars loaded, the force-stop flag and `backtest_end`.
- A forced stop, bars seen below bars loaded, any `OrderDenied` or `OrderRejected`, or an adapter module in
  `sys.modules` makes the run invalid. An invalid run withholds the verdict.

---

## 13. Open questions for the owner

1. T-RO-01 amendment: approve a single allow-listed sandbox file for `self.submit_order`, plus full-dotted-name
   denial of `nautilus_trader.live`, `.adapters`, `.network` and `nautilus_pyo3` (section 9.3)?
2. Version: 1.231.0 (last v1, frozen) or a 2.0 release candidate (section 10.4)?
3. Fill timing for the verdict: same-bar close (matches QUANTGEN, passes parity) or next-open (more realistic,
   may fail the 0.99 correlation bar on real gaps)? My proposal: parity and verdict on close fills; next-open as
   a reported realism delta.
4. Whole shares (`Equity`) or a fractional stand-in (`Cfd` with `asset_class=EQUITY`)? And what starting cash?
5. Rebalance rule in the Nautilus strategy: trade only on a signal change (matches QUANTGEN) or a drift band?
6. Initial-entry cost: follow `run_backtest` (costed) or `costed_path` (uncosted) for the parity reference?
7. Is headroom sizing (exposure 1/(1 + cost)) acceptable, or should the bridge use a MARGIN account at
   leverage 1 to hold exactly 100%? The margin route is untested.
8. Does the bridge record `source: "nautilus"` in the optional ledger field (`core/quant/gate_ledger.py:64-65`)?
   It is not in the row-set key, so it would not change `config_id`.

---

## Appendix A. Probe script (seed of the sandbox module)

Path: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nt_probe/probe_backtest.py`.
Run: `ntvenv/bin/python -I probe_backtest.py`. This file is a probe, not production code. It re-targets every
bar (section 2.5), and it calls `submit_order`, which the current T-RO-01 forbids inside the repo.

```python
"""QUANTGEN x NautilusTrader 1.231.0 backtest probe (scratch; NOT part of the QUANTGEN repo).

Seed of the bridge's sandbox module. One US equity, daily LAST bars, CASH account, a 200-day SMA on/off
switch that targets a weight. Runs on synthetic deterministic data only. Run with the venv interpreter:

    ntvenv/bin/python -I probe_backtest.py

Every Nautilus import is from the backtest / model / config / persistence / analysis / trading layers.
Nothing from nautilus_trader.live, nautilus_trader.adapters, nautilus_trader.network or TradingNode.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from decimal import ROUND_FLOOR, Decimal

import numpy as np
import pandas as pd

import nautilus_trader
from nautilus_trader.analysis.analyzer import PortfolioAnalyzer  # noqa: F401  (engine.portfolio.analyzer)
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel, LatencyModel, MakerTakerFeeModel
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType, TradeTick
from nautilus_trader.model.enums import (AccountType, AggressorSide, AssetClass, OmsType, OrderSide,
                                         TimeInForce)
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TradeId, TraderId, Venue
from nautilus_trader.model.instruments import Cfd, Equity
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("ARCA")
SPY = InstrumentId(Symbol("SPY"), VENUE)
SMA_WINDOW = 200
START_CASH = 100_000
COST_BP_US = 50.0   # QUANTGEN gate table, "us" row (core/quant/validate.py:78); 2x run uses 100 bp


# --------------------------------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------------------------------- #
def synthetic_daily(n: int = 600, seed: int = 7) -> pd.DataFrame:
    """Deterministic random-walk OHLCV, one row per business day, stamped at the CLOSE (21:00 UTC)."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2020-01-02", periods=n, tz="UTC")
    r = rng.normal(0.0003, 0.012, n)
    close = 300.0 * np.exp(np.cumsum(r))
    gap = rng.normal(0.0, 0.003, n)
    open_ = np.empty(n)
    open_[0] = 300.0
    open_[1:] = close[:-1] * np.exp(gap[1:])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    o, c = np.round(open_, 2), np.round(close, 2)
    df = pd.DataFrame({
        "open": o,
        "high": np.maximum(np.round(high, 2), np.maximum(o, c)),
        "low": np.minimum(np.round(low, 2), np.minimum(o, c)),
        "close": c,
        "volume": 50_000_000.0,
    }, index=days + pd.Timedelta(hours=21))      # ts_event = ts_init = bar close (docs: bar-execution.md)
    return df[["open", "high", "low", "close", "volume"]]   # BarDataWrangler reads columns BY POSITION


def open_ticks(df: pd.DataFrame, instrument) -> list[TradeTick]:
    """One synthetic trade print per day at the open (14:30 UTC) - used only by the next-open mode."""
    out = []
    for i, (ts, row) in enumerate(df.iterrows()):
        t = (ts.normalize() + pd.Timedelta(hours=14, minutes=30)).value
        out.append(TradeTick(instrument.id, instrument.make_price(row["open"]), instrument.make_qty(1_000_000),
                             AggressorSide.NO_AGGRESSOR, TradeId(f"OPEN-{i}"), t, t))
    return out


# --------------------------------------------------------------------------------------------------- #
# Instruments
# --------------------------------------------------------------------------------------------------- #
def spy_equity() -> Equity:
    """Whole shares only: Equity hard-codes size_precision=0, size_increment=1 (model/instruments/equity.pyx)."""
    return Equity(instrument_id=SPY, raw_symbol=Symbol("SPY"), currency=USD, price_precision=2,
                  price_increment=Price.from_str("0.01"), lot_size=Quantity.from_int(1),
                  ts_event=0, ts_init=0, maker_fee=Decimal("0"), taker_fee=Decimal("0"))


def spy_fractional(taker_fee: Decimal = Decimal("0")) -> Cfd:
    """Fractional-share stand-in: a Cfd with asset_class EQUITY and 4 size decimals."""
    return Cfd(instrument_id=SPY, raw_symbol=Symbol("SPY"), asset_class=AssetClass.EQUITY, quote_currency=USD,
               price_precision=2, size_precision=4, price_increment=Price.from_str("0.01"),
               size_increment=Quantity.from_str("0.0001"), ts_event=0, ts_init=0,
               maker_fee=taker_fee, taker_fee=taker_fee)


# --------------------------------------------------------------------------------------------------- #
# Costs: QUANTGEN's bp-of-traded-notional, per side, as a Nautilus FeeModel
# --------------------------------------------------------------------------------------------------- #
class BpsNotionalFeeModel(FeeModel):
    """commission = |fill_qty| x fill_px x multiplier x bp / 1e4, in the quote currency (USD, 2 dp)."""

    def __init__(self, bp_per_side: float, stress: float = 1.0):
        super().__init__()
        self.rate = Decimal(repr(bp_per_side)) * Decimal(repr(stress)) / Decimal(10_000)

    def get_commission(self, order, fill_qty, fill_px, instrument):
        notional = instrument.notional_value(fill_qty, fill_px)
        return Money(notional.as_decimal() * self.rate, instrument.quote_currency)


# --------------------------------------------------------------------------------------------------- #
# Strategy: decide at the close of bar t, target a weight, trade with one MARKET order
# --------------------------------------------------------------------------------------------------- #
class SmaTargetConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    sma_window: int = SMA_WINDOW
    weight_on: float = 1.0
    headroom_bp: float = 0.0      # size down so cash covers the fee (a CASH account cannot go negative)
    tif: str = "GTC"


class SmaTargetWeight(Strategy):
    def __init__(self, config: SmaTargetConfig):
        super().__init__(config)
        self.closes: list[float] = []
        self.rows: list[dict] = []          # one row per bar: pre-trade state at the close
        self.denied: list[str] = []
        self.rejected: list[str] = []

    def on_start(self):
        self.instrument = self.cache.instrument(self.config.instrument_id)
        self.subscribe_bars(self.config.bar_type)

    def on_order_denied(self, event):
        self.denied.append(str(event.reason))

    def on_order_rejected(self, event):
        self.rejected.append(str(event.reason))

    def on_bar(self, bar):
        close = float(bar.close)
        self.closes.append(close)
        account = self.portfolio.account(self.config.instrument_id.venue)
        cash = float(account.balance_total(USD))
        qty = float(self.portfolio.net_position(self.config.instrument_id))
        equity = cash + qty * close                                  # mark-to-market at this close, pre-trade
        nt_equity = self.portfolio.equity(self.config.instrument_id.venue).get(USD)
        signal = None
        if len(self.closes) >= self.config.sma_window:
            sma = sum(self.closes[-self.config.sma_window:]) / self.config.sma_window
            signal = 1 if close > sma else 0
        self.rows.append({"ts": bar.ts_event, "close": close, "cash": cash, "qty": qty, "equity": equity,
                          "nt_equity": nt_equity, "signal": signal})
        if signal is None:
            return
        target_w = self.config.weight_on if signal else 0.0
        inc = self.instrument.size_increment.as_decimal()
        raw = Decimal(repr(target_w * equity / (close * (1 + self.config.headroom_bp * 1e-4))))
        target = (raw / inc).to_integral_value(rounding=ROUND_FLOOR) * inc
        delta = target - Decimal(repr(qty))
        if abs(delta) < inc:
            return
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY if delta > 0 else OrderSide.SELL,
            quantity=self.instrument.make_qty(abs(delta)),
            time_in_force=TimeInForce[self.config.tif],
        )
        self.submit_order(order)


# --------------------------------------------------------------------------------------------------- #
# One run
# --------------------------------------------------------------------------------------------------- #
def run_once(df: pd.DataFrame, *, instrument=None, fee_model=None, tif: str = "GTC", headroom_bp: float = 0.0,
             latency_ns: int | None = None, with_open_ticks: bool = False, allow_cash_borrowing: bool = False,
             fill_seed: int = 42) -> dict:
    t0 = time.perf_counter()
    instrument = instrument or spy_equity()
    bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
    bars = BarDataWrangler(bar_type, instrument).process(df)
    engine = BacktestEngine(BacktestEngineConfig(
        trader_id=TraderId("QGPROBE-001"),
        logging=LoggingConfig(log_level="ERROR"),
    ))
    engine.add_venue(
        venue=VENUE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USD,
        starting_balances=[Money(START_CASH, USD)],
        fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=fill_seed),
        fee_model=fee_model if fee_model is not None else BpsNotionalFeeModel(COST_BP_US),
        latency_model=LatencyModel(base_latency_nanos=latency_ns) if latency_ns else None,
        bar_execution=True,
        bar_adaptive_high_low_ordering=False,
        allow_cash_borrowing=allow_cash_borrowing,
    )
    engine.add_instrument(instrument)
    engine.add_data(bars)
    if with_open_ticks:
        engine.add_data(open_ticks(df, instrument))
    strat = SmaTargetWeight(SmaTargetConfig(instrument_id=instrument.id, bar_type=bar_type, tif=tif,
                                            headroom_bp=headroom_bp))
    engine.add_strategy(strat)
    engine.run()
    wall = time.perf_counter() - t0

    trader = engine.trader
    account = engine.portfolio.account(VENUE)
    out = {
        "wall_s": wall,
        "orders": trader.generate_orders_report(),
        "order_fills": trader.generate_order_fills_report(),
        "fills": trader.generate_fills_report(),
        "positions": trader.generate_positions_report(),
        "account": trader.generate_account_report(VENUE),
        "rows": pd.DataFrame(strat.rows).set_index("ts"),
        "denied": list(strat.denied),
        "rejected": list(strat.rejected),
        "final_cash": float(account.balance_total(USD)),
        "analyzer_returns": engine.portfolio.analyzer.returns().copy(),
        "analyzer_stats": engine.portfolio.analyzer.get_performance_stats_returns(),
        "analyzer_general": engine.portfolio.analyzer.get_performance_stats_general(),
        "commissions": [str(m) for m in account.commissions().values()] if hasattr(account, "commissions") else None,
    }
    engine.dispose()
    return out


# --------------------------------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------------------------------- #
UUID_COLS = ("init_id", "event_id", "last_event_id")


def report_hash(df: pd.DataFrame, drop_uuid: bool) -> str:
    d = df.drop(columns=[c for c in UUID_COLS if c in df.columns]) if drop_uuid else df
    return hashlib.sha256(d.to_csv().encode()).hexdigest()[:16]


def fill_price_vs_bars(fills: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Classify each fill as same-bar close, next-bar open, next-bar close, or other."""
    closes = df["close"]
    opens = df["open"]
    idx = df.index
    tally = {"same_close": 0, "next_open": 0, "next_close": 0, "other": 0}
    examples = []
    for _, f in fills.iterrows():
        ts = pd.Timestamp(f["ts_event"]).tz_convert("UTC") if pd.Timestamp(f["ts_event"]).tzinfo else pd.Timestamp(f["ts_event"], tz="UTC")
        px = float(f["last_px"])
        pos = idx.searchsorted(ts, side="right") - 1          # last bar at or before the fill
        tag = "other"
        if pos >= 0 and idx[pos] == ts and abs(px - closes.iloc[pos]) < 1e-9:
            tag = "same_close"
        elif pos >= 0 and abs(px - opens.iloc[min(pos + 1, len(df) - 1)]) < 1e-9 and idx[pos] != ts:
            tag = "next_open"
        elif pos >= 0 and abs(px - closes.iloc[pos]) < 1e-9:
            tag = "next_close"
        tally[tag] += 1
        if len(examples) < 3:
            examples.append({"fill_ts": str(ts), "last_px": px, "tag": tag})
    tally["examples"] = examples
    return tally


def local_vectorized(df: pd.DataFrame, cost_bp: float) -> pd.DataFrame:
    """QUANTGEN-convention reference (core/quant/backtest.py:116-119): decide at close t, earn t->t+1,
    pay |dw| x bp when the position changes. Re-implemented here; the repo is not imported."""
    px = df["close"].to_numpy()
    sma = pd.Series(px).rolling(SMA_WINDOW).mean().to_numpy()
    pos = np.where(np.isfinite(sma) & (px > sma), 1.0, 0.0)
    daily = px[1:] / px[:-1] - 1.0
    trades = np.abs(np.diff(np.concatenate([[0.0], pos])))
    strat = pos[:-1] * daily - trades[:-1] * cost_bp * 1e-4
    return pd.DataFrame({"pos": pos[:-1], "ret": strat}, index=df.index[1:])   # ret earned INTO this date


def parity(nt: dict, df: pd.DataFrame, cost_bp: float) -> dict:
    rows = nt["rows"]
    rows.index = pd.to_datetime(rows.index, utc=True)
    eq = rows["equity"]
    nt_ret = (eq / eq.shift(1) - 1.0).dropna()           # pre-trade MTM equity, close-to-close
    loc = local_vectorized(df, cost_bp)
    j = pd.concat([nt_ret.rename("nt"), loc["ret"].rename("loc")], axis=1, join="inner").dropna()
    sig_nt = rows["signal"].dropna().astype(int)
    sig_loc = pd.Series(np.where(pd.Series(df["close"].to_numpy()).rolling(SMA_WINDOW).mean().to_numpy() < df["close"].to_numpy(), 1, 0), index=df.index).loc[sig_nt.index]

    def sharpe(x):
        return float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")
    return {
        "signal_agree": float((sig_nt == sig_loc).mean()),
        "n_signal_days": int(sig_nt.size),
        "switches": int((sig_nt.diff().abs() > 0).sum()),
        "corr": float(np.corrcoef(j["nt"], j["loc"])[0, 1]),
        "sharpe_nt": sharpe(j["nt"]),
        "sharpe_loc": sharpe(j["loc"]),
        "sharpe_diff": abs(sharpe(j["nt"]) - sharpe(j["loc"])),
        "max_abs_ret_diff": float((j["nt"] - j["loc"]).abs().max()),
        "nt_equity_vs_portfolio_equity_maxdiff": float((rows["equity"] - rows["nt_equity"].astype(float)).abs().max()),
    }


def main() -> None:
    print("python", sys.version.split()[0], "| nautilus_trader", nautilus_trader.__version__,
          "| numpy", np.__version__, "| pandas", pd.__version__)
    df = synthetic_daily()
    print("bars", len(df), df.index[0], "->", df.index[-1])
    res: dict = {}

    # A, B: baseline twice (determinism), whole shares, 50 bp custom fee, headroom = fee
    a = run_once(df, headroom_bp=COST_BP_US)
    b = run_once(df, headroom_bp=COST_BP_US)
    res["A_wall_s"] = round(a["wall_s"], 3)
    res["B_wall_s"] = round(b["wall_s"], 3)
    res["A_n_orders"] = len(a["orders"])
    res["A_n_fills"] = len(a["fills"])
    res["fills_report_columns"] = list(a["fills"].columns)
    res["order_fills_columns"] = list(a["order_fills"].columns)
    res["account_report_columns"] = list(a["account"].columns)
    res["positions_report_columns"] = list(a["positions"].columns)
    res["hash_order_fills_raw_A_B"] = (report_hash(a["order_fills"], False), report_hash(b["order_fills"], False))
    res["hash_order_fills_nouuid_A_B"] = (report_hash(a["order_fills"], True), report_hash(b["order_fills"], True))
    res["hash_fills_raw_A_B"] = (report_hash(a["fills"], False), report_hash(b["fills"], False))
    res["hash_fills_nouuid_A_B"] = (report_hash(a["fills"], True), report_hash(b["fills"], True))
    res["equity_identical_A_B"] = bool(a["rows"]["equity"].equals(b["rows"]["equity"]))
    res["A_fill_px"] = fill_price_vs_bars(a["fills"], df)
    f0 = a["fills"].iloc[0]
    res["A_first_fill"] = {k: str(f0[k]) for k in ("order_side", "last_qty", "last_px", "commission",
                                                   "liquidity_side", "ts_event") if k in f0}
    fee_check = []
    for _, f in a["fills"].head(3).iterrows():
        expect = float(f["last_qty"]) * float(f["last_px"]) * COST_BP_US * 1e-4
        fee_check.append((str(f["commission"]), round(expect, 6)))
    res["A_fee_vs_bp_formula"] = fee_check
    res["A_denied"], res["A_rejected"] = a["denied"][:2], a["rejected"][:2]
    res["A_final_cash"] = a["final_cash"]
    res["A_final_equity"] = float(a["rows"]["equity"].iloc[-1])
    res["A_parity_1x"] = parity(a, df, COST_BP_US)
    res["A_account_report_rows"] = len(a["account"])
    res["A_analyzer_returns_len"] = len(a["analyzer_returns"])
    res["A_analyzer_returns_head"] = {str(k): round(float(v), 6) for k, v in a["analyzer_returns"].head(4).items()}
    res["A_analyzer_stats"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in a["analyzer_stats"].items()}
    res["A_positions_report_rows"] = len(a["positions"])

    # C: 2x costs (100 bp), same strategy
    c = run_once(df, fee_model=BpsNotionalFeeModel(COST_BP_US, stress=2.0), headroom_bp=2 * COST_BP_US)
    res["C_2x_parity"] = parity(c, df, 2 * COST_BP_US)
    res["C_2x_final_equity"] = float(c["rows"]["equity"].iloc[-1])
    res["C_2x_total_commission"] = float(c["fills"]["commission"].map(lambda s: float(str(s).split()[0])).sum())
    res["A_1x_total_commission"] = float(a["fills"]["commission"].map(lambda s: float(str(s).split()[0])).sum())

    # D: built-in MakerTakerFeeModel with taker_fee on the instrument (fractional instrument, 0.005 = 50 bp)
    d = run_once(df, instrument=spy_fractional(Decimal("0.005")), fee_model=MakerTakerFeeModel(),
                 headroom_bp=COST_BP_US)
    e = run_once(df, instrument=spy_fractional(), fee_model=BpsNotionalFeeModel(COST_BP_US), headroom_bp=COST_BP_US)
    res["D_maker_taker_vs_custom_commissions_equal"] = bool(
        (d["fills"]["commission"].astype(str).values == e["fills"]["commission"].astype(str).values).all())
    res["E_fractional_first_qty"] = str(e["fills"]["last_qty"].iloc[0])
    res["E_fractional_parity_1x"] = parity(e, df, COST_BP_US)

    # F: AT_THE_CLOSE market orders
    f = run_once(df, tif="AT_THE_CLOSE", headroom_bp=COST_BP_US)
    res["F_at_the_close_fills"] = len(f["fills"])
    res["F_at_the_close_rejected_first"] = f["rejected"][:1]
    res["F_at_the_close_n_rejected"] = len(f["rejected"])

    # G: latency 1 hour, bars only
    g = run_once(df, latency_ns=3_600_000_000_000, headroom_bp=COST_BP_US)
    res["G_latency_fill_px"] = fill_price_vs_bars(g["fills"], df)

    # H: latency 1 hour + one open print per day -> next-open fills
    h = run_once(df, latency_ns=3_600_000_000_000, with_open_ticks=True, headroom_bp=COST_BP_US)
    res["H_next_open_fill_px"] = fill_price_vs_bars(h["fills"], df)

    # I: no headroom on a CASH account: what happens when the fee pushes cash below zero?
    i = run_once(df, headroom_bp=0.0)
    res["I_no_headroom_n_fills"] = len(i["fills"])
    res["I_no_headroom_denied"] = i["denied"][:2]
    res["I_no_headroom_n_denied"] = len(i["denied"])
    res["I_no_headroom_min_cash"] = float(i["rows"]["cash"].min())

    for k, v in res.items():
        print(f"{k}: {json.dumps(v, default=str)}")


if __name__ == "__main__":
    main()
```

## Appendix B. Follow-up probe

Path: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nt_probe/probe_followups.py`. Run: `ntvenv/bin/python -s -E probe_followups.py` from that folder (it imports
`probe_backtest`). It checks the account report and analyzer, the forced stop, cash borrowing, the next-open
recipe, slippage, the global `random` reseed, the wrangler column order and rounding, pilot-scale timing, and
which Nautilus subpackages a backtest loads.

```python
"""Follow-up checks for probe_backtest.py (scratch; NOT part of the QUANTGEN repo)."""
from __future__ import annotations

import json
import random
import sys
import time

import numpy as np
import pandas as pd

import probe_backtest as pb
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel, LatencyModel
from nautilus_trader.common.component import is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler


class InflightAware(pb.SmaTargetWeight):
    """Skip a bar while an earlier order is still in flight (needed once a latency model is on)."""

    def on_bar(self, bar):
        if self.cache.orders_inflight(instrument_id=self.config.instrument_id) or \
                self.cache.orders_open(instrument_id=self.config.instrument_id):
            self.closes.append(float(bar.close))
            account = self.portfolio.account(self.config.instrument_id.venue)
            cash = float(account.balance_total(USD))
            qty = float(self.portfolio.net_position(self.config.instrument_id))
            self.rows.append({"ts": bar.ts_event, "close": float(bar.close), "cash": cash, "qty": qty,
                              "equity": cash + qty * float(bar.close), "nt_equity": cash + qty * float(bar.close),
                              "signal": self.rows[-1]["signal"] if self.rows else None})
            return
        super().on_bar(bar)


def engine_for(df, *, strategy_cls=pb.SmaTargetWeight, headroom_bp=pb.COST_BP_US, latency_ns=None,
               open_ticks=False, allow_cash_borrowing=False, fill_model=None, sma_window=pb.SMA_WINDOW):
    instrument = pb.spy_equity()
    bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGPROBE-002"),
                                                 logging=LoggingConfig(log_level="ERROR")))
    engine.add_venue(venue=pb.VENUE, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=USD,
                     starting_balances=[Money(pb.START_CASH, USD)],
                     fill_model=fill_model or FillModel(random_seed=42),
                     fee_model=pb.BpsNotionalFeeModel(pb.COST_BP_US),
                     latency_model=LatencyModel(base_latency_nanos=latency_ns) if latency_ns else None,
                     allow_cash_borrowing=allow_cash_borrowing)
    engine.add_instrument(instrument)
    engine.add_data(BarDataWrangler(bar_type, instrument).process(df))
    if open_ticks:
        engine.add_data(pb.open_ticks(df, instrument))
    strat = strategy_cls(pb.SmaTargetConfig(instrument_id=instrument.id, bar_type=bar_type, headroom_bp=headroom_bp,
                                            sma_window=sma_window))
    engine.add_strategy(strat)
    return engine, strat


def main():
    df = pb.synthetic_daily()
    out = {}

    # 1. What the account report and the PortfolioAnalyzer see on a CASH account
    eng, st = engine_for(df)
    eng.run()
    acct = eng.trader.generate_account_report(pb.VENUE)
    out["acct_report_first3_after_start"] = [(str(i), float(r["total"])) for i, r in acct.iloc[1:4].iterrows()]
    rets = eng.portfolio.analyzer.returns()
    out["analyzer_returns_min_max"] = (round(float(rets.min()), 4), round(float(rets.max()), 4))
    out["analyzer_returns_index_freq"] = str(pd.infer_freq(rets.index[:20]))
    out["analyzer_returns_weekend_rows"] = int((rets.index.dayofweek >= 5).sum())
    rows = pd.DataFrame(st.rows).set_index("ts")
    e = rows["equity"]
    r = (e / e.shift(1) - 1).dropna()
    out["strategy_equity_returns_min_max"] = (round(float(r.min()), 4), round(float(r.max()), 4))
    out["bars_seen_vs_loaded"] = (len(st.rows), len(df))
    out["force_stop_flag_after_clean_run"] = bool(is_backtest_force_stop())
    res = eng.get_result()
    out["result_fields"] = {"iterations": res.iterations, "total_events": res.total_events,
                            "total_orders": res.total_orders, "total_positions": res.total_positions,
                            "backtest_end": str(pd.Timestamp(res.backtest_end, tz="UTC")) if res.backtest_end else None}
    eng.dispose()

    # 2. No headroom on CASH: forced stop, and how to detect it
    eng, st = engine_for(df, headroom_bp=0.0)
    eng.run()
    res = eng.get_result()
    out["nohead_force_stop_flag"] = bool(is_backtest_force_stop())
    out["nohead_bars_seen_vs_loaded"] = (len(st.rows), len(df))
    out["nohead_result_iterations"] = res.iterations
    out["nohead_backtest_end"] = str(pd.Timestamp(res.backtest_end, tz="UTC")) if res.backtest_end else None
    eng.dispose()

    # 3. Same with allow_cash_borrowing=True
    eng, st = engine_for(df, headroom_bp=0.0, allow_cash_borrowing=True)
    eng.run()
    rows = pd.DataFrame(st.rows)
    out["borrow_bars_seen"] = len(rows)
    out["borrow_min_cash"] = round(float(rows["cash"].min()), 2)
    out["borrow_n_fills"] = len(eng.trader.generate_fills_report())
    eng.dispose()

    # 4. Next-open execution done properly: open prints + 1h latency + in-flight-aware strategy + 100 bp headroom
    eng, st = engine_for(df, strategy_cls=InflightAware, headroom_bp=2 * pb.COST_BP_US, latency_ns=3_600_000_000_000,
                         open_ticks=True)
    eng.run()
    fills = eng.trader.generate_fills_report()
    out["nextopen_bars_seen"] = len(st.rows)
    out["nextopen_n_fills"] = len(fills)
    out["nextopen_fill_px"] = pb.fill_price_vs_bars(fills, df)
    nt = {"rows": pd.DataFrame(st.rows).set_index("ts")}
    out["nextopen_vs_local_close_convention"] = pb.parity(nt, df, pb.COST_BP_US)
    eng.dispose()

    # 5. prob_slippage = 1.0 -> one tick worse on every fill
    eng, st = engine_for(df, fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=1.0, random_seed=42))
    eng.run()
    fills = eng.trader.generate_fills_report()
    diffs = []
    for _, f in fills.head(4).iterrows():
        ts = pd.Timestamp(f["ts_event"])
        diffs.append((str(f["order_side"]), round(float(f["last_px"]) - float(df.loc[ts, "close"]), 4)))
    out["slip1_px_minus_close"] = diffs
    eng.dispose()

    # 6. FillModel touches the GLOBAL `random` module
    random.seed(123)
    x1 = random.random()
    random.seed(123)
    FillModel()                       # random_seed=None -> random.seed() from OS entropy
    x2 = random.random()
    FillModel(random_seed=42)
    x3 = random.random()
    random.seed(42)
    x4 = random.random()
    out["fillmodel_reseeds_global_random"] = {"unseeded_changes_stream": x1 != x2, "seeded_equals_seed42": x3 == x4}

    # 7. BarDataWrangler reads columns by position
    bad = df[["close", "open", "high", "low", "volume"]]
    inst = pb.spy_equity()
    bt = BarType.from_str(f"{inst.id}-1-DAY-LAST-EXTERNAL")
    try:
        bars = BarDataWrangler(bt, inst).process(bad.copy())
        b0 = bars[0]
        out["wrangler_wrong_column_order"] = f"built: open={b0.open} (true open {df['open'].iloc[0]}), close={b0.close} (true close {df['close'].iloc[0]})"
    except Exception as exc:  # noqa: BLE001
        out["wrangler_wrong_column_order"] = f"raised {type(exc).__name__}: {str(exc)[:160]}"
    many = df.copy()
    many["open"] = many["open"] + 0.0049
    b = BarDataWrangler(bt, inst).process(many)[0]
    out["wrangler_rounds_to_price_precision"] = f"{df['open'].iloc[0] + 0.0049:.4f} -> {b.open}"

    # 8. Pilot-scale timing: 5,600 bars (about 2004-2026), 12 SMA windows, fresh engine per run vs reset()
    big = pb.synthetic_daily(n=5600, seed=11)
    t0 = time.perf_counter()
    for w in (50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325):
        eng, st = engine_for(big, sma_window=w)
        eng.run()
        eng.dispose()
    out["timing_12_fresh_engines_5600_bars_s"] = round(time.perf_counter() - t0, 2)
    eng, st = engine_for(big, sma_window=200)
    t0 = time.perf_counter()
    eng.run()
    h1 = pb.report_hash(eng.trader.generate_fills_report(), True)
    eng.reset()
    eng.run()
    h2 = pb.report_hash(eng.trader.generate_fills_report(), True)
    out["timing_reset_rerun_s"] = round(time.perf_counter() - t0, 2)
    out["reset_rerun_same_fills_hash"] = (h1, h2)
    eng.dispose()

    # 9. Which nautilus_trader subpackages did a backtest import?
    mods = sorted({m.split(".")[1] for m in sys.modules if m.startswith("nautilus_trader.") and m.count(".") >= 1})
    out["nautilus_subpackages_loaded"] = mods
    out["live_or_adapters_loaded"] = sorted(m for m in sys.modules if m.startswith(("nautilus_trader.live",
                                                                                    "nautilus_trader.adapters",
                                                                                    "nautilus_trader.network")))
    out["third_party_net_loaded"] = sorted(m for m in ("aiohttp", "websockets", "requests", "httpx", "uvloop",
                                                       "asyncio", "ssl", "socket") if m in sys.modules)

    for k, v in out.items():
        print(f"{k}: {json.dumps(v, default=str)}")


if __name__ == "__main__":
    main()
```

## Appendix C. BTC/USD smoke probe

Path: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nt_probe/probe_btc_smoke.py`. Output keys are cited as `probe_btc:<key>`.

```python
"""Smoke check for pilot 2 shape: BTC/USD CurrencyPair on a CASH account, 7-day calendar (scratch only)."""
from __future__ import annotations

import json
from decimal import Decimal

import pandas as pd

import probe_backtest as pb
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.persistence.wranglers import BarDataWrangler

V = Venue("SIMX")
BTCUSD = CurrencyPair(instrument_id=InstrumentId(Symbol("BTC/USD"), V), raw_symbol=Symbol("BTC/USD"),
                      base_currency=BTC, quote_currency=USD, price_precision=2, size_precision=6,
                      price_increment=Price.from_str("0.01"), size_increment=Quantity.from_str("0.000001"),
                      ts_event=0, ts_init=0, maker_fee=Decimal("0"), taker_fee=Decimal("0"))


def main():
    df = pb.synthetic_daily(n=600, seed=3)
    df.index = pd.date_range("2020-01-01 00:00", periods=len(df), freq="D", tz="UTC")   # 24/7, close at 00:00 UTC
    out = {}
    for base_ccy in (USD, None):
        bt = BarType.from_str(f"{BTCUSD.id}-1-DAY-LAST-EXTERNAL")
        eng = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGPROBE-003"),
                                                  logging=LoggingConfig(log_level="ERROR")))
        eng.add_venue(venue=V, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=base_ccy,
                      starting_balances=[Money(100_000, USD)] if base_ccy else [Money(100_000, USD), Money(0, BTC)],
                      fill_model=FillModel(random_seed=42), fee_model=pb.BpsNotionalFeeModel(10.0))
        try:
            eng.add_instrument(BTCUSD)
        except Exception as exc:  # noqa: BLE001
            out[f"base={base_ccy}"] = f"add_instrument refused: {type(exc).__name__}: {str(exc)[-80:]}"
            eng.dispose()
            continue
        eng.add_data(BarDataWrangler(bt, BTCUSD).process(df))
        st = pb.SmaTargetWeight(pb.SmaTargetConfig(instrument_id=BTCUSD.id, bar_type=bt, headroom_bp=10.0))
        eng.add_strategy(st)
        try:
            eng.run()
            fills = eng.trader.generate_fills_report()
            acct = eng.portfolio.account(V)
            out[f"base={base_ccy}"] = {
                "bars_seen": len(st.rows), "n_fills": len(fills),
                "first_qty": str(fills["last_qty"].iloc[0]) if len(fills) else None,
                "balances": {str(k): str(v) for k, v in acct.balances_total().items()},
                "portfolio_equity": {str(k): str(v) for k, v in eng.portfolio.equity(V).items()},
                "analyzer_returns_len": len(eng.portfolio.analyzer.returns()),
                "parity_vs_local_10bp": {k: (round(v, 5) if isinstance(v, float) else v)
                                         for k, v in pb.parity({"rows": pd.DataFrame(st.rows).set_index("ts")},
                                                               df, 10.0).items()},
            }
        except Exception as exc:  # noqa: BLE001
            out[f"base={base_ccy}"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        eng.dispose()
    for k, v in out.items():
        print(f"{k}: {json.dumps(v, default=str)}")


if __name__ == "__main__":
    main()
```

## Appendix D. Measured output

Machine: Linux cloud container, Python 3.13.17, nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3. Wall times
vary between runs: an earlier run of the same scripts gave A 0.089 s, B 0.084 s, 12 fresh engines 11.75 s and a
reset rerun 2.19 s. The hashes did not change between runs or processes.

### D.1 `probe_backtest.py`, stdout

```text
python 3.13.17 | nautilus_trader 1.231.0 | numpy 2.3.5 | pandas 2.3.3
bars 600 2020-01-02 21:00:00+00:00 -> 2022-04-20 21:00:00+00:00
A_wall_s: 0.07
B_wall_s: 0.057
A_n_orders: 21
A_n_fills: 21
fills_report_columns: ["trader_id", "strategy_id", "instrument_id", "venue_order_id", "account_id", "trade_id", "position_id", "order_side", "order_type", "last_qty", "last_px", "currency", "commission", "liquidity_side", "event_id", "ts_event", "ts_init", "info", "reconciliation"]
order_fills_columns: ["trader_id", "strategy_id", "instrument_id", "venue_order_id", "position_id", "account_id", "last_trade_id", "type", "side", "quantity", "time_in_force", "is_reduce_only", "is_quote_quantity", "filled_qty", "liquidity_side", "avg_px", "slippage", "commissions", "emulation_trigger", "status", "contingency_type", "order_list_id", "linked_order_ids", "parent_order_id", "exec_algorithm_id", "exec_algorithm_params", "exec_spawn_id", "tags", "init_id", "ts_init", "ts_last"]
account_report_columns: ["total", "locked", "free", "currency", "account_id", "account_type", "base_currency", "margins", "reported", "info"]
positions_report_columns: ["trader_id", "strategy_id", "instrument_id", "account_id", "opening_order_id", "closing_order_id", "entry", "side", "quantity", "peak_qty", "ts_init", "ts_opened", "ts_last", "ts_closed", "duration_ns", "avg_px_open", "avg_px_close", "commissions", "realized_return", "realized_pnl", "is_snapshot"]
hash_order_fills_raw_A_B: ["ae2858c222f68fb3", "b619083a03f29b8f"]
hash_order_fills_nouuid_A_B: ["d8ec1a206665cfb5", "d8ec1a206665cfb5"]
hash_fills_raw_A_B: ["75c06e844fafe326", "f4b106a494a2dffe"]
hash_fills_nouuid_A_B: ["4443e95f46b89f8d", "4443e95f46b89f8d"]
equity_identical_A_B: true
A_fill_px: {"same_close": 21, "next_open": 0, "next_close": 0, "other": 0, "examples": [{"fill_ts": "2021-04-26 21:00:00+00:00", "last_px": 217.24, "tag": "same_close"}, {"fill_ts": "2021-04-27 21:00:00+00:00", "last_px": 216.79, "tag": "same_close"}, {"fill_ts": "2021-04-29 21:00:00+00:00", "last_px": 211.92, "tag": "same_close"}]}
A_first_fill: {"order_side": "BUY", "last_qty": "458", "last_px": "217.24", "commission": "497.48 USD", "liquidity_side": "TAKER", "ts_event": "2021-04-26 21:00:00+00:00"}
A_fee_vs_bp_formula: [["497.48 USD", 497.4796], ["3.25 USD", 3.25185], ["482.12 USD", 482.118]]
A_denied: []
A_rejected: []
A_final_cash: 80066.34999999999
A_final_equity: 80066.34999999999
A_parity_1x: {"signal_agree": 1.0, "n_signal_days": 401, "switches": 14, "corr": 0.9999992869065732, "sharpe_nt": -1.8975198881857827, "sharpe_loc": -1.8954394043275797, "sharpe_diff": 0.0020804838582029195, "max_abs_ret_diff": 0.0001681461544884577, "nt_equity_vs_portfolio_equity_maxdiff": 1.4551915228366852e-11}
A_account_report_rows: 22
A_analyzer_returns_len: 603
A_analyzer_returns_head: {"2020-01-03 00:00:00+00:00": 0.0, "2020-01-04 00:00:00+00:00": 0.0, "2020-01-05 00:00:00+00:00": 0.0, "2020-01-06 00:00:00+00:00": 0.0}
A_analyzer_stats: {"Returns Volatility (252 days)": 264.7593, "Average (Return)": 2.0423, "Average Loss (Return)": -0.9991, "Average Win (Return)": 88.4627, "Sharpe Ratio (252 days)": 1.9438, "Sortino Ratio (252 days)": 301.1763, "Profit Factor": 177.0882, "Risk Return Ratio": 0.1225}
A_positions_report_rows: 7
C_2x_parity: {"signal_agree": 1.0, "n_signal_days": 401, "switches": 14, "corr": 0.9999938160690378, "sharpe_nt": -2.327506775230344, "sharpe_loc": -2.3218906465362306, "sharpe_diff": 0.005616128694113431, "max_abs_ret_diff": 0.00035063805371415846, "nt_equity_vs_portfolio_equity_maxdiff": 1.4551915228366852e-11}
C_2x_final_equity: 74716.61
C_2x_total_commission: 12136.900000000001
A_1x_total_commission: 6276.219999999999
D_maker_taker_vs_custom_commissions_equal: true
E_fractional_first_qty: "458.0302"
E_fractional_parity_1x: {"signal_agree": 1.0, "n_signal_days": 401, "switches": 14, "corr": 0.9999996203534053, "sharpe_nt": -1.8969550277271112, "sharpe_loc": -1.8954394043275797, "sharpe_diff": 0.001515623399531485, "max_abs_ret_diff": 0.00012198746641067792, "nt_equity_vs_portfolio_equity_maxdiff": 0.004880000022239983}
F_at_the_close_fills: 0
F_at_the_close_rejected_first: ["time in force AT_THE_CLOSE is not currently supported"]
F_at_the_close_n_rejected: 53
G_latency_fill_px: {"same_close": 2, "next_open": 0, "next_close": 0, "other": 0, "examples": [{"fill_ts": "2021-04-27 21:00:00+00:00", "last_px": 216.79, "tag": "same_close"}, {"fill_ts": "2021-04-28 21:00:00+00:00", "last_px": 215.32, "tag": "same_close"}]}
H_next_open_fill_px: {"same_close": 0, "next_open": 1, "next_close": 0, "other": 0, "examples": [{"fill_ts": "2021-04-27 14:30:00+00:00", "last_px": 217.47, "tag": "next_open"}]}
I_no_headroom_n_fills: 1
I_no_headroom_denied: []
I_no_headroom_n_denied: 0
I_no_headroom_min_cash: 100000.0
```

### D.2 `probe_backtest.py`, stderr (engine error log, colour codes removed)

These three lines are the forced stops of runs G (latency, double buy), H (next open sized at the close, gap up)
and I (no headroom). They are expected.

```text
2021-04-28T21:00:00.000000000Z [ERROR] QGPROBE-001.BacktestEngine: Stopping backtest from AccountBalanceNegative(balance=-98895.91, currency=USD)
2021-04-27T14:30:00.000000000Z [ERROR] QGPROBE-001.BacktestEngine: Stopping backtest from AccountBalanceNegative(balance=-99.27, currency=USD)
2021-04-26T21:00:00.000000000Z [ERROR] QGPROBE-001.BacktestEngine: Stopping backtest from AccountBalanceNegative(balance=-430.05, currency=USD)
```

### D.3 `probe_followups.py`, stdout

```text
acct_report_first3_after_start: [["2021-04-26 21:00:00+00:00", 6.6], ["2021-04-27 21:00:00+00:00", 653.72], ["2021-04-29 21:00:00+00:00", 96595.2]]
analyzer_returns_min_max: [-0.9999, 192.5254]
analyzer_returns_index_freq: "D"
analyzer_returns_weekend_rows: 172
strategy_equity_returns_min_max: [-0.0227, 0.0228]
bars_seen_vs_loaded: [600, 600]
force_stop_flag_after_clean_run: false
result_fields: {"iterations": 600, "total_events": 42, "total_orders": 21, "total_positions": 7, "backtest_end": "2022-04-20 21:00:00+00:00"}
nohead_force_stop_flag: true
nohead_bars_seen_vs_loaded: [343, 600]
nohead_result_iterations: 342
nohead_backtest_end: "2021-04-26 21:00:00+00:00"
borrow_bars_seen: 600
borrow_min_cash: -439.52
borrow_n_fills: 24
nextopen_bars_seen: 600
nextopen_n_fills: 20
nextopen_fill_px: {"same_close": 0, "next_open": 20, "next_close": 0, "other": 0, "examples": [{"fill_ts": "2021-04-27 14:30:00+00:00", "last_px": 217.47, "tag": "next_open"}, {"fill_ts": "2021-04-28 14:30:00+00:00", "last_px": 216.77, "tag": "next_open"}, {"fill_ts": "2021-04-30 14:30:00+00:00", "last_px": 211.6, "tag": "next_open"}]}
nextopen_vs_local_close_convention: {"signal_agree": 1.0, "n_signal_days": 401, "switches": 14, "corr": 0.9914291376947464, "sharpe_nt": -1.9230558895936019, "sharpe_loc": -1.8954394043275797, "sharpe_diff": 0.027616485266022117, "max_abs_ret_diff": 0.006592564753717727, "nt_equity_vs_portfolio_equity_maxdiff": 2405.720000000001}
slip1_px_minus_close: [["BUY", 0.01], ["SELL", -0.01], ["SELL", -0.01], ["BUY", 0.01]]
fillmodel_reseeds_global_random: {"unseeded_changes_stream": true, "seeded_equals_seed42": true}
wrangler_wrong_column_order: "raised ValueError: high was < open"
wrangler_rounds_to_price_precision: "300.0049 -> 300.00"
timing_12_fresh_engines_5600_bars_s: 10.92
timing_reset_rerun_s: 1.34
reset_rerun_same_fills_hash: ["c78e7644ab507da5", "c78e7644ab507da5"]
nautilus_subpackages_loaded: ["accounting", "analysis", "backtest", "cache", "common", "config", "core", "data", "execution", "indicators", "live", "model", "persistence", "portfolio", "risk", "serialization", "system", "trading"]
live_or_adapters_loaded: ["nautilus_trader.live", "nautilus_trader.live.config", "nautilus_trader.live.data_engine", "nautilus_trader.live.enqueue", "nautilus_trader.live.execution_engine", "nautilus_trader.live.reconciliation", "nautilus_trader.live.risk_engine"]
third_party_net_loaded: ["asyncio", "socket", "ssl", "uvloop"]
```

stderr of the same run (colour codes removed). This is the expected forced stop of check 2 (no headroom):

```text
2021-04-26T21:00:00.000000000Z [ERROR] QGPROBE-002.BacktestEngine: Stopping backtest from AccountBalanceNegative(balance=-430.05, currency=USD)
```

Two further one-off checks were run inline and are not in a script: (1) the same probe with an `Equity` at
`price_precision=4` on back-adjusted 4-decimal prices gave 13 fills, all at the same-bar close, first fill
170.0887; (2) in the next-open run, `Portfolio.equity` equalled `cash + qty x open` on all 53 days where it
differed from `cash + qty x close`, to within 2.9e-11.

### D.4 `probe_btc_smoke.py`, stdout

```text
base=USD: "add_instrument refused: InvalidConfiguration: _fee=0, taker_fee=0, info=None) for a venue with a single-currency CASH account."
base=None: {"bars_seen": 600, "n_fills": 401, "first_qty": "279.268981", "balances": {"USD": "161.15 USD", "BTC": "278.86931500 BTC"}, "portfolio_equity": {"USD": "161314.15 USD", "BTC": "278.86931500 BTC"}, "analyzer_returns_len": 0, "parity_vs_local_10bp": {"signal_agree": 1.0, "n_signal_days": 401, "switches": 0, "corr": 1.0, "sharpe_nt": 1.40093, "sharpe_loc": 1.40093, "sharpe_diff": 0.0, "max_abs_ret_diff": 4e-05, "nt_equity_vs_portfolio_equity_maxdiff": 0.00497}}
```
