"""Daily price history, from whichever provider can actually serve it.

Three sources, one shape:

  * **FMP** — `/stable/historical-price-eod/full` for US (and, plan
    permitting, international) tickers.
  * **KIS** — daily OHLCV for KRX codes (6-digit tickers), through the same
    client the NEXTGEN base uses for the KRX page.
  * **SYNTHETIC** — a seeded geometric Brownian motion path derived from the
    symbol name. Deterministic per symbol, so charts and tests are stable.
    This is what makes every analysis screen in QUANTGEN work with zero keys
    configured; the result carries `source="SYNTHETIC"` and a note saying so,
    because a simulated series silently passed off as market data would poison
    every number computed downstream.

`load_history` picks a provider automatically (KIS for 6-digit codes, FMP for
everything else, synthetic as the explicit or last-resort fallback) and always
answers with a `History` whose `source` and `note` say where the prices came
from and why.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

try:
    import requests as _requests
except Exception:                                    # pragma: no cover
    _requests = None

import config

TRADING_DAYS = 252


class HistoryError(RuntimeError):
    """A provider was asked and could not answer. The message says why."""


@dataclass(frozen=True)
class History:
    symbol: str
    source: str                       # "FMP" | "KIS" | "SYNTHETIC"
    dates: tuple[str, ...]            # ISO dates, ascending
    closes: tuple[float, ...]
    note: str = ""

    def __len__(self) -> int:
        return len(self.closes)

    @property
    def last(self) -> float:
        return self.closes[-1]

    @property
    def first_date(self) -> str:
        return self.dates[0] if self.dates else ""

    @property
    def last_date(self) -> str:
        return self.dates[-1] if self.dates else ""

    def prices(self) -> np.ndarray:
        return np.asarray(self.closes, dtype=float)

    def log_returns(self) -> np.ndarray:
        px = self.prices()
        return np.diff(np.log(px))

    def simple_returns(self) -> np.ndarray:
        px = self.prices()
        return px[1:] / px[:-1] - 1.0


def _clean_rows(rows: list[tuple[str, float]]) -> tuple[tuple[str, ...], tuple[float, ...]]:
    rows = [(d, c) for d, c in rows if c is not None and c > 0]
    rows.sort(key=lambda r: r[0])
    dates = tuple(d for d, _ in rows)
    closes = tuple(float(c) for _, c in rows)
    return dates, closes


# --------------------------------------------------------------------------- #
# FMP
# --------------------------------------------------------------------------- #
def fmp_history(symbol: str, *, days: int = 504) -> History:
    if _requests is None:
        raise HistoryError("The requests package is not installed.")
    key = config.fmp_key()
    if not key:
        raise HistoryError("FMP_API_KEY is not configured.")
    start = (date.today() - timedelta(days=int(days * 1.6) + 10)).isoformat()
    url = f"{config.FMP_BASE_URL}/historical-price-eod/full"
    try:
        resp = _requests.get(url, params={"symbol": symbol, "from": start, "apikey": key},
                             timeout=config.HTTP_TIMEOUT_SECONDS)
    except Exception as exc:
        raise HistoryError(f"FMP request failed: {exc}") from exc
    if resp.status_code == 402:
        raise HistoryError(f"The FMP plan does not cover {symbol!r} (HTTP 402).")
    if resp.status_code in (401, 403):
        raise HistoryError(f"FMP rejected the API key (HTTP {resp.status_code}).")
    if resp.status_code != 200:
        raise HistoryError(f"FMP answered HTTP {resp.status_code}.")
    try:
        payload = resp.json()
    except Exception as exc:
        raise HistoryError("FMP returned a non-JSON body.") from exc
    # /stable answers a plain list; older shapes wrap it in {"historical": [...]}.
    records = payload.get("historical") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise HistoryError(f"FMP has no daily history for {symbol!r}.")
    rows = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        d = str(rec.get("date") or "")[:10]
        c = rec.get("adjClose", rec.get("close"))
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if d:
            rows.append((d, c))
    dates, closes = _clean_rows(rows)
    if len(closes) < 30:
        raise HistoryError(f"FMP returned only {len(closes)} usable sessions for {symbol!r}.")
    return History(symbol=symbol.upper(), source="FMP",
                   dates=dates[-days:], closes=closes[-days:])


# --------------------------------------------------------------------------- #
# KIS (KRX codes)
# --------------------------------------------------------------------------- #
def kis_history(code: str, *, days: int = 504) -> History:
    """KIS serves about 100 sessions per call, so the window is paged backwards:
    each call ends the day before the earliest session already held, until
    `days` sessions are in hand or the exchange has nothing older to give."""
    if not config.kis_ready():
        raise HistoryError("KIS credentials are not configured.")
    from data.krx.kis_client import KISClient
    client = KISClient()
    start = (date.today() - timedelta(days=int(days * 1.6) + 10)).strftime("%Y%m%d")
    rows_by_date: dict[str, float] = {}
    end: str | None = None
    for _ in range(days // 100 + 3):                 # a few spare pages for holidays
        try:
            page = client.daily(code, start=start, end=end)
        except Exception as exc:
            raise HistoryError(f"KIS daily history failed: {exc}") from exc
        fresh = [(r["date"], r.get("close")) for r in page
                 if r.get("date") and r["date"] not in rows_by_date]
        if not fresh:
            break
        for d, c in fresh:
            if c is not None and c > 0:
                rows_by_date[d] = float(c)
        if len(rows_by_date) >= days:
            break
        earliest = min(d for d, _ in fresh)
        end = (date.fromisoformat(earliest) - timedelta(days=1)).strftime("%Y%m%d")
        if end < start:
            break
    dates, closes = _clean_rows(list(rows_by_date.items()))
    if len(closes) < 30:
        raise HistoryError(f"KIS returned only {len(closes)} usable sessions for {code!r}.")
    return History(symbol=code, source="KIS", dates=dates[-days:], closes=closes[-days:])


# --------------------------------------------------------------------------- #
# Synthetic — deterministic per symbol
# --------------------------------------------------------------------------- #
def synthetic_history(symbol: str, *, days: int = 504, seed: int | None = None) -> History:
    """A seeded GBM path with symbol-derived drift, volatility and start price.

    The same symbol always produces the same series, so a demo screen does not
    repaint itself into a different market on every refresh.
    """
    sym = (symbol or "DEMO").upper()
    if seed is None:
        seed = int.from_bytes(hashlib.sha256(sym.encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    # Parameters vary by symbol but stay inside plausible equity ranges.
    mu = 0.02 + (seed % 17) / 100.0            # 2%..18% annual drift
    sigma = 0.14 + (seed % 23) / 100.0         # 14%..36% annual vol
    s0 = 20.0 + (seed % 400)
    dt = 1.0 / TRADING_DAYS
    shocks = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * math.sqrt(dt), size=days - 1)
    log_px = np.concatenate([[math.log(s0)], math.log(s0) + np.cumsum(shocks)])
    closes = tuple(float(x) for x in np.exp(log_px))
    end = date.today()
    ds: list[str] = []
    d = end
    while len(ds) < days:
        if d.weekday() < 5:
            ds.append(d.isoformat())
        d -= timedelta(days=1)
    dates = tuple(reversed(ds))
    return History(symbol=sym, source="SYNTHETIC", dates=dates, closes=closes,
                   note=f"Simulated series (GBM, μ={mu:.0%}, σ={sigma:.0%}) — "
                        "no market data provider was used.")


# --------------------------------------------------------------------------- #
# Yahoo Finance, crypto venues and the other KIS domains (version 3)
# --------------------------------------------------------------------------- #
def yf_history(symbol: str, *, days: int = 504) -> History:
    """Any Yahoo ticker: ETFs (SPY), indices (^VIX), continuous futures (ZN=F),
    FX (KRW=X), crypto (BTC-USD), KRX (005930.KS). Adjusted closes, through the
    FICC data module's single Yahoo touchpoint (patched to raise in tests)."""
    from core.ficc.data import _yf_fetch, _period_for
    try:
        rows = _yf_fetch([symbol], _period_for(days)).get(symbol) or []
    except Exception as exc:
        raise HistoryError(f"Yahoo Finance failed for {symbol!r}: {exc}") from exc
    dates, closes = _clean_rows([(d, c) for d, c in rows])
    if len(closes) < 30:
        raise HistoryError(f"Yahoo Finance returned only {len(closes)} usable sessions for {symbol!r}.")
    return History(symbol=symbol.upper(), source="YFINANCE", dates=dates[-days:], closes=closes[-days:],
                   note="Yahoo adjusted close")


def crypto_history(symbol: str, *, days: int = 504) -> History:
    """`KRW-BTC` (Upbit, KRW) or `BTCUSDT` (Binance spot, USDT), keyless."""
    from data.crypto.crypto_client import BinancePublic, CryptoError, UpbitPublic
    s = symbol.upper()
    try:
        if s.startswith("KRW-") or s.startswith("BTC-") or s.startswith("USDT-"):
            return UpbitPublic().daily(s, days=days).to_history()
        return BinancePublic().daily(s, days=days).to_history()
    except CryptoError as exc:
        raise HistoryError(str(exc)) from exc


def kis_market_history(symbol: str, *, days: int = 504) -> History:
    """The non-stock KIS domains by symbol shape: `NAS:AAPL` overseas stock,
    `A01612` / `A65612` / `101W12` a KRX futures contract, `KR103501GE31` a bond
    ISIN, `Y0101` a KRW benchmark yield (percent), `FX@KRW` the 원/달러 fixing."""
    if not config.kis_ready():
        raise HistoryError("KIS credentials are not configured.")
    from data.kis_markets import CHART_FX, CHART_YIELD, KISMarkets, OVERSEAS_EXCHANGES
    km = KISMarkets()
    s = symbol.strip().upper()
    try:
        if ":" in s and s.split(":", 1)[0] in OVERSEAS_EXCHANGES:
            ex, sym = s.split(":", 1)
            return km.overseas_daily(ex, sym, days=days).to_history()
        if s.startswith("KR") and len(s) == 12:
            return km.bond_daily(s).to_history()
        if s.startswith("Y0") and len(s) == 5:
            return km.overseas_chart(CHART_YIELD, s, days=days).to_history()
        if s.startswith("FX@"):
            return km.overseas_chart(CHART_FX, s, days=days).to_history()
        return km.futures_daily(s, days=days).to_history()
    except Exception as exc:
        raise HistoryError(f"KIS market history failed for {symbol!r}: {exc}") from exc


def _looks_krx(symbol: str) -> bool:
    s = symbol.strip().upper()
    if s.endswith((".KS", ".KQ")):
        s = s.split(".")[0]
    return s.isdigit() and len(s) == 6


def _looks_yahoo(symbol: str) -> bool:
    s = symbol.strip().upper()
    return s.startswith("^") or s.endswith(("=F", "=X", "-USD", "-KRW", ".KS", ".KQ"))


def _looks_crypto(symbol: str) -> bool:
    s = symbol.strip().upper()
    return s.startswith(("KRW-", "USDT-")) or (s.endswith("USDT") and s.isalnum() and 5 <= len(s) <= 12)


def _looks_kis_market(symbol: str) -> bool:
    s = symbol.strip().upper()
    if ":" in s:
        from data.kis_markets import OVERSEAS_EXCHANGES
        return s.split(":", 1)[0] in OVERSEAS_EXCHANGES
    if s.startswith("KR") and len(s) == 12 and s.isalnum():
        return True
    if s.startswith("Y0") and len(s) == 5:
        return True
    if s.startswith("FX@"):
        return True
    return len(s) in (6, 9) and s[0] in "ABCD123" and s[1:3].isdigit() and s[3:].isalnum() and not s.isdigit()


SOURCES = ("auto", "fmp", "kis", "yfinance", "crypto", "synthetic")


def load_history(symbol: str, *, source: str = "auto", days: int = 504) -> History:
    """Fetch daily closes for `symbol`. `source="auto"` routes by the symbol's
    shape: 6-digit KRX codes to KIS; `KRW-BTC` / `BTCUSDT` to Upbit / Binance
    (keyless); `^VIX`, `ZN=F`, `KRW=X`, `BTC-USD`, `005930.KS` to Yahoo
    (keyless); `NAS:AAPL`, KRX derivative codes, bond ISINs and `Y0101`-style
    yields to the KIS asset domains; everything else to FMP, falling back to
    a synthetic series (with an explicit note) when no provider is configured.
    A provider that IS configured but fails raises `HistoryError` instead of
    silently simulating — a network error must not quietly change what the
    numbers mean."""
    symbol = (symbol or "").strip()
    if not symbol:
        raise HistoryError("No symbol given.")
    source = (source or "auto").lower()
    if source == "synthetic":
        return synthetic_history(symbol, days=days)
    if source == "fmp":
        return fmp_history(symbol, days=days)
    if source == "kis":
        return kis_market_history(symbol, days=days) if _looks_kis_market(symbol) else kis_history(symbol, days=days)
    if source == "yfinance":
        return yf_history(symbol, days=days)
    if source == "crypto":
        return crypto_history(symbol, days=days)
    if source != "auto":
        raise HistoryError(f"Unknown source {source!r}. One of {SOURCES}.")
    if _looks_krx(symbol):
        if config.kis_ready():
            return kis_history(symbol.split(".")[0], days=days)
        h = synthetic_history(symbol, days=days)
        return History(h.symbol, h.source, h.dates, h.closes,
                       note="KIS credentials are not configured; " + h.note)
    if _looks_crypto(symbol):
        return crypto_history(symbol, days=days)
    if _looks_yahoo(symbol):
        return yf_history(symbol, days=days)
    if _looks_kis_market(symbol):
        if config.kis_ready():
            return kis_market_history(symbol, days=days)
        h = synthetic_history(symbol, days=days)
        return History(h.symbol, h.source, h.dates, h.closes,
                       note="KIS credentials are not configured; " + h.note)
    if config.fmp_ready():
        return fmp_history(symbol, days=days)
    h = synthetic_history(symbol, days=days)
    return History(h.symbol, h.source, h.dates, h.closes,
                   note="FMP_API_KEY is not configured; " + h.note)
