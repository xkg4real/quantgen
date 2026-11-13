"""Markets pages: one page per market with Toss-style ranked lists (owner request 2026-11-11, point 5; UI-D10).

Owner ruling UI-D10 (2026-11-11): "시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, 너가 지금 하부ui로 깔아놓은건 해당
시장의 하부ui 선택하고 차후에 검색기준으로 저걸 쓸수있게 구현하면 좋을 거 같은데, 공간 잘써서 센스있게해봐". The rail
lists the markets (`core.market.screen.PAGES`: 국내 주식, 미국 주식, 크립토, 국내 ETF, 미국 ETF; since owner ruling UI-D11
of 2026-11-12 the rail reaches them through its 시장 › 주식 / 크립토 / ETF flyouts, `shell_rail.market_menu`, and this
page itself is unchanged, "지금 시장 안의 ui는 괜찮다"); `RankingBoard` is that market's page: one compact
header row (market name, data state, a search scoped to this market, refresh), a slim index strip
(`market_summary.MarketSummary`), a criteria row (the ranking categories as chips, the sub-market, the sector and a
"조건" control that opens beginner conditions: 등락률 range, 거래대금 at least, 시가총액 at least), chips for the
active search and conditions with one-click clear, then the list using the width. Search, category, sub-market,
sector and conditions combine through `core.market.screen.Screen` (criteria as data). Each market keeps its own.

Owner: "시장 UI에는 토스증권처럼 실시간 차트를 다양한 분류기준으로 조회할수있게 변경해봐". The list ranks the
curated universe of `core.market.rankings` (KIS ranking endpoints are not on the frozen allowlist) by trading
value, volume, top gainers, top losers or market cap, for all of Korea, KOSPI, KOSDAQ or the US, optionally
one sector. A row opens the stock's screen (`markets_view.StockView`).

Data, off the UI thread and only while the list is visible with automatic refresh on:
* KIS configured: one allowlisted quote per stock (domestic ``inquire-price``, overseas ``price``) through the
  existing market data service, at most `KIS_MAX_PER_SECOND` requests a second (the KIS client also paces
  every call process-wide); during the session a round of requests starts every `LIVE_REFRESH_SECONDS`,
  timed from the start of the previous round (`RankingBoard.due`), so each stock is asked every 45 s while a
  round takes less than that (81 domestic requests take at least 9.6 s at the client's 0.12 s spacing). REST
  polling, not a trade stream: the state says "KIS 조회 · 45초마다" (US: "KIS 무료 시세 · 45초마다"),
  never "실시간"; a round that took longer than 45 s makes it "KIS · 갱신 지연" and the tooltip says so.
* Domestic market cap comes with the same ``inquire-price`` answer (`rankings.parse_kis_domestic_cap`): KIS's
  ``hts_avls`` only when it agrees with listed shares x price of that answer, else listed shares x price
  ("시가총액(계산값)") when KIS states no figure; a refused or missing figure is listed last as '—', with why.
* otherwise (or when KIS answers nothing): the Yahoo daily path, labelled "delayed · daily"; trading value is
  close x volume (an estimate, said so in the note). Refreshed every `IDLE_REFRESH_SECONDS`.
* coins: only the Yahoo daily path (``BTC-USD`` and so on; `rankings.CRYPTO`), "지연·일별", US dollars; Yahoo
  states a coin's daily volume in dollars, so that is its trading value (not estimated). Coins are not ranked by
  units traded or by market cap (no source the app uses states one); those chips are disabled and say why. A coin
  row opens nothing (the stock screen has no coin instrument) and its tooltip says so.
* US market cap (owner 2026-11-11, "아니 미국 시총 자료 찾으세요"), inside the same US fetch, in this order:
  KIS's overseas ``price-detail`` market cap in the KIS batch when KIS is configured (allowlisted with the
  owner's approval, "승인."; at most every `DETAIL_SECONDS` per stock); then (`core.market.market_cap`)
  FMP's stated figure from one batch request when FMP_API_KEY is set and the plan allows it; otherwise Yahoo
  share counts (cached a day) x the row's price, headed "시가총액(계산값)". A stock whose figure could not be
  read is listed last without a rank and shows '—'; when none could be read the list says why instead.
* ETFs (UI-D11): the curated `rankings.ETF_KR` / `ETF_US` lists on the stocks' paths above (KIS quotes when configured,
  else Yahoo daily bars), the same page and rows; an ETF row opens the stock screen like a stock. No market-cap
  ranking: an ETF's size is its net assets (AUM), which no source the app uses states (the chip is left out and the
  footnote says why, as for coins).
One fetch serves every category of its group ('kr', 'us', 'crypto', 'etf_kr' or 'etf_us'): switching category
re-ranks the cached quotes.

The source state is always shown ("KIS 조회 · 45초마다" for KIS quotes during the regular session, "KIS · 장
마감", "KIS · 갱신 지연", "지연·일별", "자료 없음") with the time since the last update; nothing polled, stale or
synthetic is presented as live. The page is headed by the market's name. Provider names and dates beyond that stay
in tooltips (owner, 2026-11-04).

UI-D10 review (2026-11-11), "공간 잘써서": the page decides its layout from the room its scroll area gives it
(`RankingBoard.available_width`; the header search and the filters take a line of their own, the index strip drops
its sparklines, and the list keeps the columns that fit, `column_plan`), so no market or language scrolls sideways
at 1000 px; the rows show the figures the quotes carry (거래대금 · 거래량 · 시가총액, the ranked one emphasised; a
heading click ranks by it) and the sector, so the numbers sit near their names; a pinned bar (`StickyBar`) keeps the
market, the ranking, a search and the column headings on screen while a long list scrolls; an empty list says
which criterion left nothing, with a one-click way out (`_empty_state`).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import math
import re
import threading
import time

from PyQt6.QtCore import QEvent, QLocale, QPoint, QPointF, QRect, QRectF, QSize, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QDoubleValidator, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QBoxLayout, QButtonGroup, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market import rankings as R
from core.market import screen as S
from core.theme import DARK, LIGHT
from .company_identity import CompanyMark
from .jobs import Jobs

LIST_LIMIT = 30
LIVE_REFRESH_SECONDS = R.POLL_SECONDS  # KIS quotes while the market is open (REST polling, not a stream)
IDLE_REFRESH_SECONDS = 300     # KIS outside the session, and delayed daily bars
RETRY_SECONDS = 60             # after a failed fetch
LIVE_STALE_SECONDS = 3 * LIVE_REFRESH_SECONDS  # a KIS list older than this is "KIS · 갱신 지연", not polled
KIS_MAX_PER_SECOND = 20
DETAIL_SECONDS = IDLE_REFRESH_SECONDS  # a US stock's KIS price-detail (market cap) is asked at most this often
DAILY_WORKERS = 4
DAILY_PERIOD = "1mo"
DOMESTIC_PRICE = ("/uapi/domestic-stock/v1/quotations/inquire-price", "FHKST01010100")
OVERSEAS_PRICE = ("/uapi/overseas-price/v1/quotations/price", "HHDFS00000300")
# Row geometry, shared by the column header so captions sit over their figures.
RANK_WIDTH, MARK_SIZE, SPARK_WIDTH, PRICE_WIDTH, CHANGE_WIDTH, VALUE_WIDTH = 30, 36, 88, 116, 88, 104
ROW_MARGINS = (12, 12, 14, 12)   # roomy rows: whitespace, not lines, separates them (owner 2026-11-11)
ROW_SPACING = 14
TOOL_PADDING = (7, 12)         # market buttons: the window's `QPushButton[tool='true']` padding (typography.py)


def _utc_now():
    return datetime.now(timezone.utc)


# Loading ----------------------------------------------------------------------------------------
def kis_batch(service, group, members, *, cancelled=None, progress=None, sleep=time.sleep, clock=time.monotonic,
              per_second=KIS_MAX_PER_SECOND, details=None, now=time.monotonic):
    """One allowlisted KIS quote per member, at most `per_second` a second; failures stay per stock.

    With `details` (a dict the caller keeps between fetches), a US member also gets KIS's overseas
    ``price-detail`` answer for its market cap (owner approval 2026-11-11), through the same pacing, at most
    once per `DETAIL_SECONDS` per stock (the answer is reused in between, with its own received time). A
    price-detail failure never costs the price quote. ADRs are not asked (`rankings.ADR_CODES`).
    """
    records, failures = [], []
    gap, last = 1.0 / per_second, [None]

    def paced(path, tr_id, params):
        if last[0] is not None:
            wait = gap - (clock() - last[0])
            if wait > 0:
                sleep(wait)
        last[0] = clock()
        return service._get(path, tr_id, params)

    for index, member in enumerate(members):
        if cancelled is not None and cancelled():
            break
        try:
            if member.overseas:  # a US stock or ETF
                params = {"AUTH": "", "EXCD": member.exchange, "SYMB": member.code}
                record = R.parse_kis_overseas(member, paced(*OVERSEAS_PRICE, params).get("output"))
                if details is not None and member.code not in R.ADR_CODES:
                    record = _with_detail(record, details, lambda: paced(*_overseas_detail(), params), now)
                records.append(record)
            else:
                payload = paced(*DOMESTIC_PRICE, {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": member.code})
                records.append(R.parse_kis_domestic(member, payload.get("output")))
        except Exception as exc:  # the class name is the whole record; provider text may hold URLs
            failures.append((member.code, type(exc).__name__))
        if progress is not None:
            progress(index + 1, len(members))
    return R.Batch(group, tuple(records), "kis" if records else "none", _utc_now().isoformat(timespec="seconds"),
                   tuple(failures))


def _overseas_detail():
    from data.kis_workspace import OVERSEAS_PRICE_DETAIL
    return OVERSEAS_PRICE_DETAIL


def _with_detail(record, details, fetch, now):
    """`record` with KIS's market cap from a price-detail answer at most `DETAIL_SECONDS` old."""
    code, moment = record.member.code, now()
    kept = details.get(code)
    if kept is None or not 0 <= moment - kept[0] < DETAIL_SECONDS:
        try:
            output = fetch().get("output")
        except Exception:  # remembered as nothing, and asked again after DETAIL_SECONDS
            output = None
        kept = (moment, output, _utc_now().isoformat(timespec="seconds"))
        details[code] = kept
    return R.with_kis_detail(record, kept[1], received_at=kept[2])


def _yahoo_candidates(member):
    """(Yahoo symbol, listing market it implies), curated market first."""
    if member.market == "CRYPTO":
        return ((R.crypto_symbol(member), ""),)
    if member.overseas:
        from core.market.routing import yahoo_symbols
        return tuple((symbol, "") for symbol in yahoo_symbols(member.instrument))
    if member.market == "ETF_KR":  # KRX ETFs are listed on the KOSPI board: '.KS'
        return ((f"{member.code}.KS", ""),)
    first, second = (("KS", "KOSPI"), ("KQ", "KOSDAQ")) if member.market == "KOSPI" else (("KQ", "KOSDAQ"), ("KS", "KOSPI"))
    return tuple((f"{member.code}.{suffix}", market) for suffix, market in (first, second))


def daily_batch(group, members, *, fetch=None, cancelled=None, progress=None, workers=DAILY_WORKERS):
    """Delayed daily bars through the existing Yahoo path (`core.market.routing._yahoo_frame`)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from core.market import routing
    fetch = fetch or (lambda symbol: routing._yahoo_frame(symbol, "1d", DAILY_PERIOD))

    def one(member):
        if cancelled is not None and cancelled():
            return None
        for symbol, market in _yahoo_candidates(member):
            rows = tuple(fetch(symbol) or ())
            if rows:
                return R.record_from_bars(member, rows, market=market)
        raise LookupError("No daily bars")

    records, failures, done = [], [], 0
    pool = ThreadPoolExecutor(max_workers=max(1, int(workers)), thread_name_prefix="qg-rankings")
    try:
        futures = {pool.submit(one, member): member for member in members}
        for future in as_completed(futures):
            member = futures[future]
            try:
                record = future.result()
            except Exception as exc:
                failures.append((member.code, type(exc).__name__))
            else:
                if record is not None:
                    records.append(record)
            done += 1
            if progress is not None:
                progress(done, len(members))
            if cancelled is not None and cancelled():
                break
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    order = {member.code: index for index, member in enumerate(members)}
    records.sort(key=lambda record: order[record.member.code])
    kept, stale = R.drop_stale(records)
    return R.Batch(group, kept, "daily" if kept else "none", _utc_now().isoformat(timespec="seconds"),
                   tuple(sorted(failures, key=lambda item: order[item[0]])), stale)


class ProductionRankingLoader:
    """KIS quotes when KIS is configured; otherwise, or when KIS answers nothing, delayed daily bars.
    US KIS quotes carry KIS's market cap (price-detail); the stocks still without one get theirs from `caps`
    (`core.market.market_cap.MarketCapSource`: FMP, then Yahoo shares x price). Coins ('crypto') are read only
    as Yahoo daily bars.

    Nothing is constructed or fetched until the first call (a window with automatic refresh off never calls).
    """

    def __init__(self, *, service_factory=None, fetch=None, caps=None):
        self._factory, self._fetch = service_factory, fetch
        self._service = None
        self._caps = caps
        self._details = {}            # US code -> (when, KIS price-detail output, received at), see kis_batch
        self._lock = threading.Lock()

    def service(self):
        with self._lock:
            if self._service is None:
                if self._factory is not None:
                    self._service = self._factory()
                else:
                    from data.kis_workspace import MarketDataService
                    self._service = MarketDataService()
            return self._service

    def market_caps(self):
        with self._lock:
            if self._caps is None:
                from core.market.market_cap import MarketCapSource
                self._caps = MarketCapSource()
            return self._caps

    def __call__(self, group, members, cancelled=None, progress=None):
        batch = self._quotes(group, members, cancelled, progress)
        if group != "us" or not batch.records or (cancelled is not None and cancelled()):
            return batch
        try:
            return self.market_caps()(batch, cancelled=cancelled, progress=progress)
        except Exception:  # a market-cap failure must not cost the quotes
            return replace(batch, caps="none")

    def _quotes(self, group, members, cancelled, progress):
        if group == "crypto":  # coins: Yahoo daily only; KIS is never asked (nor constructed) for them
            return daily_batch(group, members, fetch=self._fetch, cancelled=cancelled, progress=progress)
        service = self.service()
        if getattr(service, "ready", False):
            batch = kis_batch(service, group, members, cancelled=cancelled, progress=progress,
                              details=self._details if group == "us" else None)
            if batch.records or (cancelled is not None and cancelled()):
                return batch
            daily = daily_batch(group, members, fetch=self._fetch, cancelled=cancelled, progress=progress)
            return replace(daily, fallback=True)
        return daily_batch(group, members, fetch=self._fetch, cancelled=cancelled, progress=progress)


# Widgets ----------------------------------------------------------------------------------------
def _label(role="", rk="", *, wrap=False):
    widget = QLabel()
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if role:
        widget.setProperty("role", role)
    if rk:
        widget.setProperty("rk", rk)
    widget.setProperty("qg_literal", True)  # rendered in the window's language here; the controller skips it
    return widget


def _numbers(widget):
    from .font_policy import number_font
    widget.setFont(number_font(widget.font()))
    return widget


def mark_name(name):
    """The name the letter mark is drawn from: 'HD현대일렉트릭' -> 'HD', '삼성SDI' -> '삼성'.

    `company_identity` takes one letter from each of the first two words, and a name that switches script
    ('HD' + '현대…') would read 'H현'; its first word alone keeps one script.
    """
    words = re.findall(r"[A-Za-z]+|[가-힣]+", str(name))
    hangul = [bool(re.match("[가-힣]", word)) for word in words[:2]]
    return words[0] if len(hangul) == 2 and hangul[0] != hangul[1] else name


def ticker_mark(code):
    """Two letters of a US ticker or a coin's symbol for its letter mark: AAPL -> 'AP', MSFT -> 'MS', UNH -> 'UN',
    BTC -> 'BT', V -> 'V'. A Korean reading of an English name ('마이' for Microsoft) or two names sharing
    initials ('AC' for Amazon.com and Alphabet Class A) told nothing (UI-D10 review)."""
    letters = re.sub(r"[^A-Z]", "", str(code).split(".")[0].upper())
    if len(letters) <= 2:
        return letters or str(code)[:2]
    return letters[0] + next((c for c in letters[1:] if c != letters[0]), letters[1])


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _set_flag(widget, name, value):
    """Set a boolean style property and repolish only when it changes."""
    value = bool(value)
    if widget.property(name) != value:
        widget.setProperty(name, value)
        _repolish(widget)


class ElidedLabel(QLabel):
    """One line that elides on the right; the full text stays in the tooltip and accessible name."""

    def __init__(self, rk):
        super().__init__()
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setProperty("rk", rk)
        self.setProperty("qg_literal", True)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.full = ""

    def set_full(self, text):
        self.full = str(text)
        self._fit()

    def _fit(self):
        shown = self.fontMetrics().elidedText(self.full, Qt.TextElideMode.ElideRight, max(0, self.width()))
        super().setText(shown)
        self.setToolTip(self.full if shown != self.full else "")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._fit()


class Sparkline(QWidget):
    """Recent daily closes as one thin line in the row's rise/fall tone; no axes, nothing inferred."""

    def __init__(self, width=SPARK_WIDTH, height=30):
        super().__init__()
        self.setFixedSize(width, height)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.values, self.color = (), QColor("#646E68")

    def set_values(self, values, color):
        self.values, self.color = tuple(float(v) for v in values), QColor(color)
        self.update()

    def paintEvent(self, event):
        if len(self.values) < 2:
            return
        low, high = min(self.values), max(self.values)
        span = (high - low) or 1.0
        w, h, pad = self.width(), self.height(), 3.0
        step = (w - 2 * pad) / (len(self.values) - 1)
        path = QPainterPath()
        for index, value in enumerate(self.values):
            point = QPointF(pad + index * step, h - pad - (h - 2 * pad) * (value - low) / span)
            path.moveTo(point) if index == 0 else path.lineTo(point)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(self.color, 1.6))
        painter.drawPath(path)
        painter.end()


class Flow(QLayout):
    """Items left to right, wrapping to the next line when the width runs out; hidden items take no room and
    each line is centred vertically. Its minimum is its widest item, so a narrow page wraps instead of
    scrolling sideways."""

    def __init__(self, parent=None, *, spacing=6, line_spacing=8):
        super().__init__(parent)
        self._items, self._gap, self._line = [], spacing, line_spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), False)

    def _shown(self):
        return [item for item in self._items if not item.isEmpty()]

    def minimumSize(self):
        size = QSize()
        for item in self._shown():
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def sizeHint(self):
        shown, margins = self._shown(), self.contentsMargins()
        width = sum(item.sizeHint().width() for item in shown) + max(0, len(shown) - 1) * self._gap
        height = max((item.sizeHint().height() for item in shown), default=0)
        return QSize(width + margins.left() + margins.right(), height + margins.top() + margins.bottom())

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, True)

    def _arrange(self, rect, apply):
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        lines, line, x = [], [], 0
        for item in self._shown():
            width = max(item.minimumSize().width(), min(item.sizeHint().width(), max(1, area.width())))
            if line and x + width > area.width():
                lines.append(line)
                line, x = [], 0
            line.append((item, width))
            x += width + self._gap
        if line:
            lines.append(line)
        y = area.y()
        for index, entries in enumerate(lines):
            height = max(item.sizeHint().height() for item, _w in entries)
            x = area.x()
            for item, width in entries:
                item_height = item.sizeHint().height()
                if apply:
                    item.setGeometry(QRect(x, y + (height - item_height) // 2, width, item_height))
                x += width + self._gap
            y += height + (self._line if index < len(lines) - 1 else 0)
        return y - rect.y() + margins.bottom()


def _flow_host(spacing=6, line_spacing=8):
    host = QWidget()
    host.setObjectName("boardSection")
    flow = Flow(host, spacing=spacing, line_spacing=line_spacing)
    return host, flow


class Chip(QPushButton):
    """A ranking chip (거래대금 · 거래량 · 급상승 · 급하락 · 시가총액).

    Keyboard focus reaches only the checked chip (the chips are one exclusive group), and an accent ring on the
    chip's own accent fill showed nothing (UI-D10 review): checked and focused, it draws an inset ring in the
    on-accent colour, so the ring shows in both themes without changing the chip's size.
    """

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setProperty("chip", True)
        self.setProperty("qg_literal", True)
        self.ring = QColor(LIGHT.on_accent)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked() and self.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(self.ring, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
            radius = rect.height() / 2
            painter.drawRoundedRect(rect, radius, radius)
            painter.end()


# Columns of the list. Owner: "공간 잘써서" -- the review measured a ~616 px empty band between the names and the
# numbers at 1440 px. The row now shows the figures the quotes carry (거래대금 · 거래량 · 시가총액, the ranked one
# emphasised), the sector as a tag and, on the daily path, the sparkline right after the name; whatever width is
# left beyond NAME_TARGET is shared among the columns so the numbers sit near the names they belong to.
FIGURES = ("value", "volume", "cap", "qscore")
COLUMN_KEYS = ("spark", "sector", "price", "change") + FIGURES  # the sparkline right after the name
COLUMN_MIN = {"sector": 84, "spark": SPARK_WIDTH, "price": 96, "change": 80, "value": 92, "volume": 96, "cap": 96, "qscore": 106}
COLUMN_MAX = {"sector": 100, "spark": 220}
COLUMN_MAX_NUMBER = 200
NAME_MIN, NAME_TARGET = 150, 200


def column_plan(width, *, figure, figures=(), spark=False, sector=False):
    """The list's columns for rows `width` px wide: ((key, px), ...) in row order; the name takes the rest.

    Price, change and `figure` (the ranked figure; trading value under 급상승/급하락) always show. Then, as far as
    the width allows with at least NAME_MIN left for the name: the other `figures` the rows carry, the sparkline,
    the sector tag. Width beyond NAME_TARGET for the name is shared among the columns, each up to its cap.
    """
    inner = width - (ROW_MARGINS[0] + ROW_MARGINS[2] + RANK_WIDTH + MARK_SIZE + 2 * ROW_SPACING)
    cost = lambda keys: sum(COLUMN_MIN[key] + ROW_SPACING for key in keys)
    chosen = ["price", "change", figure]
    extras = [key for key in FIGURES if key in figures and key != figure]
    extras += (["spark"] if spark else []) + (["sector"] if sector else [])
    for key in extras:
        if cost(chosen + [key]) + NAME_MIN <= inner:
            chosen.append(key)
    order = [key for key in COLUMN_KEYS if key in chosen]
    widths = {key: COLUMN_MIN[key] for key in order}
    extra, growing = inner - cost(order) - NAME_TARGET, list(order)
    while extra > 0 and growing:
        share, still = max(1, extra // len(growing)), []
        for key in growing:
            top = COLUMN_MAX.get(key, COLUMN_MAX_NUMBER)
            give = min(share, top - widths[key], extra)
            widths[key] += give
            extra -= give
            if widths[key] < top:
                still.append(key)
            if extra <= 0:
                break
        growing = still
    return tuple((key, widths[key]) for key in order)


def _apply_plan(cells, plan):
    """Show the planned columns at their widths and hide the rest (rows and headings alike)."""
    widths = dict(plan)
    for key, widget in cells.items():
        if key in widths:
            widget.setFixedWidth(widths[key])
        widget.setVisible(key in widths)


class RankRow(QFrame):
    """rank · company mark · name and code · sparkline · sector tag · price · change % · figures (`column_plan`)."""
    opened = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("rankRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty("openable", True)
        self.row, self.plan, self.figure_kind = None, None, "value"
        self.ring = QColor(LIGHT.accent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*ROW_MARGINS)
        layout.setSpacing(ROW_SPACING)
        self.rank = _numbers(_label(rk="rank"))
        self.rank.setFixedWidth(RANK_WIDTH)
        self.rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.rank)
        self.mark = CompanyMark("", size=MARK_SIZE)
        layout.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setContentsMargins(0, 0, 0, 0)
        names.setSpacing(1)
        self.name = ElidedLabel("name")
        self.code = ElidedLabel("code")
        names.addWidget(self.name)
        names.addWidget(self.code)
        layout.addLayout(names, 1)
        self.sector = _label(rk="sector")
        self.spark = Sparkline()
        self.price = _numbers(_label(rk="price"))
        self.change = _numbers(_label(rk="change"))
        self.figures = {key: _numbers(_label(rk="figure")) for key in FIGURES}
        self.cells = {"spark": self.spark, "sector": self.sector, "price": self.price, "change": self.change,
                      **self.figures}
        for key in COLUMN_KEYS:
            widget = self.cells[key]
            if key == "sector":
                widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            elif key != "spark":
                widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self.apply_plan(column_plan(1000, figure="value"))

    @property
    def value(self):
        """The ranked figure's cell (trading value under 급상승/급하락), the list's earlier third column."""
        return self.figures[self.figure_kind]

    def apply_plan(self, plan):
        if plan != self.plan:
            self.plan = plan
            _apply_plan(self.cells, plan)

    def show_row(self, row, *, language, dark, figure, ranked="", sector="", tips=None, closed_tip=""):
        """`figure`: the figure column ranked (or trading value); `ranked`: the column emphasised ('' for none);
        `closed_tip`: why this row opens nothing (a coin); '' for a row that opens the stock's screen."""
        from .typography import TONE_COLORS, set_tone
        self.row, self.figure_kind = row, figure
        record, member = row.record, row.record.member
        name = member.label(language)
        self.rank.setText(str(row.rank) if row.rank else "")  # 0: no figure, listed after the ranked rows
        # A US stock's or a coin's mark is its ticker's letters (AP, MS, BT): a Korean reading of an English name
        # ('마이' for Microsoft) or shared initials told nothing; a Korean name keeps one script (`mark_name`).
        letters = ticker_mark(member.code) if member.group in ("us", "crypto", "etf_us") else mark_name(name)
        self.mark.set_identity(member.code, letters)
        self.mark.setAccessibleName(name)
        self.mark.setToolTip(f"{name} · {member.code}")
        palette = DARK if dark else LIGHT
        self.mark.set_theme(palette)
        self.ring = QColor(palette.accent)
        self.name.set_full(name)
        place = member.place(language, record.market)
        self.code.set_full(f"{member.code} · {place}" if place else member.code)
        openable = member.instrument is not None and not closed_tip
        _set_flag(self, "openable", openable)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus if openable else Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor if openable else Qt.CursorShape.ArrowCursor)
        self.setToolTip(closed_tip)
        self.setAccessibleDescription(closed_tip)
        self.sector.setText(sector)
        self.price.setText(R.price_text(record.price, member.currency))
        text, tone = R.change_text(record.change_pct)
        self.change.setText(text or "—")
        set_tone(self.change, tone)
        tips = tips or {}
        for key, label in self.figures.items():
            amount = {"value": record.trading_value, "volume": record.volume, "cap": record.market_cap, "qscore": record.q_score}[key]
            _kind, unit = R.value_unit(key, member.group)
            label.setText(("—" if amount is None else f"{int(amount)} " + "★" * min(5, 1 + int(amount // 20)))
                          if key == "qscore" else R.compact(amount, unit, language))
            label.setToolTip(tips.get(key, ""))
            if key == "qscore":
                from .stock_qscore import reason, as_of_text
                label.setToolTip(as_of_text(record.q_result, language) if amount is not None else
                                 " · ".join(reason(record.q_result, language)))
            _set_flag(label, "ranked", key == ranked)
        tones = TONE_COLORS[bool(dark)]
        closes = record.closes
        self.spark.set_values(closes, tones["up"] if len(closes) > 1 and closes[-1] >= closes[0] else tones["down"])
        rank = f"{row.rank}. " if row.rank else ""
        self.setAccessibleName(f"{rank}{name} {self.price.text()} {self.change.text()} {self.value.text()}")

    def _open(self):
        if self.row is not None and self.row.record.member.instrument is not None and self.property("openable"):
            self.opened.emit(self.row.record.member.instrument)  # a coin has no instrument: nothing opens

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self._open()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._open()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hasFocus():  # UI-D10 review: keyboard focus differs from hover by a 2px accent ring, not the fill alone
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(self.ring, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 12, 12)
            painter.end()


class HeadLabel(QLabel):
    """A column heading; a figure or change heading ranks the list by its column when clicked (what its chip does).
    Not a Tab stop: the chips are the keyboard path to the same choice."""
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setProperty("rk", "head")
        self.setProperty("qg_literal", True)
        self.sortable = False

    def set_sortable(self, sortable):
        self.sortable = bool(sortable)
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.sortable else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.sortable and event.button() == Qt.MouseButton.LeftButton and \
                self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
            return
        super().mouseReleaseEvent(event)


class ColumnHeader(QWidget):
    """The list's column headings on the rows' geometry (the same `column_plan`)."""
    sort_requested = pyqtSignal(str)   # 'change' or a figure key

    def __init__(self):
        super().__init__()
        self.setObjectName("boardSection")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(ROW_MARGINS[0], 0, ROW_MARGINS[2], 0)
        layout.setSpacing(ROW_SPACING)
        self.rank = HeadLabel()
        self.rank.setFixedWidth(RANK_WIDTH)
        self.rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.rank)
        self.stock = HeadLabel()
        layout.addWidget(self.stock, 1)
        self.cells, self.plan = {}, None
        for key in COLUMN_KEYS:
            cell = HeadLabel()
            if key in FIGURES:
                cell.setWordWrap(True)  # "Market cap (computed)" takes two lines in a narrow figure column
            cell.setAlignment((Qt.AlignmentFlag.AlignLeft if key == "sector" else Qt.AlignmentFlag.AlignRight)
                              | Qt.AlignmentFlag.AlignVCenter)
            if key == "change" or key in FIGURES:
                cell.clicked.connect(lambda k=key: self.sort_requested.emit(k))
            layout.addWidget(cell)
            self.cells[key] = cell
        self.apply_plan(column_plan(1000, figure="value"))

    def apply_plan(self, plan):
        if plan != self.plan:
            self.plan = plan
            _apply_plan(self.cells, plan)


class StickyBar(QFrame):
    """Pinned to the top of the page while the list scrolls under it: the market's name, the ranking in use (a
    click goes back up to the criteria), a search and the column headings (UI-D10 review: on a long list the
    criteria and the meaning of each column left the screen). Parented to the scroll area's viewport, so it stays
    put while the page moves; shown only once the list's own headings have scrolled away."""

    def __init__(self):
        super().__init__()
        self.setObjectName("stickyBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 8)
        layout.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.name = _label(rk="stickName")
        top.addWidget(self.name, 0, Qt.AlignmentFlag.AlignVCenter)
        self.rank_button = QPushButton()
        self.rank_button.setObjectName("stickyRank")
        self.rank_button.setProperty("qg_literal", True)
        self.rank_button.setCursor(Qt.CursorShape.PointingHandCursor)
        top.addWidget(self.rank_button, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch(1)
        self.search = QLineEdit()
        self.search.setObjectName("marketSearch")
        self.search.setClearButtonEnabled(True)
        self.search.setProperty("qg_literal", True)
        self.search.setMinimumWidth(SEARCH_MIN)
        self.search.setMaximumWidth(SEARCH_MAX)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top.addWidget(self.search, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(top)
        self.header = ColumnHeader()
        layout.addWidget(self.header)
        self.hide()


def blend(first, second, share=0.5):
    """`first` moved `share` of the way to `second` (hex colours)."""
    a, b = QColor(first), QColor(second)
    mix = lambda x, y: round(x + (y - x) * share)
    return QColor(mix(a.red(), b.red()), mix(a.green(), b.green()), mix(a.blue(), b.blue())).name()


def board_stylesheet(palette, dark):
    """Local rules for the market page (the window stylesheet is area S's); the closer sheet wins in Qt.

    Owner, 2026-11-11 ("구획 선을 연하게 ... 한칸한칸 공간을 넓게"): no outlined boxes here. Chips, the
    refresh button and the sector selector are soft surface fills without borders; rows are separated by
    whitespace; the one rule above the list is the border colour blended half way into the background. The index
    tiles are the page surface with that hairline; the conditions row is a soft surface_2 band.

    A rule here that sets `border` hides the window's `:focus` ring (the closer sheet wins whatever the
    selector), so every focusable control styled here has its own `:focus` rule with the window's 2px `accent`
    ring: the sub-market segments (전체·코스피·코스닥, 전체·나스닥·NYSE) keep a transparent 2px border so the ring
    does not resize them, and the search, the 조건 toggle, the condition fields, the filter chips and the text
    buttons narrow their padding by the ring's width. The checked ranking chip draws its own inset ring
    (`Chip`), and a row its own 2px ring over the hover fill (`RankRow.paintEvent`). An invalid bound is the
    palette's `error` colour (not the red that means a price rose), and focus still shows the accent ring.
    """
    from .typography import TONE_COLORS
    p, t = palette, TONE_COLORS[bool(dark)]
    line = blend(p.border, p.bg)
    chip_line = blend(p.accent, p.accent_soft, 0.6)
    return f"""
          QFrame#marketBoard {{ background: transparent; border: 0; }}
          QWidget#boardSection {{ background: transparent; }}
          QFrame#stickyBar {{ background: {p.bg}; border: 0; border-bottom: 1px solid {line}; }}
          QPushButton[chip='true'] {{ padding: 7px 16px; min-height: 18px; border: 0; border-radius: 16px;
                                     background: {p.surface_2}; color: {p.text}; }}
          QPushButton[chip='true']:hover {{ background: {p.accent_soft}; }}
          QPushButton[chip='true']:checked {{ background: {p.accent}; color: {p.on_accent}; }}
          QPushButton[chip='true']:focus {{ border: 2px solid {p.accent}; }}
          QFrame#segment {{ background: {p.surface_2}; border: 0; border-radius: 16px; }}
          QPushButton[tool='true'] {{ background: transparent; border: 2px solid transparent; border-radius: 14px;
                                     padding: {TOOL_PADDING[0] - 3}px {TOOL_PADDING[1] - 2}px; min-height: 18px;
                                     color: {p.muted}; }}
          QPushButton[tool='true']:hover {{ color: {p.text}; }}
          QPushButton[tool='true']:checked {{ background: {p.surface}; color: {p.text}; font-weight: 600; }}
          QPushButton[tool='true']:focus {{ border: 2px solid {p.accent}; }}
          QPushButton#rankRefresh {{ border: 0; border-radius: 8px; padding: 6px 12px; background: {p.surface_2}; }}
          QPushButton#rankRefresh:hover {{ background: {p.accent_soft}; }}
          QPushButton#rankRefresh:focus {{ border: 2px solid {p.accent}; }}
          QComboBox#rankSector {{ border: 0; border-radius: 8px; background: {p.surface_2}; }}
          QComboBox#rankSector:focus {{ border: 2px solid {p.accent}; }}
          QLineEdit#marketSearch {{ min-height: 22px; padding: 6px 14px; border: 1px solid {line}; border-radius: 18px;
                                   background: {p.surface}; font-size: 14px; }}
          QLineEdit#marketSearch:focus {{ border: 2px solid {p.accent}; padding: 5px 13px; }}
          QPushButton#conditionsToggle {{ border: 0; border-radius: 8px; padding: 6px 12px; background: {p.surface_2};
                                         color: {p.text}; }}
          QPushButton#conditionsToggle:hover {{ background: {p.accent_soft}; }}
          QPushButton#conditionsToggle:checked {{ background: {p.accent_soft}; color: {p.accent}; }}
          QPushButton#conditionsToggle:focus {{ border: 2px solid {p.accent}; padding: 4px 10px; }}
          QFrame#conditionsPanel {{ background: {p.surface_2}; border: 0; border-radius: 14px; }}
          QFrame#conditionsPanel QWidget#condGroup {{ background: transparent; }}
          QLineEdit#condEdit {{ min-height: 20px; padding: 4px 8px; border: 1px solid {line}; border-radius: 8px;
                               background: {p.surface}; }}
          QLineEdit#condEdit[invalid='true'] {{ border: 2px solid {p.error}; padding: 3px 7px; }}
          QLineEdit#condEdit:focus {{ border: 2px solid {p.accent}; padding: 3px 7px; }}
          QLineEdit#condEdit[invalid='true']:focus {{ border: 2px solid {p.accent}; padding: 3px 7px; }}
          QLabel[rk='condError'] {{ font-size: 13px; color: {p.error}; }}
          QComboBox#condBox {{ border: 1px solid {line}; border-radius: 8px; background: {p.surface}; }}
          QComboBox#condBox:focus {{ border: 2px solid {p.accent}; }}
          QPushButton[filterChip='true'] {{ padding: 6px 12px 6px 14px; min-height: 16px; border: 1px solid {chip_line};
                                           border-radius: 13px; background: {p.accent_soft}; color: {p.accent}; }}
          QPushButton[filterChip='true']:hover {{ border: 1px solid {p.accent}; }}
          QPushButton[filterChip='true']:focus {{ border: 2px solid {p.accent}; padding: 5px 11px 5px 13px; }}
          QPushButton[textButton='true'] {{ border: 0; border-radius: 6px; padding: 5px 8px; background: transparent;
                                           color: {p.muted}; }}
          QPushButton[textButton='true']:hover {{ color: {p.text}; background: {p.accent_soft}; }}
          QPushButton[textButton='true']:focus {{ border: 2px solid {p.accent}; padding: 3px 6px; }}
          QPushButton#otherStock, QPushButton#otherMarket, QPushButton#emptyAction {{
                                   border: 1px solid {line}; border-radius: 13px; padding: 6px 12px; min-height: 16px;
                                   background: {p.surface}; color: {p.text}; }}
          QPushButton#otherMarket {{ color: {p.accent}; }}
          QPushButton#otherStock:hover, QPushButton#otherMarket:hover, QPushButton#emptyAction:hover {{
                                   background: {p.accent_soft}; }}
          QPushButton#otherStock:focus {{ border: 2px solid {p.accent}; padding: 5px 11px; }}
          QPushButton#otherMarket:focus {{ border: 2px solid {p.accent}; padding: 5px 11px; }}
          QPushButton#emptyAction:focus {{ border: 2px solid {p.accent}; padding: 5px 11px; }}
          QPushButton#stickyRank {{ border: 0; border-radius: 13px; padding: 4px 12px; min-height: 18px;
                                   background: {p.accent}; color: {p.on_accent}; font-size: 13px; font-weight: 600; }}
          QPushButton#stickyRank:focus {{ border: 2px solid {p.on_accent}; padding: 2px 10px; }}
          QFrame#summaryTile {{ background: {p.surface}; border: 1px solid {line}; border-radius: 12px; }}
          QFrame#rankRow {{ background: transparent; border: 0; border-radius: 12px; }}
          QFrame#rankRow:hover, QFrame#rankRow:focus {{ background: {p.accent_soft}; }}
          QFrame#rankRow[openable='false']:hover {{ background: transparent; }}
          QFrame#rankDivider {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
          QLabel[rk='page'] {{ font-size: 24px; font-weight: 600; letter-spacing: -0.6px; }}
          QLabel[rk='stickName'] {{ font-size: 16px; font-weight: 600; letter-spacing: -0.3px; }}
          QLabel[rk='age'], QLabel[rk='count'], QLabel[rk='hint'] {{ font-size: 13px; font-weight: 400;
                                                                    color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='condName'] {{ font-size: 13px; font-weight: 500; letter-spacing: -0.1px; }}
          QLabel[rk='condUnit'] {{ font-size: 13px; color: {p.muted}; }}
          QLabel[rk='sumName'] {{ font-size: 13px; font-weight: 500; color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='sumValue'] {{ font-size: 15px; font-weight: 600; letter-spacing: 0px; }}
          QLabel[rk='sumChange'] {{ font-size: 13px; font-weight: 600; letter-spacing: 0px; color: {t['flat']}; }}
          QLabel[rk='sumChange'][tone='up'] {{ color: {t['up']}; }}
          QLabel[rk='sumChange'][tone='down'] {{ color: {t['down']}; }}
          QLabel[rk='sumState'] {{ font-size: 12px; font-weight: 500; color: {p.warning}; padding: 3px 10px;
                                  border-radius: 9px; background: {t['flat_tint']}; letter-spacing: -0.1px; }}
          QLabel[rk='rank'] {{ font-size: 16px; font-weight: 600; color: {p.accent}; letter-spacing: 0px; }}
          QLabel[rk='name'] {{ font-size: 15px; font-weight: 500; letter-spacing: -0.2px; }}
          QLabel[rk='code'] {{ font-size: 12px; font-weight: 400; color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='sector'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='price'] {{ font-size: 15px; font-weight: 600; letter-spacing: 0px; }}
          QLabel[rk='change'] {{ font-size: 15px; font-weight: 600; letter-spacing: 0px; color: {t['flat']}; }}
          QLabel[rk='change'][tone='up'] {{ color: {t['up']}; }}
          QLabel[rk='change'][tone='down'] {{ color: {t['down']}; }}
          QLabel[rk='figure'] {{ font-size: 14px; font-weight: 400; color: {p.muted}; letter-spacing: 0px; }}
          QLabel[rk='figure'][ranked='true'] {{ font-weight: 600; color: {p.text}; }}
          QLabel[rk='head'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='head'][ranked='true'] {{ font-weight: 700; color: {p.accent}; }}
          QLabel[rk='badge'] {{ font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 9px;
                               color: {p.muted}; background: {p.surface_2}; letter-spacing: -0.1px; }}
          QLabel[rk='badge'][state='polled'], QLabel[rk='badge'][state='polled_us'] {{ color: {p.success};
                                                                               background: {p.accent_soft}; }}
          QLabel[rk='badge'][state='daily'], QLabel[rk='badge'][state='stale'] {{ color: {p.warning};
                                                                           background: {t['flat_tint']}; }}
          QLabel[rk='empty'] {{ font-size: 14px; color: {p.muted}; padding: 28px 8px 12px 8px; }}
        """


CRITERIA_GAP = 24             # between the ranking chips and the filters when they share a line
SEARCH_MIN, SEARCH_MAX = 220, 340   # the header search shrinks to SEARCH_MIN before it moves to its own line
FIT_SLACK = 24                # extra room needed to go back from two lines to one (`_fit`)
FILTER_POOL = 3 + len(S.CONDITIONS)   # filter chips: the search text, sub-market, sector, then one per condition
OTHERS_LIMIT = 4               # stocks outside the curated list offered under the search


def _section(top=0):
    """A transparent block that adds its own top gap only while shown (no gap left behind when hidden)."""
    widget = QWidget()
    widget.setObjectName("boardSection")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, top, 0, 0)
    layout.setSpacing(8)
    return widget, layout


def _number(text):
    """A typed bound ('-3', '+5', '2.5', '−1'), or None when empty or not a number."""
    text = str(text or "").strip().replace("−", "-").replace(",", "")
    if text in ("", "-", "+", ".", "-.", "+."):
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ro(word):
    """The Korean particle after `word`: '로' after a vowel or ㄹ, else '으로'."""
    last = str(word)[-1:] or " "
    if "가" <= last <= "힣":
        return "로" if (ord(last) - 0xAC00) % 28 in (0, 8) else "으로"
    return "(으)로"


FIGURE_FIELDS = {"value": "trading_value", "volume": "volume", "cap": "market_cap", "qscore": "q_score"}


class RankingBoard(QFrame):
    """One market's page: header row, index strip, criteria, conditions, active filters and the ranked list."""
    open_requested = pyqtSignal(object)
    listing_requested = pyqtSignal(object)  # a search suggestion outside the curated list
    loaded = pyqtSignal(str)
    category_changed = pyqtSignal(str)      # a chip click or set_category() changed the list shown
    page_changed = pyqtSignal(str)          # set_page() showed another market
    search_submitted = pyqtSignal()         # Enter in the pinned bar's search (the header search's is the view's)
    _progress = pyqtSignal(int, int, int)   # epoch, done, total; emitted on the worker thread, queued here

    def __init__(self, *, loader=None, locale=None, auto_load=True, clock=None, open_fn=None, limit=LIST_LIMIT,
                 summary_loader=None):
        super().__init__()
        from .market_summary import MarketSummary
        self.setObjectName("marketBoard")
        self.loader, self.auto_load, self.limit = loader, auto_load, limit
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.clock = clock or _utc_now
        self.open_fn = open_fn or R.session_open
        self.page = "kr"
        self.screens = {page: S.Screen(page) for page in S.PAGE_KEYS}  # each market keeps its own criteria
        self.others_fn = None        # (text, page) -> [(label, payload)]: stocks outside the curated list
        self.batches = {}            # group -> Batch: one fetch serves every category of its group
        self.ranked = []
        self._attempted = {}         # group -> when the last fetch failed outright
        self._rounds = {}            # group -> (Batch, when the round that fetched it started, seconds it took)
        self._error = ""
        self._loading = None         # (group, done, total) while a fetch runs
        self._job_group, self._job_started = None, None
        self._epoch, self._cancel, self._pending, self._stopped = 0, None, False, False
        self._syncing = self._syncing_edits = False
        self._message = None         # (PAGE_TEXT key, fields) under the filters; rendered in the window language
        self._invalid = {}           # range key -> (page, its limit) while an inverted pair typed there is kept
        self._head_wide = self._criteria_wide = None
        self._spec = ("value", (), False, False)  # the shown rows' (figure, figures, sparkline, sector) for column_plan
        self._ranked_column = "value"
        self._scroll, self._fitting, self._caption_text = None, False, None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self._progress.connect(self._on_progress)
        from .ranking_scores import RankingScores
        self.scores = RankingScores(self)
        self.scores.changed.connect(self.render)
        self.tick = QTimer(self)
        self.tick.setInterval(1000)
        self.tick.timeout.connect(self._tick)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header: market name, data state, age, a search within this market, refresh. A narrow page puts the
        # search on its own line under them (`_fit`), so nothing scrolls sideways.
        self.head = QGridLayout()
        self.head.setHorizontalSpacing(10)
        self.head.setVerticalSpacing(12)
        self.heading = _label(rk="page")
        self.badge = _label(rk="badge")
        self.caption = _label(rk="age")
        self.search = QLineEdit()
        self.search.setObjectName("marketSearch")
        self.search.setClearButtonEnabled(True)
        self.search.setProperty("qg_literal", True)
        self.search.setMinimumWidth(SEARCH_MIN)
        self.search.setMaximumWidth(SEARCH_MAX)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search.textChanged.connect(self.set_query)
        self.search.installEventFilter(self)  # its placeholder follows its width (`_render_placeholder`)
        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("rankRefresh")
        self.refresh_button.setProperty("qg_literal", True)
        self.refresh_button.clicked.connect(self._refresh_all)
        for column, widget in enumerate((self.heading, self.badge, self.caption, self.search, self.refresh_button)):
            self.head.addWidget(widget, 0, column, Qt.AlignmentFlag.AlignVCenter)
        self.head.setColumnStretch(2, 1)
        self.head.setColumnStretch(3, 1)  # the search grows to SEARCH_MAX; the age column takes the rest
        layout.addLayout(self.head)

        # Index strip (hidden while it has nothing to show).
        self.summary_section, summary_layout = _section(14)
        self.summary = MarketSummary(loader=summary_loader, locale=self.ctx, auto_load=auto_load)
        self.summary.changed.connect(self._sync_summary)
        summary_layout.addWidget(self.summary)
        layout.addWidget(self.summary_section)
        layout.addSpacing(18)

        # Criteria: how the list is ranked (chips) on the left; what it includes (sub-market, sector, 조건) together
        # on the right. A narrow page puts the filters on a second line.
        self.criteria = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.criteria.setSpacing(CRITERIA_GAP)
        self.chips_layout = QHBoxLayout()
        self.chips_layout.setSpacing(6)
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        self.category_buttons = {}
        for key, _en, _ko in R.CATEGORIES:
            button = Chip()
            button.clicked.connect(lambda checked=False, k=key: self.set_category(k))
            self.category_group.addButton(button)
            self.category_buttons[key] = button
            self.chips_layout.addWidget(button)
        self.chips_layout.addStretch(1)  # chips keep their natural width when the filters wrap under them
        self.criteria.addLayout(self.chips_layout)
        self.filters_layout = QHBoxLayout()
        self.filters_layout.setSpacing(8)
        self.filters_gap = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.filters_layout.addItem(self.filters_gap)
        self.sub_groups, self._sub_buttons, self.segments = {}, {}, {}
        for page in S.PAGE_KEYS:
            group = QButtonGroup(self)
            group.setExclusive(True)
            self.sub_groups[page], self._sub_buttons[page] = group, {}
            if not S.SUBS[page]:
                continue
            segment = QFrame()  # the sub-market as one compact segmented control, not page tabs
            segment.setObjectName("segment")
            row = QHBoxLayout(segment)
            row.setContentsMargins(2, 2, 2, 2)
            row.setSpacing(2)
            for key, _en, _ko in S.SUBS[page]:
                button = QPushButton()
                button.setCheckable(True)
                button.setProperty("tool", True)
                button.setProperty("qg_literal", True)
                button.clicked.connect(lambda checked=False, k=key: self.set_sub(k))
                group.addButton(button)
                self._sub_buttons[page][key] = button
                row.addWidget(button)
            segment.hide()
            self.segments[page] = segment
            self.filters_layout.addWidget(segment, 0, Qt.AlignmentFlag.AlignVCenter)
        self.sector_box = QComboBox()
        self.sector_box.setObjectName("rankSector")
        self.sector_box.setProperty("qg_literal", True)
        self.sector_box.setMinimumWidth(150)
        self.sector_box.currentIndexChanged.connect(self._sector_changed)
        self.filters_layout.addWidget(self.sector_box, 0, Qt.AlignmentFlag.AlignVCenter)
        self.conditions_button = QPushButton()
        self.conditions_button.setObjectName("conditionsToggle")
        self.conditions_button.setProperty("qg_literal", True)
        self.conditions_button.setCheckable(True)
        self.conditions_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # the chevron after the text
        self.conditions_button.toggled.connect(self._conditions_toggled)
        self.filters_layout.addWidget(self.conditions_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.filters_tail = QSpacerItem(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.filters_layout.addItem(self.filters_tail)
        self.criteria.addLayout(self.filters_layout, 1)
        layout.addLayout(self.criteria)

        # Conditions row (조건): built from core.market.screen.CONDITIONS, so a new condition needs no UI code. Its
        # one clear action ends the flow; an inverted range says why on a line of its own.
        self.conditions_section, conditions_layout = _section(12)
        self.conditions_panel = QFrame()
        self.conditions_panel.setObjectName("conditionsPanel")
        panel = QVBoxLayout(self.conditions_panel)
        panel.setContentsMargins(18, 12, 12, 12)
        panel.setSpacing(6)
        flow_host = QWidget()
        flow_host.setObjectName("condGroup")
        self.condition_flow = Flow(flow_host, spacing=28, line_spacing=10)
        self.condition_groups, self.condition_names, self.condition_controls = {}, {}, {}
        for item in S.CONDITIONS:
            group = QWidget()
            group.setObjectName("condGroup")
            row = QHBoxLayout(group)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            name = _label(rk="condName")
            row.addWidget(name)
            row.addSpacing(4)
            if item.kind == "range":
                low, high = QLineEdit(), QLineEdit()
                validator = QDoubleValidator(-1000.0, 100000.0, 2, self)
                validator.setNotation(QDoubleValidator.Notation.StandardNotation)
                validator.setLocale(QLocale.c())
                for edit in (low, high):
                    edit.setObjectName("condEdit")
                    edit.setProperty("qg_literal", True)
                    edit.setFixedWidth(72)
                    edit.setAlignment(Qt.AlignmentFlag.AlignRight)
                    edit.setValidator(validator)
                    edit.textEdited.connect(lambda _text, k=item.key: self._range_edited(k))
                between = _label(rk="condUnit")
                between.setText("~")
                unit_low, unit_high = _label(rk="condUnit"), _label(rk="condUnit")
                unit_low.setText("%")
                unit_high.setText("%")
                for widget in (low, unit_low, between, high, unit_high):
                    row.addWidget(widget)
                self.condition_controls[item.key] = (low, high)
            else:
                box = QComboBox()
                box.setObjectName("condBox")
                box.setProperty("qg_literal", True)
                box.setMinimumWidth(130)
                box.currentIndexChanged.connect(lambda _index, k=item.key: self._minimum_chosen(k))
                row.addWidget(box)
                self.condition_controls[item.key] = (box,)
            self.condition_flow.addWidget(group)
            self.condition_groups[item.key], self.condition_names[item.key] = group, name
        self.conditions_clear = QPushButton()
        self.conditions_clear.setProperty("textButton", True)
        self.conditions_clear.setProperty("qg_literal", True)
        self.conditions_clear.clicked.connect(self.clear_conditions)
        self.condition_flow.addWidget(self.conditions_clear)
        panel.addWidget(flow_host)
        self.condition_error = _label(rk="condError", wrap=True)
        self.condition_error.hide()
        panel.addWidget(self.condition_error)
        conditions_layout.addWidget(self.conditions_panel)
        self.conditions_section.hide()
        layout.addWidget(self.conditions_section)

        # What narrows the list, as chips (one click each to remove) and one clear action; the count; then other
        # markets that have the name searched, and stocks outside the list.
        self.active_section, active_layout = _section(14)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(12)
        chips_host, self.chip_flow = _flow_host(6, 6)
        self.filter_chips = []
        for _ in range(FILTER_POOL):
            chip = QPushButton()
            chip.setProperty("filterChip", True)
            chip.setProperty("qg_literal", True)
            chip.clicked.connect(lambda checked=False, c=chip: self._chip_clicked(c))
            chip.hide()
            self.chip_flow.addWidget(chip)
            self.filter_chips.append(chip)
        self.clear_button = QPushButton()
        self.clear_button.setProperty("textButton", True)
        self.clear_button.setProperty("qg_literal", True)
        self.clear_button.clicked.connect(self.clear_filters)
        self.chip_flow.addWidget(self.clear_button)
        chips_row.addWidget(chips_host, 1)
        self.count = _label(rk="count")
        self.count.setContentsMargins(0, 6, 0, 0)
        chips_row.addWidget(self.count, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        active_layout.addLayout(chips_row)
        self.others_host, others_flow = _flow_host(6, 6)
        self.market_buttons = []
        for _ in range(len(S.PAGE_KEYS) - 1):
            button = QPushButton()
            button.setObjectName("otherMarket")
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, b=button: self._other_market_clicked(b))
            button.hide()
            others_flow.addWidget(button)
            self.market_buttons.append(button)
        self.others_label = _label(rk="hint")
        others_flow.addWidget(self.others_label)
        self.other_buttons = []
        for _ in range(OTHERS_LIMIT):
            button = QPushButton()
            button.setObjectName("otherStock")
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, b=button: self._other_clicked(b))
            button.hide()
            others_flow.addWidget(button)
            self.other_buttons.append(button)
        active_layout.addWidget(self.others_host)
        self.message = _label("caption", wrap=True)
        self.message.hide()
        active_layout.addWidget(self.message)
        self.active_section.hide()
        layout.addWidget(self.active_section)
        layout.addSpacing(20)

        divider = QFrame()
        divider.setObjectName("rankDivider")
        layout.addWidget(divider)
        layout.addSpacing(8)
        self.column_header = ColumnHeader()
        self.column_header.sort_requested.connect(self.sort_by)
        layout.addWidget(self.column_header)
        layout.addSpacing(4)
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        layout.addLayout(self.list_layout)
        self.rows = []
        self.empty = _label(rk="empty", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)
        self.empty_actions_host = QWidget()
        self.empty_actions_host.setObjectName("boardSection")
        actions = QHBoxLayout(self.empty_actions_host)
        actions.setContentsMargins(0, 0, 0, 8)
        actions.setSpacing(8)
        actions.addStretch(1)
        self.empty_actions = []
        for _ in range(2):
            button = QPushButton()
            button.setObjectName("emptyAction")
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, b=button: getattr(b, "action", lambda: None)())
            actions.addWidget(button)
            self.empty_actions.append(button)
        actions.addStretch(1)
        self.empty_actions_host.hide()
        layout.addWidget(self.empty_actions_host)
        layout.addSpacing(12)
        self.footnote = _label("caption", wrap=True)
        layout.addWidget(self.footnote)

        self.sticky = StickyBar()
        self.sticky.setParent(self)  # moved onto the scroll area's viewport once the page is in one (`_attach_scroll`)
        self.sticky.hide()
        self.sticky.search.textChanged.connect(self.set_query)
        self.sticky.search.returnPressed.connect(self.search_submitted)
        self.sticky.header.sort_requested.connect(self.sort_by)
        self.sticky.rank_button.clicked.connect(self._back_to_criteria)
        self.set_theme(False)
        self.set_locale(self.ctx)

    # Text -------------------------------------------------------------------------------------
    def _t(self, en, **fields):
        """English source; Korean from owner_ui_language/market.py (templates fill the fields)."""
        from .translations import translate
        source = en.format(**fields) if fields else en
        return translate(source, "ko") if self.ctx.language == "ko" else source

    def _lang(self):
        return "ko" if self.ctx.language == "ko" else "en"

    def _p(self, key, **fields):
        """A short word or template of the market page (owner_ui_language.market.PAGE_TEXT), in the window language."""
        from .owner_ui_language.market import PAGE_TEXT
        english, korean = PAGE_TEXT[key]
        template = korean if self.ctx.language == "ko" else english
        return template.format(**fields) if fields else template

    # Selection --------------------------------------------------------------------------------
    @property
    def screen(self):
        """The shown market's criteria (`core.market.screen.Screen`)."""
        return self.screens[self.page]

    def _set_screen(self, screen):
        self.screens[screen.page] = screen

    @property
    def category(self):
        return self.screen.category

    @property
    def sector(self):
        return self.screen.sector

    @property
    def sub(self):
        return self.screen.sub

    @property
    def query(self):
        return self.screen.text

    @property
    def market(self):
        """The list key of `rankings.MARKETS` (or 'crypto') for what is shown, as the earlier market buttons named it."""
        return self.sub if self.page == "kr" and self.sub else self.page

    @property
    def sub_buttons(self):
        """The shown market's sub-market buttons, by `screen.SUBS` key ('' is the whole market)."""
        return self._sub_buttons[self.page]

    @property
    def head_value(self):
        """The heading of the ranked figure's column (trading value under 급상승/급하락)."""
        return self.column_header.cells[self._spec[0]]

    def group(self):
        return R.group_of(self.page)

    def set_page(self, page):
        """Show one market's page (`screen.PAGE_KEYS`); its criteria are kept from its last visit."""
        if page not in S.PAGE_KEYS:
            raise ValueError(f"Unknown market page {page!r}")
        changed, group_before = page != self.page, self.group()
        self.page = page
        if changed:
            self._message = None  # a 'not found' answered the other market's search
        self.summary.set_page(page)
        self._fill_sectors()
        self._sync_search()
        self.render()
        if changed:
            self.page_changed.emit(page)
        if self.group() != group_before and self.isVisible() and self.auto_load:
            QTimer.singleShot(0, self.refresh)
        return True

    def set_market(self, key):
        """Earlier list keys: 'kr', 'kospi', 'kosdaq', 'us' (and 'crypto'): the market page and its sub-market."""
        R.group_of(key)  # refuses an unknown key
        page = key if key in S.PAGE_KEYS else "kr"
        self.set_page(page)
        self.set_sub(key if key in ("kospi", "kosdaq") else "")
        return True

    def set_sub(self, key):
        if key not in {k for k, _en, _ko in S.SUBS[self.page]} | {""}:
            raise ValueError(f"Sub-market {key!r} is not in {self.page!r}")
        self._set_screen(replace(self.screen, sub=key))
        self.render()
        return True

    def set_category(self, key):
        if key not in R.CATEGORY_KEYS:
            raise ValueError(f"Unknown ranking category {key!r}")
        changed = key != self.category
        self._set_screen(replace(self.screen, category=key))
        self.render()
        if changed:
            self.category_changed.emit(key)
        return True

    def sort_by(self, column):
        """A column heading clicked: rank by that figure, or by the change (급상승, then 급하락 on a second click)."""
        if column == "change":
            return self.set_category("losers" if self.category == "gainers" else "gainers")
        if column in FIGURES and not S.category_note(self.page, column):
            return self.set_category(column)
        return False

    def set_sector(self, key):
        index = self.sector_box.findData(key or "")
        if index < 0:
            raise ValueError(f"Sector {key!r} is not in this market")
        self.sector_box.setCurrentIndex(index)

    def _sector_changed(self, _index):
        if self._syncing:
            return
        self._set_screen(replace(self.screen, sector=self.sector_box.currentData() or ""))
        self.render()

    def _fill_sectors(self):
        lang, keep = self._lang(), self.sector
        self._syncing = True
        try:
            self.sector_box.clear()
            self.sector_box.addItem(self._t("All sectors"), "")
            for key in R.sectors_in(self.page):
                self.sector_box.addItem(R.text(R.SECTORS, key, lang), key)
            self.sector_box.setCurrentIndex(max(0, self.sector_box.findData(keep)))
        finally:
            self._syncing = False
        self.sector_box.setAccessibleName(self._t("Sector"))
        self.sector_box.setVisible(bool(R.sectors_in(self.page)))

    def set_query(self, text):
        """Narrow the shown market's list to names, codes or sectors matching `text` (the header search)."""
        text = str(text or "")
        if text == self.query:
            return
        self._message = None  # a 'not found' message belongs to the text it answered
        self._set_screen(replace(self.screen, text=text))
        self._sync_search()
        self.render()

    def _sync_search(self):
        """Both search fields show the shown market's text. No blockSignals: the field's own clear button follows
        its textChanged (UI-D10 review: a blocked signal left the clear mark on an empty field); the set_query
        it reaches finds the text unchanged and stops."""
        for edit in (self.search, self.sticky.search):
            if edit.text() != self.query:
                edit.setText(self.query)

    def set_limit(self, key, low=None, high=None):
        """Set one condition of the shown market (`screen.CONDITIONS`); no bound clears it."""
        self._set_screen(self.screen.with_limit(key, low, high))
        self.render()

    def clear_conditions(self):
        self._set_screen(self.screen.cleared())
        self.render()

    def clear_filters(self):
        """One click: the search text, the sub-market, the sector and every condition of this market (the ranking
        stays: it orders the list, it does not narrow it)."""
        self._set_screen(replace(self.screen.cleared(), text="", sub="", sector=""))
        self._sync_search()
        self.render()

    def _clear_place(self):
        self._set_screen(replace(self.screen, sub="", sector=""))
        self.render()

    def set_conditions_open(self, shown):
        self.conditions_button.setChecked(bool(shown))

    def _conditions_toggled(self, shown):
        self.conditions_section.setVisible(bool(shown))
        self._render_conditions_button()
        self._render_active(self.ranked)  # the condition chips show only while the panel is closed

    def _mark_range(self, key, bad):
        """Mark a range condition's two fields as inverted (or not), with the reason as tooltip."""
        for edit in self.condition_controls[key]:
            _set_flag(edit, "invalid", bad)
            edit.setToolTip(self._t("The lower bound is above the upper bound.") if bad else "")

    def _range_edited(self, key):
        low_edit, high_edit = self.condition_controls[key]
        low, high = _number(low_edit.text()), _number(high_edit.text())
        if low is not None and high is not None and low > high:
            # The list keeps the last valid range until the bounds agree; the typed pair stays while that range
            # does (`_render_conditions`).
            self._invalid[key] = (self.page, self.screen.limit(key))
            self._mark_range(key, True)
            self._render_condition_error()
            return
        self._invalid.pop(key, None)
        self._set_screen(self.screen.with_limit(key, low, high))
        self._syncing_edits = True
        try:
            self.render()
        finally:
            self._syncing_edits = False

    def _minimum_chosen(self, key):
        if self._syncing:
            return
        box = self.condition_controls[key][0]
        value = box.currentData()
        self._set_screen(self.screen.with_limit(key, value if value else None))
        self.render()

    def _chip_clicked(self, chip):
        key = chip.property("filterKey")
        if key == "text":
            self.set_query("")
        elif key == "sub":
            self.set_sub("")
        elif key == "sector":
            self.set_sector("")
        elif key:
            self.set_limit(key)

    def _other_clicked(self, button):
        payload = getattr(button, "payload", None)
        if payload is not None:
            self.listing_requested.emit(payload)

    def _other_market_clicked(self, button):
        """'미국 주식에서 보기: 테슬라 TSLA': that market's page, searching the same text."""
        page = getattr(button, "payload", None)
        if page in S.PAGE_KEYS:
            self.screens[page] = replace(self.screens[page], text=self.query)
            self.set_page(page)

    def _refresh_all(self):
        self.refresh(manual=True)
        self.summary.refresh(manual=True)

    def _back_to_criteria(self):
        """The pinned bar's ranking chip: back up to the criteria, focus on the chip in use."""
        if self._scroll is not None:
            self._scroll.verticalScrollBar().setValue(0)
        self.category_buttons[self.category].setFocus(Qt.FocusReason.OtherFocusReason)

    # Loading ----------------------------------------------------------------------------------
    def due(self, group=None, now=None):
        """Whether the group's next round of requests should start.

        Timed from the START of the round that fetched the batch shown (its `fetched_at` is stamped after the
        last request), so during the session a round starts every `LIVE_REFRESH_SECONDS` and each stock is
        asked every 45 s, as the state says, while a round takes less than that; a longer round makes the
        next one due at once and the state "KIS · 갱신 지연" (`state`). A batch set from outside, with no
        round recorded, is timed from its `fetched_at`.
        """
        group = group or self.group()
        now = now or self.clock()
        batch = self.batches.get(group)
        failed_at = self._attempted.get(group)
        if failed_at is not None and (batch is None or failed_at > _parse(batch.fetched_at)):
            return (now - failed_at).total_seconds() >= RETRY_SECONDS
        if batch is None:
            return True
        if not batch.records:
            limit = RETRY_SECONDS
        elif batch.mode == "kis" and self.open_fn(group, now):
            limit = LIVE_REFRESH_SECONDS
        else:
            limit = IDLE_REFRESH_SECONDS
        round_ = self._round(group, batch)
        since = round_[0] if round_ is not None else _parse(batch.fetched_at)
        return (now - since).total_seconds() >= limit

    def _round(self, group, batch):
        """(when the round that fetched `batch` started, seconds it took), or None for a batch set from outside."""
        kept = self._rounds.get(group)
        return kept[1:] if kept is not None and kept[0] is batch else None

    def refresh(self, *, manual=False):
        """Fetch the current group when due (or now, when `manual`); False when nothing started.

        Automatic fetches run only while the list is visible: a market switched underneath a stock's screen
        (`markets_view.open_instrument`) loads when the list comes back, not behind the stock screen."""
        group = self.group()
        if self._stopped:
            return False
        if self.jobs.busy:
            self._pending = self._pending or manual
            return False
        if self.loader is None or (not manual and (not self.isVisible() or not self.due(group))):
            return False
        self._epoch += 1
        epoch, cancel, loader = self._epoch, threading.Event(), self.loader
        self._cancel, self._job_group, self._error = cancel, group, ""
        self._job_started = self.clock()   # the next round is timed from here (`due`)
        members = R.members_of(group)
        self._loading = (group, 0, len(members))
        self._pending = False

        def progress(done, total):
            self._progress.emit(epoch, done, total)

        started = self.jobs.start(lambda: (epoch, group, loader(group, members, cancel.is_set, progress)))
        self.render()
        return started

    @pyqtSlot(int, int, int)
    def _on_progress(self, epoch, done, total):
        if epoch == self._epoch and self._loading is not None:
            self._loading = (self._loading[0], done, total)
            self._render_status()

    @pyqtSlot(object)
    def _loaded(self, value):
        epoch, group, batch = value
        if epoch != self._epoch:
            return
        self._loading = None
        if isinstance(batch, R.Batch):
            self.batches[group] = batch
            self._attempted.pop(group, None)
            if self._job_started is not None:
                took = max(0.0, (self.clock() - self._job_started).total_seconds())
                self._rounds[group] = (batch, self._job_started, took)
        self.render()
        self.loaded.emit(group)

    @pyqtSlot(str)
    def _failed(self, code):
        if self._stopped:
            return
        self._loading = None
        self._error = code
        if self._job_group is not None:
            self._attempted[self._job_group] = self.clock()
        self.render()

    @pyqtSlot(bool)
    def _busy(self, busy):
        self.refresh_button.setEnabled(not busy)
        if not busy and (self._pending or (self.auto_load and self.isVisible() and self.due())):
            manual = self._pending
            QTimer.singleShot(0, lambda: self.refresh(manual=manual))

    def _tick(self):
        if not self.isVisible():
            return
        self._render_status()
        if self.auto_load and not self.jobs.busy and self.due():
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self._attach_scroll()
        self._fit()
        if self.auto_load:
            self.tick.start()
            QTimer.singleShot(0, self.refresh)
        QTimer.singleShot(0, self._place_sticky)

    def hideEvent(self, event):
        self.tick.stop()
        self.scores.stop()
        self.sticky.hide()
        super().hideEvent(event)

    def stop(self):
        """Window closing: cancel the fetch between requests, drop its answer, start nothing more."""
        self.tick.stop()
        self.scores.stop()
        self.sticky.hide()
        self._stopped, self._pending = True, False
        self._epoch += 1
        self._loading = None
        if self._cancel is not None:
            self._cancel.set()

    # Width: the page decides from the room it has in its scroll area, never from its own width (a page cannot be
    # narrower than its minimum, so judging by its own width it never knew it overflowed; UI-D10 review).
    def _scroll_area(self):
        from PyQt6.QtWidgets import QScrollArea
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        return parent

    def _attach_scroll(self):
        scroll = self._scroll_area()
        if scroll is None or scroll is self._scroll:
            return
        self._scroll = scroll
        scroll.viewport().installEventFilter(self)
        scroll.verticalScrollBar().valueChanged.connect(self._place_sticky)
        self.sticky.setParent(scroll.viewport())
        self.sticky.setStyleSheet(self.styleSheet())
        self.sticky.hide()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            if watched is self.search:
                self._render_placeholder()
            elif self._scroll is not None and watched is self._scroll.viewport():
                self._fit()
                self._place_sticky()
        return False

    def available_width(self):
        """The width this page can take without a sideways scroll: its scroll area's viewport less the margins
        around the page; its own width outside a scroll area."""
        scroll = self._scroll
        if scroll is None or scroll.widget() is None:
            return self.width()
        chrome = max(0, scroll.widget().width() - self.width())
        return max(0, scroll.viewport().width() - chrome)

    def _list_width(self):
        return min(self.width(), self.available_width()) if self._scroll is not None else self.width()

    def _fit(self):
        """One line or two for the header and the criteria, sparklines in the strip or not, and the list's
        columns, from the room there is (`available_width`)."""
        if self._fitting:
            return
        self._fitting = True
        try:
            room = self.available_width()
            if room > 0:
                before = (self._head_wide, self._criteria_wide, self.summary.compact)
                spacing = self.head.horizontalSpacing()
                head = (self.heading.sizeHint().width() + self.badge.sizeHint().width()
                        + (self.caption.sizeHint().width() if self.caption.isVisibleTo(self) else 0)
                        + SEARCH_MIN + self.refresh_button.sizeHint().width() + 4 * spacing)
                # A little slack before going back to one line, so an age caption ticking from "9초" to "10초"
                # at the threshold does not make the header jump between one line and two.
                slack = lambda wide: 0 if wide else FIT_SLACK
                self._set_head_wide(room >= head + slack(self._head_wide))
                need = self.chips_layout.sizeHint().width() + CRITERIA_GAP + self.filters_layout.sizeHint().width()
                self._set_criteria_wide(room >= need + slack(self._criteria_wide))
                self.summary.set_compact(room < self.summary.wide_width())
                if (self._head_wide, self._criteria_wide, self.summary.compact) != before:
                    self.summary.updateGeometry()
                    self.updateGeometry()  # a smaller minimum reaches the scroll area now, not at the next relayout
            self._reflow()
            self._fit_scroll_page()
        finally:
            self._fitting = False

    def _fit_scroll_page(self):
        """Give the scroll area's page the viewport's width as soon as the narrower columns allow it.

        After a window shrinks, the rows keep their wider fixed columns until `_reflow`; the scroll area had already
        sized its page to that old minimum and only widens or narrows it again at a later layout pass. On a slow
        runner (PR 109, Windows CI) that pass had not come 3 s later, so the page scrolled sideways at 1000 px.
        """
        scroll = self._scroll
        page = scroll.widget() if scroll is not None else None
        if page is None or not scroll.widgetResizable():
            return
        if page.layout() is not None:
            page.layout().activate()  # the rows' new fixed widths, now: the minimum below must be the new one
        want = max(scroll.viewport().width(), page.minimumSizeHint().width())
        if page.width() != want:
            page.resize(want, page.height())

    def _set_head_wide(self, wide):
        if wide == self._head_wide:
            return
        self._head_wide = wide
        self.head.removeWidget(self.search)
        if wide:
            self.head.addWidget(self.search, 0, 3, Qt.AlignmentFlag.AlignVCenter)
            self.search.setMaximumWidth(SEARCH_MAX)
        else:
            self.head.addWidget(self.search, 1, 0, 1, 5)
            self.search.setMaximumWidth(16777215)
        self._render_placeholder()

    def _set_criteria_wide(self, wide):
        if wide == self._criteria_wide:
            return
        self._criteria_wide = wide
        self.criteria.setDirection(QBoxLayout.Direction.LeftToRight if wide else QBoxLayout.Direction.TopToBottom)
        self.criteria.setSpacing(CRITERIA_GAP if wide else 12)
        grow, keep = QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        self.filters_gap.changeSize(0, 0, grow if wide else keep, QSizePolicy.Policy.Minimum)
        self.filters_tail.changeSize(0, 0, keep if wide else grow, QSizePolicy.Policy.Minimum)
        self.filters_layout.invalidate()

    def _plan(self):
        figure, figures, spark, sector = self._spec
        return column_plan(self._list_width(), figure=figure, figures=figures, spark=spark, sector=sector)

    def _reflow(self):
        plan = self._plan()
        self.column_header.apply_plan(plan)
        self.sticky.header.apply_plan(plan)
        for row in self.rows:
            row.apply_plan(plan)

    def _place_sticky(self, *_args):
        """Show the pinned bar while the list's own headings are above the view and rows are still under it."""
        bar, scroll = self.sticky, self._scroll
        if scroll is None:
            return
        viewport = scroll.viewport()
        rows = [row for row in self.rows if row.isVisible()]
        show = False
        if self.isVisible() and rows and self.column_header.isVisible():
            height = bar.sizeHint().height()
            top = self.column_header.mapTo(viewport, QPoint(0, 0)).y()
            bottom = rows[-1].mapTo(viewport, QPoint(0, rows[-1].height())).y()
            show = top < 0 and bottom > height + 24
        if show:
            left = self.mapTo(viewport, QPoint(0, 0)).x()
            bar.setGeometry(left, 0, self.width(), bar.sizeHint().height())
            bar.raise_()
        if show != bar.isVisible():
            if not show and bar.search.hasFocus():
                self.search.setFocus(Qt.FocusReason.OtherFocusReason)
            bar.setVisible(show)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()
        self._place_sticky()

    # Presentation -----------------------------------------------------------------------------
    def set_locale(self, ctx):
        """Every text in the new language from what is already loaded: never a fetch."""
        self.ctx = ctx
        self.summary.set_locale(ctx)
        self._fill_sectors()
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        palette = DARK if self.dark else LIGHT
        sheet = board_stylesheet(palette, self.dark)
        self.setStyleSheet(sheet)
        if self.sticky.parentWidget() is not self:
            self.sticky.setStyleSheet(sheet)
        for chip in self.category_buttons.values():
            chip.ring = QColor(palette.on_accent)
            chip.update()
        self.summary.set_theme(self.dark)
        self.render()

    def _sync_summary(self):
        self.summary_section.setVisible(self.summary.wanted())
        # The strip's "지연·일별" is said once: not again beside the header badge when the list is daily too.
        self.summary.state.setVisible(self.summary.has_data() and self.state() != "daily")
        self._fit()  # tiles that just got their figures may need the compact strip

    def _render_placeholder(self):
        """The long placeholder ('…에서 찾기 · 이름, 코드, 업종') when the field has room for it, else the short one
        (its accessible name says the same)."""
        name = S.page_text(self.page, self._lang())
        short = self._t("Search within {market}", market=name)
        if self.page == "crypto":
            text = self._p("find_coins")
        elif self.page in R.ETF_GROUPS:  # an ETF list has no sectors to search by
            text = self._p("find_etfs", market=name)
        else:
            text = self._t("Find in {market}: name, code, sector", market=name)
        room = self.search.width() - 48  # its padding and the clear button
        if self.search.fontMetrics().horizontalAdvance(text) > room:
            text = short
        if self.search.placeholderText() != text:
            self.search.setPlaceholderText(text)
        self.sticky.search.setPlaceholderText(self._t("Search within {market}", market=name))

    def _render_chrome(self):
        """Labels, chips and filters for the shown market, in the window language."""
        lang, page, screen = self._lang(), self.page, self.screen
        name = S.page_text(page, lang)
        self.heading.setText(name)
        self.heading.setAccessibleName(name)
        self._render_placeholder()
        for edit in (self.search, self.sticky.search):
            edit.setAccessibleName(self._t("Search within {market}", market=name))
        # A bare 'Refresh' pair would retranslate every other Refresh button in the window.
        self.refresh_button.setText("새로고침" if lang == "ko" else "Refresh")
        self.refresh_button.setAccessibleName(self._t("Refresh the ranked list"))
        for key, button in self.category_buttons.items():
            button.setText(R.text(R.CATEGORIES, key, lang))
            # A ranking this market cannot make is left out (the footnote says why), not shown as a dead chip.
            button.setVisible(not S.category_note(page, key))
            button.setToolTip("")
            button.setChecked(key == screen.category)
        for each, buttons in self._sub_buttons.items():
            for key, button in buttons.items():
                button.setText(S.sub_text(each, key, lang))
                button.setChecked(each == page and key == screen.sub)
                button.setVisible(each == page)
        for each, segment in self.segments.items():
            segment.setVisible(each == page)
            segment.setAccessibleName(self._p("sub_market"))
        self._syncing = True
        try:
            index = self.sector_box.findData(screen.sector)
            if index >= 0 and index != self.sector_box.currentIndex():
                self.sector_box.setCurrentIndex(index)
        finally:
            self._syncing = False
        self.sticky.name.setText(name)
        self.sticky.rank_button.setText(self._p("ranked_by", name=R.text(R.CATEGORIES, screen.category, lang)))
        self.sticky.rank_button.setToolTip(self._p("back_to_criteria"))
        self.sticky.rank_button.setAccessibleName(self._p("back_to_criteria"))
        self._render_conditions()
        self._render_conditions_button()

    def _render_conditions_button(self):
        from PyQt6.QtGui import QIcon
        from .typography import icon_dir
        count = len(self.screen.limits)
        word = self._p("conditions")
        self.conditions_button.setText(f"{word} {count}" if count else word)
        shown = self.conditions_button.isChecked()
        theme = "dark" if self.dark else "light"
        self.conditions_button.setIcon(QIcon(f"{icon_dir()}/chevron-{'up' if shown else 'down'}-{theme}.svg"))
        self.conditions_button.setAccessibleName(
            self._t("Conditions: {count} set", count=count) if count else word)
        names = ", ".join(item.label(self._lang()) for item in self.screen.conditions())
        self.conditions_button.setToolTip(self._p("conditions_tip", names=names, ro=_ro(names)))

    def _render_conditions(self):
        """The condition controls of the shown market, holding its current limits (signals held back).

        An inverted range typed by the user stays in its fields, marked, while the market and that condition's
        limit are what they were when it was typed; any other change (the chip's ×, 조건 지우기, 모두 지우기,
        another market) shows the screen's own limit again, unmarked (UI-D10 review)."""
        lang, page, screen = self._lang(), self.page, self.screen
        self._syncing = True
        try:
            for item in S.CONDITIONS:
                group = self.condition_groups[item.key]
                group.setVisible(item.available(page))
                self.condition_names[item.key].setText(item.label(lang))
                low, high = screen.limit(item.key)
                controls = self.condition_controls[item.key]
                if item.kind == "range":
                    kept = self._invalid.get(item.key) == (page, (low, high))
                    if not kept:
                        self._invalid.pop(item.key, None)
                    for edit, value, hint in ((controls[0], low, self._p("min")), (controls[1], high, self._p("max"))):
                        edit.setPlaceholderText(hint)
                        edit.setAccessibleName(f"{item.label(lang)} {hint} %")
                        if not kept and not self._syncing_edits and _number(edit.text()) != value:
                            edit.setText("" if value is None else f"{value:g}")
                    self._mark_range(item.key, kept)
                    continue
                box = controls[0]
                steps = tuple(float(step) for step in item.steps.get(page, ()))
                if low is not None and float(low) not in steps:
                    steps = tuple(sorted(steps + (float(low),)))  # a bound set from code is shown as itself
                filled = (page, lang, steps)
                if getattr(box, "filled", None) != filled:  # refilled only when its market or language changes
                    box.clear()
                    box.addItem(self._p("any"), 0.0)
                    for step in steps:
                        box.addItem(self._p("or_more", value=S.threshold_text(step, item.unit, page, lang)), step)
                    box.filled = filled
                index = box.findData(float(low)) if low is not None else 0
                if box.currentIndex() != index:
                    box.setCurrentIndex(index)
                box.setAccessibleName(item.label(lang))
            self.conditions_clear.setText(self._t("Clear conditions"))
            self.conditions_clear.setEnabled(bool(screen.limits))
        finally:
            self._syncing = False
        self._render_condition_error()
        self.condition_flow.invalidate()

    def _render_condition_error(self):
        self.condition_error.setText(self._t("The lower bound is above the upper bound."))
        self.condition_error.setVisible(bool(self._invalid))

    def _limit_text(self, item, low, high):
        lang, page = self._lang(), self.page
        name = item.label(lang)
        fmt = lambda value: S.threshold_text(value, item.unit, page, lang)
        if low is not None and high is not None:
            return self._p("between", name=name, low=fmt(low), high=fmt(high))
        if low is not None:
            return self._p("at_least", name=name, value=fmt(low))
        return self._p("at_most", name=name, value=fmt(high))

    def _render_active(self, rows):
        """Chips for what narrows the list (the search text, sub-market, sector and, while the 조건 panel is
        closed, each condition), one clear action, the count, other markets that have the name, stocks outside
        the list and the message."""
        screen, lang = self.screen, self._lang()
        panel = self.conditions_button.isChecked()
        chips = []
        if screen.text.strip():
            chips.append(("text", f"‘{screen.text.strip()}’"))
        if screen.sub:
            chips.append(("sub", S.sub_text(self.page, screen.sub, lang)))
        if screen.sector:
            chips.append(("sector", R.text(R.SECTORS, screen.sector, lang)))
        if not panel:  # the open panel shows the conditions itself
            chips += [(item.key, self._limit_text(item, low, high)) for item, low, high in screen.active()]
        for index, chip in enumerate(self.filter_chips):
            if index < len(chips):
                key, text = chips[index]
                chip.setProperty("filterKey", key)
                chip.setText(f"{text}  ×")
                chip.setAccessibleName(self._t("Remove filter: {name}", name=text))
                chip.setToolTip(self._t("Remove this filter"))
                chip.show()
            else:
                chip.setProperty("filterKey", "")
                chip.hide()
        self.clear_button.setText(self._p("clear_all"))
        self.clear_button.setToolTip(self._p("clear_all_tip"))
        self.clear_button.setVisible(len(chips) > 1 and not panel)  # one clear action at a time
        ranked = sum(1 for row in rows if row.rank)
        counted = {"crypto": "coin_results", "etf_kr": "etf_results", "etf_us": "etf_results"}.get(self.page, "results")
        self.count.setText(self._p(counted, count=ranked))
        counted = bool(rows) and bool(chips or screen.limits)
        self.count.setVisible(counted)
        pointers = self._other_markets()
        for button, item in zip(self.market_buttons, pointers + [None] * (len(self.market_buttons) - len(pointers))):
            button.payload = item[0] if item else None
            button.setText(item[1] if item else "")
            button.setVisible(item is not None)
        others = self._others()
        for button, other in zip(self.other_buttons, others + [None] * (len(self.other_buttons) - len(others))):
            button.payload = other[1] if other else None
            button.setText(other[0] if other else "")
            button.setAccessibleName(self._p("open", name=other[0]) if other else "")
            button.setVisible(other is not None)
        self.others_label.setText(self._t("Outside this list:"))
        self.others_label.setVisible(bool(others))
        self.others_host.setVisible(bool(others or pointers))
        self._render_message()
        self.active_section.setVisible(bool(chips or pointers or others) or counted or self._message is not None)

    def _other_markets(self):
        """[(page, label)]: the other markets whose curated list has what the search names, when this market's has
        nothing by that name ('미국 주식에서 보기: 테슬라 TSLA'). Pure: the curated lists, no network."""
        text, lang = self.query.strip(), self._lang()
        if not text or replace(self.screen, sub="", sector="").members():
            return []
        found = []
        for page in S.PAGE_KEYS:
            if page == self.page:
                continue
            members = S.Screen(page, text=text).members()
            if members:
                first, more = members[0], len(members) - 1
                fields = dict(market=S.page_text(page, lang), name=f"{first.label(lang)} {first.code}", count=more)
                found.append((page, self._p("in_market_more" if more else "in_market", **fields)))
        return found

    def _others(self):
        """Stocks of this market outside the curated list that the search text names (the symbol directory)."""
        text = self.query.strip()
        if not text or self.others_fn is None:
            return []
        try:
            found = list(self.others_fn(text, self.page) or ())
        except Exception:  # the directory is optional; a failure only drops the suggestions
            return []
        listed = {(m.code, m.exchange) for m in R.members_of(self.group())}
        listed |= {(m.code, "") for m in R.members_of(self.group())}
        return [item for item in found if (getattr(item[1], "code", ""), getattr(item[1], "exchange", "")) not in listed
                ][:OTHERS_LIMIT]

    def say(self, key=None, **fields):
        """A short message under the filters: `PAGE_TEXT[key]` filled with `fields`, kept as a key so a language
        switch re-renders it; no key hides it. A market switch or new search text clears it."""
        self._message = (key, dict(fields)) if key else None
        self._render_message()
        shown = lambda widget: not widget.isHidden()  # its own flag: the section around it may be hidden
        self.active_section.setVisible(self._message is not None or shown(self.others_host) or shown(self.count)
                                       or any(shown(chip) for chip in self.filter_chips))

    def _render_message(self):
        text = self._p(self._message[0], **self._message[1]) if self._message else ""
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def render(self):
        lang, group, screen = self._lang(), self.group(), self.screen
        self._render_chrome()
        batch = self.batches.get(group)
        # Market cap: a stock whose figure could not be read (US) or was refused (domestic: KIS's hts_avls
        # disagreed with listed shares x price, or could not be checked) is listed last, unranked, as '—'.
        missing = "last" if screen.category in ("cap", "qscore") else "omit"
        records = batch.records if batch is not None else ()
        if group in ("kr", "us"):
            if self.category == "qscore" and self.auto_load and self.isVisible() and not self._stopped:
                self.scores.ensure(group, records, self.clock())
            from core.market.qscore_rankings import CANDIDATES
            candidates = {r.member.code for r in sorted(records, key=lambda r: (r.trading_value is None, -(r.trading_value or 0), r.member.code))[:CANDIDATES]}
            enriched = []
            for record in records:
                result = self.scores.result(record.member.instrument, self.clock())
                if result is None:
                    result = {"status": "unavailable", "reason": "ranking_waiting" if record.member.code in candidates else "not_in_candidates"}
                score = result.get("score") if result.get("status") == "ready" else None
                enriched.append(replace(record, q_score=score, q_result=result))
            records = enriched
        rows = screen.apply(records, limit=self.limit, missing=missing) if batch is not None else []
        self.ranked = rows
        figure, _unit = R.value_unit(screen.category, group)
        figures = tuple(key for key in FIGURES if key == figure or (
            not S.category_note(self.page, key) and any(_finite(getattr(row.record, FIGURE_FIELDS[key]))
                                                        for row in rows)))
        spark = any(len(row.record.closes) > 1 for row in rows)
        sector = bool(R.sectors_in(self.page)) and not screen.sector
        self._spec = (figure, figures, spark, sector)
        self._ranked_column = "change" if screen.category in ("gainers", "losers") else figure
        plan = self._plan()
        self._render_headers(rows, plan)
        while len(self.rows) < len(rows):
            row = RankRow()
            row.opened.connect(self.open_requested)
            self.rows.append(row)
            self.list_layout.addWidget(row)
        closed = self._t("Coins have no stock screen yet, so this row opens nothing.") if self.page == "crypto" else ""
        cap_shown = "cap" in dict(plan)
        for widget, row in zip(self.rows, rows):
            widget.apply_plan(plan)
            member = row.record.member
            widget.show_row(row, language=lang, dark=self.dark, figure=figure,
                            ranked=figure if self._ranked_column == figure else "",
                            sector=R.text(R.SECTORS, member.sector, lang) if member.sector else "",
                            tips={"cap": self._cap_tip(row.record)} if cap_shown else None, closed_tip=closed)
            widget.show()
        for widget in self.rows[len(rows):]:
            widget.hide()
        self.column_header.setVisible(bool(rows))
        text, actions = ("", []) if rows else self._empty_state(batch)
        self.empty.setText(text)
        self.empty.setVisible(not rows)
        for button, action in zip(self.empty_actions, actions + [None] * (len(self.empty_actions) - len(actions))):
            button.action = action[1] if action else None
            button.setText(action[0] if action else "")
            button.setVisible(action is not None)
        self.empty_actions_host.setVisible(bool(actions) and not rows)
        self.footnote.setText(self._footnote(batch) + (("\nQ-SCORE · 실험적 지표 · 투자 권유 아님 · 거래대금 기준 최대 20개 후보 · 수정 일별 기준" if lang == "ko" else "\nQ-SCORE · Experimental indicator · Not investment advice · Up to 20 trading-value candidates · Adjusted daily basis") if self.category == "qscore" else ""))
        self._render_active(rows)
        self._sync_summary()
        self._render_status()
        self._fit()
        QTimer.singleShot(0, self._place_sticky)

    def _render_headers(self, rows, plan):
        lang, group = self._lang(), self.group()
        for header in (self.column_header, self.sticky.header):
            header.apply_plan(plan)
            header.rank.setText(R.text(R.COLUMNS, "rank", lang))
            header.stock.setText(self._p("coin") if self.page == "crypto" else R.text(R.COLUMNS, "stock", lang))
            header.cells["sector"].setText(self._t("Sector"))
            header.cells["spark"].setText("")
            header.cells["price"].setText(R.text(R.COLUMNS, "price", lang))
            header.cells["change"].setText(R.text(R.COLUMNS, "change", lang))
            for key in FIGURES:
                header.cells[key].setText(R.cap_label(rows, lang) if key == "cap" else R.text(R.CATEGORIES, key, lang))
            for key in ("change",) + FIGURES:
                cell = header.cells[key]
                ranked = key == self._ranked_column
                _set_flag(cell, "ranked", ranked)
                sortable = not S.category_note(self.page, key) if key in FIGURES else True
                cell.set_sortable(sortable)
                if key == "change":
                    target = "losers" if self.category == "gainers" else "gainers"
                    hint = self._p("sort_by", name=R.text(R.CATEGORIES, target, lang))
                else:
                    hint = "" if ranked else self._p("sort_by", name=R.text(R.CATEGORIES, key, lang))
                tip = self._cap_heading_tip(rows) if key == "cap" and group in ("kr", "us") else ""
                cell.setToolTip(" ".join(part for part in (tip, hint) if part))

    def _empty_state(self, batch):
        """(why the list is empty, [(button text, action)]): what is loading or missing, else which criterion left
        nothing, said plainly with a one-click way out (UI-D10 review: 급상승 dropped falling names and the page
        blamed 조건)."""
        note = S.category_note(self.page, self.category)
        if note:
            return self._t(note), [(self._p("rank_by_value"), lambda: self.set_category("value"))]
        if self._loading is not None and self._loading[0] == self.group():
            return self._t("Loading quotes…"), []
        if batch is None:
            if self._error and self._attempted.get(self.group()):
                return self._t("Could not load quotes. Trying again shortly."), []
            if self.auto_load and self.loader is not None and not self._stopped:
                return self._t("Loading quotes…"), []  # queued behind the other market's fetch, or starting
            return self._t("Not loaded yet. Press Refresh to load the list."), []
        if not batch.records:
            return self._t("Could not load quotes. Trying again shortly."), []
        screen, coin, text = self.screen, self.page == "crypto", self.query.strip()
        place = replace(screen, limits=(), text="")
        named = [r for r in batch.records if place.matches(r) and (not text or S.matches_text(r.member, text))]
        if not named and text:
            wider = replace(screen, limits=(), sub="", sector="")
            if (screen.sub or screen.sector) and any(wider.matches(r) for r in batch.records):
                return self._p("outside_place", text=text), [(self._p("show_all_place"), self._clear_place)]
            return self._p("no_coin" if coin else "no_match", text=text), []
        if named:  # the text, sub-market and sector leave some: the conditions, else the ranking, left nothing
            kept = [r for r in named if all(S.condition(k).holds(r, lo, hi) for k, lo, hi in screen.limits)]
            if not kept:
                return (self._p("no_condition_coin" if coin else "no_condition"),
                        [(self._t("Clear conditions"), self.clear_conditions)])
            if screen.category in ("gainers", "losers"):
                key = ("none_up" if screen.category == "gainers" else "none_down") + ("_coin" if coin else "")
                return (self._p(key, count=len(kept)),
                        [(self._p("rank_by_value"), lambda: self.set_category("value"))])
        if screen.category == "cap" and self.group() == "us":
            return self._us_cap_empty(batch), []
        if screen.category == "cap":
            return self._kr_cap_empty(batch), []
        return self._t("No stocks match these filters."), []

    def _empty_text(self, batch):
        return self._empty_state(batch)[0]

    # US market cap ------------------------------------------------------------------------------
    def _us_cap_empty(self, batch):
        """Why the US market-cap list is empty: the providers' reasons when none could be read."""
        if batch.caps == "none":
            parts = [self._t("Could not read US market cap.")]
            parts += [self._t(CAP_REASON_TEXT[key]) for key in batch.cap_reasons if key in CAP_REASON_TEXT]
            return " ".join(parts)
        if batch.caps == "ok":
            return self._t("No stock in this list has a market cap.")
        return self._t("These quotes came without market cap.")

    # Domestic market cap ------------------------------------------------------------------------
    def _kr_cap_empty(self, batch):
        """Why the domestic market-cap list is empty: the daily path has none; KIS figures were refused."""
        listed = {member.code for member in self.screen.members(text=False)}
        records = [r for r in batch.records if r.member.code in listed]
        reasons = [r.cap_missing for r in records if r.cap_missing]
        if not records:
            return self._t("No stocks match these filters.")
        if batch.mode != "kis" or not reasons:
            return self._t("Market cap comes with KIS quotes of domestic stocks only; the data shown has none.")
        parts = [self._t("Could not use domestic market cap.")]
        parts += [self._t(KR_CAP_REASON_TEXT[key]) for key in KR_CAP_REASON_TEXT if key in reasons]
        return " ".join(parts)

    def _cap_tip(self, record):
        """Where one row's market cap came from, and its basis (tooltip; provider names and dates stay out
        of the list)."""
        lang = self._lang()
        money = "usd" if record.member.currency == "USD" else "krw"
        price = R.price_text(record.price, record.member.currency)
        if record.cap_basis == "computed":
            return self._t("Shares outstanding {shares} ({source}, {day}) × price {price} = {cap}.",
                           shares=R.compact(record.shares, "shares", lang), source=record.cap_source,
                           day=_day(record.cap_as_of), price=price, cap=R.compact(record.market_cap, money, lang))
        if record.cap_basis == "provider" and record.shares and record.member.group == "kr":
            return self._t("KIS market cap (hts_avls read as 100 million won), stated {when} KST; it agrees within "
                           "25% with listed shares {shares} × price {price} = {computed} of the same KIS answer.",
                           when=_kst(record.cap_as_of), shares=R.compact(record.shares, "shares", lang),
                           price=price, computed=R.compact(record.shares * record.price, money, lang))
        if record.cap_basis == "provider":
            return self._t("{source} market cap, stated {when} KST.", source=record.cap_source,
                           when=_kst(record.cap_as_of))
        if record.cap_missing in KR_CAP_REASON_TEXT:
            return self._t(KR_CAP_REASON_TEXT[record.cap_missing])
        if record.cap_missing == "adr":
            return self._t("ADR: the share count is not per ADR, so no market cap is computed.")
        if record.cap_missing:
            return self._t("The share count could not be read.")
        return ""

    def _cap_heading_tip(self, rows):
        if self.group() == "kr":
            return self._kr_cap_heading_tip(rows)
        computed = sorted({row.record.cap_source for row in rows if row.record.cap_basis == "computed"})
        stated = sorted({row.record.cap_source for row in rows if row.record.cap_basis == "provider"})
        parts = []
        if computed:
            parts.append(self._t("Computed: shares outstanding × the price in the row; share counts from {source}, "
                                 "kept for a day.", source=", ".join(computed)))
        if stated:
            parts.append(self._t("Stated by {source}.", source=", ".join(stated)))
        return " ".join(parts)

    def _kr_cap_heading_tip(self, rows):
        bases = {row.record.cap_basis for row in rows}
        parts = []
        if "provider" in bases:
            parts.append(self._t("Stated by KIS (hts_avls, read as 100 million won) and used only when it agrees "
                                 "within 25% with listed shares × price of the same KIS answer."))
        if "computed" in bases:
            parts.append(self._t("Computed: listed shares × price, both from the same KIS answer."))
        return " ".join(parts)

    def _footnote(self, batch):
        listed = {member.code for member in self.screen.members(text=False)}
        if self.page == "crypto":
            parts = [self._t("Ranked among {count} major coins, not the whole market. Prices in US dollars.",
                             count=len(listed))]
            if batch is not None and batch.records:
                parts.append(self._t("Delayed · daily: Yahoo Finance daily bars by UTC day, today's still moving; "
                                     "trading value is Yahoo's daily dollar volume."))
            # The rankings a coin page leaves out (`screen.category_note`), said where a keyboard reaches it.
            parts.append(self._t("Coins have no volume or market-cap ranking: one coin's unit is worth very "
                                 "different amounts from another's, and no source this app uses states coin "
                                 "market cap."))
        elif self.page in R.ETF_GROUPS:
            parts = [self._t("Ranked among {count} major ETFs, not the whole market. Open a row for its chart.",
                             count=len(listed)),
                     # The market-cap chip is left out (`screen.category_note`); said where a keyboard reaches it.
                     self._t("ETFs have no market-cap ranking: their size is net assets (AUM), which no source this "
                             "app uses states.")]
        else:
            parts = [self._t("Ranked among {count} major stocks, not the whole market. Open a row for its chart.",
                             count=len(listed))]
        if batch is not None and batch.mode == "daily" and self.page != "crypto":
            parts.append(self._t("Delayed · daily: the last daily bar; trading value is close × volume, estimated."))
        if self.category == "cap" and self.group() == "kr" and self.ranked:
            if any(row.record.cap_basis == "provider" for row in self.ranked):
                parts.append(self._t("Market cap is KIS's figure, used only where it agrees with listed shares × "
                                     "price of the same answer."))
            if any(row.record.cap_basis == "computed" for row in self.ranked):
                parts.append(self._t("Market cap (computed) = listed shares × price, both from the KIS answer."))
        if self.category == "cap":
            if self.group() == "us" and any(row.record.cap_basis == "computed" for row in self.ranked):
                parts.append(self._t("Market cap (computed) = shares outstanding × the price shown; "
                                     "share counts are refreshed daily."))
            unranked = sum(1 for row in self.ranked if not row.rank)
            if unranked and self.group() == "kr":
                parts.append(self._t("No usable market cap for {count} of these stocks; listed last without a rank "
                                     "(each row's tooltip says why).", count=unranked))
            elif unranked:
                parts.append(self._t("No market cap for {count} of these stocks; listed last without a rank.",
                                     count=unranked))
        failed = [code for code, _error in (batch.failures if batch is not None else ()) if code in listed]
        if failed:
            parts.append(self._t("Could not load {count} of these stocks.", count=len(failed)))
        stale = [code for code in (batch.stale if batch is not None else ()) if code in listed]
        if stale:
            parts.append(self._t("Left out for old data: {count}.", count=len(stale)))
        return " ".join(parts)

    def state(self):
        """'polled' ('polled_us'), 'stale', 'closed', 'daily' or 'none' for the current group; never live."""
        batch = self.batches.get(self.group())
        if batch is None or not batch.records:
            return "none"
        now = self.clock()
        round_ = self._round(self.group(), batch)
        return R.source_state(batch, open_now=self.open_fn(self.group(), now),
                              age_seconds=(now - _parse(batch.fetched_at)).total_seconds(),
                              live_limit=LIVE_STALE_SECONDS, round_seconds=round_[1] if round_ else None)

    def _render_status(self):
        lang, group = self._lang(), self.group()
        batch = self.batches.get(group)
        state = self.state()
        self.badge.setText(R.text(R.STATES, state, lang))
        if self.badge.property("state") != state:
            self.badge.setProperty("state", state)
            _repolish(self.badge)
        self.badge.setToolTip(self._badge_tooltip(batch))
        if self._loading is not None and self._loading[0] == group:
            _g, done, total = self._loading
            self.caption.setText(self._t("Loading… {done}/{total}", done=done, total=total))
        elif self._error and self._attempted.get(group):
            # A failed refresh keeps the last list on screen and says how old it is.
            failed = self._t("Request failed ({code})", code=self._error)
            self.caption.setText(failed if batch is None else f"{failed} · {self._age_text(_parse(batch.fetched_at))}")
        elif batch is not None:
            self.caption.setText(self._age_text(_parse(batch.fetched_at)))
        else:
            self.caption.setText("")
        self.caption.setVisible(bool(self.caption.text()))
        if self.caption.text() != self._caption_text:  # a longer caption can need the search on its own line
            self._caption_text = self.caption.text()
            self._fit()

    def _age_text(self, at):
        seconds = max(0, int((self.clock() - at).total_seconds()))
        if seconds < 5:
            return self._t("Updated just now")
        if seconds < 60:
            return self._t("Updated {seconds}s ago", seconds=seconds)
        if seconds < 3600:
            return self._t("Updated {minutes} min ago", minutes=seconds // 60)
        return self._t("Updated {hours} h ago", hours=seconds // 3600)

    def _badge_tooltip(self, batch):
        if batch is None or not batch.records:
            return ""
        sources = sorted({r.source for r in batch.records})
        if batch.mode == "daily":
            days = sorted({r.as_of for r in batch.records})
            if batch.group == "crypto":
                return self._t("{source} daily bars by UTC day, last bar {day} (still moving today); prices and "
                               "trading value in US dollars as Yahoo states them.",
                               source=", ".join(sources), day=days[-1] if days else "—")
            return self._t("{source} daily bars, last bar {day}; trading value estimated as close × volume.",
                           source=", ".join(sources), day=days[-1] if days else "—")
        from zoneinfo import ZoneInfo
        when = _parse(batch.fetched_at).astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        seconds = LIVE_REFRESH_SECONDS if self.open_fn(self.group(), self.clock()) else IDLE_REFRESH_SECONDS
        tip = self._t("{source} current quotes polled every {seconds} s (REST requests, not a trade stream); "
                      "last received {when} KST.", source=", ".join(sources), seconds=seconds, when=when)
        round_ = self._round(self.group(), batch)
        if round_ is not None and round_[1] > seconds:
            tip += " " + self._t("The last round of requests took {took} s, longer than {seconds} s, so each stock "
                                 "was asked less often than that.", took=math.ceil(round_[1]), seconds=seconds)
        if batch.group in ("us", "etf_us"):
            tip += " " + self._t("US quotes are KIS's free feed and can differ from paid consolidated quotes.")
        return tip


def _parse(stamp):
    value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _day(stamp):
    """A share count's date: '2026-10-17' as given, or the Korea-time date of a UTC ISO receipt stamp."""
    stamp = str(stamp or "")
    if "T" in stamp:
        stamp = _kst(stamp)
    return stamp[:10] if stamp and stamp != "—" else "—"


def _kst(stamp):
    """'2026-11-11 14:20' (Korea time) from a UTC ISO stamp; '—' when there is none."""
    from zoneinfo import ZoneInfo
    try:
        return _parse(stamp).astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return "—"


# Why a domestic KIS row has no market cap (`rankings.parse_kis_domestic_cap`): its tooltip, and under the
# empty list when no row has one.
KR_CAP_REASON_TEXT = {
    "mismatch": "KIS's market cap differs by more than 25% from listed shares × price of the same answer, "
                "so it is not used.",
    "bad_cap": "KIS's market cap is not a positive number, so it is not used.",
    "bad_shares": "KIS's listed share count is not a positive whole number, so the market cap could not be "
                  "checked or computed.",
    "unverified": "KIS gave no listed share count, so its market cap could not be checked and is not used.",
    "absent": "KIS gave neither a market cap nor a listed share count.",
}

# Why a US batch has no market cap (`rankings.CAP_REASONS`), as said under the empty list.
CAP_REASON_TEXT = {
    "kis_off": "KIS is not connected.",
    "kis_none": "KIS returned no usable market cap.",
    "fmp_no_key": "FMP_API_KEY is not set.",
    "fmp_plan": "The FMP plan does not include batch quotes.",
    "fmp_failed": "FMP did not answer.",
    "yahoo_missing": "yfinance is not installed.",
    "yahoo_unreachable": "Yahoo Finance could not be reached.",
    "yahoo_empty": "Yahoo Finance returned no share counts.",
    "yahoo_timeout": "Yahoo Finance did not answer in time.",
}


__all__ = ["RankingBoard", "RankRow", "Sparkline", "ProductionRankingLoader", "kis_batch", "daily_batch",
           "board_stylesheet", "LIST_LIMIT", "LIVE_REFRESH_SECONDS", "LIVE_STALE_SECONDS", "IDLE_REFRESH_SECONDS",
           "RETRY_SECONDS",
           "KIS_MAX_PER_SECOND"]
