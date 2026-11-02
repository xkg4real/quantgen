"""Read-only KIS quotation WebSocket with bounded, cancellable reconnects.

The browser and desktop consume the same immutable ``MarketTick`` values.
App keys and the 24-hour approval key stay in this server-side module. Only
quotation TRs are subscribable; encrypted account/order notifications are never
requested or decoded. Schemas follow the user-supplied KIS real-time workbooks.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
import re
import threading
import time
from typing import Callable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import config
from core.market.models import Instrument, MarketTick
from data.krx.kis_client import KISClient, KISError, KISUnavailable

try:
    import requests as _requests
    from websockets.sync.client import connect as _connect
except ImportError:  # Explicitly report an incomplete installation at start.
    _requests = _connect = None

_KST = ZoneInfo("Asia/Seoul")
_STOCK_ZONES = {
    "NAS": "America/New_York", "NYS": "America/New_York", "AMS": "America/New_York",
    "HKS": "Asia/Hong_Kong", "TSE": "Asia/Tokyo", "SHS": "Asia/Shanghai",
    "SZS": "Asia/Shanghai", "HSX": "Asia/Ho_Chi_Minh", "HNX": "Asia/Ho_Chi_Minh",
}
_APPROVAL_LOCK = threading.Lock()
_APPROVAL_CACHE: dict[tuple[str, str], tuple[str, float]] = {}
_MAX_FAILURES = 5


@dataclass(frozen=True)
class Subscription:
    tr_id: str
    tr_key: str
    widths: tuple[int, ...]
    price: int
    volume: int
    cumulative_volume: int
    change: int
    change_pct: int
    sign: int


def subscription_for(instrument: Instrument, *, paper: bool = False) -> Subscription:
    """Resolve only documented quotation channels; validate before any I/O.

    ``domestic_future.exchange`` can explicitly select F (index future), CF
    (commodity future), JF (stock future), O (index option) or JO (stock option).
    A blank market can safely infer only the documented index product codes.
    """
    if paper and instrument.asset != "domestic_stock":
        raise ValueError("KIS paper WebSocket supports domestic stocks only")
    if instrument.asset == "domestic_stock":
        return Subscription("H0STCNT0", instrument.code, (46, 47), 2, 12, 13, 4, 5, 3)
    if instrument.asset == "overseas_stock":
        return Subscription("HDFSCNT0", "D" + instrument.exchange + instrument.code,
                            (26,), 11, 19, 20, 13, 14, 12)
    if instrument.asset == "bond":
        if not re.fullmatch(r"KR[A-Z0-9]{10}", instrument.code):
            raise ValueError("Use a 12-character Korean bond ISIN")
        return Subscription("H0BJCNT0", instrument.code, (19,), 6, 7, 16, 4, 5, 3)
    if instrument.asset == "domestic_future":
        market = instrument.exchange
        if not market and instrument.code[1:3] in ("01", "05", "06", "07"):
            market = "F"
        schema = {
            "F": ("H0IFCNT0", 50, 5, 2, 4),
            "CF": ("H0CFCNT0", 50, 5, 2, 4),
            "JF": ("H0ZFCNT0", 49, 2, 4, 5),
            "O": ("H0IOCNT0", 58, 2, 4, 5),
            "JO": ("H0ZOCNT0", 53, 2, 4, 5),
        }.get(market)
        if schema is None:
            raise ValueError("Select domestic derivative market F, CF, JF, O or JO for WebSocket")
        tr_id, width, price, change, rate = schema
        return Subscription(tr_id, instrument.code, (width,), price, 9, 10, change, rate, 3)
    raise ValueError("Overseas futures WebSocket requires verified master price scaling and timestamp timezone")


def _number(value: str, *, nonnegative: bool = False) -> float | None:
    try:
        number = float(value.strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or (nonnegative and number < 0):
        return None
    return number


def _signed(value: str, sign: str) -> float | None:
    number = _number(value)
    if number is None:
        return None
    if sign in ("4", "5"):
        return -abs(number)
    if sign in ("1", "2"):
        return abs(number)
    return number


def _timestamp(day: str, clock: str, zone: ZoneInfo) -> datetime:
    if not re.fullmatch(r"\d{6}", clock):
        raise ValueError("Invalid trade time")
    if re.fullmatch(r"\d{8}", day):
        value = datetime.strptime(day + clock, "%Y%m%d%H%M%S")
    elif re.fullmatch(r"\d{6}", day):
        value = datetime.strptime(day + clock, "%y%m%d%H%M%S")
    else:
        raise ValueError("Invalid trade date")
    return value.replace(tzinfo=zone)


def _domestic_time(clock: str, now: datetime) -> datetime:
    # Day-session derivative and bond payloads omit a date. Resolve their clock
    # against receipt in Korea, including a midnight rollover. No night-session
    # TR is subscribed here, since its business-date convention differs.
    current = now.astimezone(_KST)
    value = _timestamp(current.strftime("%Y%m%d"), clock, _KST)
    if value - current > timedelta(minutes=5):
        value -= timedelta(days=1)
    return value


def parse_ticks(message: str | bytes, instrument: Instrument, *,
                now: datetime | None = None) -> tuple[MarketTick, ...]:
    """Decode and validate complete batches without guessing a record width.

    The domestic stock sheet has 47 fields while its older sample has 46;
    each batch must have one consistent supported width. Malformed, encrypted,
    unrelated and non-finite data yields no ticks and cannot move a chart.
    """
    spec = subscription_for(instrument)
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError:
            return ()
    if not isinstance(message, str) or len(message) > 524288:
        return ()
    frame = message.split("|", 3)
    if len(frame) != 4 or frame[0] != "0" or frame[1] != spec.tr_id:
        return ()
    try:
        count = int(frame[2])
    except ValueError:
        return ()
    if not 1 <= count <= 1000:
        return ()
    fields = frame[3].split("^")
    if len(fields) % count or len(fields) // count not in spec.widths:
        return ()
    width = len(fields) // count
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Tick receipt clock must have a timezone")
    received = current.isoformat(timespec="milliseconds")
    ticks = []
    for offset in range(0, len(fields), width):
        row = fields[offset:offset + width]
        if instrument.asset == "overseas_stock":
            if row[0] != spec.tr_key or row[1] != instrument.code:
                continue
        elif row[0] != instrument.code:
            continue
        price = _number(row[spec.price])
        if price is None or price <= 0:
            continue
        volume = _number(row[spec.volume], nonnegative=True)
        cumulative = _number(row[spec.cumulative_volume], nonnegative=True)
        # Every supported quotation schema requires both execution and session
        # volume. Without the session total replayed trades cannot be deduped.
        # Do not reinterpret a blank as zero or present such a row as a trade.
        if volume is None or cumulative is None:
            continue
        try:
            if instrument.asset == "domestic_stock":
                stamp = _timestamp(row[33], row[1], _KST)
                # Expected-price/VI frames are distinct from actual executions.
                if row[43] not in ("", "0"):
                    continue
            elif instrument.asset == "overseas_stock":
                stamp = _timestamp(row[4] or row[3], row[5], ZoneInfo(_STOCK_ZONES[instrument.exchange]))
            else:
                stamp = _domestic_time(row[2] if instrument.asset == "bond" else row[1], current)
        except (ValueError, OverflowError):
            continue
        source = "KIS WebSocket"
        if instrument.asset == "overseas_stock" and instrument.exchange not in ("NAS", "NYS", "AMS"):
            source += " · free feed delayed 15 min"
        elif instrument.asset in ("domestic_future", "bond"):
            source += " · trade date inferred from KST receipt"
        ticks.append(MarketTick(
            instrument=instrument, timestamp=stamp.isoformat(timespec="seconds"), price=price,
            volume=volume, cumulative_volume=cumulative,
            change=_signed(row[spec.change], row[spec.sign]),
            change_pct=_signed(row[spec.change_pct], row[spec.sign]),
            received_at=received, source=source,
        ))
    return tuple(ticks)


def subscription_message(approval_key: str, spec: Subscription, *, subscribe: bool = True) -> str:
    return json.dumps({
        "header": {"approval_key": approval_key, "custtype": "P",
                   "tr_type": "1" if subscribe else "2", "content-type": "utf-8"},
        "body": {"input": {"tr_id": spec.tr_id, "tr_key": spec.tr_key}},
    })


def _approval_key(client: KISClient) -> str:
    app_key, app_secret = config.kis_credentials()
    fingerprint = sha256((app_key + "\0" + app_secret).encode()).hexdigest()
    cache_key = (client.base_url, fingerprint)
    with _APPROVAL_LOCK:
        cached = _APPROVAL_CACHE.get(cache_key)
        if cached and time.monotonic() < cached[1]:
            return cached[0]
        try:
            response = _requests.post(
                client.base_url + "/oauth2/Approval",
                json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
                timeout=client.timeout_s,
            )
            if response.status_code != 200:
                raise KISError("KIS WebSocket approval was rejected")
            key = response.json().get("approval_key")
            if not isinstance(key, str) or not key:
                raise KISError("KIS WebSocket approval response was incomplete")
        except KISError:
            raise
        except Exception:
            raise KISError("KIS WebSocket approval request failed") from None
        _APPROVAL_CACHE[cache_key] = (key, time.monotonic() + 23 * 3600)
        return key


class _SubscriptionRejected(KISError):
    pass


class KISStream:
    """One connection for a chart or bounded watchlist; daemon callbacks.

    ``SUBSCRIBED`` means the server accepted the request, and ``LIVE`` is
    emitted only when a valid tick arrives. A connected but quiet market is not
    claimed to have produced a fresh quote. The UI should retain tick times and
    mark stale observations independently from this connection state.
    """

    def __init__(self, client: KISClient | None = None):
        self.client = client or KISClient()
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._connection = None
        self._spec: Subscription | None = None
        self._specs: tuple[Subscription, ...] = ()
        self._key = ""

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and not self._stop.is_set())

    def start(self, instrument: Instrument, on_tick: Callable[[MarketTick], None],
              on_status: Callable[[str], None]) -> None:
        self._start((instrument,), on_tick, on_status)

    def start_many(self, instruments, on_tick: Callable[[MarketTick], None],
                   on_status: Callable[[str], None]) -> None:
        """Subscribe to up to six unique domestic stocks on one connection.

        Market permissions still apply. ``SUBSCRIBED`` means *every* requested
        instrument was acknowledged; a partial subscription is not called ready.
        """
        self.stop()
        instruments = tuple(instruments)
        if (not 1 <= len(instruments) <= 6
                or any(not isinstance(i, Instrument) or i.asset != "domestic_stock"
                       for i in instruments)
                or len(set(instruments)) != len(instruments)):
            raise ValueError("Use one to six unique domestic stocks")
        self._start(instruments, on_tick, on_status)

    def _start(self, instruments, on_tick, on_status):
        # A failed instrument switch must never leave the old instrument live.
        self.stop()
        paper = urlparse(self.client.base_url).hostname == "openapivts.koreainvestment.com"
        specs = tuple(subscription_for(i, paper=paper) for i in instruments)
        if not callable(on_tick) or not callable(on_status):
            raise ValueError("Stream callbacks must be callable")
        if not self.client.ready:
            raise KISUnavailable("Set KIS_APP_KEY and KIS_APP_SECRET to enable KIS")
        if _connect is None or _requests is None:
            raise KISUnavailable("Install the websockets and requests dependencies")
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise KISError("Previous KIS stream is still stopping")
            self._stop = stop = threading.Event()
            self._specs = specs
            self._spec = specs[0]  # Retained for existing single-chart callers.
            self._thread = threading.Thread(
                target=self._run, args=(instruments, specs, paper, stop, on_tick, on_status),
                name="kis-quotation-stream", daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            connection, specs, key, thread = self._connection, self._specs, self._key, self._thread
        if connection is not None:
            try:
                if key:
                    for spec in specs:
                        connection.send(subscription_message(key, spec, subscribe=False))
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.5)

    @staticmethod
    def _status(callback, value):
        try:
            callback(value)
        except Exception:
            pass

    def _run(self, instruments, specs, paper, stop, on_tick, on_status):
        failures = 0
        fatal = False
        address = "ws://ops.koreainvestment.com:" + ("31000" if paper else "21000")
        try:
            while not stop.is_set() and failures < _MAX_FAILURES:
                self._status(on_status, "CONNECTING" if failures == 0 else "RECONNECTING")
                connection = None
                try:
                    key = _approval_key(self.client)
                    if stop.is_set():
                        break
                    connection = _connect(address, open_timeout=min(self.client.timeout_s, 10),
                                          close_timeout=0.5, ping_interval=None, max_size=524288)
                    with self._lock:
                        self._connection, self._key = connection, key
                    if stop.is_set():
                        break
                    pending = {(spec.tr_id, spec.tr_key) for spec in specs}
                    for spec in specs:
                        if stop.is_set():
                            break
                        connection.send(subscription_message(key, spec))
                    while not stop.is_set():
                        try:
                            message = connection.recv(timeout=0.5)
                        except TimeoutError:
                            continue
                        if stop.is_set():
                            break
                        if isinstance(message, (str, bytes)) and message[:1] in ("{", b"{"):
                            try:
                                control = json.loads(message)
                            except (ValueError, UnicodeDecodeError):
                                continue
                            if not isinstance(control, dict):
                                continue
                            header = control.get("header") or {}
                            if not isinstance(header, dict):
                                continue
                            if header.get("tr_id") == "PINGPONG":
                                connection.pong(message.encode() if isinstance(message, str) else message)
                                continue
                            matches = [spec for spec in specs if header.get("tr_id") == spec.tr_id
                                       and header.get("tr_key", spec.tr_key) == spec.tr_key]
                            if matches:
                                body = control.get("body") or {}
                                if not isinstance(body, dict):
                                    continue
                                if str(body.get("rt_cd", "")) == "0":
                                    # A missing key is unambiguous only for a chart.
                                    if len(matches) == 1:
                                        identity = (matches[0].tr_id, matches[0].tr_key)
                                        was_pending = identity in pending
                                        pending.discard(identity)
                                        if was_pending and not pending:
                                            self._status(on_status, "SUBSCRIBED")
                                elif "rt_cd" in body:
                                    raise _SubscriptionRejected("KIS quotation subscription was rejected; check market access")
                            continue
                        for instrument in instruments:
                            for tick in parse_ticks(message, instrument):
                                if stop.is_set():
                                    break
                                on_tick(tick)
                                if not stop.is_set():
                                    self._status(on_status, "LIVE")
                except _SubscriptionRejected:
                    fatal = True
                    self._status(on_status, "ERROR: KIS quotation subscription rejected; check market access")
                    break
                except Exception:
                    if stop.is_set():
                        break
                    failures += 1
                    if failures >= _MAX_FAILURES:
                        fatal = True
                        self._status(on_status, "ERROR: KIS WebSocket unavailable after bounded retries")
                        break
                finally:
                    if connection is not None:
                        try:
                            connection.close()
                        except Exception:
                            pass
                    with self._lock:
                        self._connection, self._key = None, ""
                if not stop.is_set():
                    self._status(on_status, "RECONNECTING")
                    stop.wait(min(16.0, 2.0 ** max(0, failures - 1)))
        finally:
            if not fatal:
                self._status(on_status, "STOPPED")
