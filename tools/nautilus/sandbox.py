"""The NautilusTrader sandbox child (spec 2026-10-26 section 5.2), run only in the hash-pinned venv and launched only
through tools/nautilus/launch.py:

    <venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> {--check-env | --guard-selftest | run --in <dir>}

Exit codes (5.2.1): 0 valid; 10 complete but invalid; 20 input refused before the engine is built; 30 a self-test
case misbehaved; any other value a crash. The structure is spec 5.2.9's. Plan Task 1 builds the two self-checks;
`run` refuses every input with exit 20 until plan Task 3 builds section 5.2 in full.
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
def run(root):                                      # plan Task 1: every input is refused (exit 20); Task 3: 5.2
    raise Refused("run is built at plan Task 3")
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
        return 20
    try:
        return run(root)
    except Refused:
        return 20
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
