"""Daily market observations for Home. Explicit providers; no synthetic fallback."""
from datetime import date, datetime, timezone
import math
import re

SPECS = (
    ("S&P 500", "^GSPC", "yfinance", "pt", "macro"),
    ("KOSPI", "^KS11", "yfinance", "pt", "krx"),
    ("USD / KRW", "DEXKOUS", "fred", "KRW/USD", "fx"),
    ("미국 10년 금리", "DGS10", "fred", "%", "rates"),
    ("VIX", "VIXCLS", "fred", "pt", "macro"),
    ("Bitcoin", "BTC-USD", "yfinance", "USD", "crypto"),
)


# Only these authored codes may cross the provider/UI boundary. In particular,
# neither URLs nor exception messages are public diagnostics.
FAILURE_REASONS = frozenset({
    "dependency_missing", "dependency_incompatible", "connection_not_configured",
    "rate_limited", "network_timeout", "network_error", "certificate_error",
    "access_denied", "no_observations", "insufficient_observations",
    "invalid_response", "provider_unavailable",
})


class MarketDataUnavailable(ValueError):
    """A local observation check failed with an authored, non-secret reason."""

    def __init__(self, reason_code):
        self.reason_code = reason_code if reason_code in FAILURE_REASONS else "invalid_response"
        super().__init__(self.reason_code)


def provider_failure_reason(exc):
    """Classify established failure evidence without exposing provider text.

    FICC wraps upstream exceptions in FICCError, and KIS wraps transport errors
    in KISError. Recognize their retained class names/status codes, not arbitrary
    prose. A Yahoo download with an empty frame remains ``no_observations``:
    that response alone does not establish rate limiting or a network failure.
    """
    declared = getattr(exc, "reason_code", None)
    if isinstance(declared, str) and declared in FAILURE_REASONS:
        return declared
    name = type(exc).__name__
    if isinstance(exc, ImportError):
        return "dependency_missing"
    if name == "KISUnavailable":
        return "connection_not_configured"
    # Inspect a bounded copy locally; the text itself is never returned/stored.
    evidence = name + ": " + str(exc)[:1500]
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    http = re.search(r"\bHTTP(?:Error)?(?:\s+|:\s*)(\d{3})\b", evidence)
    if status is None and http:
        status = int(http.group(1))
    if status == 429 or re.search(r"\b(?:YFRateLimitError|EGW00201)\b", evidence):
        return "rate_limited"
    if status in (401, 403):
        return "access_denied"
    if re.search(r"\b(?:ModuleNotFoundError|ImportError)\b", evidence) or any(text in evidence for text in (
            "yfinance is not installed", "Neither pandas_datareader nor requests is installed",
            "requests library unavailable")):
        return "dependency_missing"
    if re.search(r"\b(?:download|history)\(\) got an unexpected keyword argument\b", evidence):
        return "dependency_incompatible"
    if re.search(r"\b(?:SSLError|SSLCertVerificationError|CERTIFICATE_VERIFY_FAILED)\b", evidence):
        return "certificate_error"
    if re.search(r"\b(?:ReadTimeout|ConnectTimeout|TimeoutError|Timeout)\b", evidence):
        return "network_timeout"
    if re.search(r"\b(?:ConnectionError|ConnectionRefusedError|ConnectError|ProxyError|gaierror)\b", evidence):
        return "network_error"
    missing = re.search(r"\b(?:YFINANCE|FRED) returned only (\d+) observations\b", evidence)
    if missing:
        return "no_observations" if int(missing.group(1)) == 0 else "insufficient_observations"
    if isinstance(exc, (ValueError, TypeError, AttributeError, OverflowError)):
        return "invalid_response"
    return "provider_unavailable"


def load_markets(*, loader=None, today=None):
    if loader is None:
        from core.ficc.data import load_series
        loader = load_series
    today = today or datetime.now(timezone.utc).date()
    rows = []
    for label, symbol, provider, unit, route in SPECS:
        row = dict(label=label, symbol=symbol, provider=provider.upper(), unit=unit, route=route,
                   value=None, change=None, observation_date=None, status="UNAVAILABLE", error_code=None,
                   reason_code=None, loaded_at=datetime.now(timezone.utc).isoformat(), license="NOT_VERIFIED")
        try:
            series = loader(symbol, source=provider, days=30)
            if series.source.upper() != provider.upper(): raise ValueError("Unexpected provider/fallback")
            values, dates = list(series.values), list(series.dates)
            if len(values) != len(dates) or dates != sorted(set(dates)):
                raise ValueError("Missing or unordered observations")
            if len(values) < 2:
                raise MarketDataUnavailable("no_observations" if not values else "insufficient_observations")
            if not all(math.isfinite(float(x)) for x in values[-2:]): raise ValueError("Non-finite observation")
            age = (today - date.fromisoformat(dates[-1])).days
            if age < 0: raise ValueError("Future observation")
            value, previous = map(float, values[-2:][::-1])
            delta = ((value - previous) * 100 if unit == "%" else
                     (value / previous - 1) * 100 if previous != 0 else None)
            if delta is not None and not math.isfinite(delta):
                raise ValueError("Non-finite change")
            row.update(value=value, change=delta, observation_date=dates[-1], status="STALE" if age > 7 else "OBSERVED")
        except Exception as exc:
            row["error_code"] = type(exc).__name__  # never expose credential-bearing URLs/messages
            row["reason_code"] = provider_failure_reason(exc)
        rows.append(row)
    return rows
