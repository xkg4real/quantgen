# 03. Pilot port and parity check: QUANTGEN's vectorized backtest against a Nautilus event-driven backtest

Scope: how pilot 1 (trend on SPY, 12 settings) and pilot 2 (crypto trend on BTCUSD) run in QUANTGEN today, how
to reproduce them in a NautilusTrader `BacktestEngine` so that every difference can be explained, what the
parity check measures, and which offline fixtures pin it. Nautilus API internals are in map 01. The gate,
ledger and Lab inputs are in map 02.

Method: I read the code at commit `f5742ab414696c8cfa8ce07d3dbcd8cf44af8b30`. I then ran a parity probe:
QUANTGEN's own `trend_switch` and `simulate` in the global interpreter (read-only import, `python3 -I -B`, no
writes to the repo), and an independent re-implementation of the same rule as a Nautilus `Strategy` in the
scratchpad venv (`nautilus_trader 1.231.0`, numpy 2.3.5, pandas 2.3.3, pyarrow 26.0.0). Every repo claim cites
`file:line`. External claims cite a URL. "probe:" points to a result file in the scratchpad (section 4.1).
Anything I could not check is marked UNVERIFIED.

Data boundary (read this first): map 02 points out that a SPY-only trend run on the pilot sample, before the
pilot is registered in the trial ledger, would itself be an unregistered trial. The pilot sample starts on
2004-12-01 (`docs/asset_expansion_study.py:724`). **Every real-SPY number below comes from 1995-01-03 to
2004-11-30 (2,497 sessions), which lies entirely before the pilot window.** All crypto numbers come from synthetic
series. I did not touch the pilot-1 window or any BTC price. I wrote no ledger row and changed no tracked file
other than this map. Whether the owner wants the pre-2004 probe recorded in the ledger is open question Q2.

---

## 0. Sixteen findings

1. **Parity holds on real SPY data with a margin of three orders of magnitude.** Setting `sma / 210 / 21`,
   50 bp per side, pre-pilot window: signal agreement 100% (109 of 109 rebalance dates), correlation of daily
   returns 0.99999995, Sharpe difference -0.00006 (0.76802 QUANTGEN vs 0.76796 Nautilus). At 2x costs: 100%,
   0.9999998, +0.00013. The owner's thresholds are 98%, 0.99 and 0.05 (`probe:cmp_base0__A_base0`,
   `probe:cmp_base0__A_stress_stress`).
2. **All 12 grid settings pass at 1x and at 2x.** Over 24 runs: minimum correlation 0.99999901, maximum
   |Sharpe difference| 0.0013, signal agreement 100% everywhere, every run complete, no unfilled order
   (`probe:cmp_g_*`, section 4.3).
3. **The gate would choose the same configuration from either matrix.** Walk-forward (756 / 126, embargo 21) on
   the two 12-column P&L matrices picks the same column at all 14 origins. The out-of-sample series correlate at
   0.99999996, Sharpe difference +0.00004 (1x) and +0.00036 (2x) (section 4.4).
4. **QUANTGEN trades at the close it signals on.** The weight decided at close t earns P(t) to P(t+1) and the
   cost of |Δw| is charged in that same interval (`core/quant/strategies.py:3-5, 82-90`;
   `docs/asset_expansion_study.py:17-18`). A Nautilus MARKET order sent from `on_bar` with no latency model fills
   at the close of the same bar. Measured: every fill sat within 8e-8 bp of the bar close (`probe:cmp_base0__A_base0`
   `max_fill_vs_close_bp`). This matches the Nautilus docs: an order from `on_bar` "settles immediately against the
   book left at bar N's close" (https://github.com/nautechsystems/nautilus_trader/blob/master/docs/concepts/backtesting/bar-execution.md).
5. **The bridge must build Nautilus returns from fills, measured on pre-fill equity.** With E⁻(t) = cash + qty x
   close(t) before the fills of bar t, the series E⁻(t+1) / E⁻(t) - 1 is the exact analogue of QUANTGEN's
   `pnl[t] = w(t) r(t+1) - c |Δw(t)|` (derivation in section 2.9). The PortfolioAnalyzer returns are unusable on a
   CASH account (map 01, finding 5).
6. **One sizing rule closes the cash-account gap.** Buy `qty = floor(cash / (close x (1 + c)))` in exact Decimal
   arithmetic. Then notional plus commission never exceeds cash, and the residual return gap on an entry day is
   c(c - r)/(1 + c): at most about 1 bp per day at 50 bp. Measured maximum: 0.97 bp at 1x, 1.54 bp at 2x.
7. **Both sides must read the same adjusted-close series, and Nautilus must trade it as if it were a price.** The
   SPY cache holds one column: Yahoo's dividend-adjusted close (`docs/asset_expansion_study.py:85, 88-90`). It has
   no open, high, low, volume or dividend column. The bridge builds bars with O = H = L = C = adjusted close. Dividends
   are already inside the returns. Nautilus 1.231.0 has no dividend cash flow in its Python and Cython layers
   (only option greeks and the IB adapter mention dividends; I searched the installed package).
8. **Bar volume and price precision are parity parameters, not data.** With a synthetic volume of 1e12 and 9
   price decimals, fills are exact. With 2 decimals, the tracking error rises to 0.085% a year (still passes).
   With a thin volume (4,000 shares per bar), Nautilus filled 1,000 shares at the close and the rest one tick
   worse, cash went to -$270.23, and the engine stopped the whole backtest after 211 of 2,497 bars without raising
   (`probe:nt_C2_thin`). The bridge must fail closed on any incomplete run (section 2.10).
9. **Next-session execution is the real realism question, and it fails parity by design.** A one-bar latency
   (fill at the next close) gives correlation 0.98295 and Sharpe -0.098 against QUANTGEN (`probe:cmp_base0__C3_lag1`).
   Shifting QUANTGEN's own weights by one session gives 0.9829 and -0.0980. The two agree, so the gap is the timing
   assumption, not engine error. It must be reported as a separate, labelled realism delta, not as parity.
10. **The 98% signal-agreement bar is not the binding check.** On the probe series, flipping one 21-session block
    drops the correlation below 0.99 in only 28% of cases and moves Sharpe by more than 0.05 in only 17%. In parity
    mode both sides compute the same rule on the same closes, so any disagreement is a bug. I recommend 100% as an
    engineering check next to the owner's 98% (section 3).
11. **Walk-forward near-ties can flip the selection.** At one probe origin the best and the runner-up differ by an
    in-sample Sharpe of 0.0006. The largest engine-to-engine IS-Sharpe difference was 0.00069. On the pilot data a
    near-tie could pick a different column on each side. A tie rule is needed (metric P11).
12. **The study's "tsmom" rule is not an excess-return rule.** `trend_switch` subtracts `cash_rate_daily` from the
    lookback return (`core/quant/strategies.py:180`), but `pnl_matrix` calls `fn(prices, **theta)`
    (`core/quant/strategies.py:384`) and the grid has no rate (`docs/asset_expansion_study.py:274`). So the study's
    tsmom is "lookback return > 0". Only `ui/etf_page.py:82` passes a rate. The Nautilus port must copy the study.
    The owner should confirm this before pilot 1 is registered (Q3).
13. **Nautilus pays no interest on cash. The bridge must add it.** QUANTGEN credits the unallocated weight with
    DGS3MO / 252 (`core/quant/strategies.py:85-87`; `docs/asset_expansion_study.py:148-153, 279`). Adding
    (cash after fills / E⁻) x rf to each Nautilus return reproduces it: Sharpe difference -0.00006, tracking error
    4e-5 a year (`probe:cmp_baserf__A_baserf`).
14. **The crypto study does not apply its stated weekend slippage.** A card line says "weekend slippage set at 2x
    in the crypto backtests" (`docs/asset_expansion_study.py:594-595`). The crypto trend card charges a flat 10 bp
    (`docs/asset_expansion_study.py:337`) through a single-rate `simulate` (`core/quant/strategies.py:69-90`). Parity
    must use the flat rate. A weekend-aware fee would be a new, separately registered variant.
15. **The crypto mechanics pass parity on synthetic data.** `crypto_trend` on 1,500 synthetic calendar days, the
    study's five hysteresis values, 10 bp and 20 bp: agreement 100%, minimum correlation 0.99999984, maximum |Sharpe
    difference| 0.0003. Instrument: spot `CurrencyPair` BTC/USD, 8 size decimals, commission in USD (section 5).
16. **Two hand-checkable fixtures already pass on both engines.** F1 (trend, 12 bars) and F2 (crypto trend, 11
    bars) reproduce my hand arithmetic to the cent: every fill quantity, price, commission and cash balance
    (section 6).

---

## 1. Pilot 1 exactly as QUANTGEN runs it

### 1.1 Inputs

| Item | Value | Where |
|---|---|---|
| Price file | `docs/asset_expansion/cache/yf_SPY.csv`, columns `Date, yf_SPY`, 7,986 rows, 1995-01-03 to 2026-09-25, md5 `d2164597d576e1b2fcadde063065811d` | file; read by `_cached` `docs/asset_expansion_study.py:68-79` |
| Price meaning | Yahoo close downloaded with `auto_adjust=True`, the `Close` column only | `docs/asset_expansion_study.py:82-91` (85, 88-90) |
| Adjustment | "total" (splits and dividends) for a Yahoo equity ticker | `core/quant/history.py:61-64, 279-281` |
| Sample | rows on or after 2004-12-01: 5,489 rows to 2026-09-25 | `docs/asset_expansion_study.py:141, 724` (counted by me) |
| Panel | `concat(...).dropna()`, start filter, at least 300 rows | `docs/asset_expansion_study.py:138-145` |
| Cash rate | FRED DGS3MO, forward-filled to the panel dates, missing = 3%, / 100 / 252 | `docs/asset_expansion_study.py:94-104, 148-153` |
| Cost | `us` = 50 bp per side; stress x2 = 100 bp | `core/quant/validate.py:57, 78`; `core/quant/strategies.py:380, 387` |
| Grid | `grid_from(rule=["sma","tsmom"], lookback=[126,210,252], step=[21,42])` = 12 settings | `docs/asset_expansion_study.py:274`; `core/quant/strategies.py:392-398` |
| Benchmark | SPY's own daily return (the mean over one column) | `docs/asset_expansion_study.py:275` |
| Walk-forward | IS 756, OOS 126, embargo 21 | `core/quant/validate.py:54`; `docs/asset_expansion_study.py:278` |
| P&L dates | P&L row t is labelled with date t+1 | `docs/asset_expansion_study.py:184` |

Note: the stored grid card `S_E1_trend_us` is a four-sleeve book (SPY, QQQ, TLT, GLD) (`docs/asset_expansion_study.py:243, 724`).
SPY alone is a new set of configurations (map 02, finding 7).

### 1.2 The 12 settings, in grid column order

`grid_from` nests the axes in argument order, so the column index is
`6 x rule + 2 x lookback_index + step_index` (`core/quant/strategies.py:392-398`).

| Col | rule | lookback | step | | Col | rule | lookback | step |
|---|---|---|---|---|---|---|---|---|
| 0 | sma | 126 | 21 | | 6 | tsmom | 126 | 21 |
| 1 | sma | 126 | 42 | | 7 | tsmom | 126 | 42 |
| 2 | sma | 210 | 21 | | 8 | tsmom | 210 | 21 |
| 3 | sma | 210 | 42 | | 9 | tsmom | 210 | 42 |
| 4 | sma | 252 | 21 | | 10 | tsmom | 252 | 21 |
| 5 | sma | 252 | 42 | | 11 | tsmom | 252 | 42 |

### 1.3 The rule (N = 1 sleeve)

Let P(0..T-1) be the panel closes. Index 0 is the first panel row (2004-12-01 for the pilot).

- Decision dates: t = L, L + s, L + 2s, ... < T (`core/quant/strategies.py:146-147, 176`). They are counted from
  the first panel row, not from calendar month ends. A different start date shifts every decision.
- `sma`: on(t) = P(t) > mean(P(t-L+1), ..., P(t)). The mean includes P(t) (`core/quant/strategies.py:111-116, 178`).
- `tsmom`: on(t) = P(t) / P(t-L) - 1 - sum(rf(t-L .. t-1)) > 0 (`core/quant/strategies.py:180-181`). In the study
  rf = 0 here (finding 12), so on(t) = P(t) > P(t-L).
- w(t) = on(t) / N = 0 or 1, held until the next decision date (`core/quant/strategies.py:182, 150-156`). W = 0 for
  t < L.

### 1.4 The simulator

From `core/quant/strategies.py:82-90`, for t = 0 .. T-2:

```
r(t+1)  = P(t+1) / P(t) - 1
pnl(t)  = w(t) r(t+1) + (1 - w(t)) rf(t) - c |w(t) - w(t-1)|,   with w(-1) = 0
```

- The first entry is charged (turnover starts from a row of zeros, line 88).
- The turnover of the last row, T-1, is dropped (line 89-90). A trade on the last bar costs nothing.
- Cash earns rf only when the book is long-only (line 85), which holds here.
- Between decision dates the weight is constant, so QUANTGEN implicitly holds 100% of current equity. For w in
  {0, 1} this equals buy-and-hold. No drift rebalancing occurs.
- The local `run_backtest` uses the same timing without the cash leg (`core/quant/backtest.py:116-119`).

### 1.5 What must be fixed before registration

These choices change the configurations. Each must be fixed and written into the ledger rows before any pilot
run (map 02, sections 3.2 and 3.5):

1. Start date: 2004-12-01 (the study's US trend start) or the first cache date (1995-01-03, about ten more years of
   SPY-only history).
2. The tsmom rate: raw lookback return, as the study runs (my recommendation, for comparability), or excess
   return.
3. Cash rate: DGS3MO as in the study.
4. Cost 50 bp per side, stress 100 bp. Benchmark SPY. Embargo 21.
5. The trial count N for the DSR (map 02, finding 3).

From the row counts alone (I ran `walk_forward` on a random 5,488 x 3 matrix, not on SPY): 38 origins; the first
OOS session is row 777; 4,711 OOS sessions, about 18.7 years at 252 sessions a year. That is well above the five-year minimum (`core/quant/validate.py:585-586`).

---

## 2. Reproducing pilot 1 in Nautilus

### 2.1 Process layout

- Nautilus runs only in its own venv, in a subprocess. The global interpreter stays on numpy 2.3.5, pandas 2.3.3
  and scipy 1.18.0 (`tests/frozen_guard.py:11, 39`). The subprocess also keeps Nautilus's reseeding of Python's
  global `random` away from QUANTGEN (map 01, finding 14).
- The Nautilus side returns fills only. The QUANTGEN side rebuilds returns from those fills and the same closes
  (section 2.9). It then runs the parity check and, if parity passes, the gate.
- The strategy file calls `submit_order`. That text and call are forbidden in every scanned tree
  (`tests/macro_m0_harness.py:28-29, 44-46, 63, 137`). Where the file may live is the owner's T-RO-01 decision
  (map 01, section 9; map 02, finding 10).
- Orders inside the backtest are simulated. Nothing from `nautilus_trader.live` or `nautilus_trader.adapters` is
  imported by bridge code. The kernel itself loads some `live` modules (map 01, finding 11).

### 2.2 One price series, two engines

1. The bridge reads the cache file once and records its md5.
2. It applies the panel rules of `docs/asset_expansion_study.py:138-145` (drop NaN, start filter).
3. It rounds every close once to 9 decimals and gives that same float64 array to both sides. (The probe fed
   QUANTGEN the unrounded floats; the residue was below 1e-10 relative, so either way works. Rounding once makes it
   exact.)
4. Both sides assert identical date vectors. A missing or extra date moves every index-based decision date.

### 2.3 Bars

| Field | Value | Why |
|---|---|---|
| Bar type | `SPY.SIM-1-DAY-LAST-EXTERNAL` | Bar execution needs an EXTERNAL source (docs, bar-execution.md) |
| open = high = low = close | the adjusted close | The cache has no other column |
| Price precision | 9 | 2 decimals adds 0.085%/yr tracking error (`probe:cmp_base0__C1_cents`) |
| Volume | 1e12, at the instrument's size precision | Nautilus refuses a volume whose precision differs from the instrument's (probe error: "invalid bar.volume.precision=0 did not match instrument.size_precision=8"). Thin volume caps fills (finding 8) |
| ts_event = ts_init | date at 21:00 UTC (US equity) | The docs require `ts_init` at the bar close (bar-execution.md, "Bar timestamp convention") |

### 2.4 Venue and instrument

```
venue      SIM, OmsType.NETTING, AccountType.CASH, base_currency USD, starting balance 1,000,000 USD
           bar_execution=True, book L1_MBP, latency_model=None, default fill model (prob_slippage 0),
           allow_cash_borrowing=False, fee_model=BpFeeModel(cost_bps)
instrument Equity SPY.SIM, price_precision 9, price_increment 1e-9, lot_size 1, maker_fee 0, taker_fee 0
```

`Equity` holds whole shares only: it fixes `size_precision=0` (installed source
`nautilus_trader/model/instruments/equity.pyx:115-117`; map 01, finding 9).

### 2.5 Strategy (independent re-implementation)

- Keep a list of closes and a bar counter i (i = 0 on the first panel row).
- On each bar: compute the rule of section 1.3 only when i >= L and (i - L) % s == 0. Log (i, target).
- Trade only when the target changes. Flat to long: buy `floor(cash / (close x (1 + c)))` shares, computed in
  Decimal. Long to flat: sell the whole position.
- Do not top up or trim between decisions. QUANTGEN charges no turnover for drift, so neither may Nautilus.
- Do not close positions on stop. QUANTGEN never liquidates at the end.
- Compute the SMA as a plain mean over the last L closes. Do not use a Nautilus indicator: a running-sum indicator
  can drift in the last bits and flip a near-tie (section 3.4, source 7).

The probe's version is `scratchpad/parity_probe/nt_side.py`, class `RuleStrategy` (about 60 lines). Note: a Nautilus
component already owns an attribute named `state`; the strategy's own state needs another name.

### 2.6 Execution timing modes

| Mode | Setup | Fill price | Role |
|---|---|---|---|
| Same close (parity) | MARKET GTC from `on_bar`, `latency_model=None` | close of the decision bar | Parity. Matches `strategies.py:82-90` |
| Next close | `LatencyModel(base_latency_nanos >= 1)`, bars only | close of the next bar | Realism delta. Measured: corr 0.98295, ΔSR -0.098 (pre-pilot, `sma/210/21`) |
| Next open | One `TradeTick` at each session open (14:30 UTC) plus a 1 ns latency | open of the next session | Realism delta. Needs open prices, which the cache lacks |
| AT_THE_CLOSE | `TimeInForce.AT_THE_CLOSE` | rejected in backtest | Not usable (map 01, finding 3) |

The docs confirm there is no native next-bar-open mode (bar-execution.md, note under "Order submission timing").
I checked the next-open recipe on fixture F1 with synthetic opens open(t) = close(t-1) x 1.01: the signal at Friday's
close filled at Monday's 14:30 UTC tick at 101.00 = 100 x 1.01, and the next two fills landed at 96.96 and 99.99, as
expected (`scratchpad/parity_probe/nt_open_probe.py`). Two cautions: sizing at the close and filling at a higher
open can overdraw a CASH account (that run needed `allow_cash_borrowing=True`, final cash -$9,498.07); and a
strategy that re-targets every bar must wait while an order is in flight (map 01, section 3).

A realism leg on SPY needs an adjusted OHLC file. UNVERIFIED: that `yfinance` with `auto_adjust=True` scales open,
high and low by the same factor as the close; I did not check the yfinance source.

### 2.7 Whole shares and the cash buffer

| Variant | Account and sizing | ΔSharpe | Tracking error / yr | Note |
|---|---|---|---|---|
| A (recommended) | CASH, buffer `floor(cash / (P(1+c)))`, $1M | -0.00006 | 0.004% | mean weight while long 0.99997 |
| C4 | as A, $10,000 | -0.00020 | 0.023% | integer rounding at about 300 shares |
| C5 | CASH, `floor(cash / P)`, `allow_cash_borrowing=True` | +0.00020 | 0.055% | cash dips to minus the commission; weight drifts to about 1 + c |
| C6 | MARGIN, `floor(cash / P)` | +0.00020 | 0.055% | same as C5; ran to completion |

Sources: `probe:cmp_base0__{A_base0,C4_small,C5_full,C6_margin}`.

The integer-share error is at most one share, P / E of equity: at most 0.08% at $1M for SPY prices up to about $770.
Use $1M or more. Without the buffer, a CASH account stops the run when the fee pushes cash below zero (map 01,
finding 6; my run N1 in section 6.3).

### 2.8 Dividends and total return

- QUANTGEN signals and earns on the adjusted close. The dividend is inside the price path.
- Nautilus receives the same adjusted series. It therefore earns the same total return with no dividend events.
  It has none to add (finding 7).
- Costs are in bp of notional, so the adjusted price level does not distort them. A per-share commission or a
  tick-based slippage would be distorted. Express any slippage in bp.
- Yahoo restates the whole adjusted history after each new dividend. Pin the cache file by md5 for every run.
- The cache value on 1995-01-03 is 26.38. If SPY closed near $45.8 that day, the ratio fits about 31 years of
  reinvested dividends. UNVERIFIED: I did not check the historical raw close.

### 2.9 Return extraction (the key identity)

Let q(t), cash(t) be the position and cash after the fills of bar t, and
E⁻(t) = cash(t-1) + q(t-1) P(t), the equity marked at close t before the fills of bar t.

With the buffer sizing, a buy at t sets q(t) P(t) = E⁻(t) / (1 + c) and leaves cash near zero. So

```
E⁻(t+1) / E⁻(t) - 1 = (1 + r(t+1)) / (1 + c) - 1  on an entry bar,   r(t+1) on a held bar,
                      -c (to rounding)            on an exit bar,     0 on a flat bar.
QUANTGEN pnl(t)     = r(t+1) - c,  r(t+1),  -c,  0.
```

The entry-bar gap is c(c - r)/(1 + c). The Nautilus series labelled with date t+1 is
`R(t) = E⁻(t+1) / E⁻(t) - 1 + (cash(t) / E⁻(t)) rf(t)`. The last term is the cash-interest overlay (finding 13).

Rebuild E⁻ from the fills (quantity, price, commission per fill) and the same closes. Cross-check the final
rebuilt cash against the Nautilus account balance. In the base run they differed by $0.018 over 13 fills, from
2-decimal `Money` rounding (`probe:cmp_base0__A_base0`).

### 2.10 Costs and the 2x rerun

Map 01 (finding 7) shows the custom fee model and `MakerTakerFeeModel` with `taker_fee = c` give identical
commissions. The probe used:

```python
class BpFeeModel(FeeModel):
    def __init__(self, cost_bps: float):
        super().__init__()
        self.rate = Decimal(str(cost_bps)) / Decimal(10000)
    def get_commission(self, order, fill_qty, fill_px, instrument):
        notional = fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal()
        return Money(notional * self.rate, instrument.quote_currency)
```

The 2x rerun is a fresh engine with `BpFeeModel(2 x cost_bps)`, compared with QUANTGEN's `pnl_stress` column
(`core/quant/strategies.py:387`). The built-in model is in the installed source at
`nautilus_trader/backtest/models/fee.pyx:67-112`.

### 2.11 Fail-closed checks on every run

The bridge rejects a run (no parity, no verdict) when any of these holds:

- bars seen by the strategy < bars fed, or `get_result().backtest_end` < the last bar's timestamp
  (the forced-stop flag is a third signal; map 01, section 4);
- any order not FILLED;
- the account balance and the rebuilt cash disagree by more than $0.01 per fill. (After a forced stop they can
  disagree: in N1 the account showed one fill while the fill events showed two.)

---

## 3. Parity metrics

### 3.1 Alignment

- Both sides use the same date vector d(0..T-1). P&L rows are t = 0 .. T-2, labelled d(t+1).
- QUANTGEN series: `pnl` and `pnl_stress` from `simulate` (cost c and 2c).
- Nautilus series: R(t) from section 2.9, one engine at c and one at 2c.
- Decision set D: t = L, L + s, ... < T for trend_switch; every t >= warm-up for crypto_trend.
- Compute each metric per grid column at 1x and at 2x, then on the walk-forward OOS series.

### 3.2 The owner's three checks

| ID | Metric | Definition | Threshold |
|---|---|---|---|
| P1 | Signal agreement | share of t in D with [w_QG(t) > 0] = [target_NT(t) > 0], where target_NT is the strategy's logged decision at bar t | >= 0.98 (owner). Engineering check: = 1.00 |
| P2 | Return correlation | Pearson correlation of pnl and R over all T-1 rows, flat days included | >= 0.99 |
| P3 | Sharpe difference | \|S(R) - S(pnl)\| with S = `validate.sharpe`: mean / std(ddof=1) x sqrt(252), no rf subtracted, non-finite rows dropped (`core/quant/validate.py:137-143`) | <= 0.05 |

Use the logged decision for P1, not the position. In a lagged realism run the position moves one bar late
while the decision still agrees. The probe's position-based agreement was 0.881 in the next-close run and its
decision-based agreement 1.000 (`probe:cmp_base0__C3_lag1`).

### 3.3 Added checks

| ID | Metric | Definition | Proposed bound (parity mode) | Probe worst case (24 SPY runs) |
|---|---|---|---|---|
| P4 | Fill dates | set of bars with a Nautilus fill, excluding bar T-1, equals {t < T-1 : \|Δw(t)\| > 0} | equal | equal |
| P5 | Fill price | max \|fill price / close - 1\| | <= 1e-6 | 8e-12 |
| P6 | Turnover ratio | Σ (fill notional / E⁻) over Σ \|Δw\|, both excluding bar T-1 | [0.99, 1.005] | 0.9934 (2x) |
| P7 | Cost ratio | Σ (commission / E⁻) over c Σ \|Δw\| | [0.99, 1.005] | 0.9934 (2x) |
| P8 | Max drawdown | \|MDD(R) - MDD(pnl)\| on compounded curves | <= 0.005 | 0.0006 |
| P9 | Tracking error | std(R - pnl, ddof=1) x sqrt(252) | <= 0.001 | 0.00019 |
| P10 | Daily gap | max \|R - pnl\| | <= 5 bp | 3.8 bp |
| P11 | Selection | walk-forward chosen column per origin, both matrices; a mismatch is allowed only when the QUANTGEN IS-Sharpe gap between the two columns is < 0.005 | no other mismatch | 0 mismatches |
| P12 | OOS parity | P2 and P3 on the concatenated OOS series (1x and 2x) | as P2, P3 | corr 0.99999996, ΔSR 0.00036 |
| P13 | Completeness | the fail-closed checks of section 2.11 | all pass | all pass |

A parity failure on any column, at either cost level, withholds the verdict for the whole grid. The gate needs every
column for CSCV and the trial dispersion (map 02).

### 3.4 Expected sources of divergence

| # | Source | Mechanism | Size (estimate) | Measured |
|---|---|---|---|---|
| 1 | Cash buffer | entry-day gap c(c - r)/(1 + c) | <= 1 bp at 50 bp, <= 2 bp at 100 bp | max 0.97 / 1.54 bp |
| 2 | Whole shares | weight short by up to P/E | <= 0.08% weight at $1M | ΔSR 0.0002 at $10k |
| 3 | `Money` rounding | commission and cash to the cent | <= $0.005 per fill | $0.018 over 13 fills |
| 4 | Price precision | rounding of adjusted closes | 9 dp: < 1e-10; 2 dp: up to 2 bp/day | 2 dp: TE 0.085%/yr |
| 5 | Cash interest | overlay formula | exact up to the buffer | TE 4e-5/yr |
| 6 | Last-bar trade | QUANTGEN drops the turnover of row T-1 (`strategies.py:89-90`) | one trade | excluded by P4, P6, P7 |
| 7 | Floating-point ties | cumsum SMA vs plain mean | a flip needs \|P - SMA\|/P near 1e-13 | none in 12 x 2,497 bars |
| 8 | Selection near-ties | IS-Sharpe noise vs gap | noise <= 0.0007 | 0 flips in 14 origins; one gap of 0.0006 |
| 9 | Thin volume / overdraft | partial or one-tick-worse fills, forced stop | fatal | caught by P13 |
| 10 | Calendar mismatch | index-based decision dates move | fatal | asserted equal |
| 11 | Execution timing (realism only) | one session later | about -0.1 Sharpe on the probe | corr 0.983, ΔSR -0.098 |

### 3.5 How loose are the owner's bars?

Flipping one 21-session block of `sma/210/21` (109 blocks, one at a time, inside QUANTGEN) gives correlations from
0.9591 to 0.9983 (median 0.9933) and |ΔSharpe| up to 0.155 (median 0.028). Only 28% of single flips fall below
0.99, and only 17% exceed 0.05. Two flips are inside the 98% bar. So a real code bug can pass all three owner checks.
P1 = 100% and P4 catch it.

---

## 4. Measured parity (the probe)

### 4.1 Where things are

Scratchpad `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/parity_probe/`:

| File | Interpreter | Role |
|---|---|---|
| `common_data.py` | both | read-only loaders; mirrors `docs/asset_expansion_study.py:68-79, 94-104, 148-153` |
| `qg_side.py` | global, `-I -B` | imports `core.quant.strategies` read-only; `fn(prices, **theta)` then `simulate` at c and 2c |
| `nt_side.py` | venv, `-I -B` | `BpFeeModel`, `RuleStrategy`, engine setup, fills out |
| `compare.py` | global, `-I -B` | rebuilds E⁻ from fills; P1-P10 with `validate.sharpe` |
| `nt_open_probe.py` | venv | next-open mechanism on F1 |
| `batch_spy.sh`, `batch_grid.sh` | both | the runs below |
| `out/results_summary.json` | | all 46 comparisons and 47 Nautilus run records |

Probe labels in this map name files in `out/` (for example `probe:cmp_base0__A_base0` is `out/cmp_base0__A_base0.json`).
Runtime: 24 Nautilus runs plus 24 QUANTGEN runs plus 24 comparisons on 2,497 bars took 68 s, mostly interpreter
start-up.

### 4.2 Primary setting `sma / 210 / 21`, SPY 1995-01-03 to 2004-11-30, cash rate 0

| Run | Change from A | P1 | P2 corr | S(QG) | S(NT) | ΔS | TE/yr | max gap bp | P6 | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| A | CASH, buffer, 9 dp, vol 1e12, $1M | 1.000 | 0.99999995 | 0.76802 | 0.76796 | -0.00006 | 0.00004 | 0.97 | 0.9973 | yes |
| A 2x | 100 bp vs `pnl_stress` | 1.000 | 0.9999998 | 0.71844 | 0.71857 | +0.00013 | 0.00008 | 1.54 | 0.9947 | yes |
| A rf | cash = DGS3MO, overlay | 1.000 | 0.99999995 | 0.86416 | 0.86410 | -0.00006 | 0.00004 | 0.97 | 0.9973 | yes |
| C1 | 2 price decimals | 1.000 | 0.99998 | 0.76802 | 0.76819 | +0.00017 | 0.00085 | 2.63 | 0.9973 | yes |
| C2 | 2 dp, volume 4,000 | 0.697* | 0.713 | 0.76802 | 0.53857 | -0.229 | 0.133 | 663.6 | 0.077 | NO (engine stopped at bar 211) |
| C3 | 1-bar latency, borrowing | 1.000 / 0.881* | 0.98295 | 0.76802 | 0.67016 | -0.098 | 0.025 | 666.5 | 1.0049 | NO (timing, by design) |
| C4 | $10,000 | 1.000 | 0.9999995 | 0.76802 | 0.76782 | -0.00020 | 0.00023 | 1.65 | 0.9957 | yes |
| C5 | no buffer, borrowing | 1.000 | 0.9999997 | 0.76802 | 0.76822 | +0.00020 | 0.00055 | 2.84 | 1.0020 | yes |
| C6 | MARGIN, no buffer | 1.000 | 0.9999997 | 0.76802 | 0.76822 | +0.00020 | 0.00055 | 2.84 | 1.0020 | yes |

\* position-based agreement; C3's decision-based agreement is 1.000. 13 fills and 13 QUANTGEN switches in every
complete run. Max drawdown: -18.56% (QUANTGEN) vs -18.55% (A).

### 4.3 All 12 settings, same window, cash = DGS3MO with the overlay

| Setting | Switches | corr 1x | ΔS 1x | corr 2x | ΔS 2x | worst gap bp |
|---|---|---|---|---|---|---|
| sma 126 21 | 23 | 0.99999983 | +0.00041 | 0.99999901 | +0.00128 | 3.79 |
| sma 126 42 | 15 | 0.99999995 | -0.00003 | 0.99999979 | +0.00023 | 1.79 |
| sma 210 21 | 13 | 0.99999995 | -0.00006 | 0.99999982 | +0.00013 | 1.54 |
| sma 210 42 | 7 | 0.99999997 | -0.00004 | 0.99999989 | +0.00006 | 1.54 |
| sma 252 21 | 7 | 0.99999999 | +0.00007 | 0.99999989 | +0.00028 | 1.54 |
| sma 252 42 | 5 | 0.99999999 | +0.00007 | 0.99999990 | +0.00025 | 1.54 |
| tsmom 126 21 | 15 | 0.99999989 | +0.00017 | 0.99999943 | +0.00065 | 3.80 |
| tsmom 126 42 | 11 | 0.99999997 | +0.00011 | 0.99999977 | +0.00046 | 1.79 |
| tsmom 210 21 | 5 | 0.99999997 | +0.00011 | 0.99999979 | +0.00033 | 2.70 |
| tsmom 210 42 | 3 | 1.00000000 | -0.00001 | 0.99999999 | +0.00005 | 0.55 |
| tsmom 252 21 | 5 | 1.00000000 | -0.00000 | 0.99999998 | +0.00010 | 0.72 |
| tsmom 252 42 | 3 | 1.00000000 | +0.00001 | 0.99999998 | +0.00009 | 0.72 |

P1 = 1.000 in all 24. All runs complete with no unfilled order. The 2x gaps are slightly positive because the
buffer leaves Nautilus invested at 1/(1 + 2c) on entry days. I report no Sharpe levels here on purpose; they are
in `out/results_summary.json` for the pre-2004 window only.

### 4.4 Walk-forward selection

`validate.walk_forward` (embargo 21) on the two 12-column matrices of section 4.3: 14 origins, chosen columns
(1, 1, 2, 2, 3, 3, 4, 4, 6, 9, 9, 6, 9, 4) on both sides. Largest IS-Sharpe difference between engines 0.00069.
Near-ties on the QUANTGEN side: origin 1386 (gap 0.0006, different columns), origins 1512 and 1638 (gap 0, the two
columns are identical in the IS window; `argmax` takes the first). OOS series: 1,719 sessions, correlation
0.99999996, ΔSharpe +0.00004 at 1x and +0.00036 at 2x.

### 4.5 Crypto mechanics, synthetic data

1,500 calendar days, seeded GBM (seed 20261026, drift 0.0008, volatility 0.035 a day), `crypto_trend` with the study's
defaults and hysteresis in {0, 0.222, 0.444, 0.667, 0.889}, `CurrencyPair` BTC/USD, $100,000, 8 size decimals.

| Hysteresis | Switches | corr 1x (10 bp) | ΔS 1x | corr 2x (20 bp) | ΔS 2x |
|---|---|---|---|---|---|
| 0.000 | 149 | 0.99999996 | +0.00006 | 0.99999984 | +0.00018 |
| 0.222 | 93 | 0.99999997 | +0.00012 | 0.99999989 | +0.00027 |
| 0.444 | 61 | 0.99999998 | +0.00013 | 0.99999994 | +0.00030 |
| 0.667 | 37 | 0.99999999 | +0.00007 | 0.99999996 | +0.00016 |
| 0.889 | 25 | 1.00000000 | +0.00001 | 0.99999998 | +0.00003 |

P1 = 1.000 on all 1,300 daily decisions in every run; every run complete.

### 4.6 Reproduce

```
P=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/parity_probe
$P/batch_spy.sh ; $P/batch_grid.sh            # SPY, pre-pilot window only
python3 -I -B $P/compare.py --qg base0 --nt A_base0
```

---

## 5. Pilot 2: crypto trend on BTCUSD (only after pilot 1 passes parity)

### 5.1 QUANTGEN side

| Item | Value | Where |
|---|---|---|
| File | `docs/asset_expansion/cache/yf_BTC-USD.csv`, Yahoo `BTC-USD` close, 4,392 rows, 2014-09-17 to 2026-09-25, md5 `bc76f530ff24ab445367fe826150bc10` | `docs/asset_expansion_study.py:731` |
| Calendar | 7 days; no gap longer than one day; 1,254 weekend rows | counted by me |
| Adjustment | none ("" for `-USD`) | `core/quant/history.py:279-280` |
| Rule | `crypto_trend`: daily; nine sign votes (lookbacks 7, 14, 21, 28; MAs 10, 20, 50, 100, 200); long when the mean > h, flat when < -h, else hold; warm-up 200 | `core/quant/strategies.py:330-348` |
| Grid | h in {0.0, 0.222, 0.444, 0.667, 0.889}; domain (0, 0.889); N = 11 from the ledger listing | `docs/asset_expansion_study.py:333, 339-343` |
| Cost | `crypto` 10 bp per side, flat; stress 20 bp | `core/quant/validate.py:78`; `docs/asset_expansion_study.py:337` |
| Embargo | 1 | `docs/asset_expansion_study.py:337` |
| Benchmark | BTC buy-and-hold | `docs/asset_expansion_study.py:334` |
| Cash rate | none (the crypto card passes no `cash_daily`; default 0.0) | `docs/asset_expansion_study.py:175, 335-343` |
| Annualisation | 252 on 365-day data, on both sides | `core/quant/validate.py:48, 143` |
| OOS size | 4,391 P&L rows give 29 origins and 3,634 OOS sessions (random-matrix check, embargo 1), about ten calendar years | counted by me |

Alternative file: `binance_BTCUSDT.csv` (3,327 rows from 2017-08-17, quoted in USDT, close only; the client has OHLC
but the study keeps the close, `docs/asset_expansion_study.py:115-120`; `data/crypto/crypto_client.py:224-225`). It is
not the pilot file.

The stored card `S_C3_crypto_trend_btcusd` already ran these five configurations in QUANTGEN (verdict PASS,
`docs/asset_expansion/manifest.json:53`). A Nautilus replica with identical key fields gets the same ledger
`config_id` (map 01, finding 13).

### 5.2 Nautilus side

```
venue      SIM, NETTING, CASH, base_currency=None, balances 1,000,000 USD and 0 BTC
instrument CurrencyPair BTC/USD (spot), price_precision 9, size_precision 8 (1 satoshi), fees 0 on the instrument
fee        BpFeeModel(10) in USD (quote); 2x = BpFeeModel(20)
bars       BTC/USD.SIM-1-DAY-LAST-EXTERNAL, O=H=L=C=close, volume 1e12 at 8 decimals,
           ts = (date + 1 day) 00:00 UTC
strategy   the nine votes and the hysteresis state, decided every bar after warm-up; trade on a state change;
           buy floor_8dp(cash / (close (1 + c))) BTC; sell the whole position
```

- Spot, not `CryptoPerpetual`. QUANTGEN's crypto trend is long/flat "for a spot account"
  (`core/quant/strategies.py:332-334`). A perpetual brings funding settlements and margin
  (https://github.com/nautechsystems/nautilus_trader/blob/master/docs/concepts/backtesting/accounts-and-margin.md).
- A `CurrencyPair` needs a multi-currency CASH account (`base_currency=None`) (map 01, section 11).
- With the commission in USD, the position quantity is not reduced by the fee. A commission in the base currency
  (BTC) would reduce it (https://github.com/nautechsystems/nautilus_trader/blob/master/docs/concepts/positions.md,
  "Base currency commissions").
- Yahoo's crypto closes carry float noise (first close 457.3340148925781), so keep 9 price decimals.
- UNVERIFIED: that Yahoo's `BTC-USD` daily row is the UTC calendar day. The 00:00 UTC close timestamp is a
  convention; parity does not depend on it.
- The gate's minimum is both 1,260 sessions and five full calendar years (`core/quant/validate.py:585-586`). On a
  365-day calendar 1,260 sessions is about 3.5 years, so the calendar rule binds.

---

## 6. Offline fixtures for hermetic tests

### 6.1 Layout

- Layer 1 (global interpreter, no Nautilus): QUANTGEN-side expected values for each fixture, and unit tests of the
  parity metric functions on hand-made arrays. These run in the normal suite.
- Layer 2 (venv only): the Nautilus run of each fixture against a golden JSON of fills. Skip with NotRun when
  `nautilus_trader` cannot be imported. The global interpreter must never import it.
- No network, no cache file. Each fixture writes its prices inline. Store the goldens as JSON next to the tests.

### 6.2 F1: trend switch, 12 bars (verified on both engines)

Inputs: P = [97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97] on business days from 2001-01-02;
`trend_switch(rule="sma", lookback=3, step=2)`; c = 50 bp; capital $1,005,001; CASH; buffer sizing; Equity, 9 dp.

| t | P | SMA3 | decision | W | Nautilus fill | cash after | E⁻(t) |
|---|---|---|---|---|---|---|---|
| 0-2 | 97, 98, 99 | | | 0 | | 1,005,001.00 | 1,005,001 |
| 3 | 100 | 99.000 | on | 1 | BUY 10,000 @ 100.00, fee 5,000.00 | 1.00 | 1,005,001 |
| 4 | 104 | | | 1 | | 1.00 | 1,040,001 |
| 5 | 96 | 100.000 | off | 0 | SELL 10,000 @ 96.00, fee 4,800.00 | 955,201.00 | 960,001 |
| 6 | 95 | | | 0 | | 955,201.00 | 955,201 |
| 7 | 99 | 96.667 | on | 1 | BUY 9,600 @ 99.00, fee 4,752.00 | 49.00 | 955,201 |
| 8 | 101 | | | 1 | | 49.00 | 969,649 |
| 9 | 103 | 101.000 | on (hold) | 1 | | 49.00 | 988,849 |
| 10 | 98 | | | 1 | | 49.00 | 940,849 |
| 11 | 97 | 99.333 | off | 0 | SELL 9,600 @ 97.00, fee 4,656.00 | 926,593.00 | 931,249 |

Hand checks: 1,005,001 / (100 x 1.005) = 10,000.00995, floor 10,000. 955,201 / (99 x 1.005) = 9,600.51, floor 9,600.

Expected P&L, rows t = 0 .. 10 (labelled d(t+1)):

```
QUANTGEN pnl  0, 0, 0, +0.0350000, -0.0769231, -0.0050000, 0, +0.0152020, +0.0198020, -0.0485437, -0.0102041
QUANTGEN turnover  0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0        (the t = 11 sell is dropped, strategies.py:89-90)
Nautilus R    0, 0, 0, +0.0348258, -0.0769230, -0.0050000, 0, +0.0151256, +0.0198010, -0.0485413, -0.0102036
```

Assertions: fills exactly as the table; final cash 926,593.00 in both the account and the rebuild; every
|R - pnl| <= c(c + |r|)/(1 + c) + 1e-9 (the largest is 1.74 bp at t = 3); P1 = 1; P4 holds once bar 11 is excluded.
The fixture exercises an entry, a hold on a rebalance date, an exit, a re-entry, and a last-bar trade.

### 6.3 F2: crypto trend, 11 bars, fractional size (verified on both engines)

Inputs: P = [50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800], daily from 2021-01-01;
`crypto_trend(lookbacks=(1, 2), mas=(2, 3), hysteresis=0.2)` (warm-up 3); c = 10 bp; capital $53,053; CurrencyPair,
8 size decimals.

| t | P | votes (k=1, k=2, MA2, MA3) | mean | state | Nautilus fill |
|---|---|---|---|---|---|
| 3 | 53,000 | + + + + | 1.00 | 1 | BUY 1.00000000 @ 53,000, fee 53.00, cash 0.00 |
| 4 | 52,600 | − + − + | 0.00 | 1 (hold, inside ±0.2) | |
| 5 | 50,000 | − − − − | −1.00 | 0 | SELL 1.00000000 @ 50,000, fee 50.00, cash 49,950.00 |
| 6 | 49,000 | − − − − | −1.00 | 0 | |
| 7 | 50,500 | + + + + | 1.00 | 1 | BUY 0.98812079 @ 50,500, fee 49.90 |
| 8 | 52,000 | + + + + | 1.00 | 1 | |
| 9 | 51,000 | − + − − | −0.50 | 0 | SELL 0.98812079 @ 51,000, fee 50.39 |
| 10 | 50,800 | − − − − | −1.00 | 0 | |

Hand check: 49,950 / (50,500 x 1.001) = 0.9881207901, floor to 8 decimals 0.98812079.

```
QUANTGEN pnl  0, 0, 0, -0.0085472, -0.0494297, -0.0010000, 0, +0.0287030, -0.0192308, -0.0010000
Nautilus R    0, 0, 0, -0.0085386, -0.0494297, -0.0010000, 0, +0.0286743, -0.0192308, -0.0009999
final cash    50,343.77 (account) = 50,343.770395 (rebuild, before cent rounding)
```

This fixture exercises the hysteresis hold, a fractional quantity, and a commission in the quote currency.

### 6.4 Negative fixtures

| ID | Setup | Expected outcome | Status |
|---|---|---|---|
| N1 | F1 with bar volume 4,000 and 2 price decimals | 1,000 @ 100.00 then 9,000 @ 100.01; cash -89.45; engine stops after 4 of 12 bars; the bridge raises "incomplete run" | verified |
| N2 | F1 inputs, QUANTGEN weights with one decision flipped | P1 < 1 and P4 fails; parity FAIL | metric-level test |
| N3 | F1 with a 1 ns latency model | fills one bar later; P1 (decisions) = 1, P4 fails; labelled timing delta, not parity | design |
| N4 | two identical grid columns | P11 tolerates the tie; no false selection flag | design |
| N5 | date vector with one missing row on the Nautilus side | the bridge refuses before running | design |

---

## 7. Risks

1. A probe run touched real SPY data before registration. It stayed outside the pilot window, but it is still
   knowledge of the strategy family on SPY (Q2).
2. The owner's parity bars are loose enough to pass a real bug (section 3.5). Without P1 = 100% and P4, a broken
   port could reach the gate.
3. A near-tie in walk-forward selection can make the two engines pick different columns on the pilot data
   (finding 11). Without P11 the bridge could report a false parity failure, or hide a real one.
4. A Nautilus run can stop early and still return normally (finding 8; map 01, finding 6). Without the checks in
   section 2.11 a truncated run would look like a strategy that went flat.
5. If the realism leg (next open or next close) is fed to the gate, the verdict changes for a reason that is not
   in QUANTGEN's cost model: about -0.1 Sharpe on the probe. That must be a separate, registered variant.
6. The adjusted-close history is restated by Yahoo after each dividend. A refresh between registration and run
   changes the inputs. Pin the md5.
7. 1.231.0 is the last 1.x release (map 01, finding 12). Small API names in this map (for example the reserved
   `state` attribute, the volume-precision check) may change in 2.x.

## 8. Open questions for the owner

- Q1. Parity thresholds: keep 98% / 0.99 / 0.05 as the only gate, or add the engineering checks P1 = 100%, P4,
  P11 and P13 as hard failures (my recommendation) and P5-P10 as warnings?
- Q2. Record the pre-2004 probe (12 settings x 2 cost levels) in the trial ledger as engine-check rows, or leave
  it out because it lies outside the pilot window?
- Q3. Pilot 1 tsmom rule: raw lookback return (as the study runs) or excess over DGS3MO?
- Q4. Pilot 1 start: 2004-12-01 (comparable with `S_E1_trend_us`) or 1995-01-03 (ten more years)?
- Q5. Sizing: CASH with the cost buffer (recommended, closest match) or MARGIN without a buffer (also passes)?
- Q6. Starting capital for the parity run: $1M (recommended) or a realistic retail size? Smaller sizes add
  whole-share error.
- Q7. Is a realism leg in scope for the pilots? If yes, which timing (next open needs a new adjusted OHLC file),
  and is it registered as its own variant?
