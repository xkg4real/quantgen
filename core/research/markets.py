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
        from core import gateway
        loader = gateway.ficc().load_series
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


# --------------------------------------------------------------------------------------------------------------
# DS-H: the six Home indicators with history, display rights and live values (owner D8, 2026-11-17)
# --------------------------------------------------------------------------------------------------------------
# One call for the six daily series (the FICC loader groups them: one Yahoo download, one FRED request),
# a history per row for the chart, the display-rights outcome per row (core/research/display_rights.json),
# and live values only where D8 allows them: Bitcoin from Upbit (keyless, KRW quote, so a separate field
# with its own unit; the daily BTC-USD series stays Yahoo/USD) and KOSPI from KIS when the user's KIS key
# is set. Every provider is reached through core.gateway (KEY-4). Nothing synthetic is ever shown: a
# series the loader had to simulate is UNAVAILABLE with a reason code.

HOME_DELAY = {"yfinance": "delayed_daily", "fred": "daily"}
LIVE_SPECS = {"^KS11": ("kis_quote", "KIS", "pt", "kis_krx"), "BTC-USD": ("crypto_public", "UPBIT", "KRW", "Upbit")}


class _ProviderNote(Exception):
    """Carries a loader's fallback note to provider_failure_reason locally; never returned."""


class _Handled(Exception):
    """Internal: the row's reason is already set."""


def _note_reason(note):
    if "off in profile" in note or "company route" in note:
        return "connection_not_configured"
    return provider_failure_reason(_ProviderNote(note))


def _home_rights():
    from core.research.display_rights import display_rights
    record = display_rights()
    policies = record.get("policies", {})
    by_series = {}
    for item in record.get("home", []):
        policy = item.get("policy")
        by_series[item.get("series_id")] = {
            "source": item.get("source"), "policy": policy,
            "outcome": item.get("outcome") or policies.get(policy, {}).get("outcome", "unknown"),
        }
    authorized = bool(record.get("publication_authorization"))
    return by_series, {k: v.get("outcome", "unknown") for k, v in policies.items()}, authorized


def _default_series_loader(ids, *, source, days):
    from core import gateway
    return gateway.ficc().load_many(ids, source=source, days=days)


def _default_btc_live():
    from core import gateway
    cc = gateway.provider("data.crypto.crypto_client", source="crypto_public")
    rows = cc.UpbitPublic().ticker("KRW-BTC")
    if not rows:
        raise MarketDataUnavailable("no_observations")
    r = rows[0]
    return {"value": r.get("price"), "change_pct": r.get("change_pct"), "as_of": r.get("as_of")}


def _default_kospi_live():
    from core import gateway
    kis_client = gateway.provider("data.krx.kis_client")
    if kis_client.requests is None:
        raise ImportError("KIS transport library unavailable")
    r = kis_client.KISClient().index("KOSPI")
    return {"value": r.get("level"), "change_pct": r.get("change_pct"), "as_of": r.get("as_of")}


def _default_kis_ready():
    from core import gateway
    return gateway.keys_ready("kis_quote")


def _live_value(symbol, fetch, policies, kis_ready):
    source_id, provider, unit, policy = LIVE_SPECS[symbol]
    live = {"source": provider, "unit": unit, "value": None, "change_pct": None, "as_of": None,
            "status": "UNAVAILABLE", "reason_code": None, "display_outcome": policies.get(policy, "unknown")}
    if source_id == "kis_quote" and not kis_ready():
        live.update(status="KEY_NEEDED", reason_code="connection_not_configured")
        return live
    try:
        got = fetch()
        value = float(got["value"]) if got.get("value") is not None else None
        if value is None or not math.isfinite(value) or value <= 0:
            raise MarketDataUnavailable("invalid_response")
        change = got.get("change_pct")
        change = float(change) if change is not None else None
        if change is not None and not math.isfinite(change):
            change = None
        live.update(value=value, change_pct=change, as_of=got.get("as_of"), status="LIVE")
    except Exception as exc:  # reason code only; provider text never leaves
        live["reason_code"] = provider_failure_reason(exc)
    return live


def load_home_indicators(days=30, *, series_loader=None, btc_live=None, kospi_live=None, kis_ready=None,
                         live=True, today=None):
    """Six rows (SPECS order), each with value/change/status like ``load_markets`` plus ``history``
    ([{"date", "value"}], oldest first, at most ``days`` points), ``delay``, ``display`` (display-rights
    outcome) and ``live`` (None for rows without a live feed). One series-loader call for all six.

    All providers are injectable for tests: ``series_loader(ids, source=, days=)`` returns {id: Series},
    ``btc_live()``/``kospi_live()`` return {"value", "change_pct", "as_of"}, ``kis_ready()`` -> bool.
    """
    days = max(int(days), 5)                      # the FICC loader refuses fewer than five observations
    series_loader = series_loader or _default_series_loader
    kis_ready = kis_ready or _default_kis_ready
    fetchers = {"^KS11": kospi_live or _default_kospi_live, "BTC-USD": btc_live or _default_btc_live}
    today = today or datetime.now(timezone.utc).date()
    rights, policies, authorized = _home_rights()
    loaded_at = datetime.now(timezone.utc).isoformat()

    batch, batch_error = {}, None
    try:
        batch = series_loader([spec[1] for spec in SPECS], source="auto", days=days) or {}
    except Exception as exc:
        batch_error = exc

    rows = []
    for label, symbol, provider, unit, route in SPECS:
        right = rights.get(symbol, {"source": None, "policy": None, "outcome": "unknown"})
        row = dict(label=label, symbol=symbol, provider=provider.upper(), unit=unit, route=route,
                   value=None, change=None, observation_date=None, status="UNAVAILABLE", error_code=None,
                   reason_code=None, loaded_at=loaded_at, license="NOT_VERIFIED", history=[],
                   delay=HOME_DELAY[provider],
                   display=dict(right, publication_authorization=authorized), live=None)
        try:
            if batch_error is not None:
                raise batch_error
            series = batch.get(symbol)
            if series is None:
                raise MarketDataUnavailable("invalid_response")
            if series.source.upper() != provider.upper():
                note = getattr(series, "note", "") or ""
                row["error_code"] = "ProviderFallback"
                row["reason_code"] = _note_reason(note) if note else "provider_unavailable"
                raise _Handled()
            values, dates = list(series.values), list(series.dates)
            if len(values) != len(dates) or dates != sorted(set(dates)):
                raise ValueError("Missing or unordered observations")
            points = [(d, float(v)) for d, v in zip(dates, values) if v is not None and math.isfinite(float(v))]
            if len(points) < 2:
                raise MarketDataUnavailable("no_observations" if not points else "insufficient_observations")
            last_date = points[-1][0]
            age = (today - date.fromisoformat(last_date)).days
            if age < 0:
                raise ValueError("Future observation")
            value, previous = points[-1][1], points[-2][1]
            delta = ((value - previous) * 100 if unit == "%" else
                     (value / previous - 1) * 100 if previous != 0 else None)
            if delta is not None and not math.isfinite(delta):
                raise ValueError("Non-finite change")
            row.update(value=value, change=delta, observation_date=last_date,
                       status="STALE" if age > 7 else "OBSERVED",
                       history=[{"date": d, "value": v} for d, v in points[-days:]])
        except _Handled:
            pass
        except Exception as exc:
            row["error_code"] = type(exc).__name__
            row["reason_code"] = provider_failure_reason(exc)
        if live and symbol in LIVE_SPECS:
            row["live"] = _live_value(symbol, fetchers[symbol], policies, kis_ready)
        rows.append(row)
    return rows

