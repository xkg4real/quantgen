"""US market capitalisation for the Markets ranked lists (owner 2026-11-11: "아니 미국 시총 자료 찾으세요").

First choice is KIS: when KIS is configured, the ranking's KIS batch reads each US stock's overseas
``price-detail`` market cap (allowlisted with the owner's approval, 2026-11-11 "승인."; see
`quantgen_desktop.market_rankings.kis_batch` and `rankings.parse_kis_overseas_detail`). This step keeps
those figures and fills the stocks still without one from two providers the app already uses, in order:

1. FMP, when FMP_API_KEY is set: ONE `/stable/batch-quote` request for the whole US universe, `marketCap` as
   FMP states it (basis 'provider'), kept `PROVIDER_TTL_SECONDS`. A plan without batch quotes refuses it
   (HTTP 402, see data/fmp/quote_client.py); that is remembered for `PLAN_RETRY_SECONDS` and the Yahoo path
   answers. One FMP request per stock is deliberately not used: about 55 a refresh would spend a free
   plan's daily quota (250) within the hour, and the engine's quote path shares that quota.
2. Yahoo Finance through yfinance (keyless; the provider of the delayed daily bars): each stock's share
   count from Yahoo's share-count series (`Ticker.get_shares_full`, the call behind `fast_info.shares`),
   kept `SHARES_TTL_SECONDS` (24 h) in memory and as `SHARES_YFINANCE_<SYMBOL>.json` in the history cache
   directory (`config.ficc_cache_dir()`, as `core.quant.history` keeps its HIST_* files; never the
   repository). Market cap = shares x the row's own price (the KIS last price when KIS answered, else the
   daily close), basis 'computed'. At most `WORKERS` requests run at once and the whole step waits at most
   `DEADLINE_SECONDS`; an answer that arrives later is still cached for the next refresh. A stock that
   failed is not asked again for `FAILURE_RETRY_SECONDS`.

A stock without a figure keeps none (shown as '—'); nothing is estimated, carried over or made up. ADRs get
no computed figure (`rankings.ADR_CODES`). Called on the ranking worker thread, never on the UI thread;
nothing is read or fetched on import.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import threading
import time

from core.market import rankings as R

DAY = 86400.0
SHARES_TTL_SECONDS = DAY          # a share count changes with filings, not with prices
PROVIDER_TTL_SECONDS = 300.0      # one FMP batch request at most every five minutes
PLAN_RETRY_SECONDS = DAY          # a plan refusal is a subscription fact, not an outage
FMP_RETRY_SECONDS = 1800.0        # after any other FMP failure
FAILURE_RETRY_SECONDS = 1800.0    # a Yahoo symbol that failed is not asked again before this
WORKERS = 4
DEADLINE_SECONDS = 20.0
SHARES_WINDOW_DAYS = 548          # as yfinance's fast_info.shares: long enough to hold the latest filing
FMP_SOURCE, YAHOO_SOURCE = "FMP", "Yahoo Finance"


def fmp_symbol(member):
    return member.code.replace(".", "-")


def yahoo_symbol(member):
    from core.market.routing import yahoo_symbols
    symbols = yahoo_symbols(member.instrument)
    return symbols[0] if symbols else member.code


# Providers ----------------------------------------------------------------------------------------
def fmp_batch(symbols, *, key, base_url=None, timeout=None, get=None):
    """{SYMBOL: (market cap, stated at UTC ISO)} from one FMP `/stable/batch-quote` request.

    Raises `FMPPlanError` when the plan refuses batch quotes (HTTP 402/403) and `FMPError` otherwise; the
    key never appears in an error.
    """
    import config
    from data.fmp.quote_client import FMPError, FMPPlanError, FMPQuoteClient, _redact
    if get is None:
        import requests
        get = requests.get
    url = f"{(base_url or config.FMP_BASE_URL).rstrip('/')}/batch-quote"
    try:
        response = get(url, params={"symbols": ",".join(symbols), "apikey": key},
                       timeout=timeout or config.HTTP_TIMEOUT_SECONDS)
    except Exception as exc:
        raise FMPError(f"{type(exc).__name__}: {_redact(str(exc), key)}") from None
    status = int(getattr(response, "status_code", 0) or 0)
    if status in (402, 403):
        raise FMPPlanError(f"The FMP plan does not cover batch quotes (HTTP {status}).")
    if status >= 400 or status == 0:
        raise FMPError(f"FMP answered HTTP {status}.")
    try:
        payload = response.json()
    except Exception:
        raise FMPError("FMP returned a non-JSON body.") from None
    if isinstance(payload, dict):
        message = str(payload.get("Error Message") or payload.get("message") or "")
        if re.search(r"(?i)restricted|premium|subscription|upgrade", message):
            raise FMPPlanError("The FMP plan does not cover batch quotes.")
        raise FMPError(f"FMP: {_redact(message[:160], key)}")
    if not isinstance(payload, list):
        raise FMPError("FMP returned an unexpected payload shape.")
    out = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        quote = FMPQuoteClient._to_quote(row)
        cap = quote.market_cap
        if quote.symbol and cap is not None and math.isfinite(cap) and cap > 0:
            out[quote.symbol.upper()] = (float(cap), quote.as_of)
    return out


def latest_shares(series):
    """The newest positive share count of a yfinance share series (or one-column frame) and its date."""
    if series is None:
        return None
    if hasattr(series, "columns"):
        if len(series.columns) == 0:
            return None
        series = series[series.columns[0]]
    try:
        items = sorted(series.items(), key=lambda item: item[0])
    except Exception:
        return None
    for stamp, value in reversed(items):
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and number > 0:
            day = stamp.date().isoformat() if hasattr(stamp, "date") else str(stamp)[:10]
            return number, day
    return None


def yahoo_shares(symbol):
    """(shares, date) from Yahoo's share-count series through the FICC module's yfinance handle; None
    when Yahoo has none. yfinance hides request errors by default, so an unreachable Yahoo also gives None."""
    from core.ficc import data
    if data._yf is None:
        raise ModuleNotFoundError("yfinance is not installed")
    start = (datetime.now(timezone.utc).date() - timedelta(days=SHARES_WINDOW_DAYS)).isoformat()
    return latest_shares(data._yf.Ticker(symbol).get_shares_full(start=start))


def _yahoo_installed():
    from core.ficc import data
    return data._yf is not None


def _default_directory():
    """The history cache directory; None (memory only) when that cache is switched off."""
    import config
    if float(config.FICC_CACHE_TTL_SECONDS) <= 0:
        return None
    return config.ficc_cache_dir()


# Cache --------------------------------------------------------------------------------------------
class SharesCache:
    """Share counts per Yahoo symbol, `ttl` seconds: memory, plus one JSON file each in `directory`
    (a path, a callable returning one, or None for memory only). A file that cannot be read or written
    is simply not used."""

    def __init__(self, directory=None, *, ttl=SHARES_TTL_SECONDS, clock=time.time):
        self._directory, self.ttl, self.clock = directory, float(ttl), clock
        self._memory = {}
        self._lock = threading.Lock()

    def path(self, symbol):
        folder = self._directory() if callable(self._directory) else self._directory
        if not folder:
            return None
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", f"SHARES_YFINANCE_{symbol.upper()}")
        return Path(folder) / f"{name}.json"

    def get(self, symbol):
        """(shares, date) stored less than `ttl` seconds ago, or None."""
        key = symbol.upper()
        with self._lock:
            hit = self._memory.get(key)
        if hit is None:
            try:
                payload = json.loads(self.path(key).read_text("utf-8"))
                hit = (float(payload["ts"]), float(payload["shares"]), str(payload["as_of"]))
            except Exception:
                return None
        stored, shares, day = hit
        if not (0 <= self.clock() - stored < self.ttl and math.isfinite(shares) and shares > 0):
            return None
        with self._lock:
            self._memory[key] = hit
        return shares, day

    def put(self, symbol, shares, day):
        key = symbol.upper()
        hit = (float(self.clock()), float(shares), str(day))
        with self._lock:
            self._memory[key] = hit
        try:
            path = self.path(key)
            if path is None:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"ts": hit[0], "symbol": key, "shares": hit[1], "as_of": hit[2],
                                        "source": YAHOO_SOURCE}), "utf-8")
        except Exception:
            pass  # a cache that cannot be written is not an error


# The step -----------------------------------------------------------------------------------------
class MarketCapSource:
    """Adds market caps to a US `rankings.Batch`: a figure already in the batch (KIS price-detail) is kept;
    the rest get FMP's stated figure, else Yahoo shares x the row price.

    Every provider is injectable: `fmp_key()` (default `config.fmp_key`), `fmp_fetch(symbols, key=...)`,
    `yahoo_fetch(symbol) -> (shares, date) | None` and `cache` (a `SharesCache`).
    """

    def __init__(self, *, fmp_key=None, fmp_fetch=None, yahoo_fetch=None, yahoo_ready=None, cache=None,
                 clock=time.time, workers=WORKERS, deadline=DEADLINE_SECONDS):
        if fmp_key is None:
            import config
            fmp_key = config.fmp_key
        self._fmp_key, self._fmp_fetch = fmp_key, fmp_fetch or fmp_batch
        self._yahoo_fetch = yahoo_fetch or yahoo_shares
        self._yahoo_ready = yahoo_ready or ((lambda: True) if yahoo_fetch is not None else _yahoo_installed)
        self.cache = cache if cache is not None else SharesCache(_default_directory, clock=clock)
        self.clock, self.workers, self.deadline = clock, max(1, min(WORKERS, int(workers))), float(deadline)
        self._lock = threading.Lock()
        self._fmp = None              # (fetched at, {SYMBOL: (cap, stated at)}, symbols asked)
        self._fmp_skip = (0.0, "")    # (until, reason) after a refusal or a failure
        self._failed = {}             # Yahoo symbol -> (when, reason)
        self._inflight = set()        # Yahoo symbols a worker (maybe from an earlier refresh) is fetching

    def __call__(self, batch, *, cancelled=None, progress=None):
        if batch.group != "us" or not batch.records:
            return batch
        records, reasons, out = list(batch.records), [], {}
        for index, record in enumerate(records):
            if record.cap_basis and record.market_cap:  # stated in the quote batch (KIS price-detail)
                out[index] = record
        if not any(r.cap_source == "KIS" for r in out.values()):
            reasons.append("kis_none" if batch.mode == "kis" or batch.fallback else "kis_off")
        rest = [index for index in range(len(records)) if index not in out]
        if not rest:
            return replace(batch, caps="ok", cap_reasons=())
        provider = self._provider([fmp_symbol(records[index].member) for index in rest], reasons)
        pending = []
        for index in rest:
            record = records[index]
            stated = provider.get(fmp_symbol(record.member).upper())
            if stated is not None:
                out[index] = R.with_cap(record, stated[0], basis="provider", source=FMP_SOURCE, as_of=stated[1])
            elif record.member.code in R.ADR_CODES:
                out[index] = R.without_cap(record, "adr")
            else:
                pending.append(index)
        outcomes = self._computed(records, pending, out, cancelled, progress) if pending else []
        final = tuple(out.get(index, record) for index, record in enumerate(records))
        if any(r.market_cap for r in final):
            return replace(batch, records=final, caps="ok", cap_reasons=tuple(reasons))
        if pending:
            reasons.append(self._yahoo_reason(outcomes))
        return replace(batch, records=final, caps="none", cap_reasons=tuple(r for r in reasons if r))

    # FMP ----------------------------------------------------------------------------------------
    def _provider(self, symbols, reasons):
        key = self._fmp_key()
        if not key:
            reasons.append("fmp_no_key")
            return {}
        now = self.clock()
        with self._lock:
            cached, (until, why) = self._fmp, self._fmp_skip
        if cached is not None and 0 <= now - cached[0] < PROVIDER_TTL_SECONDS and set(symbols) <= cached[2]:
            return cached[1]
        if now < until:
            reasons.append(why)
            return {}
        from data.fmp.quote_client import FMPPlanError
        try:
            stated = self._fmp_fetch(symbols, key=key)
        except FMPPlanError:
            stated, why, wait_for = None, "fmp_plan", PLAN_RETRY_SECONDS
        except Exception:  # the class is all that is kept; provider text may carry the key in a URL
            stated, why, wait_for = None, "fmp_failed", FMP_RETRY_SECONDS
        else:
            why, wait_for = "fmp_failed", FMP_RETRY_SECONDS
        if not stated:
            with self._lock:
                self._fmp_skip = (now + wait_for, why)
            reasons.append(why)
            return {}
        stated = {str(k).upper(): v for k, v in stated.items()}
        with self._lock:
            self._fmp, self._fmp_skip = (now, stated, frozenset(symbols)), (0.0, "")
        return stated

    # Yahoo --------------------------------------------------------------------------------------
    def _computed(self, records, pending, out, cancelled, progress):
        """Fills `out` for `pending` rows from cached or fetched share counts; returns the Yahoo outcomes."""
        if not self._yahoo_ready():
            for index in pending:
                out[index] = R.without_cap(records[index], "error")
            return ["missing"]
        now, outcomes, wanted = self.clock(), [], {}
        for index in pending:
            symbol = yahoo_symbol(records[index].member)
            hit = self.cache.get(symbol)
            if hit is not None:
                out[index] = self._cap(records[index], hit)
                outcomes.append("ok")
                continue
            with self._lock:
                failed, busy = self._failed.get(symbol), symbol in self._inflight
            if failed is not None and 0 <= now - failed[0] < FAILURE_RETRY_SECONDS:
                out[index] = R.without_cap(records[index], failed[1])
                outcomes.append(failed[1])
            elif busy:
                out[index] = R.without_cap(records[index], "timeout")
                outcomes.append("timeout")
            else:
                wanted.setdefault(symbol, []).append(index)
        if not wanted:
            return outcomes
        answers = self._fetch(list(wanted), cancelled, progress)
        for symbol, indexes in wanted.items():
            answer = answers.get(symbol, ("timeout",))
            outcomes.append(answer[0])
            for index in indexes:
                out[index] = (self._cap(records[index], answer[1:]) if answer[0] == "ok"
                              else R.without_cap(records[index], answer[0]))
        return outcomes

    @staticmethod
    def _cap(record, hit):
        shares, day = hit
        try:
            return R.computed_cap(record, shares, source=YAHOO_SOURCE, as_of=day)
        except ValueError:
            return R.without_cap(record, "no_shares")

    def _one(self, symbol):
        """One share count; never raises. Caches and remembers its own result, even after the deadline."""
        try:
            try:
                got = self._yahoo_fetch(symbol)
                shares, day = got if got is not None else (None, "")
            except Exception:
                answer = ("error",)
            else:
                if isinstance(shares, (int, float)) and math.isfinite(shares) and shares > 0:
                    self.cache.put(symbol, float(shares), day)
                    answer = ("ok", float(shares), str(day))
                else:
                    answer = ("no_shares",)
            with self._lock:
                if answer[0] == "ok":
                    self._failed.pop(symbol, None)
                else:
                    self._failed[symbol] = (self.clock(), answer[0])
            return answer
        finally:
            with self._lock:
                self._inflight.discard(symbol)

    def _fetch(self, symbols, cancelled, progress):
        answers = {}
        with self._lock:
            self._inflight.update(symbols)
        pool = ThreadPoolExecutor(max_workers=min(self.workers, len(symbols)), thread_name_prefix="qg-market-cap")
        futures = {pool.submit(self._one, symbol): symbol for symbol in symbols}
        left, end, done = set(futures), time.monotonic() + self.deadline, 0
        try:
            while left and not (cancelled is not None and cancelled()):
                remaining = end - time.monotonic()
                if remaining <= 0:
                    break
                finished, left = wait(left, timeout=min(remaining, 0.25), return_when=FIRST_COMPLETED)
                for future in finished:
                    answers[futures[future]] = future.result()
                    done += 1
                    if progress is not None:
                        progress(done, len(symbols))
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
            with self._lock:
                for future in left:
                    if future.cancelled():
                        self._inflight.discard(futures[future])
        return answers

    @staticmethod
    def _yahoo_reason(outcomes):
        tried = [o for o in outcomes if o != "adr"]
        if "missing" in tried:
            return "yahoo_missing"
        if tried and all(o == "error" for o in tried):
            return "yahoo_unreachable"
        if "timeout" in tried:
            return "yahoo_timeout"
        return "yahoo_empty" if tried else ""


__all__ = ["MarketCapSource", "SharesCache", "fmp_batch", "yahoo_shares", "latest_shares", "fmp_symbol",
           "yahoo_symbol", "SHARES_TTL_SECONDS", "PROVIDER_TTL_SECONDS", "PLAN_RETRY_SECONDS", "FMP_RETRY_SECONDS",
           "FAILURE_RETRY_SECONDS", "WORKERS", "DEADLINE_SECONDS", "FMP_SOURCE", "YAHOO_SOURCE"]
