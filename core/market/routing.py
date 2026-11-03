"""Automatic chart-provider choice: KIS first, then the first valid fallback.

Owner request UI-8 (2026-11-03): the Markets screen has no data-source selector.
Domestic and overseas instruments try KIS first; when KIS is not configured,
fails or returns unusable data, every other ready provider is asked at once and
the first *valid* answer is shown. Synthetic data never takes part.

Rules kept from the existing product:
  * nothing runs on construction; only quotation reads are made;
  * a fallback answer is labelled with its own provider and adjustment, and never
    starts the KIS trade stream or feeds Q-SCORE (both accept KIS sources only);
  * missing credentials are reported by environment-variable *name* only;
  * losers of a race are abandoned on daemon threads, so a hung provider can
    neither block the user nor hold the application open at exit.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import queue
import threading
import time

from core.market.models import Candle, MarketQuote, MarketSnapshot, utc_now

OK, FAILED, NOT_RUN, INVALID, LATE = "OK", "FAILED", "NOT_RUN", "INVALID", "LATE"


@dataclass(frozen=True)
class Attempt:
    provider: str
    status: str
    reason: str = ""          # exception class name or a short code; never provider text or URLs
    missing: tuple = ()       # .env variable names when NOT_RUN for credentials
    elapsed_ms: int = 0


class ProvidersNotRun(RuntimeError):
    """No provider able to serve the request is configured."""


class ProvidersUnavailable(RuntimeError):
    """Every ready provider failed or returned unusable data."""


def _valid(request, snapshot, minimum=2):
    """The minimum a chart can show honestly: ordered, finite bars for this instrument.

    The primary keeps its previous contract (one bar is enough; KIS already refuses none);
    a fallback must bring at least two bars before it may replace the primary.
    """
    if not isinstance(snapshot, MarketSnapshot) or snapshot.request.instrument != request.instrument:
        return "wrong_instrument"
    bars = snapshot.candles
    if request.interval in ("1d", "1w", "1M") and len(bars) < minimum:
        return "too_few_bars"
    stamps = [bar.timestamp for bar in bars]
    if stamps != sorted(set(stamps)):
        return "unordered_bars"
    if any(not (bar.close > 0 and math.isfinite(bar.close)) for bar in bars):
        return "bad_price"
    return ""


class ChartRouter:
    """Primary first (alone), then a race among the remaining ready providers."""

    def __init__(self, primary, fallbacks=(), *, deadline=12.0, clock=time.monotonic, validate=None):
        """`validate(request, result, minimum)` returns a problem code or ''; charts use `_valid`."""
        self.primary, self.fallbacks = primary, tuple(fallbacks)
        self._validate = validate or _valid
        self.deadline, self._clock = float(deadline), clock
        self.last_attempts: tuple = ()

    def _ready(self, provider, request, attempts):
        if not provider.supports(request):
            return False
        ready, missing = provider.ready()
        if not ready:
            attempts.append(Attempt(provider.name, NOT_RUN, "not_configured", tuple(missing)))
        return ready

    def load(self, request) -> MarketSnapshot:
        attempts = []
        try:
            return self._load(request, attempts)
        finally:
            self.last_attempts = tuple(attempts)

    def _load(self, request, attempts):
        primary_error = None
        if self._ready(self.primary, request, attempts):
            start = self._clock()
            try:
                snapshot = self.primary.load(request)
            except Exception as exc:  # the class name is the whole record
                primary_error = exc
                attempts.append(Attempt(self.primary.name, FAILED, type(exc).__name__,
                                        elapsed_ms=int((self._clock() - start) * 1000)))
            else:
                problem = self._validate(request, snapshot, 1)
                elapsed = int((self._clock() - start) * 1000)
                if not problem:
                    attempts.append(Attempt(self.primary.name, OK, elapsed_ms=elapsed))
                    return snapshot
                attempts.append(Attempt(self.primary.name, INVALID, problem, elapsed_ms=elapsed))
        racers = [p for p in self.fallbacks if self._ready(p, request, attempts)]
        if not racers and primary_error is not None:
            raise primary_error  # nothing else to ask: keep the primary's own, specific error
        if not racers:
            if any(a.status in (FAILED, INVALID) for a in attempts):
                raise ProvidersUnavailable("No configured provider returned usable data")
            raise ProvidersNotRun("No provider is configured for this instrument")
        winner = self._race(request, racers, attempts)
        if winner is None:
            raise ProvidersUnavailable("No configured provider returned usable data")
        return winner

    def _race(self, request, racers, attempts):
        results = queue.Queue()
        start = self._clock()

        def run(provider):
            try:
                results.put((provider, provider.load(request), None))
            except Exception as exc:
                results.put((provider, None, type(exc).__name__))

        for provider in racers:
            threading.Thread(target=run, args=(provider,), daemon=True,
                             name=f"quantgen-chart-{provider.name}").start()
        pending = {p.name for p in racers}
        while pending:
            remaining = self.deadline - (self._clock() - start)
            if remaining <= 0:
                break
            try:
                provider, snapshot, error = results.get(timeout=remaining)
            except queue.Empty:
                break
            pending.discard(provider.name)
            elapsed = int((self._clock() - start) * 1000)
            if error:
                attempts.append(Attempt(provider.name, FAILED, error, elapsed_ms=elapsed))
                continue
            problem = self._validate(request, snapshot, 2)
            if problem:
                attempts.append(Attempt(provider.name, INVALID, problem, elapsed_ms=elapsed))
                continue
            attempts.append(Attempt(provider.name, OK, elapsed_ms=elapsed))
            return snapshot
        for name in sorted(pending):
            attempts.append(Attempt(name, LATE, "deadline", elapsed_ms=int(self.deadline * 1000)))
        return None


class KISChartProvider:
    """The existing KIS quotation service; constructed lazily by the caller."""
    name = "KIS"

    def __init__(self, service):
        # A callable is read on every use, so a pane whose service is replaced keeps one route.
        self._service = service if callable(service) and not hasattr(service, "load") else (lambda: service)

    @property
    def service(self):
        return self._service()

    def ready(self):
        return bool(getattr(self.service, "ready", True)), ("KIS_APP_KEY", "KIS_APP_SECRET")

    def supports(self, request):
        return True

    def load(self, request):
        return self.service.load(request)


_YAHOO_SUFFIX = {"NAS": "", "NYS": "", "AMS": "", "HKS": ".HK", "TSE": ".T", "SHS": ".SS", "SZS": ".SZ"}
_CURRENCY = {"NAS": "USD", "NYS": "USD", "AMS": "USD", "HKS": "HKD", "TSE": "JPY", "SHS": "CNY", "SZS": "CNY"}
_YAHOO_INTERVAL = {"1d": ("1d", "2y"), "1w": ("1wk", "10y"), "1M": ("1mo", "max")}


def yahoo_symbols(instrument):
    """Yahoo tickers to try, in order; empty when there is no verified mapping."""
    if instrument.asset == "domestic_stock":
        return (instrument.code + ".KS", instrument.code + ".KQ")
    if instrument.asset != "overseas_stock" or instrument.exchange not in _YAHOO_SUFFIX:
        return ()
    code = instrument.code
    if instrument.exchange == "HKS":
        code = code.lstrip("0").rjust(4, "0")
    elif instrument.exchange in ("NAS", "NYS", "AMS"):
        code = code.replace(".", "-")
    return (code + _YAHOO_SUFFIX[instrument.exchange],)


class YahooChartProvider:
    """Daily/weekly/monthly unadjusted OHLC from Yahoo Finance; keyless and delayed."""
    name = "Yahoo Finance"

    def __init__(self, fetch=None):
        self._fetch = fetch or _yahoo_frame

    def ready(self):
        return True, ()

    def supports(self, request):
        return request.interval in _YAHOO_INTERVAL and bool(yahoo_symbols(request.instrument))

    def load(self, request):
        interval, period = _YAHOO_INTERVAL[request.interval]
        instrument = request.instrument
        rows = ()
        for symbol in yahoo_symbols(instrument):
            rows = tuple(self._fetch(symbol, interval, period))
            if rows:
                break
        candles = []
        for stamp, o, h, l, c, v in rows:
            try:
                candles.append(Candle(str(stamp)[:10], float(o), float(h), float(l), float(c),
                                      float(v) if v is not None and math.isfinite(float(v)) and v >= 0 else None))
            except (TypeError, ValueError):
                continue  # one malformed row must not hide the rest
        candles = tuple(candles[-request.limit:])
        if len(candles) < 2:
            raise LookupError("Yahoo returned no usable bars")
        last, prev = candles[-1], candles[-2]
        currency = "KRW" if instrument.asset == "domestic_stock" else _CURRENCY.get(instrument.exchange, "")
        quote = MarketQuote(instrument, price=last.close, change=last.close - prev.close,
                            change_pct=(last.close / prev.close - 1) * 100 if prev.close else None,
                            volume=last.volume, open=last.open, high=last.high, low=last.low,
                            currency=currency, market_time=last.timestamp, received_at=utc_now(),
                            source=self.name)
        note = ("Yahoo Finance fallback: unadjusted OHLC, delayed; not a KIS quote. "
                "Live trade updates and Q-SCORE use KIS only.")
        if len(candles) < request.limit:
            note += f" Partial history: {len(candles)}/{request.limit} requested bars."
        return MarketSnapshot(request, candles, quote, utc_now(), self.name, note)


def _yahoo_frame(symbol, interval, period):
    """One Yahoo request through the FICC module's yfinance handle (patched in tests)."""
    from core.ficc import data
    if data._yf is None:
        raise LookupError("yfinance is not installed")
    frame = data._yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False, timeout=10)
    if frame is None or len(frame) == 0:
        return ()
    out = []
    for stamp, row in frame.iterrows():
        values = [row.get(k) for k in ("Open", "High", "Low", "Close", "Volume")]
        if any(v is None or not math.isfinite(float(v)) for v in values[:4]):
            continue
        out.append((stamp.date().isoformat() if hasattr(stamp, "date") else str(stamp)[:10], *values))
    return out


def default_chart_router(service):
    """Production wiring: KIS first, Yahoo for stocks when KIS cannot answer.

    `service` may be a callable returning the current KIS service.
    """
    return ChartRouter(KISChartProvider(service), (YahooChartProvider(),))


def describe(attempts, language="ko"):
    """One short line naming each provider tried; variable names only, never values."""
    words = {"ko": {OK: "성공", FAILED: "실패", NOT_RUN: "미설정", INVALID: "자료 부족", LATE: "응답 지연"},
             "en": {OK: "ok", FAILED: "failed", NOT_RUN: "not configured", INVALID: "unusable data", LATE: "timed out"}}
    table = words["ko" if language == "ko" else "en"]
    parts = []
    for a in attempts:
        text = f"{a.provider} {table.get(a.status, a.status)}"
        if a.missing:
            text += " (" + ", ".join(a.missing) + ")"
        elif a.status == FAILED and a.reason:
            text += f" ({a.reason})"
        parts.append(text)
    return " · ".join(parts)
