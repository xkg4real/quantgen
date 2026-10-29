"""Daily market observations for Home. Explicit providers; no synthetic fallback."""
from datetime import date, datetime, timezone
import math

SPECS = (
    ("S&P 500", "^GSPC", "yfinance", "pt", "macro"),
    ("KOSPI", "^KS11", "yfinance", "pt", "krx"),
    ("USD / KRW", "DEXKOUS", "fred", "KRW/USD", "fx"),
    ("미국 10년 금리", "DGS10", "fred", "%", "rates"),
    ("VIX", "VIXCLS", "fred", "pt", "macro"),
    ("Bitcoin", "BTC-USD", "yfinance", "USD", "crypto"),
)


def load_markets(*, loader=None, today=None):
    if loader is None:
        from core.ficc.data import load_series
        loader = load_series
    today = today or datetime.now(timezone.utc).date()
    rows = []
    for label, symbol, provider, unit, route in SPECS:
        row = dict(label=label, symbol=symbol, provider=provider.upper(), unit=unit, route=route,
                   value=None, change=None, observation_date=None, status="UNAVAILABLE", error_code=None,
                   loaded_at=datetime.now(timezone.utc).isoformat(), license="NOT_VERIFIED")
        try:
            series = loader(symbol, source=provider, days=30)
            if series.source.upper() != provider.upper(): raise ValueError("Unexpected provider/fallback")
            values, dates = list(series.values), list(series.dates)
            if len(values) != len(dates) or len(values) < 2 or dates != sorted(set(dates)):
                raise ValueError("Missing or unordered observations")
            if not all(math.isfinite(float(x)) for x in values[-2:]): raise ValueError("Non-finite observation")
            age = (today - date.fromisoformat(dates[-1])).days
            if age < 0: raise ValueError("Future observation")
            value, previous = map(float, values[-2:][::-1])
            delta = ((value - previous) * 100 if unit == "%" else
                     (value / previous - 1) * 100 if previous != 0 else None)
            row.update(value=value, change=delta, observation_date=dates[-1], status="STALE" if age > 7 else "OBSERVED")
        except Exception as exc:
            row["error_code"] = type(exc).__name__  # never expose credential-bearing URLs/messages
        rows.append(row)
    return rows
