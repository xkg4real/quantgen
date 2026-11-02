"""KIS quotation adapter shared by native and browser market workspaces.

Specifications: the owner's 2026-11-02 ``기본시세.xlsx`` attachments for domestic
stocks, overseas stocks, domestic futures/options and exchange-traded bonds.
Only quotation GETs are used. Account and order APIs are intentionally absent.
All pagination is bounded; insufficient provider history stays visibly partial.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from math import isfinite
from typing import Callable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from core.market.models import (Candle, ChartRequest, Instrument, HISTORY_INTERVALS, LIVE_INTERVALS,
                                MarketQuote, MarketSnapshot, utc_now)
from data.krx.kis_client import KISClient, KISError
from data.kis_markets import KISMarkets, load_master

_KST = ZoneInfo("Asia/Seoul")
_EXCHANGE_ZONES = {"NAS": "America/New_York", "NYS": "America/New_York", "AMS": "America/New_York",
                   "HKS": "Asia/Hong_Kong", "TSE": "Asia/Tokyo", "SHS": "Asia/Shanghai",
                   "SZS": "Asia/Shanghai", "HSX": "Asia/Ho_Chi_Minh", "HNX": "Asia/Ho_Chi_Minh"}
_CURRENCIES = {"NAS": "USD", "NYS": "USD", "AMS": "USD", "HKS": "HKD", "TSE": "JPY",
               "SHS": "CNY", "SZS": "CNY", "HSX": "VND", "HNX": "VND"}
_MAX_PAGES = 20
_FUTURE_MARKETS = {"F", "O", "JF", "JO", "CF", "CM", "EU"}


def _number(value):
    try:
        v = float(str(value).strip().replace(",", ""))
        return v if isfinite(v) else None
    except (ValueError, TypeError):
        return None


def _signed(value, sign):
    v = _number(value)
    if v is None:
        return None
    return -abs(v) if str(sign).strip() in ("4", "5") else v


def _rows(payload, key="output2"):
    value = payload.get(key) or payload.get(key.capitalize()) or []
    return value if isinstance(value, list) else [value] if isinstance(value, dict) else []


def _date(value):
    text = str(value or "").strip()
    if len(text) != 8 or not text.isdigit():
        raise ValueError("Invalid provider date")
    return datetime.strptime(text, "%Y%m%d").date()


def _timestamp(day, hour, zone):
    """Domestic overnight HH>=24 belongs to the following civil day."""
    text = str(hour or "").strip().zfill(6)
    if len(text) != 6 or not text.isdigit():
        raise ValueError("Invalid provider time")
    h, m, s = int(text[:2]), int(text[2:4]), int(text[4:])
    if h > 47 or m > 59 or s > 59:
        raise ValueError("Invalid provider time")
    d = _date(day)
    dt = datetime(d.year, d.month, d.day, tzinfo=zone) + timedelta(hours=h, minutes=m, seconds=s)
    return dt.isoformat(timespec="seconds")


def _candle(row, timestamp, columns, *, scale=1.0, signed_price=False):
    prices = [_number(row.get(k)) for k in columns[:4]]
    if any(v is None or (v <= 0 and not signed_price) for v in prices):
        return None
    op, hi, lo, close = (v * scale for v in prices)
    if any(not isfinite(v) for v in (op, hi, lo, close)) or hi < max(op, close) or lo > min(op, close) or hi < lo:
        return None
    volume = _number(row.get(columns[4]))
    if volume is not None and volume < 0:
        return None
    return Candle(timestamp, op, hi, lo, close, volume)


def _parse(rows, columns, *, zone=_KST, date_key="stck_bsop_date", time_key=None, scale=1.0, signed_price=False):
    parsed = {}
    for row in rows:
        try:
            stamp = (_timestamp(row.get(date_key), row.get(time_key), zone) if time_key
                     else _date(row.get(date_key)).isoformat())
        except (TypeError, ValueError, OverflowError):
            continue
        candle = _candle(row, stamp, columns, scale=scale, signed_price=signed_price)
        if candle:
            # First (newest) provider page wins when page boundaries overlap.
            parsed.setdefault(stamp, candle)
    return tuple(parsed[k] for k in sorted(parsed))


def _resample_minutes(candles, minutes):
    """Aggregate observed minutes within local civil-day buckets; never fill gaps."""
    if minutes == 1:
        return candles
    groups = {}
    for c in candles:
        dt = datetime.fromisoformat(c.timestamp)
        minute = (dt.hour * 60 + dt.minute) // minutes * minutes
        bucket = dt.replace(hour=minute // 60, minute=minute % 60, second=0, microsecond=0).isoformat(timespec="seconds")
        groups.setdefault(bucket, []).append(c)
    result = []
    for stamp, group in sorted(groups.items()):
        volumes = [c.volume for c in group]
        volume = sum(volumes) if all(v is not None for v in volumes) else None
        result.append(Candle(stamp, group[0].open, max(c.high for c in group), min(c.low for c in group),
                             group[-1].close, volume))
    return tuple(result)


def _period_candles(candles, interval):
    """KIS vendors can label a week/month by different trading dates."""
    result = {}
    for candle in candles:
        day = datetime.fromisoformat(candle.timestamp).date()
        day = day - timedelta(days=day.weekday()) if interval == "1w" else day.replace(day=1)
        stamp = day.isoformat()
        result.setdefault(stamp, replace(candle, timestamp=stamp))
    return tuple(result[k] for k in sorted(result))


def _future_market(instrument):
    if instrument.exchange:
        if instrument.exchange not in _FUTURE_MARKETS:
            raise KISError("Select F/O/JF/JO/CF/CM/EU for a domestic derivative")
        return instrument.exchange
    if instrument.code[1:3] in ("01", "05", "06", "07"):
        return "F"
    raise KISError("Select the domestic derivative market; its code alone is ambiguous")


def supported_intervals(instrument, *, paper=False):
    """Historical periods plus receive-only periods with a verified feed."""
    from data.kis_stream import subscription_for
    history = (("1d",) if instrument.asset == "bond" else
               ("1d", "1w", "1M") if instrument.asset == "overseas_future" else HISTORY_INTERVALS)
    try:
        subscription_for(instrument, paper=paper)
    except ValueError:
        return history
    return LIVE_INTERVALS + history


def availability_note(instrument):
    if instrument.asset == "overseas_future":
        return ("Overseas futures prices require verified ffcode.mst sCalcDesz scaling. "
                "Minute charts are unavailable until provider timestamp conventions are verified. "
                "CME/SGX require a market-data subscription.")
    if instrument.asset == "bond":
        return "Bond history: up to 100 daily bars; the supplied KIS specification has no historical minute-bar endpoint. Prices per KRW 10,000 face."
    if instrument.asset == "overseas_stock":
        return ("US free Nasdaq market-center feed · 0-minute delay; coverage and OHLC can differ from paid consolidated feeds. "
                "Minute history covers regular sessions only; intraday opening prices may be corrected next day." if instrument.exchange in ("NAS", "NYS", "AMS")
                else "KIS free overseas feed · 15-minute delay. Minute-bar history covers regular sessions only.")
    if instrument.asset == "domestic_future":
        return ("Dated domestic derivative contract; select the market matching the contract. "
                "Prices are in contract quote units (points or product-specific units), not a generic KRW cash amount. "
                "The latest bar is provisional.")
    return ("KRX market · latest candle is provisional; the forming minute volume is unavailable until confirmed "
            "because KIS can temporarily repeat the preceding minute volume. No empty-session candles are fabricated.")


class MarketDataService:
    """No network on construction. The existing KISClient owns auth and pacing."""
    def __init__(self, client=None, *, now: Callable[[], datetime] | None = None, master_loader=None):
        self.client = client or KISClient()
        self.markets = KISMarkets(self.client)
        self._now = now or (lambda: datetime.now(_KST))
        self._master_loader = master_loader or load_master
        self._future_cache = {}

    @property
    def ready(self):
        return bool(self.client.ready)

    def _get(self, path, tr_id, params):
        return self.client._get(path, tr_id, params)

    def load(self, request: ChartRequest) -> MarketSnapshot:
        instrument = request.instrument
        paper = urlparse(getattr(self.client, "base_url", "")).hostname == "openapivts.koreainvestment.com"
        if request.interval not in supported_intervals(instrument, paper=paper):
            raise KISError(availability_note(instrument))
        if request.adjusted and instrument.asset not in ("domestic_stock", "overseas_stock"):
            raise KISError("Adjusted charts are supported for stocks only")
        if instrument.asset == "domestic_future":
            _future_market(instrument)  # reject ambiguous inputs before reading credentials
        if request.interval in LIVE_INTERVALS:
            if request.adjusted:
                raise KISError("Tick and second bars contain raw executions; adjusted live bars are unavailable")
            note = (availability_note(instrument) + " Received executions only: tick/second bars begin when the "
                    "stream connects. Historical tick/second bars are unavailable; gaps are not filled. "
                    "The first/current bar can be partial; volume is received trade volume, not session volume.")
            quote = None
            try:
                quote = self.quote(instrument)
            except KISError:
                note += " Current quote unavailable; waiting for a valid streaming execution."
            return MarketSnapshot(request, (), quote, utc_now(), "KIS WebSocket", note)
        if request.interval.endswith("m"):
            candles = self._minutes(request)
        else:
            candles = self._daily(request)
        if not candles:
            raise KISError("KIS returned no valid OHLC bars for this instrument and interval")
        if request.interval in ("1w", "1M"):
            candles = _period_candles(candles, request.interval)
        candles = candles[-request.limit:]
        note = availability_note(instrument)
        if len(candles) < request.limit:
            note += f" Partial history: {len(candles)}/{request.limit} requested bars (provider window or paging limit)."
        if request.interval.endswith("m"):
            note += " Clock-aligned aggregation of observed one-minute bars; first/latest bars can be partial."
        if request.adjusted:
            note += " Adjusted historical prices; live raw-price candle updates must remain disabled."
        quote = None
        try:
            quote = self.quote(instrument)
        except KISError:
            note += " Current quote unavailable; historical bars retained."
        return MarketSnapshot(request, candles, quote, utc_now(), "KIS REST", note)

    def quote(self, instrument: Instrument) -> MarketQuote:
        asset = instrument.asset
        if asset == "overseas_future":
            scale, exchange = self._future_metadata(instrument)
            p = self._get("/uapi/overseas-futureoption/v1/quotations/inquire-price", "HHDFC55010000",
                          {"SRS_CD": instrument.code})
            o = p.get("output1") or {}
            price = _number(o.get("last_price"))
            if price is None:
                raise KISError("KIS returned no valid overseas futures quote")
            scaled = lambda key: None if _number(o.get(key)) is None else _number(o.get(key)) * scale
            change = _signed(o.get("prev_diff_price"), o.get("prev_diff_flag"))
            return MarketQuote(instrument, price * scale, change * scale if change is not None else None,
                               _signed(o.get("prev_diff_rate"), o.get("prev_diff_flag")), _number(o.get("vol")),
                               scaled("open_price"), scaled("high_price"), scaled("low_price"),
                               currency=str(o.get("crc_cd") or ""), received_at=utc_now(), source="KIS REST",
                               note=availability_note(instrument) + " REST snapshot; quote timestamp convention unverified.")
        if asset == "domestic_stock":
            p = self._get("/uapi/domestic-stock/v1/quotations/inquire-price", "FHKST01010100",
                          {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": instrument.code})
            o = p.get("output") or {}
            keys = ("stck_prpr", "prdy_vrss", "prdy_ctrt", "acml_vol", "stck_oprc", "stck_hgpr", "stck_lwpr")
        elif asset == "domestic_future":
            p = self._get("/uapi/domestic-futureoption/v1/quotations/inquire-price", "FHMIF10000000",
                          {"FID_COND_MRKT_DIV_CODE": _future_market(instrument), "FID_INPUT_ISCD": instrument.code})
            o = p.get("output1") or {}
            keys = ("futs_prpr", "futs_prdy_vrss", "futs_prdy_ctrt", "acml_vol", "futs_oprc", "futs_hgpr", "futs_lwpr")
        elif asset == "bond":
            p = self._get("/uapi/domestic-bond/v1/quotations/inquire-price", "FHKBJ773400C0",
                          {"FID_COND_MRKT_DIV_CODE": "B", "FID_INPUT_ISCD": instrument.code})
            o = p.get("output") or {}
            keys = ("bond_prpr", "bond_prdy_vrss", "prdy_ctrt", "acml_vol", "bond_oprc", "bond_hgpr", "bond_lwpr")
        else:
            p = self._get("/uapi/overseas-price/v1/quotations/price", "HHDFS00000300",
                          {"AUTH": "", "EXCD": instrument.exchange, "SYMB": instrument.code})
            o = p.get("output") or {}
            keys = ("last", "diff", "rate", "tvol", "open", "high", "low")
        if not isinstance(o, dict):
            raise KISError("Invalid KIS current quote")
        price = _number(o.get(keys[0]))
        if price is None or (price <= 0 and asset != "domestic_future"):
            raise KISError("KIS returned no valid current price")
        sign = o.get("prdy_vrss_sign", o.get("sign"))
        change = _signed(o.get(keys[1]), sign)
        if change is None and asset == "overseas_stock":
            prev = _number(o.get("base"))
            change = price - prev if prev is not None else None
        return MarketQuote(instrument, price, change, _signed(o.get(keys[2]), sign), _number(o.get(keys[3])),
                           *(_number(o.get(k)) for k in keys[4:]), currency="quote units" if asset == "domestic_future" else _CURRENCIES.get(instrument.exchange, "KRW"),
                           received_at=utc_now(), source="KIS REST", note=availability_note(instrument) + " REST snapshot; market timestamp not provided.")

    def _daily(self, request):
        ins = request.instrument
        period = {"1d": "D", "1w": "W", "1M": "M"}[request.interval]
        if ins.asset == "overseas_future":
            return self._overseas_future_daily(request)
        zone = ZoneInfo(_EXCHANGE_ZONES[ins.exchange]) if ins.asset == "overseas_stock" else _KST
        end = self._now().astimezone(zone).date()
        span = request.limit * {"D": 2, "W": 9, "M": 40}[period] + 40
        start = end - timedelta(days=span)
        seen = {}
        for _ in range(min(_MAX_PAGES, request.limit // 40 + 2)):
            if ins.asset == "domestic_stock":
                p = self._get("/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", "FHKST03010100",
                              {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ins.code,
                               "FID_INPUT_DATE_1": start.strftime("%Y%m%d"), "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
                               "FID_PERIOD_DIV_CODE": period, "FID_ORG_ADJ_PRC": "0" if request.adjusted else "1"})
                page = _parse(_rows(p), ("stck_oprc", "stck_hgpr", "stck_lwpr", "stck_clpr", "acml_vol"))
            elif ins.asset == "overseas_stock":
                p = self._get("/uapi/overseas-price/v1/quotations/dailyprice", "HHDFS76240000",
                              {"AUTH": "", "EXCD": ins.exchange, "SYMB": ins.code,
                               "GUBN": {"D": "0", "W": "1", "M": "2"}[period], "BYMD": end.strftime("%Y%m%d"),
                               "MODP": "1" if request.adjusted else "0", "KEYB": ""})
                page = _parse(_rows(p), ("open", "high", "low", "clos", "tvol"), date_key="xymd")
            elif ins.asset == "domestic_future":
                p = self._get("/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice", "FHKIF03020100",
                              {"FID_COND_MRKT_DIV_CODE": _future_market(ins), "FID_INPUT_ISCD": ins.code,
                               "FID_INPUT_DATE_1": start.strftime("%Y%m%d"), "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
                               "FID_PERIOD_DIV_CODE": period})
                page = _parse(_rows(p), ("futs_oprc", "futs_hgpr", "futs_lwpr", "futs_prpr", "acml_vol"), signed_price=True)
            else:  # bonds: this endpoint contains OHLC and up to 100 observed sessions
                p = self._get("/uapi/domestic-bond/v1/quotations/inquire-daily-price", "FHKBJ773404C0",
                              {"FID_COND_MRKT_DIV_CODE": "B", "FID_INPUT_ISCD": ins.code})
                page = _parse(_rows(p, "output"), ("bond_oprc", "bond_hgpr", "bond_lwpr", "bond_prpr", "acml_vol"))
            previous = len(seen)
            for c in page:
                seen.setdefault(c.timestamp, c)
            if not page or len(seen) == previous or len(seen) >= request.limit or ins.asset == "bond":
                break
            earliest = datetime.fromisoformat(min(c.timestamp for c in page)).date()
            next_end = earliest - timedelta(days=1)
            if next_end >= end or next_end < start:
                break
            end = next_end
        return tuple(seen[k] for k in sorted(seen))

    def _future_metadata(self, instrument):
        """Official 해외선물정보.h: CP949 byte offsets, not character offsets.

        Symbol[0:32], exchange[132:142], sCalcDesz[160:165]; record 223 bytes.
        A display precision (disp_digit) is NOT a calculation scaling exponent.
        """
        if instrument in self._future_cache:
            return self._future_cache[instrument]
        matches = []
        try:
            lines = self._master_loader("ffcode")
            for line in lines:
                if isinstance(line, bytes):
                    raw = line.rstrip(b"\r\n")
                elif "\ufffd" not in line:
                    raw = line.rstrip("\r\n").encode("cp949")
                else:
                    continue
                if len(raw) < 223 or raw[:32].decode("ascii").strip().upper() != instrument.code:
                    continue
                exchange = raw[132:142].decode("ascii").strip().upper()
                exponent = int(raw[160:165].decode("ascii").strip())
                if not -12 <= exponent <= 12 or (instrument.exchange and instrument.exchange != exchange):
                    continue
                matches.append((10.0 ** exponent, exchange))
        except Exception:
            raise KISError("Overseas futures unavailable: verified ffcode.mst price scaling could not be loaded") from None
        if len(matches) != 1:
            raise KISError("Overseas futures unavailable: contract needs one exact ffcode.mst scale/exchange match")
        self._future_cache[instrument] = matches[0]
        return matches[0]

    def _overseas_future_daily(self, request):
        ins = request.instrument
        scale, exchange = self._future_metadata(ins)
        endpoint, tr_id = {"1d": ("/uapi/overseas-futureoption/v1/quotations/daily-ccnl", "HHDFC55020100"),
                           "1w": ("/uapi/overseas-futureoption/v1/quotations/weekly-ccnl", "HHDFC55020000"),
                           "1M": ("/uapi/overseas-futureoption/v1/quotations/monthly-ccnl", "HHDFC55020300")}[request.interval]
        key, seen = "", {}
        end = self._now().astimezone(_KST).strftime("%Y%m%d")
        for page_index in range(min(_MAX_PAGES, request.limit // 40 + 2)):
            p = self._get(endpoint, tr_id,
                          {"SRS_CD": ins.code, "EXCH_CD": exchange, "START_DATE_TIME": "",
                           "CLOSE_DATE_TIME": end, "QRY_TP": "P" if page_index else "Q",
                           "QRY_CNT": "40", "QRY_GAP": "", "INDEX_KEY": key})
            page = _parse(_rows(p), ("open_price", "high_price", "low_price", "last_price", "vol"),
                          date_key="data_date", scale=scale, signed_price=True)
            previous = len(seen)
            for c in page:
                seen.setdefault(c.timestamp, c)
            if not page or len(seen) == previous or len(seen) >= request.limit:
                break
            meta = p.get("output1") or {}
            next_key = str(meta.get("index_key") or "").strip() if isinstance(meta, dict) else ""
            if not next_key or next_key == key:
                break
            key = next_key
        return tuple(seen[k] for k in sorted(seen))

    def _minutes(self, request):
        ins = request.instrument
        minutes = int(request.interval[:-1])
        now = self._now().astimezone(_KST)
        cursor = now.replace(second=0, microsecond=0)
        key = ""
        seen = {}
        # Request only documented 1m bars. Vendor N-minute anchors are unspecified;
        # resampling here keeps REST and live ticks on exactly the same clock buckets.
        target = request.limit * minutes
        for page_index in range(_MAX_PAGES):
            if ins.asset == "domestic_stock":
                p = self._get("/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice", "FHKST03010230",
                              {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ins.code,
                               "FID_INPUT_DATE_1": cursor.strftime("%Y%m%d"), "FID_INPUT_HOUR_1": cursor.strftime("%H%M%S"),
                               "FID_PW_DATA_INCU_YN": "Y", "FID_FAKE_TICK_INCU_YN": ""})
                page = _parse(_rows(p), ("stck_oprc", "stck_hgpr", "stck_lwpr", "stck_prpr", "cntg_vol"),
                              time_key="stck_cntg_hour")
            elif ins.asset == "domestic_future":
                mk = _future_market(ins)
                # Night sessions encode post-midnight times as +24 hours on the trading date.
                query_day = cursor.date()
                hour = cursor.strftime("%H%M%S")
                if mk in ("CM", "EU") and cursor.hour < 6:
                    query_day -= timedelta(days=1)
                    hour = f"{cursor.hour + 24:02d}" + cursor.strftime("%M%S")
                p = self._get("/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice", "FHKIF03020200",
                              {"FID_COND_MRKT_DIV_CODE": mk, "FID_INPUT_ISCD": ins.code,
                               "FID_HOUR_CLS_CODE": "60", "FID_PW_DATA_INCU_YN": "Y",
                               "FID_FAKE_TICK_INCU_YN": "N", "FID_INPUT_DATE_1": query_day.strftime("%Y%m%d"),
                               "FID_INPUT_HOUR_1": hour})
                page = _parse(_rows(p), ("futs_oprc", "futs_hgpr", "futs_lwpr", "futs_prpr", "cntg_vol"),
                              time_key="stck_cntg_hour", signed_price=True)
            else:
                p = self._get("/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice", "HHDFS76950200",
                              {"AUTH": "", "EXCD": ins.exchange, "SYMB": ins.code, "NMIN": "1",
                               "PINC": "1", "NEXT": "1" if page_index else "", "NREC": "120", "FILL": "", "KEYB": key})
                zone = ZoneInfo(_EXCHANGE_ZONES[ins.exchange])
                page = _parse(_rows(p), ("open", "high", "low", "last", "evol"), zone=zone,
                              date_key="xymd", time_key="xhms")
            # Ignore future timestamps instead of displaying KIS's repeated-current-price artifacts.
            page = tuple(c for c in page if datetime.fromisoformat(c.timestamp) <= now)
            previous = len(seen)
            for c in page:
                seen.setdefault(c.timestamp, c)
            if not page or len(seen) == previous or len(seen) >= target:
                break
            earliest = datetime.fromisoformat(min(c.timestamp for c in page))
            if ins.asset == "overseas_stock":
                nxt = earliest - timedelta(minutes=1)
                next_key = nxt.strftime("%Y%m%d%H%M%S")
                if next_key == key:
                    break
                key = next_key
            else:
                nxt = earliest.astimezone(_KST) - timedelta(minutes=1)
                if nxt >= cursor:
                    break
                cursor = nxt
        candles = tuple(seen[k] for k in sorted(seen))
        if ins.asset == "domestic_stock":
            forming = now.replace(second=0, microsecond=0)
            candles = tuple(replace(c, volume=None) if datetime.fromisoformat(c.timestamp) == forming else c for c in candles)
        return _resample_minutes(candles, minutes)
