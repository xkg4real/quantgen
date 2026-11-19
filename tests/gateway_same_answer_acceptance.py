"""KEY-4 "app behaviour unchanged": the same request gives the same answer before and after core/ moved to
core/gateway.

Each case below calls a core function whose provider access KEY-4 changed, with the providers replaced by fixed
fakes at the provider module (data.*, core.ficc.data, config, sys.modules for gs_quant), which is where both the old
code (an import inside the function) and the new code (core.gateway, looked up at call time) find them. Every fake
also records how it was called, bound to the real provider's signature (``inspect.signature(real).bind``), so a call
the real client would refuse (a wrong argument name, a missing argument) fails here too, and a changed argument
changes the recorded answer. The answers are written as canonical JSON and compared with
tests/fixtures/gateway/same_answers_main.json, which was written by running this same file on main 9f76b07 (before
KEY-4), from the repository root:

    python -m tests.gateway_same_answer_acceptance --write "main <sha>"

No network, no real key, no `.env` (dotenv is patched before import; config functions are patched per case; the
history disk cache is switched off). Nothing that depends on today's date is recorded: dates given to providers are
written as "<date>", and synthetic series are recorded without their dates.
"""
from __future__ import annotations

import dataclasses
import hashlib
import importlib
import inspect
import json
import math
import re
import sys
import types
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    from core.ficc import curve_models, macro
    from core.ficc import data as ficc_data
    from core.market import market_cap, routing
    from core.quant import gsq, history, insights as quant_insights
    from core.research import (analysis, bond_analysis, connections, crypto_workflow, derivatives_workflow,
                               etf_workflow, fx_analysis, market_board, markets, rates_analysis, structuring_analysis,
                               watchlist)
    from data.crypto import crypto_client
    from data.krx import kis_client, krx_market_client
    import data.kis_markets as kis_markets

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "fixtures" / "gateway" / "same_answers_main.json"
DATES = tuple(f"2026-0{1 + i // 28}-{1 + i % 28:02d}" for i in range(45))
LONG = tuple((date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(800))
FAKE_KEY = "fake-key-for-same-answer-test"

# The real provider callables, taken before any patch: each fake binds its arguments against these.
REAL = {
    "KISClient": kis_client.KISClient, "KISClient.daily": kis_client.KISClient.daily,
    "KISMarkets": kis_markets.KISMarkets,
    **{f"KISMarkets.{m}": getattr(kis_markets.KISMarkets, m) for m in (
        "overseas_daily", "krw_yield_daily", "probe", "option_expiries", "etf_quote", "etf_nav_daily",
        "etf_components", "index_daily")},
    "domestic_index_code": kis_markets.domestic_index_code,
    "UpbitPublic.daily": crypto_client.UpbitPublic.daily, "UpbitPublic.ticker": crypto_client.UpbitPublic.ticker,
    "BinancePublic.daily": crypto_client.BinancePublic.daily,
    "BinancePublic.funding": crypto_client.BinancePublic.funding,
    "BinancePublic.premium_index": crypto_client.BinancePublic.premium_index,
    "BinancePublic.open_interest_hist": crypto_client.BinancePublic.open_interest_hist,
    "UpbitAccount.balances": crypto_client.UpbitAccount.balances,
    "KRXMarketClient": krx_market_client.KRXMarketClient, "KRXMarketClient.probe": krx_market_client.KRXMarketClient.probe,
    "_yf_fetch": ficc_data._yf_fetch, "_provider_rows": ficc_data._provider_rows,
}
CALLS: list = []
_AGE = re.compile(r"\d+ business days old")
_DATE_ARGS = {"start", "end", "from"}


def _scrub(name, value):
    if isinstance(value, str) and (value == FAKE_KEY or name in ("apikey", "key", "client_id", "client_secret")):
        return "<key>"
    if name in _DATE_ARGS and value is not None:
        return "<date>"
    return value


def rec(label: str, args=(), kwargs=None, method: bool = True) -> None:
    """Record a fake's call, bound to the real signature (TypeError when the real one would refuse it)."""
    real = REAL[label]
    bound = inspect.signature(real).bind(*((None,) + tuple(args) if method else tuple(args)), **(kwargs or {}))
    CALLS.append([label, {k: _scrub(k, v) for k, v in bound.arguments.items() if k != "self"}])


LONG_LIST = 24


def _summary(items: list):
    """A long list (over 24 items) as its length, its first and last 8 items (exact) and checks over all of it, so
    the fixture stays small while a changed, added, dropped or moved item still changes the answer:

    - floats, in the order they appear: sum, sum of squares, position-weighted sum ``sum((i+1)*x_i)`` and sum of
      squared steps ``sum((x_{i+1}-x_i)**2)``, each compared within the float tolerance. The weighted sum moves when
      values change place; the squared steps move when two neighbours are swapped (by 2*(b-a)*(q-p) for p,a,b,q),
      which the weighted sum of a long, level series alone could hide inside the tolerance;
    - everything else exactly, as a sha256: strings, keys, structure and integers (review 3 DOC3-5: an integer is
      never float noise, so +500 in the middle of a list of integers changes the hash), floats replaced by "#"."""
    numbers: list[float] = []

    def shape(value):
        if isinstance(value, float):
            numbers.append(value)
            return "#"
        if isinstance(value, list):
            return [shape(v) for v in value]
        if isinstance(value, dict):
            return {k: shape(v) for k, v in value.items()}
        return value

    text = json.dumps(shape(items), sort_keys=True, ensure_ascii=False)
    finite = [v for v in numbers if math.isfinite(v)]           # "nan"/"inf" are strings by now, kept in the sha
    return {"__n__": len(items), "head": items[:8], "tail": items[-8:],
            "sum": float(sum(finite)), "sumsq": float(sum(v * v for v in finite)),
            "wsum": float(sum((i + 1) * v for i, v in enumerate(finite))),
            "dsq": float(sum((b - a) ** 2 for a, b in zip(finite, finite[1:]))),
            "shape_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def canon(obj, depth: int = 0):
    """JSON-safe, order-stable form of an answer (dataclasses by field, floats exact, other objects by their
    attributes)."""
    if depth > 12:
        return type(obj).__name__
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {"__type__": type(obj).__name__,
                **{f.name: canon(getattr(obj, f.name), depth + 1) for f in dataclasses.fields(obj)}}
    if isinstance(obj, str):
        return _AGE.sub("<n> business days old", obj)        # the curve note counts days up to today
    if isinstance(obj, bool) or obj is None or isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return repr(float(obj)) if not math.isfinite(obj) else float(obj)
    if isinstance(obj, (list, tuple)):
        items = [canon(v, depth + 1) for v in obj]
        return _summary(items) if len(items) > LONG_LIST else items
    if isinstance(obj, dict):
        return {str(k): canon(v, depth + 1) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if hasattr(obj, "tolist"):
        return canon(obj.tolist(), depth + 1)
    if isinstance(obj, BaseException):
        return {"__error__": type(obj).__name__, "message": str(obj)}
    if callable(obj):
        return f"<callable {getattr(obj, '__name__', type(obj).__name__)}>"
    if hasattr(obj, "__dict__"):
        return {"__type__": type(obj).__name__,
                **{k: canon(v, depth + 1) for k, v in sorted(vars(obj).items()) if not k.startswith("_")}}
    return type(obj).__name__


def _history(symbol, source, closes, dates=DATES):
    return history.History(symbol=symbol, source=source, dates=dates[:len(closes)], closes=tuple(closes))


def _undated(h):
    """A History without its dates: synthetic series end today."""
    return {"symbol": h.symbol, "source": h.source, "note": h.note, "adjustment": h.adjustment,
            "closes": list(h.closes), "n": len(h.dates)}


def _bars(dates, close, **extra):
    return SimpleNamespace(dates=tuple(dates), close=tuple(close), extra=extra, symbol=extra.pop("symbol", ""),
                           source=extra.pop("source", "KIS"))


class FakeKISClient:
    ready = True

    def __init__(self, *a, **k):
        rec("KISClient", a, k, method=False)
        self.calls = 0

    def daily(self, code, *a, **k):
        rec("KISClient.daily", (code,) + a, k)
        self.calls += 1
        if self.calls > 1:
            return []
        return [{"date": d, "close": 100.0 + i} for i, d in enumerate(DATES[:40])]


class FakeKISMarkets:
    ready = True
    expiries: list = []

    def __init__(self, *a, **k):
        rec("KISMarkets", a, k, method=False)

    def overseas_daily(self, *a, **k):
        rec("KISMarkets.overseas_daily", a, k)
        return SimpleNamespace(to_history=lambda: _history(f"{a[0]}:{a[1]}", "KIS", [50.0 + i for i in range(35)]))

    def krw_yield_daily(self, *a, **k):
        rec("KISMarkets.krw_yield_daily", a, k)
        code = a[0] if a else k.get("code", "")
        base = 3.0 + (sum(map(ord, code)) % 7) / 10
        return SimpleNamespace(dates=DATES[:40], close=tuple(base + i / 100 for i in range(40)))

    def probe(self, *a, **k):
        rec("KISMarkets.probe", a, k)
        return {"quote": {"ok": True, "detail": "fake kis"}, "chart": {"ok": False, "detail": "fake down"}}

    def option_expiries(self, *a, **k):
        rec("KISMarkets.option_expiries", a, k)
        return list(self.expiries)

    def etf_quote(self, *a, **k):
        rec("KISMarkets.etf_quote", a, k)
        return {"code": a[0], "price": 10000.0}

    def etf_nav_daily(self, *a, **k):
        rec("KISMarkets.etf_nav_daily", a, k)
        n = 300
        close = [10000.0 * math.exp(0.002 * math.sin(i / 5) + 0.0004 * i) for i in range(n)]
        return _bars(LONG[:n], close, nav=[c * 0.999 for c in close], premium_pct=[0.1] * n)

    def etf_components(self, *a, **k):
        rec("KISMarkets.etf_components", a, k)
        return [{"code": "005930", "weight": 0.3}]

    def index_daily(self, *a, **k):
        rec("KISMarkets.index_daily", a, k)
        code = a[0] if a else k.get("code", "2001")
        n = 600
        close = [300.0 * math.exp(0.01 * math.sin(i / 9) + 0.0003 * i) for i in range(n)]
        return _bars(LONG[:n], close, symbol=f"INDEX:{code}", source="KIS")


class FakeUpbit:
    def daily(self, *a, **k):
        rec("UpbitPublic.daily", a, k)
        market = a[0] if a else k.get("market", "KRW-BTC")
        n = 760
        close = [9e7 * math.exp(0.02 * math.sin(i / 11) + 0.0006 * i) for i in range(n)]
        return SimpleNamespace(dates=LONG[:n], close=tuple(close),
                               to_history=lambda: _history(market, "UPBIT", [9e7 + i for i in range(35)]))

    def ticker(self, *a, **k):
        rec("UpbitPublic.ticker", a, k)
        markets = a[0] if a else k.get("markets", "KRW-BTC")
        markets = [markets] if isinstance(markets, str) else list(markets)
        if len(markets) > 1 and "KRW-NOPE" in markets:
            raise crypto_client.CryptoError("fake rejected list", status=404)
        if markets == ["KRW-NOPE"]:
            raise crypto_client.CryptoError("fake unknown market", status=404)
        return [{"market": m, "price": 1000.0 + len(m)} for m in markets]


class FakeBinance:
    def daily(self, *a, **k):
        rec("BinancePublic.daily", a, k)
        symbol = a[0] if a else k.get("symbol", "BTCUSDT")
        n = 760
        scale = 6e4 if symbol.startswith("BTC") else 3e3
        close = [scale * math.exp(0.025 * math.sin(i / 13 + len(symbol)) + 0.0005 * i) for i in range(n)]
        return SimpleNamespace(dates=LONG[:n], close=tuple(close), quote_volume=tuple(1e9 + i for i in range(n)),
                               to_history=lambda: _history(symbol, "BINANCE", [6e4 + i for i in range(35)]))

    def funding(self, *a, **k):
        rec("BinancePublic.funding", a, k)
        return SimpleNamespace(daily=lambda: {d: 0.0001 * (1 + math.sin(i / 7)) for i, d in enumerate(LONG[:760])})

    def premium_index(self, *a, **k):
        rec("BinancePublic.premium_index", a, k)
        return {"mark": 60000.0, "premium_pct": 0.01, "last_funding_rate": 0.0001}

    def open_interest_hist(self, *a, **k):
        rec("BinancePublic.open_interest_hist", a, k)
        return [{"date": LONG[0], "oi": 1.0}]


class FakeUpbitAccount:
    def balances(self, *a, **k):
        rec("UpbitAccount.balances", a, k)
        return [{"currency": "KRW", "balance": 1000.0, "locked": 0.0, "total": 1000.0, "avg_buy_price": 0.0},
                {"currency": "BTC", "balance": 0.5, "locked": 0.0, "total": 0.5, "avg_buy_price": 8e7},
                {"currency": "NOPE", "balance": 3.0, "locked": 0.0, "total": 3.0, "avg_buy_price": 10.0}]


class FakeKRXMarket:
    def __init__(self, *a, **k):
        rec("KRXMarketClient", a, k, method=False)

    def probe(self, *a, **k):
        rec("KRXMarketClient.probe", a, k)
        return {"ready": True, "path": "/fake/path", "reason": ""}


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def get(self, url, params=None, timeout=None):
        CALLS.append(["session.get", {"url": url, "params": {k: _scrub(k, v) for k, v in sorted((params or {}).items())}}])
        return FakeResponse(200, [{"date": d, "adjClose": 200.0 + i} for i, d in enumerate(reversed(DATES[:40]))])


def _rows(provider, ids, days, **kwargs):
    rec("_provider_rows", (provider, ids, days), kwargs, method=False)
    dates = LONG[-max(days, 40):] if days > 45 else DATES[:40]
    rows = {i: [(d, 2.0 + (len(i) % 5) / 10 + n / 1000) for n, d in enumerate(dates)] for i in ids}
    return rows, {}


def _yf_fetch(tickers, period):
    rec("_yf_fetch", (tickers, period), method=False)
    return {tickers[0]: [(d, 400.0 + n) for n, d in enumerate(DATES[:35])]}


class FakeTicker:
    def __init__(self, symbol):
        CALLS.append(["yfinance.Ticker", {"symbol": symbol}])

    def get_shares_full(self, start=None):
        import pandas as pd
        return pd.Series([1.0e9, 1.1e9], index=pd.to_datetime(["2026-01-02", "2026-02-02"]))

    def history(self, period=None, interval=None, auto_adjust=None, timeout=None):
        import pandas as pd
        CALLS.append(["yfinance.history", {"period": period, "interval": interval}])
        index = pd.to_datetime(list(DATES[:3]))
        return pd.DataFrame({"Open": [1.0, 2.0, 3.0], "High": [1.5, 2.5, 3.5], "Low": [0.5, 1.5, 2.5],
                             "Close": [1.2, 2.2, 3.2], "Volume": [10.0, 20.0, 30.0]}, index=index)


def _fake_gs_quant():
    """A stand-in gs_quant package (top level, timeseries, session, instrument) for sys.modules."""
    top = types.ModuleType("gs_quant")
    top.__version__ = "0.0-fake"
    timeseries = types.ModuleType("gs_quant.timeseries")
    session = types.ModuleType("gs_quant.session")
    instrument = types.ModuleType("gs_quant.instrument")

    class GsSession:
        @staticmethod
        def use(environment, client_id=None, client_secret=None, scopes=()):
            CALLS.append(["GsSession.use", {"environment": environment, "client_id": _scrub("client_id", client_id),
                                            "client_secret": _scrub("client_secret", client_secret),
                                            "scopes": list(scopes)}])

    class IRSwap:
        def __init__(self, side, tenor, ccy):
            CALLS.append(["IRSwap", {"side": side, "tenor": tenor, "ccy": ccy}])
            self.fixed_rate = 0.0375

        def resolve(self):
            CALLS.append(["IRSwap.resolve", {}])

    session.Environment = SimpleNamespace(PROD="PROD")
    session.GsSession = GsSession
    instrument.IRSwap = IRSwap
    top.timeseries, top.session, top.instrument = timeseries, session, instrument
    return {"gs_quant": top, "gs_quant.timeseries": timeseries, "gs_quant.session": session,
            "gs_quant.instrument": instrument}


def _gsq_run(with_keys: bool):
    """gsq with a fake gs_quant installed: reload, status, connect, a priced swap; then reload without the fake."""
    try:
        with patch.dict(sys.modules, _fake_gs_quant()):
            module = importlib.reload(gsq)
            first = module.status()
            connected = module.connect()
            priced = module.price_example_swap("10y", "USD")
        return {"status": first, "connect": connected, "swap": priced}
    finally:
        importlib.reload(gsq)


def _keys(**present):
    """Config key functions patched to fixed answers ("" or a fake value); never real keys."""
    values = {"kis_ready": lambda: bool(present.get("kis")),
              "fmp_key": lambda: FAKE_KEY if present.get("fmp") else "",
              "fmp_ready": lambda: bool(present.get("fmp")),
              "anthropic_key": lambda: FAKE_KEY if present.get("ai") else "",
              "gs_client_id": lambda: FAKE_KEY if present.get("gs") else "",
              "gs_client_secret": lambda: FAKE_KEY if present.get("gs") else "",
              "upbit_ready": lambda: bool(present.get("upbit"))}
    return [patch.object(config, name, fn) for name, fn in values.items()] + [
        patch.object(config, "FICC_CACHE_TTL_SECONDS", 0)]          # the history disk cache is not used


def run(case):
    """Start the case's patches (a patch that cannot start is a test error, not an answer), call, record."""
    del CALLS[:]
    patches = []
    for p in case.get("patches", []):
        p.start()
        patches.append(p)
    try:
        try:
            answer = canon(case["call"]())
        except Exception as exc:                      # an error is an answer too, and must stay the same
            answer = canon(exc)
        return {"answer": answer, "calls": canon(list(CALLS))}
    finally:
        for p in reversed(patches):
            p.stop()


def cases():
    session = FakeSession()
    status_rows = {"quant_provider_status": [{"id": "fmp", "label": "FMP", "ready": True, "vars": ["FMP_API_KEY"]}],
                   "krx_provider_status": [{"id": "kis", "label": "KIS", "ready": False, "vars": ["KIS_APP_KEY"]}],
                   "ficc_provider_status": [{"id": "fred", "label": "FRED", "ready": True, "note": "keyless"}],
                   "crypto_provider_status": [{"id": "upbit", "label": "Upbit", "ready": False, "vars": []}]}
    status = [patch.object(config, name, (lambda rows=rows: rows)) for name, rows in status_rows.items()]
    ficc_probe = {"fred": {"ok": True, "detail": "fake"}, "yfinance": {"ok": False, "detail": "fake down"}}
    crypto_probe = {"upbit": {"ok": True, "detail": "last 1.00"}}
    presence = SimpleNamespace(tool="presence", validate=lambda: None)
    probe = lambda tool: SimpleNamespace(tool=tool, validate=lambda: None)  # noqa: E731
    kis = [patch.object(kis_client, "KISClient", FakeKISClient), patch.object(kis_markets, "KISMarkets", FakeKISMarkets)]
    crypto = [patch.object(crypto_client, "UpbitPublic", FakeUpbit), patch.object(crypto_client, "BinancePublic", FakeBinance),
              patch.object(crypto_client, "UpbitAccount", FakeUpbitAccount)]
    rows = [patch.object(ficc_data, "_provider_rows", _rows)]
    yahoo = [patch.object(ficc_data, "_yf_fetch", _yf_fetch)]
    fmp = [patch.object(history, "_requests", session)]
    every = kis + crypto + rows + yahoo + fmp
    load = lambda symbol, source="auto": _undated(history.load_history(symbol, source=source, days=40))  # noqa: E731

    def plan_refused(symbols, key):
        raise market_cap_quote_client().FMPPlanError("fake plan")

    def market_cap_quote_client():
        import data.fmp.quote_client as quote_client
        return quote_client

    def fmp_get(status, payload):
        def get(url, params=None, timeout=None):
            CALLS.append(["requests.get", {"url": url, "params": {k: _scrub(k, v) for k, v in sorted((params or {}).items())},
                                           "timeout": timeout}])
            return FakeResponse(status, payload)
        return get

    out = {
        "history.kis_history": {"patches": _keys(kis=True) + kis, "call": lambda: history.kis_history("005930", days=40)},
        "history.kis_history.no_key": {"patches": _keys(), "call": lambda: history.kis_history("005930", days=40)},
        "history.kis_market_history": {"patches": _keys(kis=True) + kis,
                                       "call": lambda: history.kis_market_history("NAS:AAPL", days=35)},
        "history.looks_kis_market": {"call": lambda: [history._looks_kis_market(s) for s in
                                                      ("NAS:AAPL", "XXX:AAPL", "KR103501GE31", "005930")]},
        "history.yf_history": {"patches": yahoo, "call": lambda: history.yf_history("SPY", days=35)},
        "history.crypto_history": {"patches": crypto, "call": lambda: [history.crypto_history("KRW-BTC"),
                                                                       history.crypto_history("BTCUSDT")]},
        "history.fmp_history": {"patches": _keys(fmp=True) + fmp, "call": lambda: history.fmp_history("AAPL", days=40)},
        "history.fmp_history.no_key": {"patches": _keys() + fmp, "call": lambda: history.fmp_history("AAPL", days=40)},
        "history.fmp_history.no_requests": {"patches": _keys(fmp=True) + [patch.object(history, "_requests", None)],
                                            "call": lambda: history.fmp_history("AAPL", days=40)},
        "history.ready": {"patches": _keys(kis=True),
                          "call": lambda: {k: f() for k, f in sorted(history._READY.items()) if k in ("FMP", "KIS")}},
        "curve_models.krw_curve_panel": {"patches": kis, "call": lambda: curve_models.krw_curve_panel(days=40)},
        "connections.presence": {"patches": status, "call": lambda: connections.execute_connections(presence).rows},
        "connections.probes": {"patches": [patch.object(ficc_data, "probe", lambda: ficc_probe),
                                           patch.object(kis_markets, "KISMarkets", FakeKISMarkets),
                                           patch.object(krx_market_client, "KRXMarketClient", FakeKRXMarket),
                                           patch.object(crypto_client, "probe", lambda: crypto_probe)],
                               "call": lambda: [connections.execute_connections(probe(t)).rows
                                                for t in ("ficc", "kis", "krx", "crypto")]},
        "analysis.funding_rate": {"patches": rows,
                                  "call": lambda: [analysis.funding_rate("AAPL"), analysis.funding_rate("005930")]},
        "markets.load_markets": {"patches": rows,
                                 "call": lambda: [{k: v for k, v in row.items() if k != "loaded_at"}   # clock time
                                                  for row in markets.load_markets(today=date(2026, 2, 20))]},
        "market_board.ficc_fetch": {"patches": rows, "call": lambda: [market_board._ficc_fetch("FRED")("DGS10"),
                                                                      market_board._ficc_fetch("YFINANCE")("^GSPC")]},
        "macro.load_many": {"patches": rows, "call": lambda: macro.load_many(["DGS10", "^GSPC", "DEXKOUS"], days=40)},
        "market_cap.yahoo": {"patches": [patch.object(ficc_data, "_yf", SimpleNamespace(Ticker=FakeTicker))],
                             "call": lambda: [market_cap.yahoo_shares("AAPL"), market_cap._yahoo_installed()]},
        "market_cap.no_yahoo": {"patches": [patch.object(ficc_data, "_yf", None)],
                                "call": lambda: [market_cap._yahoo_installed()]},
        "market_cap.fmp_key": {"patches": _keys(fmp=True),
                               "call": lambda: bool(market_cap.MarketCapSource(cache=object())._fmp_key())},
        "market_cap.fmp_batch": {"call": lambda: [
            market_cap.fmp_batch(["AAPL", "MSFT"], key=FAKE_KEY, get=fmp_get(200, [
                {"symbol": "AAPL", "marketCap": 3.0e12, "timestamp": 1767225600, "price": 200.0},
                {"symbol": "MSFT", "marketCap": 2.5e12, "timestamp": 1767225600, "price": 400.0}])),
            _err(lambda: market_cap.fmp_batch(["AAPL"], key=FAKE_KEY, get=fmp_get(402, {}))),
            _err(lambda: market_cap.fmp_batch(["AAPL"], key=FAKE_KEY, get=fmp_get(500, {}))),
            _err(lambda: market_cap.fmp_batch(["AAPL"], key=FAKE_KEY,
                                              get=fmp_get(200, {"Error Message": "premium endpoint"})))]},
        "market_cap.provider_plan_refused": {"patches": _keys(fmp=True), "call": lambda: _provider_reasons(
            market_cap.MarketCapSource(fmp_fetch=plan_refused, cache=object(), clock=lambda: 1000.0))},
        "routing.yahoo_frame": {"patches": [patch.object(ficc_data, "_yf", SimpleNamespace(Ticker=FakeTicker))],
                                "call": lambda: routing._yahoo_frame("AAPL", "1d", "1mo")},
        "quant_insights.ai_ready": {"patches": _keys(ai=True), "call": lambda: [quant_insights.ai_ready(),
                                                                                quant_insights._API_URL]},
        "quant_insights.not_configured": {"patches": _keys(),
                                          "call": lambda: quant_insights.deep_analysis("risk", {"x": 1}).error_code},
        "watchlist.quote_client": {"patches": [patch.object(kis_client, "KISClient", FakeKISClient)],
                                   "call": lambda: type(watchlist._quote_client()).__name__},
        "watchlist.no_transport": {"patches": [patch.object(kis_client, "requests", None)],
                                   "call": lambda: watchlist._quote_client()},
        # load_history: every auto branch, with each provider's key present or not (synthetic answers undated)
        "load_history.krx.kis": {"patches": _keys(kis=True) + every, "call": lambda: load("005930")},
        "load_history.krx.no_kis": {"patches": _keys(fmp=True, upbit=True) + every, "call": lambda: load("005930")},
        "load_history.kis_market.kis": {"patches": _keys(kis=True) + every, "call": lambda: load("NAS:AAPL")},
        "load_history.kis_market.no_kis": {"patches": _keys(fmp=True) + every, "call": lambda: load("NAS:AAPL")},
        "load_history.us.fmp": {"patches": _keys(fmp=True) + every, "call": lambda: load("AAPL")},
        "load_history.us.upbit_only": {"patches": _keys(upbit=True) + every, "call": lambda: load("AAPL")},
        "load_history.us.no_key": {"patches": _keys() + every, "call": lambda: load("AAPL")},
        "load_history.crypto": {"patches": _keys() + every, "call": lambda: load("KRW-BTC")},
        "load_history.yahoo": {"patches": _keys() + every, "call": lambda: load("^VIX")},
        "load_history.explicit": {"patches": _keys(kis=True, fmp=True) + every, "call": lambda: [
            load("005930", "kis"), load("NAS:AAPL", "kis"), load("AAPL", "fmp"), load("SPY", "yfinance"),
            load("BTCUSDT", "crypto")]},
        # crypto workflow: prices with a rejected market, and the live analysis with the account balances
        "crypto_workflow.krw_prices": {"patches": crypto, "call": lambda: [
            crypto_workflow.krw_prices(FakeUpbit(), ["KRW-BTC", "KRW-ETH"]),
            crypto_workflow.krw_prices(FakeUpbit(), ["KRW-BTC", "KRW-NOPE"]), crypto_workflow.krw_prices(FakeUpbit(), [])]},
        "crypto_workflow.analyze.balances": {"patches": _keys(upbit=True) + crypto + rows, "call": lambda: _crypto(
            crypto_workflow.analyze(days=730, source="live", card_loader=lambda path: [], include_balances=True))},
        "crypto_workflow.analyze.no_upbit": {"patches": _keys() + crypto + rows, "call": lambda: _crypto(
            crypto_workflow.analyze(days=730, source="live", card_loader=lambda path: [], include_balances=True))},
        # derivatives and ETF workflows on the KIS branch
        "derivatives.snapshot.kis": {"patches": _keys(kis=True) + kis,
                                     "call": lambda: derivatives_workflow.snapshot(source="kis")},
        "derivatives.snapshot.no_kis": {"patches": _keys() + kis,
                                        "call": lambda: derivatives_workflow.snapshot(source="kis")},
        "etf.analyze.kis_letf": {"patches": _keys(kis=True) + kis + [
            patch.object(kis_markets, "domestic_index_code", _domestic_index_code)],
            "call": lambda: _etf(etf_workflow.analyze("122630", days=300, source="kis", card_loader=lambda path: []))},
        # research workflows with their default loaders (FRED/Yahoo rows from the fake provider)
        "execute_bond": {"patches": rows, "call": lambda: bond_analysis.execute_bond(bond_analysis.BondRequest())},
        "execute_rates.curve": {"patches": rows, "call": lambda: rates_analysis.execute_rates(rates_analysis.RatesRequest())},
        "execute_rates.sim": {"patches": rows, "call": lambda: rates_analysis.execute_rates(
            rates_analysis.RatesRequest(tool="sim", n_paths=200))},
        "execute_structuring": {"patches": rows, "call": lambda: structuring_analysis.execute_structuring(
            structuring_analysis.StructuringRequest())},
        "execute_fx": {"patches": rows, "call": lambda: fx_analysis.execute_fx(fx_analysis.FXRequest())},
        "execute_fx.carry": {"patches": rows, "call": lambda: fx_analysis.execute_fx(fx_analysis.FXRequest(tool="carry"))},
        "gsq.with_keys": {"patches": _keys(gs=True), "call": lambda: _gsq_run(True)},
        "gsq.no_keys": {"patches": _keys(), "call": lambda: _gsq_run(False)},
    }
    return out


def _domestic_index_code(index):
    rec("domestic_index_code", (index,), method=False)
    return {"KOSPI200": "2001", "KOSDAQ150": "3003"}[index]


def _err(call):
    try:
        return call()
    except Exception as exc:
        return exc


def _provider_reasons(source):
    reasons = []
    got = source._provider(["AAPL"], reasons)
    return {"got": got, "reasons": reasons, "skip": source._fmp_skip[1]}


KIMCHI_FITTED = ("adf_p", "half_life_days", "decay", "pred_slope", "pred_t")


def _crypto(out):
    """The parts of the crypto analysis that come from the providers, and the kimchi premium computed from them by
    plain arithmetic. Only the fitted statistics are left out (kimchi ADF p-value, half-life, AR(1) decay, the
    Newey-West prediction slope and t; the GARCH fit; the weekday table): they depend on the numpy/statsmodels build
    (an ADF p-value on these smooth fake series differs by 0.17 between builds), and this test proves the gateway
    hands the same inputs to the same functions, not that a library reproduces its numbers. Kept: prices, balances,
    premium index, open interest, dates, and from the kimchi premium its dates, premium_pct, z_1y, btc_usd, last
    and mean/max values (review 3 SA3-2: these carry the Upbit KRW closes and the USD/KRW series, so a scaled
    exchange rate or Upbit price changes the answer); every provider call is recorded exactly."""
    keep = ("source", "usdkrw_source", "balances", "balances_error", "premium_index", "oi", "btc_dates", "btc")
    answer = {k: out.get(k) for k in keep}
    kimchi = out.get("kimchi")
    answer["kimchi"] = None if kimchi is None else {
        f.name: getattr(kimchi, f.name) for f in dataclasses.fields(kimchi) if f.name not in KIMCHI_FITTED}
    return answer


def _etf(out):
    keep = ("code", "source", "is_krx", "quote", "data_source", "components", "letf")
    return {k: out.get(k) for k in keep}


def answers() -> dict:
    return {name: run(case) for name, case in sorted(cases().items())}


REL_TOL, ABS_TOL = 1e-6, 1e-9


def same(now, then, path="") -> list[str]:
    """Every difference between ``now`` and ``then`` (empty list when they match). Structure, keys, strings,
    integers, booleans and lengths are compared exactly; floats within rel 1e-6 / abs 1e-9. A list over 24 items
    was written by ``_summary``: its first and last 8 items are compared as above, the rest through the summary
    (integers, strings and structure exactly by the sha256; floats by sum, sum of squares, position-weighted sum and
    sum of squared steps within the same tolerance).

    Why a float tolerance is enough to catch a gateway change: the results of iterative fits (Nelson-Siegel, GARCH
    conditional volatility) move by up to ~1e-8 relative between numpy/BLAS builds and operating systems, while the
    thing this test guards (that the gateway hands the same inputs to the same functions) is checked exactly by the
    recorded provider calls and the input series, which carry no float noise. A wrong loader, argument or branch
    changes those, or moves results far beyond 1e-6."""
    if isinstance(then, float) and isinstance(now, (int, float)) and not isinstance(now, bool):
        return [] if math.isclose(now, then, rel_tol=REL_TOL, abs_tol=ABS_TOL) else [f"{path}: {now!r} != {then!r}"]
    if type(now) is not type(then):
        return [f"{path}: type {type(now).__name__} != {type(then).__name__}"]
    if isinstance(then, dict):
        if sorted(now) != sorted(then):
            return [f"{path}: keys {sorted(now)} != {sorted(then)}"]
        return [d for k in sorted(then) for d in same(now[k], then[k], f"{path}.{k}")]
    if isinstance(then, list):
        if len(now) != len(then):
            return [f"{path}: length {len(now)} != {len(then)}"]
        return [d for i, (a, b) in enumerate(zip(now, then)) for d in same(a, b, f"{path}[{i}]")]
    return [] if now == then else [f"{path}: {now!r} != {then!r}"]


class SameAnswerTest(unittest.TestCase):
    def test_same_request_same_answer_as_main(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        now = json.loads(json.dumps(answers(), ensure_ascii=False))
        self.assertEqual(sorted(now), sorted(golden["answers"]), "cases differ from the recorded set")
        for name in sorted(golden["answers"]):
            with self.subTest(case=name):
                self.assertEqual(same(now[name], golden["answers"][name], name), [])

    def test_comparison_is_exact_except_float_noise(self):
        self.assertEqual(same({"a": [1.0, "x"]}, {"a": [1.0 + 1e-15, "x"]}), [])
        self.assertEqual(same({"a": [0.0134652515]}, {"a": [0.0134652510]}), [])          # fit noise, ~4e-8
        self.assertNotEqual(same({"a": [1.0]}, {"a": [1.00001]}), [])                    # 1e-5 still fails
        self.assertNotEqual(same({"a": [1]}, {"a": [2]}), [])
        self.assertNotEqual(same({"a": "x"}, {"a": "y"}), [])
        self.assertNotEqual(same({"a": [1.0]}, {"a": [1.0, 2.0]}), [])
        self.assertNotEqual(same({"a": 1}, {"b": 1}), [])
        self.assertEqual(len(same({"a": 1.0, "b": 2.0}, {"a": 1.5, "b": 2.5})), 2)       # every difference reported

    def test_long_list_summary_sees_order_and_integers(self):
        """Review 3 SA3-1/DOC3-5: in the middle of a long list (not in the 8 exact items at either end) two swapped
        neighbours, a reversed stretch and +500 on one integer each change the summarised answer."""
        level = [100.0 + 0.01 * math.sin(i) for i in range(500)]       # a level series: the hardest case for sums
        swapped = list(level)
        swapped[250], swapped[251] = swapped[251], swapped[250]
        reversed_middle = level[:8] + level[8:-8][::-1] + level[-8:]
        for changed in (swapped, reversed_middle):
            self.assertNotEqual(same(canon(changed), canon(level)), [])
        integers = list(range(100))
        bumped = list(integers)
        bumped[50] += 500
        self.assertNotEqual(same(canon(bumped), canon(integers)), [])
        # review 3 SA-INT-1: integers are compared exactly inside the hash, never as float sums; a summary that
        # masked integers like floats would still see +500 through "sum" and pass the line above, so pin it here.
        plain, moved = _summary(integers), _summary(bumped)
        self.assertNotEqual(plain["shape_sha256"], moved["shape_sha256"])
        self.assertEqual((plain["sum"], plain["sumsq"], plain["wsum"], plain["dsq"]), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(same(canon([v * (1 + 1e-12) for v in level]), canon(level)), [])   # float noise passes

    def test_no_fake_key_in_the_recorded_answers(self):
        self.assertNotIn(FAKE_KEY, GOLDEN.read_text(encoding="utf-8"))

    def test_fakes_refuse_a_call_the_real_client_would_refuse(self):
        """C1: a fake is bound to the real signature, so a wrong argument fails here as it would for real."""
        with self.assertRaises(TypeError):
            FakeKISClient(paper=True)
        with self.assertRaises(TypeError):
            FakeKISMarkets().index_daily("2001", 600)            # days is keyword-only on the real one


if __name__ == "__main__":
    if "--write" in sys.argv:                       # run on the tree that is "before" (main 9f76b07)
        label = sys.argv[sys.argv.index("--write") + 1] if len(sys.argv) > sys.argv.index("--write") + 1 else ""
        result = answers()
        GOLDEN.write_text(json.dumps({"written_on": label, "answers": result}, ensure_ascii=False, indent=1,
                                     sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {len(result)} answers")
    else:
        unittest.main()
