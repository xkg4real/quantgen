"""Markets "real-time charts": Toss-style ranked lists (owner request 2026-11-11, point 5).

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

from PyQt6.QtCore import QPointF, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market import rankings as R
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
    (`core.market.market_cap.MarketCapSource`: FMP, then Yahoo shares x price).

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

    def __init__(self):
        super().__init__()
        self.setFixedSize(SPARK_WIDTH, 30)
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

    def show_row(self, row, *, language, dark, category, spark, value_tip=""):
        from .typography import TONE_COLORS, set_tone
        self.row = row
        record, member = row.record, row.record.member
        name = member.label(language)
        self.rank.setText(str(row.rank) if row.rank else "")  # 0: no figure, listed after the ranked rows
        self.mark.set_identity(member.code, mark_name(name))
        self.mark.setAccessibleName(name)
        self.mark.setToolTip(f"{name} · {member.code}")
        self.mark.set_theme(DARK if dark else LIGHT)
        self.name.set_full(name)
        self.code.set_full(f"{member.code} · {member.place(language, record.market)}")
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
        if self.row is not None:
            self.opened.emit(self.row.record.member.instrument)

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
    """Local rules for the list (the window stylesheet is area S's); the closer sheet wins in Qt.

    Owner, 2026-11-11 ("구획 선을 연하게 ... 한칸한칸 공간을 넓게"): no outlined boxes here. Chips, the
    refresh button and the sector selector are soft surface fills without borders; rows are separated by
    whitespace; the one rule under the filters is the border colour blended half way into the background.

    A rule here that sets `border` hides the window's `:focus` ring (the closer sheet wins whatever the
    selector), so every focusable control styled here has its own `:focus` rule: the market buttons
    (국내 전체·코스피·코스닥·미국) take the window's 2px `accent` ring, their padding 2px smaller while focused
    so the button keeps its size and the unfocused look is unchanged.
    """
    from .typography import TONE_COLORS
    p, t = palette, TONE_COLORS[bool(dark)]
    line = blend(p.border, p.bg)
    return f"""
          QPushButton[chip='true'] {{ padding: 7px 16px; min-height: 18px; border: 0; border-radius: 16px;
                                     background: {p.surface_2}; color: {p.text}; }}
          QPushButton[chip='true']:hover {{ background: {p.accent_soft}; }}
          QPushButton[chip='true']:checked {{ background: {p.accent}; color: {p.on_accent}; }}
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
          QFrame#rankRow {{ background: transparent; border: 0; border-radius: 12px; }}
          QFrame#rankRow:hover, QFrame#rankRow:focus {{ background: {p.accent_soft}; }}
          QFrame#rankDivider {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
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


class RankingBoard(QFrame):
    """Category chips, market and sector filters, and the ranked list with its source state."""
    open_requested = pyqtSignal(object)
    loaded = pyqtSignal(str)
    category_changed = pyqtSignal(str)      # a chip click or set_category() changed the list shown
    _progress = pyqtSignal(int, int, int)   # epoch, done, total; emitted on the worker thread, queued here

    def __init__(self, *, loader=None, locale=None, auto_load=True, clock=None, open_fn=None, limit=LIST_LIMIT):
        super().__init__()
        self.setObjectName("panel")
        self.setProperty("card", "rankings")
        self.loader, self.auto_load, self.limit = loader, auto_load, limit
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.clock = clock or _utc_now
        self.open_fn = open_fn or R.session_open
        self.category, self.market, self.sector = "value", "kr", ""
        self.batches = {}            # group -> Batch: one fetch serves every category of its group
        self.ranked = []
        self._attempted = {}         # group -> when the last fetch failed outright
        self._rounds = {}            # group -> (Batch, when the round that fetched it started, seconds it took)
        self._error = ""
        self._loading = None         # (group, done, total) while a fetch runs
        self._job_group, self._job_started = None, None
        self._epoch, self._cancel, self._pending, self._stopped = 0, None, False, False
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self._progress.connect(self._on_progress)
        self.tick = QTimer(self)
        self.tick.setInterval(1000)
        self.tick.timeout.connect(self._tick)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.heading = _label("heading")
        head.addWidget(self.heading, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addStretch(1)
        self.badge = _label(rk="badge")
        head.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.caption = _label("caption")
        head.addWidget(self.caption, 0, Qt.AlignmentFlag.AlignVCenter)
        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("rankRefresh")
        self.refresh_button.setProperty("qg_literal", True)
        self.refresh_button.clicked.connect(lambda: self.refresh(manual=True))
        head.addWidget(self.refresh_button)
        layout.addLayout(head)
        layout.addSpacing(6)

        chips = QHBoxLayout()
        chips.setSpacing(8)
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
        chips.addStretch(1)
        layout.addLayout(chips)

        filters = QHBoxLayout()
        filters.setSpacing(4)
        self.market_group = QButtonGroup(self)
        self.market_group.setExclusive(True)
        self.market_buttons = {}
        for key, _en, _ko in R.MARKETS:
            button = QPushButton()
            button.setCheckable(True)
            button.setProperty("tool", True)
            button.setProperty("qg_literal", True)
            button.clicked.connect(lambda checked=False, k=key: self.set_market(k))
            self.market_group.addButton(button)
            self.market_buttons[key] = button
            filters.addWidget(button)
        filters.addStretch(1)
        self.sector_box = QComboBox()
        self.sector_box.setObjectName("rankSector")
        self.sector_box.setProperty("qg_literal", True)
        self.sector_box.setMinimumWidth(150)
        self.sector_box.currentIndexChanged.connect(self._sector_changed)
        filters.addWidget(self.sector_box)
        layout.addLayout(filters)
        layout.addSpacing(10)  # about 24-32px between the controls and the list (owner 2026-11-11)

        divider = QFrame()
        divider.setObjectName("rankDivider")
        layout.addWidget(divider)
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
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        layout.addLayout(self.list_layout)
        self.rows = []
        self.empty = _label(rk="empty", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)
        layout.addSpacing(10)
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

    # Selection --------------------------------------------------------------------------------
    def group(self):
        return R.group_of(self.market)

    def set_category(self, key):
        if key not in R.CATEGORY_KEYS:
            raise ValueError(f"Unknown ranking category {key!r}")
        changed, self.category = key != self.category, key
        self.render()
        if changed:
            self.category_changed.emit(key)
        return True

    def set_market(self, key):
        group_before = self.group()
        R.group_of(key)  # refuses an unknown key
        self.market = key
        self._fill_sectors()
        self.render()
        if self.group() != group_before and self.isVisible() and self.auto_load:
            QTimer.singleShot(0, self.refresh)
        return True

    def set_sector(self, key):
        index = self.sector_box.findData(key or "")
        if index < 0:
            raise ValueError(f"Sector {key!r} is not in this market")
        self.sector_box.setCurrentIndex(index)

    def _sector_changed(self, _index):
        self.sector = self.sector_box.currentData() or ""
        self.render()

    def _fill_sectors(self):
        lang, keep = self._lang(), self.sector
        self.sector_box.blockSignals(True)
        self.sector_box.clear()
        self.sector_box.addItem(self._t("All sectors"), "")
        for key in R.sectors_in(self.market):
            self.sector_box.addItem(R.text(R.SECTORS, key, lang), key)
        index = max(0, self.sector_box.findData(keep))
        self.sector_box.setCurrentIndex(index)
        self.sector = self.sector_box.currentData() or ""
        self.sector_box.blockSignals(False)
        self.sector_box.setAccessibleName(self._t("Sector"))

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
        self.ctx = ctx
        lang = self._lang()
        self.heading.setText(self._t("Real-time charts"))
        for key, button in self.category_buttons.items():
            button.setText(R.text(R.CATEGORIES, key, lang))
        for key, button in self.market_buttons.items():
            button.setText(R.text(R.MARKETS, key, lang))
        # A bare 'Refresh' pair would retranslate every other Refresh button in the window.
        self.refresh_button.setText("새로고침" if lang == "ko" else "Refresh")
        self.refresh_button.setAccessibleName(self._t("Refresh the ranked list"))
        self.head_rank.setText(R.text(R.COLUMNS, "rank", lang))
        self.head_stock.setText(R.text(R.COLUMNS, "stock", lang))
        self.head_price.setText(R.text(R.COLUMNS, "price", lang))
        self.head_change.setText(R.text(R.COLUMNS, "change", lang))
        self._fill_sectors()
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.setStyleSheet(board_stylesheet(DARK if self.dark else LIGHT, self.dark))
        self.render()

    def render(self):
        lang, group = self._lang(), self.group()
        for key, button in self.category_buttons.items():
            button.setChecked(key == self.category)
        for key, button in self.market_buttons.items():
            button.setChecked(key == self.market)
        batch = self.batches.get(group)
        # Market cap: a stock whose figure could not be read (US) or was refused (domestic: KIS's hts_avls
        # disagreed with listed shares x price, or could not be checked) is listed last, unranked, as '—'.
        missing = "last" if self.category == "cap" else "omit"
        rows = R.rank(batch.records, self.category, market=self.market, sector=self.sector,
                      limit=self.limit, missing=missing) if batch is not None else []
        self.ranked = rows
        spark = self.width() >= SPARK_MIN_WIDTH and any(len(row.record.closes) > 1 for row in rows)
        self.head_spark.setVisible(spark and bool(rows))
        kind, _unit = R.value_unit(self.category, group)
        self.head_value.setText(R.cap_label(rows, lang) if kind == "cap" else R.text(R.CATEGORIES, kind, lang))
        self.head_value.setToolTip(self._cap_heading_tip(rows) if kind == "cap" else "")
        while len(self.rows) < len(rows):
            row = RankRow()
            row.opened.connect(self.open_requested)
            self.rows.append(row)
            self.list_layout.addWidget(row)
        for widget, row in zip(self.rows, rows):
            widget.show_row(row, language=lang, dark=self.dark, category=self.category, spark=spark,
                            value_tip=self._cap_tip(row.record) if kind == "cap" else "")
            widget.show()
        for widget in self.rows[len(rows):]:
            widget.hide()
        for widget in (self.head_rank, self.head_stock, self.head_price, self.head_change, self.head_value):
            widget.setVisible(bool(rows))
        self.empty.setText("" if rows else self._empty_text(batch))
        self.empty.setVisible(not rows)
        self.footnote.setText(self._footnote(batch))
        self._render_status()

    def _empty_text(self, batch):
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
        listed = {member.code for member in R.universe(self.market, self.sector)}
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
        listed = {member.code for member in R.universe(self.market, self.sector)}
        parts = [self._t("Ranked among {count} major stocks, not the whole market. Open a row for its chart.",
                         count=len(listed))]
        if batch is not None and batch.mode == "daily":
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
        spark = event.size().width() >= SPARK_MIN_WIDTH
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
