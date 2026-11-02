"""Home watchlist: existing daily indicators plus explicit KIS quote snapshots.

No synthetic or cross-provider fallback is used. A quote receipt is not an
exchange observation time, so stock snapshots never claim a current trading
date or a live-stream state. This module does not fetch charts or subscribe to
WebSockets; those remain explicit actions in the market-chart screen.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from .markets import SPECS, load_markets


KR_STOCK_SPECS = (
    ("삼성전자", "005930", "Samsung Electronics"),
    ("SK하이닉스", "000660", "SK hynix"),
    ("현대차", "005380", "Hyundai Motor"),
    ("KB금융", "105560", "KB Financial Group"),
    ("LG에너지솔루션", "373220", "LG Energy Solution"),
    ("삼성바이오로직스", "207940", "Samsung Biologics"),
)


def _now():
    return datetime.now(timezone.utc)


def _blank_row(label, symbol, provider, unit, route, status, *, kind):
    return dict(label=label, symbol=symbol, provider=provider.upper(), unit=unit,
                route=route, kind=kind, value=None, change=None,
                absolute_change=None, volume=None, open=None, high=None, low=None,
                market_cap=None, market_cap_raw=None, market_cap_unit=None,
                observation_date=None, received_at=None, loaded_at=None,
                quote_time_kind=None, status=status, error_code=None,
                reason_code=None, license="NOT_VERIFIED")


def default_home_rows(status="NOT_LOADED"):
    """Return independent, data-free rows without constructing a provider."""
    rows = [_blank_row(label, symbol, provider, unit, route, status,
                       kind="market_indicator")
            for label, symbol, provider, unit, route in SPECS]
    for label, symbol, english in KR_STOCK_SPECS:
        row = _blank_row(label, symbol, "KIS", "KRW", "krx", status,
                         kind="domestic_stock")
        row["label_en"] = english
        rows.append(row)
    return rows


def _quote_client():
    from data.krx.kis_client import KISClient
    return KISClient()


def _number(value, *, optional=False, positive=False, nonnegative=False):
    if value is None and optional:
        return None
    if isinstance(value, bool):
        raise ValueError("Invalid quote number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0) or (nonnegative and result < 0):
        raise ValueError("Invalid quote number")
    return result


def _optional_price(value):
    # An unopened session can return zero for OHLC fields. Do not display those
    # placeholders as observed zero-valued prices or discard a valid last price.
    result = _number(value, optional=True, nonnegative=True)
    return result if result else None


def _receipt_time(value, now):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Quote receipt lacks a timezone")
    parsed = parsed.astimezone(timezone.utc)
    if parsed > now + timedelta(seconds=60):
        raise ValueError("Quote receipt is in the future")
    return parsed.isoformat()


def load_home_markets(*, loader=None, quote_client=None, today=None):
    """Read each of the six daily series and six configured KIS quotes once.

    ``loader`` follows ``load_markets``'s injected series-loader contract.
    ``quote_client`` provides ``ready`` and ``quote(code)`` like ``KISClient``.
    Missing KIS configuration leaves six explicit unavailable stock rows while
    retaining the independent indicator results. Provider exceptions are never
    surfaced verbatim because they can contain keys or credential-bearing URLs.
    """
    defaults = default_home_rows()
    indicators = load_markets(loader=loader, today=today)
    rows = []
    for default, observation in zip(defaults[:len(SPECS)], indicators):
        row = {**default, **observation}
        row["kind"] = "market_indicator"
        if row["status"] == "UNAVAILABLE":
            row["reason_code"] = ("invalid_response" if row.get("error_code") == "ValueError"
                                  else "provider_unavailable")
        rows.append(row)

    stocks = defaults[len(SPECS):]
    try:
        client = quote_client if quote_client is not None else _quote_client()
        ready = bool(client.ready)
    except Exception as exc:
        reason = "dependency_missing" if isinstance(exc, ImportError) else "provider_unavailable"
        for row in stocks:
            row.update(status="UNAVAILABLE", reason_code=reason,
                       error_code=type(exc).__name__, loaded_at=_now().isoformat())
        return rows + stocks

    if not ready:
        for row in stocks:
            row.update(status="UNAVAILABLE", reason_code="connection_not_configured",
                       loaded_at=_now().isoformat())
        return rows + stocks

    for row in stocks:
        try:
            quote = client.quote(row["symbol"])
            now = _now()
            if (str(quote.ticker) != row["symbol"] or str(quote.source).upper() != "KIS"
                    or str(quote.currency).upper() != "KRW"):
                raise ValueError("Unexpected instrument, provider or unit")
            values = dict(
                value=_number(quote.price, positive=True),
                change=_number(quote.change_pct, optional=True),
                absolute_change=_number(quote.change, optional=True),
                volume=_number(quote.volume, optional=True, nonnegative=True),
                open=_optional_price(quote.open), high=_optional_price(quote.high),
                low=_optional_price(quote.low),
                market_cap_raw=_number(quote.market_cap, optional=True, nonnegative=True),
                received_at=_receipt_time(quote.as_of, now),
            )
            # KISClient currently exposes raw hts_avls without a unit contract.
            # Keep it separate; a view must not label that raw number as KRW.
            row.update(**values, market_cap_unit="UNVERIFIED", status="SNAPSHOT",
                       quote_time_kind="receipt", loaded_at=now.isoformat())
        except Exception as exc:
            row.update(status="UNAVAILABLE", reason_code=("invalid_response"
                       if isinstance(exc, (ValueError, TypeError, AttributeError, OverflowError))
                       else "provider_unavailable"), error_code=type(exc).__name__,
                       loaded_at=_now().isoformat())
    return rows + stocks
