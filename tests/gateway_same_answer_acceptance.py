"""KEY-4 "app behaviour unchanged": the same request gives the same answer before and after core/ moved to
core/gateway.

Each case below calls a core function whose provider access KEY-4 changed, with the providers replaced by fixed
fakes at the provider module (data.*, core.ficc.data, config), which is where both the old code (an import inside
the function) and the new code (core.gateway, looked up at call time) find them. The answers are written as
canonical JSON and compared with tests/fixtures/gateway/same_answers_main.json, which was written by running this
same file on main 9f76b07 (before KEY-4) with ``--write``:

    python tests/gateway_same_answer_acceptance.py --write

No network, no real key, no `.env` (dotenv is patched before import; config functions are patched per case).
Answers that depend on today's date (synthetic series) are not used, so the file stays valid on any day.
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    from core.ficc import curve_models, macro
    from core.ficc import data as ficc_data
    from core.market import market_cap, routing
    from core.quant import history, insights as quant_insights
    from core.research import analysis, connections, market_board, markets, watchlist
    from data.crypto import crypto_client
    from data.krx import kis_client, krx_market_client
    import data.kis_markets as kis_markets

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "fixtures" / "gateway" / "same_answers_main.json"
DATES = tuple(f"2026-0{1 + i // 28}-{1 + i % 28:02d}" for i in range(45))


def canon(obj):
    """JSON-safe, order-stable form of an answer (dataclasses by field, floats exact via repr)."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {"__type__": type(obj).__name__,
                **{f.name: canon(getattr(obj, f.name)) for f in dataclasses.fields(obj)}}
    if isinstance(obj, float):
        return repr(float(obj)) if not math.isfinite(obj) else float(obj)
    if isinstance(obj, (list, tuple)):
        return [canon(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): canon(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if hasattr(obj, "tolist"):
        return canon(obj.tolist())
    if isinstance(obj, BaseException):
        return {"__error__": type(obj).__name__, "message": str(obj)}
    return obj


def _history(symbol, source, closes):
    return history.History(symbol=symbol, source=source, dates=DATES[:len(closes)], closes=tuple(closes))


class FakeKISClient:
    ready = True

    def __init__(self, *a, **k):
        self.calls = 0

    def daily(self, code, start=None, end=None):
        self.calls += 1
        if self.calls > 1:
            return []
        return [{"date": d, "close": 100.0 + i} for i, d in enumerate(DATES[:40])]


class FakeKISMarkets:
    ready = True

    def __init__(self, *a, **k):
        pass

    def overseas_daily(self, ex, sym, days=0):
        return SimpleNamespace(to_history=lambda: _history(f"{ex}:{sym}", "KIS", [50.0 + i for i in range(35)]))

    def krw_yield_daily(self, code, days=0):
        base = 3.0 + (sum(map(ord, code)) % 7) / 10
        return SimpleNamespace(dates=DATES[:40], close=tuple(base + i / 100 for i in range(40)))

    def probe(self):
        return {"quote": {"ok": True, "detail": "fake kis"}, "chart": {"ok": False, "detail": "fake down"}}


class FakeUpbit:
    def daily(self, market, days=0):
        return SimpleNamespace(to_history=lambda: _history(market, "UPBIT", [9e7 + i for i in range(35)]))


class FakeBinance:
    def daily(self, symbol, days=0, **k):
        return SimpleNamespace(to_history=lambda: _history(symbol, "BINANCE", [6e4 + i for i in range(35)]))


class FakeKRXMarket:
    def probe(self):
        return {"ready": True, "path": "/fake/path", "reason": ""}


class FakeResponse:
    status_code = 200

    def json(self):
        return [{"date": d, "adjClose": 200.0 + i} for i, d in enumerate(reversed(DATES[:40]))]


class FakeSession:
    def __init__(self):
        self.asked = []

    def get(self, url, params=None, timeout=None):
        self.asked.append((url, sorted(k for k in (params or {}) if k != "apikey")))
        return FakeResponse()


def _rows(provider, ids, days, **kwargs):
    rows = {i: [(d, 2.0 + (len(i) % 5) / 10 + n / 1000) for n, d in enumerate(DATES[:40])] for i in ids}
    return rows, {}


class FakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol

    def get_shares_full(self, start=None):
        import pandas as pd
        return pd.Series([1.0e9, 1.1e9], index=pd.to_datetime(["2026-01-02", "2026-02-02"]))

    def history(self, period=None, interval=None, auto_adjust=None, timeout=None):
        import pandas as pd
        index = pd.to_datetime(list(DATES[:3]))
        return pd.DataFrame({"Open": [1.0, 2.0, 3.0], "High": [1.5, 2.5, 3.5], "Low": [0.5, 1.5, 2.5],
                             "Close": [1.2, 2.2, 3.2], "Volume": [10.0, 20.0, 30.0]}, index=index)


def _keys(**present):
    """Config key functions patched to fixed answers ("" or a fake value); never real keys."""
    fake = "fake-key-for-same-answer-test"
    values = {"kis_ready": lambda: bool(present.get("kis")),
              "fmp_key": lambda: fake if present.get("fmp") else "",
              "fmp_ready": lambda: bool(present.get("fmp")),
              "anthropic_key": lambda: fake if present.get("ai") else "",
              "gs_client_id": lambda: fake if present.get("gs") else "",
              "gs_client_secret": lambda: fake if present.get("gs") else "",
              "upbit_ready": lambda: bool(present.get("upbit"))}
    return [patch.object(config, name, fn) for name, fn in values.items()]


def run(case):
    patches = []
    try:
        for p in case.get("patches", []):
            p.start()
            patches.append(p)
        return canon(case["call"]())
    except Exception as exc:                          # an error is an answer too, and must stay the same
        return canon(exc)
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
    return {
        "history.kis_history": {"patches": _keys(kis=True) + [patch.object(kis_client, "KISClient", FakeKISClient)],
                                "call": lambda: history.kis_history("005930", days=40)},
        "history.kis_history.no_key": {"patches": _keys(),
                                       "call": lambda: history.kis_history("005930", days=40)},
        "history.kis_market_history": {"patches": _keys(kis=True) + [patch.object(kis_markets, "KISMarkets",
                                                                                   FakeKISMarkets)],
                                       "call": lambda: history.kis_market_history("NAS:AAPL", days=35)},
        "history.looks_kis_market": {"call": lambda: [history._looks_kis_market(s) for s in
                                                      ("NAS:AAPL", "XXX:AAPL", "KR103501GE31", "005930")]},
        "history.yf_history": {"patches": [patch.object(ficc_data, "_yf_fetch",
                                                        lambda t, p: {t[0]: [(d, 400.0 + n) for n, d in
                                                                             enumerate(DATES[:35])], "period": p})],
                               "call": lambda: history.yf_history("SPY", days=35)},
        "history.crypto_history": {"patches": [patch.object(crypto_client, "UpbitPublic", FakeUpbit),
                                               patch.object(crypto_client, "BinancePublic", FakeBinance)],
                                   "call": lambda: [history.crypto_history("KRW-BTC"),
                                                    history.crypto_history("BTCUSDT")]},
        "history.fmp_history": {"patches": _keys(fmp=True) + [patch.object(history, "_requests", session)],
                                "call": lambda: [history.fmp_history("AAPL", days=40), session.asked[-1]]},
        "history.fmp_history.no_key": {"patches": _keys() + [patch.object(history, "_requests", session)],
                                       "call": lambda: history.fmp_history("AAPL", days=40)},
        "history.ready": {"patches": _keys(kis=True),
                          "call": lambda: {k: f() for k, f in sorted(history._READY.items())}},
        "curve_models.krw_curve_panel": {"patches": [patch.object(kis_markets, "KISMarkets", FakeKISMarkets)],
                                         "call": lambda: curve_models.krw_curve_panel(days=40)},
        "connections.presence": {"patches": status,
                                 "call": lambda: connections.execute_connections(presence).rows},
        "connections.probes": {"patches": [patch.object(ficc_data, "probe", lambda: ficc_probe),
                                           patch.object(kis_markets, "KISMarkets", FakeKISMarkets),
                                           patch.object(krx_market_client, "KRXMarketClient", FakeKRXMarket),
                                           patch.object(crypto_client, "probe", lambda: crypto_probe)],
                               "call": lambda: [connections.execute_connections(probe(t)).rows
                                                for t in ("ficc", "kis", "krx", "crypto")]},
        "analysis.funding_rate": {"patches": [patch.object(ficc_data, "_provider_rows", _rows)],
                                  "call": lambda: [analysis.funding_rate("AAPL"), analysis.funding_rate("005930")]},
        "markets.load_markets": {"patches": [patch.object(ficc_data, "_provider_rows", _rows)],
                                 "call": lambda: [{k: v for k, v in row.items() if k != "loaded_at"}   # clock time
                                                  for row in markets.load_markets(
                                                      today=__import__("datetime").date(2026, 2, 20))]},
        "market_board.ficc_fetch": {"patches": [patch.object(ficc_data, "_provider_rows", _rows)],
                                    "call": lambda: [market_board._ficc_fetch("FRED")("DGS10"),
                                                     market_board._ficc_fetch("YFINANCE")("^GSPC")]},
        "macro.load_many": {"patches": [patch.object(ficc_data, "_provider_rows", _rows)],
                            "call": lambda: macro.load_many(["DGS10", "^GSPC", "DEXKOUS"], days=40)},
        "market_cap.yahoo": {"patches": [patch.object(ficc_data, "_yf", SimpleNamespace(Ticker=FakeTicker))],
                             "call": lambda: [market_cap.yahoo_shares("AAPL"), market_cap._yahoo_installed()]},
        "market_cap.no_yahoo": {"patches": [patch.object(ficc_data, "_yf", None)],
                                "call": lambda: [market_cap._yahoo_installed()]},
        "market_cap.fmp_key": {"patches": _keys(fmp=True),
                               "call": lambda: bool(market_cap.MarketCapSource(cache=object())._fmp_key())},
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
    }


def answers() -> dict:
    return {name: run(case) for name, case in sorted(cases().items())}


class SameAnswerTest(unittest.TestCase):
    def test_same_request_same_answer_as_main(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        now = json.loads(json.dumps(answers(), ensure_ascii=False))
        self.assertEqual(sorted(now), sorted(golden["answers"]), "cases differ from the recorded set")
        for name in sorted(golden["answers"]):
            with self.subTest(case=name):
                self.assertEqual(now[name], golden["answers"][name])

    def test_no_fake_key_in_the_recorded_answers(self):
        self.assertNotIn("fake-key-for-same-answer-test", GOLDEN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if "--write" in sys.argv:                       # run on the tree that is "before" (main 9f76b07)
        import subprocess
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip()
        GOLDEN.write_text(json.dumps({"written_on": sys.argv[sys.argv.index("--write") + 1]
                                      if len(sys.argv) > sys.argv.index("--write") + 1 else commit,
                                      "answers": answers()}, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(f"wrote {len(answers())} answers")
    else:
        unittest.main()
