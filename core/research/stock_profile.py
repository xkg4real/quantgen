"""Everything QUANTGEN already knows about one stock, as display rows.

Owner request 2026-11-04: "검색한 한 종목의 모든 것을 한 화면에". This module is the pure core of that view; it has
no Qt and draws nothing.

* `build_profile` computes from the data it is handed and performs no I/O.
* `sections` formats a profile for one language ('ko' or 'en'; English output contains no Hangul).
* `load_profile` is the only function that reads providers, and only through the objects the caller injects:
    - price history: `router.load(ChartRequest(instrument, "1d", 260, adjusted=True))`, the Markets chart router
      (core.market.routing.ChartRouter: KIS first, then Yahoo for stocks). Synthetic data never takes part:
      `load_history(source="auto")` is not used.
    - domestic stocks only: `quote_client.quote(code)` (KISClient.quote, the inquire-price endpoint: name, OHLC,
      volume, PER, EPS, sector, listed shares), `markets.investor_daily(code, days=20)` and
      `markets.short_sale_daily(code, days=20)` (data.kis_markets.KISMarkets).
  No new KIS endpoint is used; every call above already exists in the allowlisted client code.

Every source is optional. A missing or failing source empties only its own sections and leaves a short authored
reason code (never provider text, a URL or a credential); the 'unavailable' section states each such gap plainly,
together with what QUANTGEN does not provide at all (news, analyst ratings, dividends, order book, overseas
fundamentals). Nothing raises except programming errors (for example a non-stock instrument).

Provider names and timestamps appear only in row hints (tooltips): the owner removed the provider and
observation-date columns. A fallback that is not KIS (Yahoo Finance) is still named in the hints and notes,
because its prices are delayed and unadjusted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
import math
import re
from typing import Any, Mapping

from babel.numbers import format_compact_decimal

from core.i18n import LocaleContext
from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot, utc_now
from core.market.presentation import indicator_values
from core.market.routing import ProvidersNotRun, ProvidersUnavailable, describe
from core.quant.history import History
from core.quant.risk import analyze_history
from core.quant.signals import compute_signals
from core.research.markets import provider_failure_reason
from core.research.watchlist import KR_STOCK_SPECS

HISTORY_BARS = 260               # one adjusted daily request covers 1Y returns (253 closes) with spare sessions
MAX_BARS = 500                   # ChartRequest's own upper bound
FLOW_SESSIONS = 20
RANGE_SESSIONS = 252
RANGE_MIN_SESSIONS = 200
RISK_MIN_SESSIONS = 21           # analyze_history needs 20 returns
INDICATOR_MIN_SESSIONS = 12      # EMA12 is the shortest indicator
STALE_DAYS = 7                   # the Q-SCORE history-age limit
RETURN_PERIODS = (("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252))
SECTION_KEYS = ("key_figures", "range", "returns", "risk", "signals", "indicators", "flows",
                "short_selling", "unavailable")
SOURCE_KEYS = ("history", "quote", "flows", "short_selling")
_HISTORY_SECTIONS = ("range", "returns", "risk", "signals", "indicators")
_INVESTOR_KEYS = ("foreign", "institution", "individual")
_KIS_SOURCES = frozenset({"KIS", "KIS REST"})
_KST = timezone(timedelta(hours=9))
_CURRENCIES = {"NAS": "USD", "NYS": "USD", "AMS": "USD", "HKS": "HKD", "TSE": "JPY",
               "SHS": "CNY", "SZS": "CNY", "HSX": "VND", "HNX": "VND"}
_HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏ꥠ-꥿가-힯ힰ-퟿]")


# --------------------------------------------------------------------------- #
# Public contracts
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ProfileRow:
    label: str
    value: str          # already formatted for display in the requested language
    tone: str | None    # 'up', 'down', 'flat' or None
    hint: str = ''      # tooltip text; carries provider and timestamps (no provider or date columns exist)


@dataclass(frozen=True)
class ProfileSection:
    key: str            # stable id, one of SECTION_KEYS
    title: str
    rows: tuple[ProfileRow, ...]
    note: str = ''      # one short line, e.g. the price basis


@dataclass(frozen=True)
class StockProfile:
    """Raw numbers for one stock; `sections` formats them.

    Units: `change_pct` is in percent (1.45 means +1.45%), as in the KIS and chart quote contracts. Every computed
    ratio inside `values` is a fraction (0.0145 means +1.45%). Flow and short-sale quantities are shares.

    `values` maps a section key to its raw numbers. `reasons` maps a section key (and 'fundamentals') to an
    authored code saying why it is empty; `errors` holds the exception class name when a source failed.
    `sources` and `fetched` map a source key ('history', 'quote', 'flows', 'short_selling') to the provider and
    the ISO UTC time it was received. Treat the mappings as read-only.
    """
    instrument: Instrument
    name: str = ""                    # as supplied or from the KIS quote (Korean for domestic stocks); may be ''
    name_en: str = ""                 # bundled English name when one is known; may be ''
    currency: str = ""
    last_price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    price_basis: str = ""             # 'quote' (a quote's last price), 'daily_close' (last daily bar) or ''
    candles: tuple[Candle, ...] = ()  # the daily bars every history section used, ascending
    adjusted: bool = False            # True only for adjusted (KIS) bars; Yahoo bars are unadjusted
    as_of: str = ""                   # ISO date of the last daily bar
    today: date | None = None
    stale: bool = False               # last daily bar older than STALE_DAYS
    live_eligible: bool = False       # history came from KIS, so the chart's KIS live stream may run
    values: dict = field(default_factory=dict, hash=False)
    reasons: dict = field(default_factory=dict, hash=False)
    errors: dict = field(default_factory=dict, hash=False)
    sources: dict = field(default_factory=dict, hash=False)
    fetched: dict = field(default_factory=dict, hash=False)
    attempts: tuple = ()              # core.market.routing.Attempt records of the history load

    @property
    def symbol(self) -> str:
        return self.instrument.symbol

    def daily_snapshot(self) -> MarketSnapshot | None:
        """The daily bars as a MarketSnapshot (for the chart or QScoreController.set_history); None without bars.

        The request's `adjusted` flag is the profile's own, so Yahoo bars are never presented as adjusted.
        """
        if not self.candles:
            return None
        request = ChartRequest(self.instrument, "1d", min(MAX_BARS, max(20, len(self.candles))),
                               adjusted=self.adjusted)
        return MarketSnapshot(request, self.candles, None, self.fetched.get("history", ""),
                              self.sources.get("history", ""))


# --------------------------------------------------------------------------- #
# Small validators (never raise)
# --------------------------------------------------------------------------- #
def _finite(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _positive(value):
    number = _finite(value)
    return number if number is not None and number > 0 else None


def _field(obj, key):
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def _has(obj, key):
    return key in obj if isinstance(obj, Mapping) else hasattr(obj, key)


def _text(value, limit=80):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or len(text) > limit or any(ord(ch) < 32 or ch in "<>" for ch in text):
        return None
    return text


def _shares(value):
    number = _finite(value)
    if number is None or not 0 < number <= 2 ** 53 - 1 or not number.is_integer():
        return None
    return int(number)


def _iso_day(value):
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except (TypeError, ValueError):
        return None


def _today(value):
    if isinstance(value, datetime):
        return value.astimezone(_KST).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if value:
        parsed = _iso_day(value)
        if parsed is not None:
            return parsed
    return datetime.now(_KST).date()


def _stamp_text(value):
    """An ISO timestamp with a timezone, or ''."""
    if not isinstance(value, str) or not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return value if parsed.tzinfo is not None else ""


def _check_instrument(instrument):
    if not isinstance(instrument, Instrument):
        raise TypeError("instrument must be a core.market.models.Instrument")
    if instrument.asset not in ("domestic_stock", "overseas_stock"):
        raise ValueError("A stock profile needs a domestic or overseas stock")


def _failure(exc):
    if isinstance(exc, ProvidersNotRun):
        return "connection_not_configured"
    if isinstance(exc, ProvidersUnavailable):
        return "provider_unavailable"
    try:
        return provider_failure_reason(exc)
    except Exception:  # the classification itself must not hide the original failure
        return "provider_unavailable"


# --------------------------------------------------------------------------- #
# Input normalisation
# --------------------------------------------------------------------------- #
def _as_candle(item):
    if isinstance(item, Candle):
        return item
    try:
        volume = _finite(_field(item, "volume"))
        return Candle(str(_field(item, "timestamp")), float(_field(item, "open")), float(_field(item, "high")),
                      float(_field(item, "low")), float(_field(item, "close")),
                      volume if volume is not None and volume >= 0 else None)
    except (TypeError, ValueError, OverflowError):
        return None


def _daily(candles):
    """Valid daily bars, one per date, ascending; and whether any input was given."""
    try:
        items = tuple(candles or ())
    except TypeError:
        return (), True
    by_day = {}
    for item in items:
        candle = _as_candle(item)
        day = _iso_day(candle.timestamp) if candle is not None else None
        if day is None or not candle.close > 0:
            continue
        by_day[day] = candle
    return tuple(by_day[d] for d in sorted(by_day))[-MAX_BARS:], bool(items)


def _quote_view(instrument, quote):
    """(fields, reason): a quote's validated display fields, or None and why it was rejected."""
    if quote is None:
        return None, None
    ticker = _field(quote, "ticker")
    owner = _field(quote, "instrument")
    if ticker is not None and str(ticker).strip().upper() != instrument.code:
        return None, "invalid_response"
    if isinstance(owner, Instrument) and owner != instrument:
        return None, "invalid_response"
    source = str(_field(quote, "source") or "")
    currency = str(_field(quote, "currency") or "").upper()
    if instrument.asset == "domestic_stock" and currency and currency != "KRW":
        return None, "invalid_response"
    price = _positive(_field(quote, "price"))
    if price is None:
        return None, "no_observations"
    view = {
        "price": price, "change": _finite(_field(quote, "change")), "change_pct": _finite(_field(quote, "change_pct")),
        # An unopened session can report zero OHLC; zero is a placeholder, not an observed price.
        "open": _positive(_field(quote, "open")), "high": _positive(_field(quote, "high")),
        "low": _positive(_field(quote, "low")),
        "volume": _finite(_field(quote, "volume")),
        "currency": currency, "source": source, "name": _text(_field(quote, "name")) or "",
        "received_at": _stamp_text(_field(quote, "as_of")) or _stamp_text(_field(quote, "received_at")),
        "market_time": str(_field(quote, "market_time") or ""),
        "fundamentals": None,
    }
    if view["volume"] is not None and view["volume"] < 0:
        view["volume"] = None
    if (instrument.asset == "domestic_stock" and source.upper() == "KIS"
            and any(_has(quote, k) for k in ("per", "eps", "sector", "listed_shares"))):
        # Only the KISClient Quote carries these (the chart's MarketQuote does not). They come from the same
        # inquire-price payload; no TTM, consolidation or dilution basis is supplied with them.
        view["fundamentals"] = {"per": _finite(_field(quote, "per")), "eps": _finite(_field(quote, "eps")),
                                "sector": _text(_field(quote, "sector")),
                                "listed_shares": _shares(_field(quote, "listed_shares"))}
    return view, None


def _rows(data, columns):
    """(rows, ok): {'date': iso, column: float|None} per date, ascending; ok False when unreadable."""
    try:
        items = list(data)
    except TypeError:
        return [], False
    by_day = {}
    for item in items:
        day = _iso_day(_field(item, "date"))
        if day is None:
            continue
        by_day[day] = {key: _finite(_field(item, name)) for key, name in columns}
    return [dict(by_day[d], date=d.isoformat()) for d in sorted(by_day)], True


def _known_name(instrument, language):
    if instrument.asset == "domestic_stock":
        for korean, code, english in KR_STOCK_SPECS:
            if code == instrument.code:
                return korean if language == "ko" else english
        return ""
    try:
        from core.market.symbols import lookup
        entry = lookup(instrument.code, instrument.exchange)
    except Exception:  # a bundled-file problem must not block the profile
        entry = None
    if entry is None:
        return ""
    return entry.name_ko if language == "ko" else entry.name_en


# --------------------------------------------------------------------------- #
# Computations
# --------------------------------------------------------------------------- #
def _range(dates, closes):
    window_d, window_c = dates[-RANGE_SESSIONS:], closes[-RANGE_SESSIONS:]
    hi = max(range(len(window_c)), key=lambda i: (window_c[i], i))     # the latest of equal highs
    lo = min(range(len(window_c)), key=lambda i: (window_c[i], -i))    # the latest of equal lows
    high, low, last = window_c[hi], window_c[lo], closes[-1]
    return {"sessions": len(window_c), "first_date": window_d[0], "last_date": window_d[-1],
            "high": high, "high_date": window_d[hi], "low": low, "low_date": window_d[lo], "last": last,
            "position": (last - low) / (high - low) if high > low else None,
            "from_high": last / high - 1.0, "from_low": last / low - 1.0}


def _returns(dates, closes):
    out = {}
    for key, offset in RETURN_PERIODS:
        if len(closes) > offset:
            base = closes[-1 - offset]
            out[key] = {"value": closes[-1] / base - 1.0, "offset": offset, "base": base,
                        "base_date": dates[-1 - offset]}
    return out


def _risk(history):
    try:
        report = analyze_history(history)
    except (ArithmeticError, ValueError, TypeError):
        return None
    data = asdict(report)
    return data if all(math.isfinite(v) for v in data.values() if isinstance(v, float)) else None


def _signals(history):
    try:
        report = compute_signals(history)
    except (ArithmeticError, ValueError, TypeError, IndexError):
        return None
    if not math.isfinite(report.composite):
        return None
    return {"composite": float(report.composite), "stance": report.stance, "direction": report.direction,
            "components": tuple({"key": c.key, "label": c.label, "score": float(c.score), "weight": float(c.weight),
                                 "value": c.value, "reason": c.reason}
                                for c in report.components if math.isfinite(c.score))}


def _flows(rows):
    """Net-buying sums per window; None when no session reported any investor value (dated rows, empty fields)."""
    out = {"sessions": len(rows), "first_date": rows[0]["date"], "last_date": rows[-1]["date"], "windows": {}}
    for length in sorted({min(w, len(rows)) for w in (5, FLOW_SESSIONS)}):
        window = rows[-length:]
        entry = {"first_date": window[0]["date"], "last_date": window[-1]["date"], "reported": {}}
        for investor in _INVESTOR_KEYS:
            reported = [r[investor] for r in window if r[investor] is not None]
            entry[investor] = sum(reported) if reported else None
            entry["reported"][investor] = len(reported)
        out["windows"][length] = entry
    if not any(entry[k] is not None for entry in out["windows"].values() for k in _INVESTOR_KEYS):
        return None
    return out


def _shorts(rows):
    latest = next((r for r in reversed(rows) if r["short_ratio_pct"] is not None or r["short_qty"] is not None), None)
    if latest is None:
        return None
    window = rows[-FLOW_SESSIONS:]
    ratios = [r["short_ratio_pct"] for r in window if r["short_ratio_pct"] is not None]
    quantities = [r["short_qty"] for r in window if r["short_qty"] is not None]
    return {"sessions": len(rows), "latest": dict(latest),
            "average": {"sessions": len(window), "first_date": window[0]["date"], "last_date": window[-1]["date"],
                        "short_ratio_pct": sum(ratios) / len(ratios) if ratios else None,
                        "short_qty": sum(quantities) / len(quantities) if quantities else None,
                        "reported_ratio": len(ratios), "reported_qty": len(quantities)}}


def build_profile(instrument, *, candles, quote=None, flows=None, shorts=None, name="", today=None,
                  source="", adjusted=True, fetched_at="", reasons=None, errors=None, fetched=None,
                  attempts=()) -> StockProfile:
    """Compute a profile from supplied data; no I/O.

    `candles`: daily bars (Candle, or objects/mappings with timestamp/open/high/low/close/volume), adjusted unless
    `adjusted=False`; a Yahoo `source` is always treated as unadjusted. `quote`: a KISClient Quote (domestic; the
    only quote that carries fundamentals) or a chart MarketQuote. `flows`/`shorts`: rows as returned by
    KISMarkets.investor_daily / short_sale_daily. `reasons`/`errors`/`fetched` (keyed by SOURCE_KEYS) let a loader
    say why a source is missing and when the others arrived.
    """
    _check_instrument(instrument)
    today = _today(today)
    reasons_in, errors_in, fetched_in = dict(reasons or {}), dict(errors or {}), dict(fetched or {})
    source = str(source or "")
    domestic = instrument.asset == "domestic_stock"
    adjusted = bool(adjusted) and not source.lower().startswith("yahoo")
    values, why, failed, sources, stamps = {}, {}, {}, {}, {}

    def missing(key, origin, default):
        why[key] = reasons_in.get(origin) or default
        if origin in errors_in and errors_in[origin]:
            failed[key] = str(errors_in[origin])

    # Daily history ------------------------------------------------------------------
    bars, given = _daily(candles)
    history_default = "invalid_response" if given else "no_history"
    if bars and _iso_day(bars[-1].timestamp) > today:
        bars, history_default = (), "future_history"
    if bars:
        sources["history"] = source
        stamps["history"] = _stamp_text(fetched_at)
    dates = [c.timestamp[:10] for c in bars]
    closes = [float(c.close) for c in bars]
    count = len(closes)
    last_day = _iso_day(dates[-1]) if bars else None
    stale = bool(last_day and (today - last_day).days > STALE_DAYS)

    # Quote and key figures ----------------------------------------------------------
    view, quote_problem = _quote_view(instrument, quote)
    if view:
        sources["quote"] = view["source"]
        stamps["quote"] = view["received_at"] or _stamp_text(fetched_in.get("quote"))
        last_price, change, change_pct, basis = view["price"], view["change"], view["change_pct"], "quote"
    elif bars:
        last_price, basis = closes[-1], "daily_close"
        change = closes[-1] - closes[-2] if count > 1 else None
        change_pct = (closes[-1] / closes[-2] - 1.0) * 100 if count > 1 else None
    else:
        last_price = change = change_pct = None
        basis = ""
    currency = (view or {}).get("currency") or ("KRW" if domestic else _CURRENCIES.get(instrument.exchange, ""))

    figures = {}
    if view and any(view[k] is not None for k in ("open", "high", "low", "volume")):
        figures.update({k: view[k] for k in ("open", "high", "low", "volume")}, basis="quote",
                       market_time=view["market_time"])
    elif bars:
        bar = bars[-1]
        figures.update(open=bar.open, high=bar.high, low=bar.low, volume=bar.volume, basis="daily_bar",
                       date=dates[-1])
    fundamentals = (view or {}).get("fundamentals")
    if not domestic:
        why["fundamentals"] = "domestic_only"
    elif fundamentals is None:
        missing("fundamentals", "quote", quote_problem or "not_provided")
    else:
        shares = fundamentals["listed_shares"]
        cap = _finite(view["price"] * shares) if shares is not None else None
        figures.update(fundamentals, market_cap=cap, market_cap_unit="KRW" if cap is not None else None,
                       market_cap_basis="price_x_listed_shares" if cap is not None else None)
        if not any(fundamentals[k] is not None for k in ("per", "eps", "sector", "listed_shares")):
            why["fundamentals"] = "no_observations"
    if figures:
        values["key_figures"] = figures
    else:
        missing("key_figures", "quote" if "quote" in reasons_in else "history", quote_problem or history_default)

    # History sections -----------------------------------------------------------------
    if not bars:
        for key in _HISTORY_SECTIONS:
            missing(key, "history", history_default)
    else:
        series = History(instrument.symbol, source, tuple(dates), tuple(closes),
                         adjustment="split" if adjusted else "")
        if count >= RANGE_MIN_SESSIONS:
            values["range"] = _range(dates, closes)
        else:
            why["range"] = "insufficient_history"
            values["range"] = {"sessions": count, "needed": RANGE_MIN_SESSIONS}
        found = _returns(dates, closes)
        if found:
            values["returns"] = found
        else:
            why["returns"] = "insufficient_history"
            values["returns"] = {"sessions": count, "needed": RETURN_PERIODS[0][1] + 1}
        for key, compute in (("risk", _risk), ("signals", _signals)):
            if count < RISK_MIN_SESSIONS:
                why[key] = "insufficient_history"
                values[key] = {"sessions": count, "needed": RISK_MIN_SESSIONS}
                continue
            result = compute(series)
            if result is None:
                why[key] = "engine_unavailable"
            else:
                values[key] = dict(result, sessions=count, first_date=dates[0], last_date=dates[-1])
        snapshot = MarketSnapshot(ChartRequest(instrument, "1d", min(MAX_BARS, max(20, count)), adjusted=adjusted),
                                  bars)
        found = {k: float(v) for k, v in indicator_values(snapshot).items()
                 if _finite(v) is not None}
        if found:
            values["indicators"] = dict(found, date=dates[-1])
        else:
            why["indicators"] = "insufficient_history"
            values["indicators"] = {"sessions": count, "needed": INDICATOR_MIN_SESSIONS}

    # Investor flows and short selling (domestic KIS only) -------------------------------
    for key, data, columns, compute in (
            ("flows", flows, (("foreign", "foreign_net_qty"), ("institution", "institution_net_qty"),
                              ("individual", "individual_net_qty")), _flows),
            ("short_selling", shorts, (("short_qty", "short_qty"), ("short_ratio_pct", "short_ratio_pct"),
                                       ("volume", "volume")), _shorts)):
        if not domestic:
            why[key] = "domestic_only"
            continue
        if data is None:
            missing(key, key, "not_provided")
            continue
        rows, readable = _rows(data, columns)
        result = compute(rows) if rows else None
        if not readable:
            why[key] = "invalid_response"
        elif result is None:
            why[key] = "no_observations"
        else:
            values[key] = result
            sources[key] = "KIS"
            stamps[key] = _stamp_text(fetched_in.get(key))

    supplied = _text(str(name or ""), 120) or ""
    return StockProfile(
        instrument=instrument, name=supplied or (view or {}).get("name") or _known_name(instrument, "ko"),
        name_en=_known_name(instrument, "en"), currency=currency, last_price=last_price, change=change,
        change_pct=change_pct, price_basis=basis, candles=bars, adjusted=adjusted and bool(bars),
        as_of=dates[-1] if bars else "", today=today, stale=stale,
        live_eligible=bool(bars) and source.upper() in _KIS_SOURCES, values=values, reasons=why, errors=failed,
        sources=sources, fetched=stamps, attempts=tuple(attempts or ()))


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #
def _ask(key, client, call, reasons, errors, fetched):
    """One optional provider call; a missing, unready or failing client leaves a reason instead."""
    if client is None:
        reasons[key] = "connection_not_configured"
        return None
    try:
        if not bool(getattr(client, "ready", True)):
            reasons[key] = "connection_not_configured"
            return None
        result = call(client)
    except Exception as exc:  # provider text can carry URLs or keys: keep the class name only
        reasons[key], errors[key] = _failure(exc), type(exc).__name__
        return None
    fetched[key] = utc_now()
    return result


def load_profile(instrument, *, router, quote_client=None, markets=None, today=None) -> StockProfile:
    """Read every allowlisted source this view uses, then `build_profile`. Run it off the GUI thread.

    Calls, in order: router.load(ChartRequest(instrument, "1d", 260, adjusted=True)); for domestic stocks only,
    quote_client.quote(code), markets.investor_daily(code, days=20), markets.short_sale_daily(code, days=20).
    Each is optional and failure-tolerant. When the KIS quote is unavailable the chart snapshot's own quote
    still supplies price and OHLC (never fundamentals).
    """
    _check_instrument(instrument)
    reasons, errors, fetched = {}, {}, {}
    request = ChartRequest(instrument, "1d", HISTORY_BARS, adjusted=True)
    snapshot, attempts = None, ()
    if router is None:
        reasons["history"] = "connection_not_configured"
    else:
        try:
            snapshot = router.load(request)
        except Exception as exc:
            reasons["history"], errors["history"] = _failure(exc), type(exc).__name__
        attempts = tuple(getattr(router, "last_attempts", ()) or ())
        if snapshot is not None and (not isinstance(snapshot, MarketSnapshot)
                                     or snapshot.request.instrument != instrument
                                     or snapshot.request.interval != "1d"):
            snapshot, reasons["history"] = None, "invalid_response"
    quote = flows = shorts = None
    if instrument.asset == "domestic_stock":
        code = instrument.code
        quote = _ask("quote", quote_client, lambda c: c.quote(code), reasons, errors, fetched)
        if quote is not None:
            _view, problem = _quote_view(instrument, quote)
            if problem:
                quote, reasons["quote"] = None, problem
        flows = _ask("flows", markets, lambda m: m.investor_daily(code, days=FLOW_SESSIONS), reasons, errors, fetched)
        shorts = _ask("short_selling", markets, lambda m: m.short_sale_daily(code, days=FLOW_SESSIONS),
                      reasons, errors, fetched)
    if quote is None and snapshot is not None and snapshot.quote is not None:
        quote = snapshot.quote          # price and OHLC only; fundamentals stay with reasons["quote"]
    source = str(snapshot.source) if snapshot is not None else ""
    return build_profile(
        instrument, candles=snapshot.candles if snapshot is not None else (), quote=quote, flows=flows,
        shorts=shorts, today=today, source=source,
        adjusted=bool(snapshot is not None and snapshot.request.adjusted and source.upper() in _KIS_SOURCES),
        fetched_at=snapshot.fetched_at if snapshot is not None else "", reasons=reasons, errors=errors,
        fetched=fetched, attempts=attempts)


# --------------------------------------------------------------------------- #
# Display text
# --------------------------------------------------------------------------- #
_LOCALES = {"ko": LocaleContext("ko_KR"), "en": LocaleContext("en_US")}

_TITLES = {
    "key_figures": ("주요 지표", "Key figures"),
    "range": ("52주 범위", "52-week range"),
    "returns": ("기간 수익률", "Returns"),
    "risk": ("위험 지표", "Risk"),
    "signals": ("기술적 신호", "Technical signals"),
    "indicators": ("기술 지표", "Indicators"),
    "flows": ("투자자별 순매수", "Investor net buying"),
    "short_selling": ("공매도", "Short selling"),
    "unavailable": ("제공되지 않는 정보", "Not available here"),
}

_REASONS = {
    "domestic_only": ("국내 주식에만 제공됩니다", "Provided for Korean stocks only"),
    "connection_not_configured": ("KIS 연결 설정 필요", "KIS connection not configured"),
    "not_provided": ("자료가 전달되지 않았습니다", "No data supplied"),
    "no_history": ("가격 이력을 불러오지 못했습니다", "Price history unavailable"),
    "future_history": ("가격 이력의 날짜가 오늘 이후입니다", "Price history is dated after today"),
    "insufficient_history": ("{n}거래일 자료 · {need}거래일 이상 필요", "{n} sessions · needs at least {need}"),
    "engine_unavailable": ("계산할 수 없습니다", "Could not be computed"),
    "no_observations": ("자료 없음", "No data"),
    "insufficient_observations": ("자료 부족", "Too little data"),
    "rate_limited": ("요청 제한", "Rate limited"),
    "network_timeout": ("응답 지연", "Timed out"),
    "network_error": ("연결 확인 필요", "Connection problem"),
    "certificate_error": ("인증서 확인 필요", "Certificate problem"),
    "access_denied": ("권한 확인 필요", "Access denied"),
    "dependency_missing": ("설치 확인 필요", "Missing package"),
    "dependency_incompatible": ("버전 확인 필요", "Version issue"),
    "invalid_response": ("응답 확인 필요", "Unexpected response"),
    "provider_unavailable": ("조회 실패", "Request failed"),
}

# The Korean display labels of the existing catalogue (quantgen_desktop/display_prose_catalog.py), used for
# SIGNAL_STANCES and the authored component labels; core never imports the desktop package.
_STANCES_KO = {"strong bullish": "강한 상승 우위", "bullish": "상승 우위", "neutral": "중립",
               "bearish": "하락 우위", "strong bearish": "강한 하락 우위"}
_COMPONENTS_KO = {"Price vs 50-day SMA": "가격과 50일 이동평균", "Price vs 200-day SMA": "가격과 200일 이동평균",
                  "3-month momentum": "3개월 모멘텀", "Volatility regime": "변동성 상태"}
# SignalsPane's own status line (quantgen_desktop/signals.py; Korean in quantgen_desktop/translations.py).
SIGNALS_CONTEXT = ("참고용 · v2 신호 아님 (DO-NOT-BUILD TF-12). 거래 원장에 연결되지 않습니다.",
                   "Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.")
_NOT_ADVICE = ("매수·매도 추천이 아닙니다.", "Not a buy or sell recommendation.")
# The Home watchlist's sector vocabulary (quantgen_desktop/watchlist.py _SECTORS_EN).
_SECTORS_EN = {"전기전자": "Electronics", "전기,전자": "Electronics", "전기·전자": "Electronics",
               "운수장비": "Transport equipment", "금융업": "Financials", "의약품": "Pharmaceuticals",
               "서비스업": "Services", "기계": "Machinery", "화학": "Chemicals"}
_PER_EPS_CAVEAT = ("KIS 제공값 · 회계 기준과 기준일은 확인되지 않았습니다. EPS 단위·희석 여부도 확인되지 않았습니다.",
                   "KIS-provided value. Accounting basis and reference date are unconfirmed; "
                   "EPS unit and dilution basis are also unconfirmed.")
_RETURN_LABELS = {"1W": ("1주", "1W"), "1M": ("1개월", "1M"), "3M": ("3개월", "3M"), "6M": ("6개월", "6M"),
                  "1Y": ("1년", "1Y")}
_INDICATORS = (("SMA20", ("SMA 20", "SMA 20"), True), ("EMA12", ("EMA 12", "EMA 12"), True),
               ("EMA26", ("EMA 26", "EMA 26"), True), ("RSI14", ("RSI 14", "RSI 14"), False),
               ("MACD", ("MACD (12/26)", "MACD (12/26)"), False),
               ("SIGNAL", ("MACD 시그널 (9)", "MACD signal (9)"), False),
               ("BB_UPPER", ("볼린저 상단 (20, 2σ)", "Bollinger upper (20, 2σ)"), True),
               ("BB_LOWER", ("볼린저 하단 (20, 2σ)", "Bollinger lower (20, 2σ)"), True))
_INVESTORS = (("foreign", ("외국인", "Foreign")), ("institution", ("기관", "Institutions")),
              ("individual", ("개인", "Individuals")))
_ALWAYS_MISSING = (
    (("뉴스", "News"), ("QUANTGEN에 연결된 뉴스 공급원이 없습니다.", "QUANTGEN has no news source connected.")),
    (("애널리스트 의견·목표주가", "Analyst ratings and price targets"),
     ("애널리스트 자료 공급원이 없습니다.", "No analyst data source is connected.")),
    (("배당", "Dividends"),
     ("배당 자료를 읽지 않습니다. 기간 수익률은 배당을 뺀 가격 기준입니다.",
      "Dividend data is not read; returns here are price-only.")),
    (("호가", "Order book"), ("호가 잔량은 이 화면에서 조회하지 않습니다.", "Bid and ask depth is not loaded in this view.")),
)


def _language(lang):
    text = str(getattr(lang, "language", lang) or "").lower()
    return "ko" if text.startswith("ko") else "en"


class _Writer:
    def __init__(self, profile, lang):
        self.p, self.lang, self.ctx = profile, lang, _LOCALES[lang]

    def t(self, ko, en):
        return ko if self.lang == "ko" else en

    def pair(self, texts):
        return texts[0] if self.lang == "ko" else texts[1]

    # numbers ---------------------------------------------------------------
    def num(self, value, digits=2):
        return self.ctx.number(float(value), digits)

    def signed(self, value, digits=2):
        rounded = round(float(value), digits)
        if rounded == 0:
            return self.num(0, digits)
        return ("+" if rounded > 0 else "-") + self.num(abs(rounded), digits)

    def pct(self, fraction, digits=2, signed=True):
        value = float(fraction) * 100
        return (self.signed(value, digits) if signed else self.num(value, digits)) + "%"

    @staticmethod
    def tone(value, digits=2):
        rounded = round(float(value), digits)
        return "flat" if rounded == 0 else ("up" if rounded > 0 else "down")

    def price_digits(self):
        return 0 if self.p.currency in ("KRW", "JPY", "VND") else 2

    def price(self, value):
        return (self.num(value, self.price_digits()) + " " + self.p.currency).strip()

    def shares(self, value, signed=False):
        text = self.signed(value, 0) if signed else self.num(value, 0)
        return text + self.t("주", " shares")

    def compact(self, value):
        return format_compact_decimal(float(value), format_type="short", locale=self.ctx.locale, fraction_digits=2)

    def plain(self, value):
        number = float(value)
        return self.num(number, 0 if number.is_integer() else 2)

    # dates and provenance ---------------------------------------------------
    def day(self, iso):
        try:
            return self.ctx.date(str(iso)[:10]) if iso else "—"
        except (TypeError, ValueError):
            return str(iso)

    def stamp(self, iso):
        try:
            moment = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return ""
        if moment.tzinfo is None:
            return ""
        return self.ctx.timestamp(moment.astimezone(timezone.utc)) + " UTC"

    def span(self, first, last):
        return self.day(first) + " → " + self.day(last)

    def provider(self, key):
        name = str(self.p.sources.get(key) or "")
        return "KIS" if name.upper() in _KIS_SOURCES else name

    def yahoo(self):
        return self.provider("history").lower().startswith("yahoo")

    def basis(self):
        if self.p.adjusted:
            return self.t("수정주가 일별 종가", "Adjusted daily closes")
        if self.yahoo():
            return self.t("Yahoo Finance 일별 종가 (수정 전·지연)", "Yahoo Finance daily closes (unadjusted, delayed)")
        return self.t("일별 종가 (수정 여부 미확인)", "Daily closes (adjustment unconfirmed)")

    def history_hint(self, *extra):
        p = self.p
        parts = [part for part in extra if part]
        if p.candles:
            parts.append(self.basis())
            parts.append(self.span(p.candles[0].timestamp, p.candles[-1].timestamp)
                         + self.t(f" · {len(p.candles)}거래일", f" · {len(p.candles)} sessions"))
            provider = self.provider("history")
            if provider:
                fetched = self.stamp(p.fetched.get("history"))
                parts.append(provider + (self.t(" · 조회 ", " · fetched ") + fetched if fetched else ""))
        if p.attempts and not p.live_eligible:
            parts.append(describe(p.attempts, self.lang))
        return "\n".join(parts)

    def quote_hint(self):
        """Where the price fields came from: a KIS quote, or a fallback's last daily bar."""
        if self.provider("quote").lower().startswith("yahoo"):
            data = self.p.values.get("key_figures") or {}
            bar = str(data.get("market_time") or self.p.as_of)
            return ("Yahoo Finance · " + self.t("지연·수정 전 일봉 ", "delayed, unadjusted daily bar ")
                    + self.day(bar) + "\n" + self.history_hint())
        return self.source_hint("quote", "현재가 조회", "quote")

    def source_hint(self, key, label_ko, label_en):
        provider = self.provider(key) or self.t("공급원 미확인", "Source unconfirmed")
        received = self.stamp(self.p.fetched.get(key))
        text = provider + " · " + self.t(label_ko, label_en)
        return text + (self.t(" · 수신 ", " · received ") + received if received else "")

    def reported(self, count, length):
        """A hint line when a window's figure rests on fewer sessions than the window holds; else ''."""
        if count >= length:
            return ""
        return self.t(f"\n{length}거래일 중 {count}일만 보고됨", f"\nReported on {count} of {length} sessions")

    def reason(self, key):
        code = self.p.reasons.get(key, "not_provided")
        template = self.pair(_REASONS.get(code, _REASONS["provider_unavailable"]))
        if code == "insufficient_history":
            data = self.p.values.get(key) or {}
            return template.format(n=data.get("sessions", 0), need=data.get("needed", 0))
        return template

    def history_note(self):
        p = self.p
        note = self.basis() + self.t(f" · {len(p.candles)}거래일", f" · {len(p.candles)} sessions")
        if p.stale:
            note += self.t(f" · 마지막 일봉 {self.day(p.as_of)}, 오래된 자료", f" · last bar {self.day(p.as_of)}, stale")
        elif p.today is not None and p.as_of == p.today.isoformat():
            note += self.t(" · 오늘 일봉은 장중 잠정값일 수 있음", " · today's bar may be provisional")
        return note


# --------------------------------------------------------------------------- #
# Section builders
# --------------------------------------------------------------------------- #
def _key_figures(w):
    data = w.p.values.get("key_figures")
    if not data:
        return ()
    if data.get("basis") == "quote":
        where = w.quote_hint()
    else:
        where = w.history_hint(w.t(f"마지막 일봉 {w.day(data.get('date'))}", f"Last daily bar {w.day(data.get('date'))}"))
    rows = []
    for key, labels in (("open", ("시가", "Open")), ("high", ("고가", "High")), ("low", ("저가", "Low"))):
        if data.get(key) is not None:
            rows.append(ProfileRow(w.pair(labels), w.price(data[key]), None, where))
    if data.get("volume") is not None:
        rows.append(ProfileRow(w.t("거래량", "Volume"), w.shares(data["volume"]), None, where))
    fundamentals = w.source_hint("quote", "현재가 조회", "quote")
    if data.get("market_cap") is not None:
        rows.append(ProfileRow(
            w.t("시가총액 (계산값)", "Market cap (computed)"), w.compact(data["market_cap"]) + " KRW", None,
            w.t("가격 × 상장 주식 수로 계산한 값입니다. 실제 가격 관측 시각은 제공되지 않았습니다.",
                "Calculated as price × listed shares; the actual price observation time was not supplied.")
            + "\n" + w.num(data["market_cap"], 0) + " KRW\n" + fundamentals))
    for key, label in (("per", "PER"), ("eps", "EPS")):
        if data.get(key) is not None:
            value = w.num(data[key], 2) if key == "per" else w.plain(data[key])
            rows.append(ProfileRow(label, value, None, w.pair(_PER_EPS_CAVEAT) + "\n" + fundamentals))
    if data.get("sector"):
        raw = data["sector"]
        shown = raw if w.lang == "ko" else _SECTORS_EN.get(raw, "Untranslated")
        hint = (w.t("KIS 제공 업종 · 공급처 기준일 미제공", "KIS-provided sector · original text is Korean; "
                    "provider reference date not supplied") + "\n" + fundamentals)
        rows.append(ProfileRow(w.t("업종", "Sector"), shown, None, hint))
    if data.get("listed_shares") is not None:
        rows.append(ProfileRow(w.t("상장 주식 수", "Listed shares"), w.shares(data["listed_shares"]), None,
                               w.t("KIS 제공값 · 공급처 기준일 미제공", "KIS-provided value · provider reference "
                                   "date not supplied") + "\n" + fundamentals))
    return tuple(rows)


def _range_rows(w):
    data = w.p.values.get("range")
    if not data or "high" not in data:
        return ()
    hint = w.history_hint()
    rows = [ProfileRow(w.t("52주 최고", "52-week high"), w.price(data["high"]), None,
                       w.day(data["high_date"]) + "\n" + hint),
            ProfileRow(w.t("52주 최저", "52-week low"), w.price(data["low"]), None,
                       w.day(data["low_date"]) + "\n" + hint)]
    if data["position"] is not None:
        rows.append(ProfileRow(w.t("범위 내 위치", "Position in range"), w.pct(data["position"], signed=False), None,
                               w.t("0% = 52주 최저, 100% = 52주 최고 · 마지막 종가 ",
                                   "0% = 52-week low, 100% = 52-week high · last close ")
                               + w.price(data["last"]) + "\n" + hint))
    rows.append(ProfileRow(w.t("52주 최고 대비", "From 52-week high"), w.pct(data["from_high"]),
                           w.tone(data["from_high"] * 100), hint))
    rows.append(ProfileRow(w.t("52주 최저 대비", "From 52-week low"), w.pct(data["from_low"]),
                           w.tone(data["from_low"] * 100), hint))
    return tuple(rows)


def _range_note(w):
    data = w.p.values.get("range") or {}
    note = w.history_note()
    if data.get("sessions", RANGE_SESSIONS) < RANGE_SESSIONS:
        note += w.t(f" · 범위는 {data['sessions']}거래일 기준 (52주 미만)",
                    f" · range uses {data['sessions']} sessions (under 52 weeks)")
    return note


def _return_rows(w):
    data = w.p.values.get("returns") or {}
    rows = []
    for key, _offset in RETURN_PERIODS:
        item = data.get(key)
        if not isinstance(item, dict):
            continue
        hint = w.t(f"{item['offset']}거래일 전 종가({w.day(item['base_date'])}, {w.price(item['base'])}) 대비",
                   f"vs the close {item['offset']} sessions earlier ({w.day(item['base_date'])}, "
                   f"{w.price(item['base'])})")
        rows.append(ProfileRow(w.pair(_RETURN_LABELS[key]), w.pct(item["value"]), w.tone(item["value"] * 100),
                               hint + "\n" + w.history_hint()))
    return tuple(rows)


def _risk_rows(w):
    data = w.p.values.get("risk")
    if not data or "ann_vol" not in data:
        return ()
    level = w.num(data["var_level"] * 100, 0) + "%"
    hint = w.history_hint(w.t(f"일간 로그수익률 · 계산 엔진 {data['engine']}",
                              f"Daily log returns · engine {data['engine']}"))
    rows = [
        ProfileRow(w.t("연간 변동성", "Annual volatility"), w.pct(data["ann_vol"], signed=False), None, hint),
        ProfileRow(w.t("최대 낙폭", "Max drawdown"), w.pct(data["max_drawdown"]), w.tone(data["max_drawdown"] * 100),
                   w.t("고점 대비 가장 큰 하락", "Largest peak-to-trough fall") + "\n" + hint),
        ProfileRow(w.t(f"1일 VaR {level}", f"1-day VaR {level}"), w.pct(data["var_1d"], signed=False), None,
                   w.t("과거 일간 손실 분위수 (역사적 방식)", "Historical 1-day loss quantile") + "\n" + hint),
        ProfileRow(w.t(f"1일 CVaR {level}", f"1-day CVaR {level}"), w.pct(data["cvar_1d"], signed=False), None,
                   w.t("VaR 이상 손실의 평균", "Average loss at or beyond VaR") + "\n" + hint),
        ProfileRow(w.t("최대 일간 상승", "Best day"), w.pct(data["best_day"]), w.tone(data["best_day"] * 100), hint),
        ProfileRow(w.t("최대 일간 하락", "Worst day"), w.pct(data["worst_day"]), w.tone(data["worst_day"] * 100), hint),
        ProfileRow(w.t("상승일 비율", "Up days"), w.pct(data["positive_days"], 1, signed=False), None, hint),
    ]
    return tuple(rows)


def _signal_rows(w):
    data = w.p.values.get("signals")
    if not data or "composite" not in data:
        return ()
    hint = w.history_hint()
    tone = {1: "up", -1: "down"}.get(data["direction"], "flat")
    stance = _STANCES_KO.get(data["stance"], data["stance"]) if w.lang == "ko" else data["stance"]
    count = len(data["components"])
    rows = [ProfileRow(w.t("종합 점수", "Composite score"), w.signed(data["composite"], 1), tone,
                       w.t(f"범위 -100~100 · 구성요소 {count}개", f"Range -100 to 100 · {count} components") + "\n" + hint),
            ProfileRow(w.t("판단", "Stance"), stance, tone, hint)]
    for item in data["components"]:
        label = _COMPONENTS_KO.get(item["label"], item["label"]) if w.lang == "ko" else item["label"]
        weight = w.num(item["weight"] * 100, 0) + "%"
        detail = (item["value"] + " · " if item["value"] else "") + w.t(f"비중 {weight}", f"weight {weight}")
        rows.append(ProfileRow(label, w.signed(item["score"], 1), w.tone(item["score"], 1), detail + "\n" + hint))
    return tuple(rows)


def _indicator_rows(w):
    data = w.p.values.get("indicators")
    if not data or "date" not in data:
        return ()
    hint = w.history_hint(w.t(f"{w.day(data['date'])} 일봉 기준", f"As of the {w.day(data['date'])} daily bar"))
    rows = []
    for key, labels, price_like in _INDICATORS:
        if data.get(key) is not None:
            value = w.price(data[key]) if price_like else w.num(data[key], 1 if key == "RSI14" else 2)
            rows.append(ProfileRow(w.pair(labels), value, None, hint))
    return tuple(rows)


def _flow_rows(w):
    data = w.p.values.get("flows")
    if not data or "windows" not in data:
        return ()
    source = w.source_hint("flows", "투자자별 매매동향", "investor trading by stock")
    rows = []
    for length, entry in sorted(data["windows"].items()):
        span = w.span(entry["first_date"], entry["last_date"])
        for key, labels in _INVESTORS:
            total = entry.get(key)
            if total is None:
                continue
            hint = span + "\n" + source + w.reported(entry["reported"][key], length)
            rows.append(ProfileRow(w.pair(labels) + w.t(f" · 최근 {length}거래일", f" · last {length} sessions"),
                                   w.shares(total, signed=True), w.tone(total, 0), hint))
    return tuple(rows)


def _short_rows(w):
    data = w.p.values.get("short_selling")
    if not data or "latest" not in data:
        return ()
    source = w.source_hint("short_selling", "일별 공매도", "daily short sales")
    latest, average = data["latest"], data["average"]
    rows = []
    when = w.day(latest["date"]) + "\n" + source
    if latest["short_ratio_pct"] is not None:
        rows.append(ProfileRow(w.t("최근 공매도 비중", "Latest short-sale share"),
                               w.num(latest["short_ratio_pct"], 2) + "%", None, when))
    if latest["short_qty"] is not None:
        rows.append(ProfileRow(w.t("최근 공매도 수량", "Latest short-sale volume"), w.shares(latest["short_qty"]),
                               None, when))
    length = average["sessions"]
    span = w.span(average["first_date"], average["last_date"]) + "\n" + source
    if average["short_ratio_pct"] is not None:
        rows.append(ProfileRow(w.t(f"{length}거래일 평균 공매도 비중", f"{length}-session average short-sale share"),
                               w.num(average["short_ratio_pct"], 2) + "%", None,
                               span + w.reported(average["reported_ratio"], length)))
    if average["short_qty"] is not None:
        rows.append(ProfileRow(w.t(f"{length}거래일 평균 공매도 수량", f"{length}-session average short-sale volume"),
                               w.shares(average["short_qty"]), None,
                               span + w.reported(average["reported_qty"], length)))
    return tuple(rows)


def _unavailable_rows(w, skipped):
    p = w.p
    rows = []
    for key in skipped:
        hint = ""
        if key in p.errors:
            hint = w.t("오류 유형: ", "Error type: ") + p.errors[key]
        if key in _HISTORY_SECTIONS or (key == "key_figures" and not p.candles):
            hint = "\n".join(part for part in (hint, w.history_hint()) if part)
        rows.append(ProfileRow(w.pair(_TITLES[key]), w.reason(key), None, hint))
    if "fundamentals" in p.reasons and "key_figures" not in skipped:
        if p.instrument.asset == "domestic_stock":
            hint = w.t("오류 유형: ", "Error type: ") + p.errors["fundamentals"] if "fundamentals" in p.errors else ""
            rows.append(ProfileRow(w.t("재무 지표 (PER·EPS·업종·상장 주식 수·시가총액)",
                                       "Fundamentals (PER, EPS, sector, listed shares, market cap)"),
                                   w.reason("fundamentals"), None, hint))
    if p.instrument.asset == "overseas_stock":
        rows.append(ProfileRow(w.t("해외 종목 재무 지표", "Overseas fundamentals"), w.t("제공되지 않음", "Not provided"),
                               None, w.t("해외 종목의 PER·EPS·시가총액 등은 조회하지 않습니다.",
                                         "PER, EPS, market cap and other fundamentals are not loaded for "
                                         "overseas stocks.")))
    if p.candles and not p.live_eligible:
        rows.append(ProfileRow(w.t("실시간 체결", "Live trades"), w.t("KIS 자료에서만 제공", "KIS data only"), None,
                               w.t("현재 가격 이력은 KIS 자료가 아니므로 실시간 체결 갱신과 Q-SCORE를 쓰지 않습니다.",
                                   "This price history is not from KIS, so live trade updates and Q-SCORE "
                                   "do not run.") + "\n" + w.history_hint()))
    for labels, hints in _ALWAYS_MISSING:
        rows.append(ProfileRow(w.pair(labels), w.t("제공되지 않음", "Not provided"), None, w.pair(hints)))
    return tuple(rows)


def sections(profile, lang) -> list[ProfileSection]:
    """Display sections in SECTION_KEYS order. A section without rows is left out and named in 'unavailable'.

    `lang` is 'ko' or 'en' (a LocaleContext also works); anything else is English. English output contains no
    Hangul: Korean-only provider text (the KIS stock name, sector text) is never placed in it.
    """
    if not isinstance(profile, StockProfile):
        raise TypeError("profile must be a StockProfile")
    w = _Writer(profile, _language(lang))
    builders = (("key_figures", _key_figures, lambda: ""),
                ("range", _range_rows, lambda: _range_note(w)),
                ("returns", _return_rows, lambda: w.history_note()),
                ("risk", _risk_rows, lambda: w.history_note() + w.t(" · 과거 자료이며 예측이 아님",
                                                                     " · historical, not a forecast")),
                ("signals", _signal_rows, lambda: w.pair(SIGNALS_CONTEXT) + " " + w.pair(_NOT_ADVICE)),
                ("indicators", _indicator_rows, lambda: w.history_note()),
                ("flows", _flow_rows, lambda: w.t("순매수 = 매수 수량 - 매도 수량 (주)",
                                                  "Net buying = shares bought minus shares sold")),
                ("short_selling", _short_rows, lambda: w.t("비중은 KIS가 제공하는 공매도 거래량 비중입니다",
                                                           "Share is the short-sale volume share KIS supplies")))
    out, skipped = [], []
    for key, build, note in builders:
        rows = build(w)
        if rows:
            out.append(ProfileSection(key, w.pair(_TITLES[key]), rows, note()))
        else:
            skipped.append(key)
    out.append(ProfileSection("unavailable", w.pair(_TITLES["unavailable"]), _unavailable_rows(w, skipped),
                              w.t("아래 정보는 이 화면에서 제공되지 않습니다.", "The items below are not provided in this view.")))
    return out


def display_name(profile, lang) -> str:
    """The stock's name for a header; in English never Hangul (falls back to the code)."""
    language = _language(lang)
    if language == "ko":
        return profile.name or profile.name_en or profile.instrument.code
    for candidate in (profile.name_en, profile.name):
        if candidate and not _HANGUL.search(candidate):
            return candidate
    return profile.instrument.code


def headline(profile, lang) -> ProfileRow:
    """One header row: name and code, last price with change, tone by the change's sign; provenance in the hint."""
    w = _Writer(profile, _language(lang))
    label = display_name(profile, w.lang)
    code = profile.instrument.symbol
    label = code if label == profile.instrument.code else label + " · " + code
    if profile.last_price is None:
        return ProfileRow(label, "—", None, w.reason("key_figures") if "key_figures" in profile.reasons else "")
    value, tone = w.price(profile.last_price), None
    if profile.change is not None:
        digits = w.price_digits()
        value += "  " + w.signed(profile.change, digits)
        tone = w.tone(profile.change, digits)
        if profile.change_pct is not None:
            value += " (" + w.signed(profile.change_pct, 2) + "%)"
    if profile.price_basis == "quote":
        hint = w.quote_hint()
    else:
        hint = w.history_hint(w.t(f"마지막 일봉 종가 {w.day(profile.as_of)}", f"Last daily close {w.day(profile.as_of)}"))
    return ProfileRow(label, value, tone, hint)
