"""Four market-indicator charts for the Markets screen (owner request UI-7, 2026-11-03).

The Markets indicator table is replaced by four line charts of market indicators;
individual stocks are excluded (they stay on Home with Q-SCORE). Each indicator is
resolved like the price chart (core/market/routing.py): KIS first when it serves the
series, then every other ready provider at once, first valid answer wins. No
synthetic data. Nothing runs on construction; the board loads when it is shown.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import math

from core.market.routing import ChartRouter, ProvidersNotRun, ProvidersUnavailable, describe

HISTORY_DAYS = 130          # about six months of sessions for each card
STALE_AFTER_DAYS = 7


@dataclass(frozen=True)
class BoardSpec:
    key: str
    name_ko: str
    name_en: str
    unit: str               # 'pt', 'KRW', '%'
    chain: tuple            # ((provider name, kind, argument), ...) in priority order

    def name(self, language="ko"):
        return self.name_ko if language == "ko" else self.name_en


# No individual stock appears here (UI-7). KIS serves the domestic series first.
BOARD_SPECS = (
    BoardSpec("kospi", "코스피", "KOSPI", "pt",
              (("KIS", "kis_index", "0001"), ("Yahoo Finance", "yfinance", "^KS11"))),
    BoardSpec("spx", "S&P 500", "S&P 500", "pt",
              (("KIS", "kis_chart", ("N", "SPX")), ("Yahoo Finance", "yfinance", "^GSPC"))),
    # FRED DEXKOUS is published with a weekly lag, so it is asked only after Yahoo fails
    # (a "then" step) instead of racing a fresher daily rate.
    BoardSpec("usdkrw", "원/달러 환율", "USD/KRW", "KRW",
              (("KIS", "kis_fx", None), ("Yahoo Finance", "yfinance", "KRW=X"), ("FRED", "then_fred", "DEXKOUS"))),
    BoardSpec("ust10y", "미국 10년 국채금리", "US 10-year Treasury yield", "%",
              (("FRED", "fred", "DGS10"),)),
)
BY_KEY = {spec.key: spec for spec in BOARD_SPECS}


@dataclass(frozen=True)
class BoardSeries:
    key: str
    dates: tuple
    values: tuple
    source: str
    fetched_at: str = ""
    note: str = ""

    @property
    def last(self):
        return self.values[-1]

    @property
    def change(self):
        """Percent change, or basis points for a yield in percent."""
        previous, last = self.values[-2], self.values[-1]
        if BY_KEY[self.key].unit == "%":
            return (last - previous) * 100
        return (last / previous - 1) * 100 if previous else None

    def stale(self, today=None):
        today = today or datetime.now(timezone.utc).date()
        return (today - date.fromisoformat(self.dates[-1])).days > STALE_AFTER_DAYS


@dataclass
class BoardResult:
    key: str
    series: BoardSeries | None = None
    attempts: tuple = ()
    error: str = ""          # ProvidersNotRun / ProvidersUnavailable / exception class name
    loaded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def tried(self, language="ko"):
        return describe(self.attempts, language)


def valid_series(key, series, minimum=2):
    """Ordered, finite, positive observations of the requested indicator."""
    if not isinstance(series, BoardSeries) or series.key != key:
        return "wrong_series"
    if len(series.values) < max(2, minimum) or len(series.values) != len(series.dates):
        return "too_few_values"
    if list(series.dates) != sorted(set(series.dates)):
        return "unordered_dates"
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in series.values):
        return "bad_value"
    return ""


class SeriesProvider:
    """One provider for one indicator; `fetch(argument)` returns (dates, values)."""

    def __init__(self, name, key, fetch, argument, *, ready=None, note=""):
        self.name, self.key, self._fetch, self.argument = name, key, fetch, argument
        self._ready = ready or (lambda: (True, ()))
        self.note = note

    def ready(self):
        return self._ready()

    def supports(self, request):
        return request == self.key

    def load(self, request):
        dates, values = self._fetch(self.argument)
        return BoardSeries(self.key, tuple(dates), tuple(float(v) for v in values), self.name,
                           datetime.now(timezone.utc).isoformat(timespec="seconds"), self.note)


class ThenProvider:
    """Ask `first`; only if it fails or is invalid, ask `second` (used for lagged sources)."""

    def __init__(self, first, second):
        self.first, self.second = first, second
        self.name = f"{first.name} → {second.name}"

    def ready(self):
        return True, ()

    def supports(self, request):
        return self.first.supports(request)

    def load(self, request):
        try:
            result = self.first.load(request)
            if not valid_series(request, result):
                return result
        except Exception:  # the first provider's failure is why the second is asked
            pass
        return self.second.load(request)


def _ficc_fetch(source):
    def fetch(series_id):
        from core.ficc.data import load_series
        series = load_series(series_id, source=source, days=HISTORY_DAYS)
        if str(series.source).upper() != source.upper():
            raise LookupError("provider fallback is not this provider's answer")
        pairs = [(d, float(v)) for d, v in zip(series.dates, series.values)
                 if v is not None and math.isfinite(float(v))]
        return [d for d, _ in pairs], [v for _, v in pairs]
    return fetch


class KISBoardFetch:
    """Lazily built KIS market reader shared by the KIS cards; no work on construction."""

    def __init__(self, factory=None):
        self._factory = factory
        self._markets = None

    def markets(self):
        if self._markets is None:
            if self._factory is not None:
                self._markets = self._factory()
            else:
                from data.kis_markets import KISMarkets
                self._markets = KISMarkets()
        return self._markets

    def ready(self):
        return bool(getattr(self.markets(), "ready", False)), ("KIS_APP_KEY", "KIS_APP_SECRET")

    def fetch(self, kind):
        def run(argument):
            markets = self.markets()
            if kind == "kis_index":
                bars = markets.index_daily(argument, days=HISTORY_DAYS)
            elif kind == "kis_chart":
                bars = markets.overseas_chart(*argument, days=HISTORY_DAYS)
            else:
                bars = markets.usdkrw_daily(days=HISTORY_DAYS)
            return bars.dates, bars.close
        return run


def build_routers(*, kis=None, fetchers=None, deadline=12.0):
    """One router per card. `fetchers` maps provider kinds to fetch callables (tests)."""
    kis = kis or KISBoardFetch()
    fetchers = dict(fetchers or {})
    routers = {}
    for spec in BOARD_SPECS:
        providers = []
        for name, kind, argument in spec.chain:
            if kind.startswith("then_"):
                base = kind[len("then_"):]
                fetch = fetchers.get(base) or _ficc_fetch(base)
                second = SeriesProvider(name, spec.key, fetch, argument,
                                        note="FRED daily observation (published with a lag).")
                providers[-1] = ThenProvider(providers[-1], second)
                continue
            if kind.startswith("kis"):
                fetch = fetchers.get(kind) or kis.fetch(kind)
                ready = fetchers.get("kis_ready") or kis.ready
                note = "KIS daily series; the latest session updates during trading."
            else:
                fetch = fetchers.get(kind) or _ficc_fetch(kind)
                ready = None
                note = "FRED daily observation (published with a lag)." if kind == "fred" else \
                       "Yahoo Finance daily series, delayed."
            providers.append(SeriesProvider(name, spec.key, fetch, argument, ready=ready, note=note))
        routers[spec.key] = ChartRouter(providers[0], providers[1:], deadline=deadline,
                                        validate=valid_series)
    return routers


def load_board(routers, keys=None):
    """Load each card in turn (KIS paces its own calls); failures stay per card."""
    results = []
    for key in keys or [spec.key for spec in BOARD_SPECS]:
        router = routers[key]
        try:
            series = router.load(key)
            results.append(BoardResult(key, series, tuple(router.last_attempts)))
        except (ProvidersNotRun, ProvidersUnavailable) as exc:
            results.append(BoardResult(key, None, tuple(router.last_attempts), type(exc).__name__))
        except Exception as exc:  # the class name is the whole record
            results.append(BoardResult(key, None, tuple(router.last_attempts), type(exc).__name__))
    return results
