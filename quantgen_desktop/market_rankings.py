"""Markets pages: one page per market with Toss-style ranked lists (owner request 2026-11-11, point 5; UI-D10).

Owner ruling UI-D10 (2026-11-11): "시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, 너가 지금 하부ui로 깔아놓은건 해당
시장의 하부ui 선택하고 차후에 검색기준으로 저걸 쓸수있게 구현하면 좋을 거 같은데, 공간 잘써서 센스있게해봐". The rail
lists 국내 주식 / 미국 주식 / 코인 (`core.market.screen.PAGES`); `RankingBoard` is that market's page: one compact
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
  polling, not a trade stream: the state says "KIS 조회 · 45초마다" (US: "KIS 무료 시세 · 45초마다 조회"),
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
One fetch serves every category of its group ('kr' or 'us'): switching category re-ranks the cached quotes.

The source state is always shown ("KIS 조회 · 45초마다" for KIS quotes during the regular session, "KIS · 장
마감", "KIS · 갱신 지연", "지연·일별", "자료 없음") with the time since the last update; nothing polled, stale or
synthetic is presented as live. The heading "실시간 차트" is the owner's name for the page (Toss style), not a
data state. Provider names and dates beyond that stay in tooltips (owner, 2026-11-04).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import math
import threading
import time

from PyQt6.QtCore import QLocale, QPointF, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QDoubleValidator, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QBoxLayout, QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QSizePolicy, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market import rankings as R
from core.market import screen as S
from core.theme import DARK, LIGHT
from .category_picker import CategoryFlow
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
SPARK_MIN_WIDTH = 820          # below this list width the sparkline column is dropped
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
            if member.market == "US":
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
    if member.market == "US":
        from core.market.routing import yahoo_symbols
        return tuple((symbol, "") for symbol in yahoo_symbols(member.instrument))
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
    import re
    words = re.findall(r"[A-Za-z]+|[가-힣]+", str(name))
    hangul = [bool(re.match("[가-힣]", word)) for word in words[:2]]
    return words[0] if len(hangul) == 2 and hangul[0] != hangul[1] else name


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


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
        from PyQt6.QtCore import QEvent
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


class RankRow(QFrame):
    """rank · company mark · name and code · sparkline · price · change % · ranking figure."""
    opened = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("rankRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.row = None
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
        self.spark = Sparkline()
        layout.addWidget(self.spark, 0, Qt.AlignmentFlag.AlignVCenter)
        self.price = _numbers(_label(rk="price"))
        self.change = _numbers(_label(rk="change"))
        self.value = _numbers(_label(rk="value"))
        for widget, width in ((self.price, PRICE_WIDTH), (self.change, CHANGE_WIDTH), (self.value, VALUE_WIDTH)):
            widget.setFixedWidth(width)
            widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(widget)

    def show_row(self, row, *, language, dark, category, spark, value_tip="", closed_tip=""):
        """`closed_tip`: why this row opens nothing (a coin); '' for a row that opens the stock's screen."""
        from .typography import TONE_COLORS, set_tone
        self.row = row
        record, member = row.record, row.record.member
        name = member.label(language)
        self.rank.setText(str(row.rank) if row.rank else "")  # 0: no figure, listed after the ranked rows
        # A coin's mark is its symbol's letter (B, E, X): two Hangul syllables of '비트코인' would read as a company.
        self.mark.set_identity(member.code, member.code if member.group == "crypto" else mark_name(name))
        self.mark.setAccessibleName(name)
        self.mark.setToolTip(f"{name} · {member.code}")
        self.mark.set_theme(DARK if dark else LIGHT)
        self.name.set_full(name)
        place = member.place(language, record.market)
        self.code.set_full(f"{member.code} · {place}" if place else member.code)
        self.setCursor(Qt.CursorShape.PointingHandCursor if member.instrument is not None and not closed_tip
                       else Qt.CursorShape.ArrowCursor)
        self.setToolTip(closed_tip)
        self.setAccessibleDescription(closed_tip)
        self.price.setText(R.price_text(record.price, member.currency))
        text, tone = R.change_text(record.change_pct)
        self.change.setText(text or "—")
        set_tone(self.change, tone)
        kind, unit = R.value_unit(category, member.group)
        figure = {"value": record.trading_value, "volume": record.volume, "cap": record.market_cap}[kind]
        self.value.setText(R.compact(figure, unit, language))
        self.value.setToolTip(value_tip)
        tones = TONE_COLORS[bool(dark)]
        closes = record.closes
        self.spark.set_values(closes, tones["up"] if len(closes) > 1 and closes[-1] >= closes[0] else tones["down"])
        self.spark.setVisible(spark)
        place = f"{row.rank}. " if row.rank else ""
        self.setAccessibleName(f"{place}{name} {self.price.text()} {self.change.text()} {self.value.text()}")

    def _open(self):
        if self.row is not None and self.row.record.member.instrument is not None:
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
    ring: the sub-market buttons (전체·코스피·코스닥, 전체·나스닥·NYSE) with their padding 2px smaller while focused
    so the button keeps its size, and the search, the 조건 toggle, the condition fields, the filter chips and the
    text buttons the same way.
    """
    from .typography import TONE_COLORS
    p, t = palette, TONE_COLORS[bool(dark)]
    line = blend(p.border, p.bg)
    chip_line = blend(p.accent, p.accent_soft, 0.6)
    return f"""
          QFrame#marketBoard {{ background: transparent; border: 0; }}
          QWidget#boardSection {{ background: transparent; }}
          QPushButton[chip='true'] {{ padding: 7px 16px; min-height: 18px; border: 0; border-radius: 16px;
                                     background: {p.surface_2}; color: {p.text}; }}
          QPushButton[chip='true']:hover {{ background: {p.accent_soft}; }}
          QPushButton[chip='true']:checked {{ background: {p.accent}; color: {p.on_accent}; }}
          QPushButton[chip='true']:disabled {{ background: transparent; color: {p.muted}; }}
          QPushButton[chip='true']:focus {{ border: 2px solid {p.accent}; }}
          QPushButton[tool='true'] {{ background: transparent; border: 0; border-bottom: 2px solid transparent;
                                     padding: {TOOL_PADDING[0]}px {TOOL_PADDING[1]}px; }}
          QPushButton[tool='true']:hover {{ background: {p.accent_soft}; }}
          QPushButton[tool='true']:checked {{ background: transparent; color: {p.accent};
                                             border-bottom: 2px solid {p.accent}; }}
          QPushButton[tool='true']:focus {{ border: 2px solid {p.accent}; border-radius: 5px;
                                           padding: {TOOL_PADDING[0] - 2}px {TOOL_PADDING[1] - 2}px
                                                    {TOOL_PADDING[0]}px; }}
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
          QLineEdit#condEdit:focus {{ border: 2px solid {p.accent}; padding: 3px 7px; }}
          QLineEdit#condEdit[invalid='true'] {{ border: 1px solid {t['up']}; }}
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
          QPushButton#otherStock {{ border: 1px solid {line}; border-radius: 13px; padding: 6px 12px; min-height: 16px;
                                   background: {p.surface}; color: {p.text}; }}
          QPushButton#otherStock:hover {{ background: {p.accent_soft}; }}
          QPushButton#otherStock:focus {{ border: 2px solid {p.accent}; padding: 5px 11px; }}
          QFrame#summaryTile {{ background: {p.surface}; border: 1px solid {line}; border-radius: 12px; }}
          QFrame#rankRow {{ background: transparent; border: 0; border-radius: 12px; }}
          QFrame#rankRow:hover, QFrame#rankRow:focus {{ background: {p.accent_soft}; }}
          QFrame#rankDivider {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
          QLabel[rk='page'] {{ font-size: 24px; font-weight: 600; letter-spacing: -0.6px; }}
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
          QLabel[rk='price'] {{ font-size: 15px; font-weight: 600; letter-spacing: 0px; }}
          QLabel[rk='change'] {{ font-size: 15px; font-weight: 600; letter-spacing: 0px; color: {t['flat']}; }}
          QLabel[rk='change'][tone='up'] {{ color: {t['up']}; }}
          QLabel[rk='change'][tone='down'] {{ color: {t['down']}; }}
          QLabel[rk='value'] {{ font-size: 14px; font-weight: 400; color: {p.muted}; letter-spacing: 0px; }}
          QLabel[rk='head'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: -0.1px; }}
          QLabel[rk='badge'] {{ font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 9px;
                               color: {p.muted}; background: {p.surface_2}; letter-spacing: -0.1px; }}
          QLabel[rk='badge'][state='polled'], QLabel[rk='badge'][state='polled_us'] {{ color: {p.success};
                                                                               background: {p.accent_soft}; }}
          QLabel[rk='badge'][state='daily'], QLabel[rk='badge'][state='stale'] {{ color: {p.warning};
                                                                           background: {t['flat_tint']}; }}
          QLabel[rk='empty'] {{ font-size: 14px; color: {p.muted}; padding: 28px 8px; }}
        """


CRITERIA_WIDE = 940            # below this page width the filters wrap under the category chips
SEARCH_WIDTHS = (320, 220)     # the header search: wide page, narrow page
FILTER_POOL = 1 + len(S.CONDITIONS)   # filter chips: the search text, then one per condition
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


class RankingBoard(QFrame):
    """One market's page: header row, index strip, criteria, conditions, active filters and the ranked list."""
    open_requested = pyqtSignal(object)
    listing_requested = pyqtSignal(object)  # a search suggestion outside the curated list
    loaded = pyqtSignal(str)
    category_changed = pyqtSignal(str)      # a chip click or set_category() changed the list shown
    page_changed = pyqtSignal(str)          # set_page() showed another market
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
        self._wide = None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self._progress.connect(self._on_progress)
        self.tick = QTimer(self)
        self.tick.setInterval(1000)
        self.tick.timeout.connect(self._tick)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header row: market name, data state, search within this market, refresh.
        head = QHBoxLayout()
        head.setSpacing(10)
        self.heading = _label(rk="page")
        head.addWidget(self.heading, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addSpacing(6)
        self.badge = _label(rk="badge")
        head.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.caption = _label(rk="age")
        head.addWidget(self.caption, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addStretch(1)
        self.search = QLineEdit()
        self.search.setObjectName("marketSearch")
        self.search.setClearButtonEnabled(True)
        self.search.setProperty("qg_literal", True)
        self.search.setFixedWidth(SEARCH_WIDTHS[0])
        self.search.textChanged.connect(self.set_query)
        head.addWidget(self.search, 0, Qt.AlignmentFlag.AlignVCenter)
        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("rankRefresh")
        self.refresh_button.setProperty("qg_literal", True)
        self.refresh_button.clicked.connect(self._refresh_all)
        head.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)

        # Index strip (hidden while it has nothing to show).
        self.summary_section, summary_layout = _section(14)
        self.summary = MarketSummary(loader=summary_loader, locale=self.ctx, auto_load=auto_load)
        self.summary.changed.connect(self._sync_summary)
        summary_layout.addWidget(self.summary)
        layout.addWidget(self.summary_section)
        layout.addSpacing(18)

        # Criteria row: how the list is ranked (chips), then the filters. Wraps to two lines when narrow.
        self.criteria = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.criteria.setSpacing(24)
        chips = QHBoxLayout()
        chips.setSpacing(6)
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        self.category_buttons = {}
        for key, _en, _ko in R.CATEGORIES:
            button = QPushButton()
            button.setCheckable(True)
            button.setProperty("chip", True)
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, k=key: self.set_category(k))
            self.category_group.addButton(button)
            self.category_buttons[key] = button
            chips.addWidget(button)
        chips.addStretch(1)  # chips keep their natural width when the filters wrap under them
        self.criteria.addLayout(chips)
        filters = QHBoxLayout()
        filters.setSpacing(4)
        self.sub_groups, self._sub_buttons = {}, {}
        for page in S.PAGE_KEYS:
            group = QButtonGroup(self)
            group.setExclusive(True)
            self.sub_groups[page], self._sub_buttons[page] = group, {}
            for key, _en, _ko in S.SUBS[page]:
                button = QPushButton()
                button.setCheckable(True)
                button.setProperty("tool", True)
                button.setProperty("qg_literal", True)
                button.clicked.connect(lambda checked=False, k=key: self.set_sub(k))
                group.addButton(button)
                self._sub_buttons[page][key] = button
                filters.addWidget(button)
        filters.addStretch(1)
        self.sector_box = QComboBox()
        self.sector_box.setObjectName("rankSector")
        self.sector_box.setProperty("qg_literal", True)
        self.sector_box.setMinimumWidth(150)
        self.sector_box.currentIndexChanged.connect(self._sector_changed)
        filters.addWidget(self.sector_box)
        filters.addSpacing(4)
        self.conditions_button = QPushButton()
        self.conditions_button.setObjectName("conditionsToggle")
        self.conditions_button.setProperty("qg_literal", True)
        self.conditions_button.setCheckable(True)
        self.conditions_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # the chevron after the text
        self.conditions_button.toggled.connect(self._conditions_toggled)
        filters.addWidget(self.conditions_button)
        self.criteria.addLayout(filters, 1)
        layout.addLayout(self.criteria)

        # Conditions row (조건): built from core.market.screen.CONDITIONS, so a new condition needs no UI code.
        self.conditions_section, conditions_layout = _section(12)
        self.conditions_panel = QFrame()
        self.conditions_panel.setObjectName("conditionsPanel")
        panel = QHBoxLayout(self.conditions_panel)
        panel.setContentsMargins(18, 12, 12, 12)
        panel.setSpacing(12)
        flow_host = QWidget()
        flow_host.setObjectName("condGroup")
        self.condition_flow = CategoryFlow(flow_host)
        self.condition_flow.setSpacing(28)
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
        panel.addWidget(flow_host, 1)
        self.conditions_clear = QPushButton()
        self.conditions_clear.setProperty("textButton", True)
        self.conditions_clear.setProperty("qg_literal", True)
        self.conditions_clear.clicked.connect(self.clear_conditions)
        panel.addWidget(self.conditions_clear, 0, Qt.AlignmentFlag.AlignVCenter)
        conditions_layout.addWidget(self.conditions_panel)
        self.conditions_section.hide()
        layout.addWidget(self.conditions_section)

        # Active search and conditions as chips, one click each to remove; a count; stocks outside the list.
        self.active_section, active_layout = _section(14)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        self.filter_chips = []
        for _ in range(FILTER_POOL):
            chip = QPushButton()
            chip.setProperty("filterChip", True)
            chip.setProperty("qg_literal", True)
            chip.clicked.connect(lambda checked=False, c=chip: self._chip_clicked(c))
            chip.hide()
            chips_row.addWidget(chip)
            self.filter_chips.append(chip)
        self.clear_button = QPushButton()
        self.clear_button.setProperty("textButton", True)
        self.clear_button.setProperty("qg_literal", True)
        self.clear_button.clicked.connect(self.clear_filters)
        chips_row.addWidget(self.clear_button)
        chips_row.addStretch(1)
        self.count = _label(rk="count")
        chips_row.addWidget(self.count, 0, Qt.AlignmentFlag.AlignVCenter)
        active_layout.addLayout(chips_row)
        others_row = QHBoxLayout()
        others_row.setSpacing(6)
        self.others_label = _label(rk="hint")
        others_row.addWidget(self.others_label)
        self.other_buttons = []
        for _ in range(OTHERS_LIMIT):
            button = QPushButton()
            button.setObjectName("otherStock")
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, b=button: self._other_clicked(b))
            button.hide()
            others_row.addWidget(button)
            self.other_buttons.append(button)
        others_row.addStretch(1)
        self.others_host = QWidget()
        self.others_host.setObjectName("boardSection")
        self.others_host.setLayout(others_row)
        others_row.setContentsMargins(0, 0, 0, 0)
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
        header = QHBoxLayout()
        header.setContentsMargins(*ROW_MARGINS[:1], 0, ROW_MARGINS[2], 0)
        header.setSpacing(ROW_SPACING)
        self.head_rank = _label(rk="head")
        self.head_rank.setFixedWidth(RANK_WIDTH)
        self.head_rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.head_rank)
        self.head_stock = _label(rk="head")
        header.addWidget(self.head_stock, 1)
        self.head_spark = _label(rk="head")
        self.head_spark.setFixedWidth(SPARK_WIDTH)
        header.addWidget(self.head_spark)
        self.head_price, self.head_change, self.head_value = (_label(rk="head") for _ in range(3))
        for widget, width in ((self.head_price, PRICE_WIDTH), (self.head_change, CHANGE_WIDTH),
                              (self.head_value, VALUE_WIDTH)):
            widget.setFixedWidth(width)
            widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            header.addWidget(widget)
        self.head_value.setWordWrap(True)  # "Market cap (computed)" takes two lines in the figure column
        layout.addLayout(header)
        layout.addSpacing(4)
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        layout.addLayout(self.list_layout)
        self.rows = []
        self.empty = _label(rk="empty", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)
        layout.addSpacing(12)
        self.footnote = _label("caption", wrap=True)
        layout.addWidget(self.footnote)
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

    def group(self):
        return R.group_of(self.page)

    def set_page(self, page):
        """Show one market's page (`screen.PAGE_KEYS`); its criteria are kept from its last visit."""
        if page not in S.PAGE_KEYS:
            raise ValueError(f"Unknown market page {page!r}")
        changed, group_before = page != self.page, self.group()
        self.page = page
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
        self.sector_box.blockSignals(True)
        self.sector_box.clear()
        self.sector_box.addItem(self._t("All sectors"), "")
        for key in R.sectors_in(self.page):
            self.sector_box.addItem(R.text(R.SECTORS, key, lang), key)
        index = max(0, self.sector_box.findData(keep))
        self.sector_box.setCurrentIndex(index)
        self.sector_box.blockSignals(False)
        self.sector_box.setAccessibleName(self._t("Sector"))
        self.sector_box.setVisible(bool(R.sectors_in(self.page)))

    def set_query(self, text):
        """Narrow the shown market's list to names, codes or sectors matching `text` (the header search)."""
        text = str(text or "")
        if text == self.query:
            return
        self.message.hide()  # a 'not found' message belongs to the text it answered
        self._set_screen(replace(self.screen, text=text))
        self._sync_search()
        self.render()

    def _sync_search(self):
        if self.search.text() != self.query:
            self.search.blockSignals(True)
            self.search.setText(self.query)
            self.search.blockSignals(False)

    def set_limit(self, key, low=None, high=None):
        """Set one condition of the shown market (`screen.CONDITIONS`); no bound clears it."""
        self._set_screen(self.screen.with_limit(key, low, high))
        self.render()

    def clear_conditions(self):
        self._set_screen(self.screen.cleared())
        self.render()

    def clear_filters(self):
        """One click: the search text and every condition of this market (category, market and sector stay)."""
        self._set_screen(replace(self.screen.cleared(), text=""))
        self._sync_search()
        self.render()

    def set_conditions_open(self, shown):
        self.conditions_button.setChecked(bool(shown))

    def _conditions_toggled(self, shown):
        self.conditions_section.setVisible(bool(shown))
        self._render_conditions_button()

    def _range_edited(self, key):
        low_edit, high_edit = self.condition_controls[key]
        low, high = _number(low_edit.text()), _number(high_edit.text())
        bad = low is not None and high is not None and low > high
        for edit in (low_edit, high_edit):
            if bool(edit.property("invalid")) != bad:
                edit.setProperty("invalid", bad)
                _repolish(edit)
            edit.setToolTip(self._t("The lower bound is above the upper bound.") if bad else "")
        if bad:
            return  # the list keeps the last valid range until the bounds agree
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
        elif key:
            self.set_limit(key)

    def _other_clicked(self, button):
        payload = getattr(button, "payload", None)
        if payload is not None:
            self.listing_requested.emit(payload)

    def _refresh_all(self):
        self.refresh(manual=True)
        self.summary.refresh(manual=True)

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
        """Fetch the current group when due (or now, when `manual`); False when nothing started."""
        group = self.group()
        if self._stopped:
            return False
        if self.jobs.busy:
            self._pending = self._pending or manual
            return False
        if self.loader is None or (not manual and not self.due(group)):
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
        if self.auto_load:
            self.tick.start()
            QTimer.singleShot(0, self.refresh)

    def hideEvent(self, event):
        self.tick.stop()
        super().hideEvent(event)

    def stop(self):
        """Window closing: cancel the fetch between requests, drop its answer, start nothing more."""
        self.tick.stop()
        self._stopped, self._pending = True, False
        self._epoch += 1
        self._loading = None
        if self._cancel is not None:
            self._cancel.set()

    # Presentation -----------------------------------------------------------------------------
    def set_locale(self, ctx):
        """Every text in the new language from what is already loaded: never a fetch."""
        self.ctx = ctx
        self.summary.set_locale(ctx)
        self._fill_sectors()
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.setStyleSheet(board_stylesheet(DARK if self.dark else LIGHT, self.dark))
        self.summary.set_theme(self.dark)
        self.render()

    def _sync_summary(self):
        self.summary_section.setVisible(self.summary.wanted())
        # The strip's "지연·일별" is said once: not again beside the header badge when the list is daily too.
        self.summary.state.setVisible(self.summary.has_data() and self.state() != "daily")

    def _render_chrome(self):
        """Labels, chips and filters for the shown market, in the window language."""
        lang, page, screen = self._lang(), self.page, self.screen
        name = S.page_text(page, lang)
        self.heading.setText(name)
        self.heading.setAccessibleName(name)
        if self._wide is False:  # a narrow page keeps the short form; the full one is the accessible description
            self.search.setPlaceholderText(self._t("Search within {market}", market=name))
        else:
            self.search.setPlaceholderText(self._t("Find in {market}: name, code, sector", market=name)
                                           if page != "crypto" else self._t("Find coins: name or symbol"))
        self.search.setAccessibleName(self._t("Search within {market}", market=name))
        # A bare 'Refresh' pair would retranslate every other Refresh button in the window.
        self.refresh_button.setText("새로고침" if lang == "ko" else "Refresh")
        self.refresh_button.setAccessibleName(self._t("Refresh the ranked list"))
        for key, button in self.category_buttons.items():
            button.setText(R.text(R.CATEGORIES, key, lang))
            note = S.category_note(page, key)
            button.setEnabled(not note)
            button.setToolTip(self._t(note) if note else "")
            button.setChecked(key == screen.category)
        for each, buttons in self._sub_buttons.items():
            for key, button in buttons.items():
                button.setText(S.sub_text(each, key, lang))
                button.setChecked(each == page and key == screen.sub)
                button.setVisible(each == page)
        self._syncing = True
        try:
            index = self.sector_box.findData(screen.sector)
            if index >= 0 and index != self.sector_box.currentIndex():
                self.sector_box.setCurrentIndex(index)
        finally:
            self._syncing = False
        self.head_rank.setText(R.text(R.COLUMNS, "rank", lang))
        self.head_stock.setText(self._p("coin") if page == "crypto" else R.text(R.COLUMNS, "stock", lang))
        self.head_price.setText(R.text(R.COLUMNS, "price", lang))
        self.head_change.setText(R.text(R.COLUMNS, "change", lang))
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
        self.conditions_button.setToolTip(self._t("Narrow this list by change, trading value or market cap."))

    def _render_conditions(self):
        """The condition controls of the shown market, holding its current limits (signals held back)."""
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
                    for edit, value, hint in ((controls[0], low, self._p("min")), (controls[1], high, self._p("max"))):
                        edit.setPlaceholderText(hint)
                        edit.setAccessibleName(f"{item.label(lang)} {hint} %")
                        if not getattr(self, "_syncing_edits", False) and _number(edit.text()) != value:
                            edit.setText("" if value is None else f"{value:g}")
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
        self.condition_flow.invalidate()

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
        """Chips for the search text and each condition; one-click clear; how many rows remain."""
        screen = self.screen
        chips = []
        if screen.text.strip():
            chips.append(("text", f"‘{screen.text.strip()}’"))
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
        self.clear_button.setVisible(len(chips) > 1)
        ranked = sum(1 for row in rows if row.rank)
        self.count.setText(self._p("coin_results" if self.page == "crypto" else "results", count=ranked))
        self.count.setVisible(bool(chips) and self.batches.get(self.group()) is not None)
        others = self._others()
        for button, other in zip(self.other_buttons, others + [None] * (len(self.other_buttons) - len(others))):
            button.payload = other[1] if other else None
            button.setText(other[0] if other else "")
            button.setAccessibleName(self._p("open", name=other[0]) if other else "")
            button.setVisible(other is not None)
        self.others_label.setText(self._t("Outside this list:"))
        self.others_host.setVisible(bool(others))
        self.active_section.setVisible(bool(chips) or bool(others) or self.message.isVisibleTo(self))

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

    def say(self, text):
        """A short message under the filters (the search's 'not found'); '' hides it."""
        self.message.setText(text)
        self.message.setVisible(bool(text))
        self.active_section.setVisible(bool(text) or any(c.isVisibleTo(self) for c in self.filter_chips)
                                       or self.others_host.isVisibleTo(self))

    def render(self):
        lang, group, screen = self._lang(), self.group(), self.screen
        self._render_chrome()
        batch = self.batches.get(group)
        # Market cap: a stock whose figure could not be read (US) or was refused (domestic: KIS's hts_avls
        # disagreed with listed shares x price, or could not be checked) is listed last, unranked, as '—'.
        missing = "last" if screen.category == "cap" else "omit"
        rows = screen.apply(batch.records, limit=self.limit, missing=missing) if batch is not None else []
        self.ranked = rows
        spark = self.width() >= SPARK_MIN_WIDTH and any(len(row.record.closes) > 1 for row in rows)
        self.head_spark.setVisible(spark and bool(rows))
        kind, _unit = R.value_unit(screen.category, group)
        self.head_value.setText(R.cap_label(rows, lang) if kind == "cap" else R.text(R.CATEGORIES, kind, lang))
        self.head_value.setToolTip(self._cap_heading_tip(rows) if kind == "cap" else "")
        while len(self.rows) < len(rows):
            row = RankRow()
            row.opened.connect(self.open_requested)
            self.rows.append(row)
            self.list_layout.addWidget(row)
        closed = self._t("Coins have no stock screen yet, so this row opens nothing.") if self.page == "crypto" else ""
        for widget, row in zip(self.rows, rows):
            widget.show_row(row, language=lang, dark=self.dark, category=screen.category, spark=spark,
                            value_tip=self._cap_tip(row.record) if kind == "cap" else "", closed_tip=closed)
            widget.show()
        for widget in self.rows[len(rows):]:
            widget.hide()
        for widget in (self.head_rank, self.head_stock, self.head_price, self.head_change, self.head_value):
            widget.setVisible(bool(rows))
        self.empty.setText("" if rows else self._empty_text(batch))
        self.empty.setVisible(not rows)
        self.footnote.setText(self._footnote(batch))
        self._render_active(rows)
        self._sync_summary()
        self._render_status()

    def _empty_text(self, batch):
        note = S.category_note(self.page, self.category)
        if note:
            return self._t(note)
        if self._loading is not None and self._loading[0] == self.group():
            return self._t("Loading quotes…")
        if batch is None:
            if self._error and self._attempted.get(self.group()):
                return self._t("Could not load quotes. Trying again shortly.")
            if self.auto_load and self.loader is not None and not self._stopped:
                return self._t("Loading quotes…")  # queued behind the other market's fetch, or starting
            return self._t("Not loaded yet. Press Refresh to load the list.")
        if not batch.records:
            return self._t("Could not load quotes. Trying again shortly.")
        if self.query.strip() and not any(replace(self.screen, limits=()).matches(r) for r in batch.records):
            return self._t("Nothing in this list matches ‘{text}’.", text=self.query.strip())
        if self.screen.limits:
            return self._t("No stocks match these filters.")
        if self.category == "cap" and self.group() == "us":
            return self._us_cap_empty(batch)
        if self.category == "cap":
            return self._kr_cap_empty(batch)
        if self.category == "gainers":
            return self._t("No stock in this list is up.")
        if self.category == "losers":
            return self._t("No stock in this list is down.")
        return self._t("No stocks match these filters.")

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
        if batch.group == "us":
            tip += " " + self._t("US quotes are KIS's free feed and can differ from paid consolidated quotes.")
        return tip

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width()
        wide = width >= CRITERIA_WIDE
        if wide != self._wide:
            self._wide = wide
            self.criteria.setDirection(QBoxLayout.Direction.LeftToRight if wide else QBoxLayout.Direction.TopToBottom)
            self.criteria.setSpacing(24 if wide else 12)
            self.search.setFixedWidth(SEARCH_WIDTHS[0] if wide else SEARCH_WIDTHS[1])
            self._render_chrome()
        spark = width >= SPARK_MIN_WIDTH
        if spark != (event.oldSize().width() >= SPARK_MIN_WIDTH):
            self.render()


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
