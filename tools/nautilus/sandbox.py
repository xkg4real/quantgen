"""The NautilusTrader sandbox child (spec 2026-10-26 section 5.2), run only in the hash-pinned venv and launched only
through tools/nautilus/launch.py:

    <venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> {--check-env | --guard-selftest | run --in <dir>}

Exit codes (5.2.1): 0 valid; 10 complete but invalid (manifest.json says why); 20 input refused before the engine is
built (one "C-05: ..." line on stderr, no file written); 30 a self-test case misbehaved; any other value a crash.
The structure is spec 5.2.9's. This is the only file that places simulated orders: one call in Port.place (5.6
rule A). It opens only files that inside() builds in its temp dir (5.2.8).
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("SIM")
class Refused(Exception): pass                     # input refused before the engine is built: exit 20
def inside(root, name):                             # 5.2.8: builds every path the sandbox opens
    p = (root / name).resolve()
    if p.parent != root:
        raise Refused(name)
    return p
def plain_mean(xs):                                 # 5.2.5, both ports: a left-to-right loop, never sum()
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)
def require_backtest_environment(env):              # 5.2.5 (C-2)
    if env is not Environment.BACKTEST:
        raise RuntimeError(f"kernel environment {env.name}, not BACKTEST")
def require_backtest_clock(clock):
    if not isinstance(clock, TestClock):
        raise RuntimeError("the strategy clock is not a TestClock")
def make_fee_model(cost_bps, stress):               # 5.2.3: a closure, so no __init__ and no super()
    if Decimal(stress) < 1:
        raise ValueError("stress below 1")
    rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)
    class BpFeeModel(FeeModel):
        def get_commission(self, order, fill_qty, fill_px, instrument):
            return Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate,
                         instrument.quote_currency)
    return BpFeeModel()
def build_engine():                                 # 5.2.3, rows Engine and Kernel check
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), run_analysis=False,
                                                 logging=LoggingConfig(log_level="ERROR", log_colors=False)))
    require_backtest_environment(engine.kernel.environment)
    return engine
class PortConfig(StrategyConfig, frozen=True):      # every parameter lives here, never in an __init__ (rule F3)
    instrument_id: str; bar_type: str; cost_bps: str; stress: str
    closes: list; ts: list                          # the close strings of bars.csv and their ts_ns
class TrendSwitchConfig(PortConfig, frozen=True):
    rule: str; lookback: int; step: int
class CryptoTrendConfig(PortConfig, frozen=True):
    hysteresis: float; lookbacks: list; mas: list
class Port(Strategy):                               # no __init__: Strategy's own stores the config
    def on_start(self):
        require_backtest_clock(self.clock)          # first statement (C-15)
        self.iid = InstrumentId.from_str(self.config.instrument_id)
        self.inst = self.cache.instrument(self.iid)
        self.px = [float(c) for c in self.config.closes]
        self.i, self.held, self.fills, self.decisions, self.equity, self.invalid_reasons = -1, 0, [], [], [], []
        self.denied = self.rejected = 0
        self.subscribe_bars(BarType.from_str(self.config.bar_type))
        self.strategy_started = True                # last statement (C-15)
    def on_bar(self, bar):                          # never raises: Nautilus re-raises, which ends the child
        self.i += 1
        if bar.ts_event != self.config.ts[self.i] or bar.close != Price.from_str(self.config.closes[self.i]):
            self.invalid_reasons.append(f"C-12: bar {self.i} differs from bars.csv")   # id first (QA-R3-8)
            return
        i, close = self.i, self.config.closes[self.i]
        cash = self.portfolio.account(VENUE).balance_total(USD).as_decimal()
        qty = self.portfolio.net_position(self.iid)
        self.equity.append([i, bar.ts_event, close, str(cash), str(qty), str(cash + qty * Decimal(close))])
        decision, margin = self.decide(i)
        if decision is None:
            return
        if self.cache.orders_inflight_count() or self.cache.orders_open_count():
            self.invalid_reasons.append(f"C-13: bar {i}: an order in flight on a decision bar")
            return
        action = "hold"
        if decision != self.held:
            if decision == 1:                       # fee-inclusive sizing: q = floor(cash / (P (1 + c s)))
                c = Decimal(self.config.cost_bps) * Decimal(self.config.stress) / Decimal(10000)
                unit = Decimal(1).scaleb(-self.inst.size_precision)
                q = (cash / (Decimal(close) * (1 + c)) / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
                side = OrderSide.BUY
            else:                                   # exit: the whole net position
                q, side = qty, OrderSide.SELL
            action = "skip_zero_qty"
            if q > 0:
                action = "buy" if decision == 1 else "sell"
                self.held = decision
        self.decisions.append([i, bar.ts_event, decision, repr(margin), action])
        if action not in ("buy", "sell"):
            return
        self.place(self.order_factory.market(self.iid, side, Quantity(q, self.inst.size_precision),
                                             time_in_force=TimeInForce.GTC))
    def place(self, order):                         # the one exempt call (5.6 rule A)
        self.submit_order(order)
    def on_order_filled(self, ev):                  # one fills.csv row (5.2.6), no UUID
        self.fills.append([ev.ts_event, ev.order_side.name, str(ev.last_qty), str(ev.last_px),
                           f"{ev.commission.as_decimal():.2f}", ev.commission.currency.code, str(ev.trade_id),
                           str(ev.venue_order_id)])
    def on_order_denied(self, ev): self.denied += 1
    def on_order_rejected(self, ev): self.rejected += 1
class TrendSwitchPort(Port):
    def decide(self, i):                            # -> (decision or None, margin), the table of 5.2.5
        L, s, P = self.config.lookback, self.config.step, self.px
        if i < L or (i - L) % s:
            return None, None
        if self.config.rule == "sma":
            mean = plain_mean(P[i - L + 1:i + 1])
            return (1 if P[i] > mean else 0), abs(P[i] - mean) / P[i]
        r = P[i] / P[i - L] - 1.0                   # tsmom, raw: pnl_matrix passes no rate
        return (1 if r > 0.0 else 0), abs(r)
class CryptoTrendPort(Port):
    def decide(self, i):
        P, cfg = self.px, self.config
        if i < max(max(cfg.lookbacks), max(cfg.mas)):
            return None, None
        refs = [P[i - k] for k in cfg.lookbacks] + [plain_mean(P[i - n + 1:i + 1]) for n in cfg.mas]
        votes = [(P[i] - ref > 0) - (P[i] - ref < 0) for ref in refs]
        comp = sum(votes) / len(votes)
        held = 1 if comp > cfg.hysteresis else 0 if comp < -cfg.hysteresis else self.held
        return held, min(abs(P[i] - ref) / P[i] for ref in refs)
FIELDS = frozenset({"schema", "strategy", "params", "instrument", "capital_usd", "cost_bps", "stress", "fill_seed",
                    "price_precision", "size_precision", "volume", "n_bars", "bars_sha256",
                    "ledger_hash_after_registration"})
def need(ok, what):                                 # one rule of 6.1; a refusal is exit 20 (C-05)
    if not ok:
        raise Refused(what)
def is_int(x, lo, hi):
    return type(x) is int and lo <= x <= hi
def int_text(x, lo, hi):                            # len first: int() raises past 4300 digits
    return type(x) is str and len(x) <= 20 and x.isascii() and x.isdigit() and x == str(int(x)) and lo <= int(x) <= hi
def is_hex(x, n):
    return type(x) is str and len(x) == n and all(ch in "0123456789abcdef" for ch in x)
def check_params(inp):                              # 6.1, row params
    prm = inp["params"]
    need(type(prm) is dict, "params is not an object")
    if inp["strategy"] == "trend_switch":
        need(set(prm) == {"rule", "lookback", "step"}, "params fields")
        need(prm["rule"] in ("sma", "tsmom"), "params.rule")
        need(is_int(prm["lookback"], 1, 5000) and is_int(prm["step"], 1, 5000), "params.lookback or params.step")
        return
    need(set(prm) == {"hysteresis", "lookbacks", "mas"}, "params fields")
    need(type(prm["hysteresis"]) is float and 0.0 <= prm["hysteresis"] < 1.0, "params.hysteresis")
    for k in ("lookbacks", "mas"):
        v = prm[k]
        need(type(v) is list and 1 <= len(v) <= 16 and all(is_int(x, 1, 5000) for x in v), "params." + k)
def check_input(inp, bars_bytes):                   # 6.1, one rule at a time -> (close strings, ts_ns)
    need(type(inp) is dict and set(inp) == FIELDS, "unknown or missing field")
    need(inp["schema"] == "nautilus-bridge-input/2", "schema")
    need(inp["strategy"] in ("trend_switch", "crypto_trend"), "strategy")
    check_params(inp)
    need(inp["instrument"] in ("SPY", "BTC/USD"), "instrument")
    need(int_text(inp["capital_usd"], 1, PRICE_MAX), "capital_usd")
    c = inp["cost_bps"]
    need(type(c) is str and c != "" and c.strip(".") != "" and c.count(".") <= 1
         and all(ch in "0123456789." for ch in c) and Decimal(c) <= 1000, "cost_bps")
    need(inp["stress"] in ("1", "2"), "stress")
    need(is_int(inp["fill_seed"], 0, 2**32 - 1), "fill_seed")
    need(is_int(inp["price_precision"], 0, FIXED_PRECISION), "price_precision")
    need(is_int(inp["size_precision"], 0, FIXED_PRECISION), "size_precision")
    need(inp["instrument"] != "SPY" or inp["size_precision"] == 0, "size_precision")   # Equity: whole shares (5.2.3)
    need(int_text(inp["volume"], 1, QUANTITY_MAX), "volume")
    need(is_int(inp["n_bars"], 1, 100000), "n_bars")
    need(is_hex(inp["bars_sha256"], 64), "bars_sha256 format")
    need(is_hex(inp["ledger_hash_after_registration"], 32), "ledger_hash_after_registration format")
    need(hashlib.sha256(bars_bytes).hexdigest() == inp["bars_sha256"], "bars_sha256 differs from bars.csv")
    try:
        text = bars_bytes.decode("utf-8")
    except ValueError:
        raise Refused("bars.csv is not UTF-8")
    need("\r" not in text and text.endswith("\n"), "bars.csv line ends")
    lines = text.split("\n")[:-1]
    need(lines[0] == "i,ts_ns,close", "bars.csv header")
    need(len(lines) - 1 == inp["n_bars"], "n_bars differs from bars.csv")
    p, closes, ts = inp["price_precision"], [], []
    for k, line in enumerate(lines[1:]):
        f = line.split(",")
        need(len(f) == 3 and f[0] == str(k) and int_text(f[1], 1, 2**63 - 1), f"bars.csv row {k}")
        whole, dot, frac = f[2].partition(".")
        need(whole.isascii() and whole.isdigit() and (len(frac) == p and frac.isascii() and frac.isdigit()
                                                      if p else dot == "") and Decimal(f[2]) > 0, f"close {k}")
        need(Decimal(f[2]) <= PRICE_MAX, f"close {k}")   # Price.from_str raises above PRICE_MAX
        closes.append(f[2])
        ts.append(int(f[1]))
    need(all(b > a for a, b in zip(ts, ts[1:])), "timestamps not strictly increasing")
    return closes, ts
def make_instrument(inp):                           # 5.2.3: rows SPY and BTC/USD -> (instrument, base, balances)
    p, sp = inp["price_precision"], inp["size_precision"]
    if inp["instrument"] == "SPY":
        inst = Equity(instrument_id=InstrumentId(Symbol("SPY"), VENUE), raw_symbol=Symbol("SPY"), currency=USD,
                      price_precision=p, price_increment=Price(Decimal(1).scaleb(-p), p),
                      lot_size=Quantity.from_int(1), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))
        return inst, USD, [Money(int(inp["capital_usd"]), USD)]
    inst = CurrencyPair(instrument_id=InstrumentId(Symbol("BTC/USD"), VENUE), raw_symbol=Symbol("BTC/USD"),
                        base_currency=BTC, quote_currency=USD, price_precision=p, size_precision=sp,
                        price_increment=Price(Decimal(1).scaleb(-p), p),
                        size_increment=Quantity(Decimal(1).scaleb(-sp), sp), ts_event=0, ts_init=0,
                        maker_fee=Decimal(0), taker_fee=Decimal(0))
    return inst, None, [Money(int(inp["capital_usd"]), USD), Money(0, BTC)]
def write_csv(root, name, header, rows):            # 5.2.6: UTF-8, LF; returns the file's SHA-256
    with inside(root, name).open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    return hashlib.sha256(inside(root, name).read_bytes()).hexdigest()
def write_outputs(root, port):                      # 5.2.6's three CSV files -> {name: SHA-256}
    return {
        "fills.csv": write_csv(root, "fills.csv", ["ts_event", "order_side", "last_qty", "last_px", "commission",
                                                   "commission_ccy", "trade_id", "venue_order_id"], port.fills),
        "decisions.csv": write_csv(root, "decisions.csv", ["i", "ts_event", "decision", "margin", "action"],
                                   port.decisions),
        "onbar_equity.csv": write_csv(root, "onbar_equity.csv", ["i", "ts_event", "close", "cash", "qty",
                                                                 "equity_pre"], port.equity)}
def child_reasons(port, result, not_filled, n_bars, last_ts):   # 5.2.7: every reason starts with its id
    reasons = list(port.invalid_reasons)
    if is_backtest_force_stop():
        reasons.append("C-01: forced stop")
    if port.i + 1 < n_bars or result.backtest_end is None or result.backtest_end < last_ts:
        reasons.append("C-02: bars seen fewer than bars fed")
    if not_filled:
        reasons.append(f"C-03: {len(not_filled)} order(s) not FILLED")
    if port.denied or port.rejected:
        reasons.append(f"C-04: {port.denied} order(s) denied, {port.rejected} rejected")
    if not port.strategy_started:
        reasons.append("C-15: the strategy did not start")
    return reasons
def run(root):                                      # exit 0, 10 or 20 (5.2.1)
    raw = inside(root, "input.json").read_bytes()
    try:
        inp = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise Refused("input.json is not UTF-8 JSON")
    closes, ts = check_input(inp, inside(root, "bars.csv").read_bytes())
    inst, base, balances = make_instrument(inp)
    bar_type = BarType.from_str(f"{inst.id}-1-DAY-LAST-EXTERNAL")
    bars = [Bar(bar_type, Price.from_str(c), Price.from_str(c), Price.from_str(c), Price.from_str(c),
                Quantity(Decimal(inp["volume"]), inp["size_precision"]), t, t) for c, t in zip(closes, ts)]
    engine = build_engine()
    engine.add_venue(venue=VENUE, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=base,
                     starting_balances=balances,
                     fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=inp["fill_seed"]),
                     fee_model=make_fee_model(inp["cost_bps"], inp["stress"]), bar_execution=True,
                     bar_adaptive_high_low_ordering=False, allow_cash_borrowing=False)
    engine.add_instrument(inst)
    engine.add_data(bars)
    common = dict(instrument_id=str(inst.id), bar_type=str(bar_type), cost_bps=inp["cost_bps"],
                  stress=inp["stress"], closes=closes, ts=ts)
    if inp["strategy"] == "trend_switch":
        port = TrendSwitchPort(TrendSwitchConfig(**common, **inp["params"]))
    else:
        port = CryptoTrendPort(CryptoTrendConfig(**common, **inp["params"]))
    port.i, port.held, port.fills, port.decisions, port.equity, port.invalid_reasons = -1, 0, [], [], [], []
    port.denied = port.rejected = 0                 # on_start sets them again; kept if it never runs (C-15)
    port.strategy_started = False
    engine.add_strategy(port)
    engine.run()
    result, orders = engine.get_result(), engine.cache.orders()
    not_filled = sorted(str(o.client_order_id) for o in orders if o.status.name != "FILLED")
    reasons = child_reasons(port, result, not_filled, len(bars), ts[-1])
    hashes = write_outputs(root, port)
    u, balance = platform.uname(), engine.portfolio.account(VENUE).balance_total(USD)
    manifest = {
        "schema": "nautilus-bridge-manifest/2", "read_only": True, "mode": "run",
        "python": platform.python_version(), "system": u.system, "machine": u.machine,
        "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                      "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX},
        "environment": engine.kernel.environment.name, "strategy_started": port.strategy_started,
        "input": {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                  "bars_fed": len(bars), "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                  "stress": inp["stress"], "ledger_hash_after_registration": inp["ledger_hash_after_registration"]},
        "engine": {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                   "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True,
                   "fill_seed": inp["fill_seed"]},
        "result": {"bars_seen": port.i + 1, "iterations": result.iterations, "backtest_end": result.backtest_end,
                   "force_stop": is_backtest_force_stop(), "orders_total": len(orders),
                   "orders_filled": len(orders) - len(not_filled), "denied": port.denied,
                   "rejected": port.rejected, "orders_not_filled": not_filled,
                   "account_balance_usd": f"{balance.as_decimal():.2f}",
                   "final_qty": str(engine.portfolio.net_position(inst.id)),
                   "stats_pnls_empty": not result.stats_pnls},
        "hashes": hashes, "valid": not reasons, "invalid_reasons": reasons}
    inside(root, "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                             encoding="utf-8", newline="\n")
    engine.dispose()
    return 0 if not reasons else 10
def check_env():                                    # --check-env: one JSON line, no file (5.2.1)
    engine = build_engine()
    u = platform.uname()                            # not platform.system(): rule F6 flags any call named system
    print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                      "system": u.system, "machine": u.machine, "environment": engine.kernel.environment.name,
                      "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                                    "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX}}))
    engine.dispose()
    return 0
def guard_selftest():                               # --guard-selftest: exit 0, or 30 on a wrong outcome (5.2.1)
    out = {}
    env, clock = require_backtest_environment, require_backtest_clock
    for name, fn, arg in (("sandbox", env, Environment.SANDBOX), ("live", env, Environment.LIVE),
                          ("live_clock", clock, LiveClock()), ("backtest", env, Environment.BACKTEST),
                          ("test_clock", clock, TestClock())):
        try:
            fn(arg)
            out[name] = "passed"
        except RuntimeError:
            out[name] = "raised"
    print(json.dumps(out, sort_keys=True))
    return 0 if list(out.values()) == ["raised"] * 3 + ["passed"] * 2 else 30
def main():
    ap = argparse.ArgumentParser(prog="sandbox.py")
    ap.add_argument("--check-env", action="store_true"); ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv[1:])
    if a.check_env or a.guard_selftest:
        return check_env() if a.check_env else guard_selftest()
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute() or root != root.resolve():
        ap.exit(20, "C-05: run needs --in <an absolute directory equal to its own resolve()>\n")
    try:
        return run(root)
    except Refused as exc:                          # C-05: stderr only, no file (section 7)
        ap.exit(20, f"C-05: input refused: {exc}\n")
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
