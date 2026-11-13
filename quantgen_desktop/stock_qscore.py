"""The open stock's Q-SCORE on the stock screen (owner UI-D13, 2026-11-12).

Owner, verbatim: "아 그리고 상세차트 들어가면 Q-SCORE 도 같이 볼수있게 하자. !!" — binding reading R-D13-1: the screen shows the
stock's own Q-SCORE, not only a small chip that mostly read "산정 불가": a card high in the right column's 종목 tab (score,
stars, one short 해요체 reading, the engine's three parts as small bars with their weights, the as-of time and
"실험적 지표 · 투자 권유 아님", the methodology behind "자세히 ›") and a compact badge in the toolbar that never covers the chart
(R-D9-1). When there is no score the card says why in plain words and what would give one, never a bare "산정 불가".

`StockScore` computes the score itself with core.research.qscore.compute_q_score (methodology unchanged: Q-SCORE v0.2,
Korean or US stock, KIS adjusted daily prices, at least 200 sessions) from the daily history the screen already loads: the
stock profile's adjusted 260-session request (StockProfile.daily_snapshot). The chart's own request is unadjusted, so
the engine would refuse it; no provider is called here. It runs on the screen's job runner (quantgen_desktop.jobs.Jobs,
off the UI thread), once per loaded history and at most every LIVE_SECONDS for KIS live trades, and drops a result
whose stock or history changed while it ran. The screen also takes a score the app's controllers already have (the
watchlist feed or the chart's score history, MarketChartPane.q_score_result) and shows the newer ready one (`pick`).

The pure helpers (`reading`, `reason`, `as_of_text`, `badge_text`, `pick`) take a compute_q_score result and a language
('ko' or 'en'); display text lives in owner_ui_language/stock.py (keys 'qs_*').
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
import time
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QObject, QRectF, QSize, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from core.market.models import MarketTick
from core.research.qscore import MIN_SESSIONS, compute_q_score, q_score_help
from .jobs import Jobs
from .owner_ui_language.stock import TEXT
from .stock_detail_style import label, numbers, polite

_KST = timezone(timedelta(hours=9))
PARTS = ("technical", "drawdown", "tail_loss")
LIVE_STATES = ("streaming", "subscribed", "connecting")
# Engine reasons that share one plain sentence.
_REASON_GROUPS = {
    "invalid_history": "bad_dates", "invalid_history_dates": "bad_dates", "future_history": "bad_dates",
    "invalid_engine_output": "engine", "engine_unavailable": "engine",
    "invalid_quote": "quote", "future_quote": "quote", "stale_quote": "quote", "out_of_order_quote": "quote",
    "adjustment_mismatch": "quote",
}
_REASONS = ("unsupported_instrument", "unverified_source", "connection_not_configured", "adjusted_history_required",
            "daily_history_required", "insufficient_history", "flat_history", "stale_history", "history_unavailable",
            "invalid_clock", "not_in_candidates", "ranking_waiting")


def _t(lang, key, **fields):
    en, ko = TEXT[key]
    value = ko if lang == "ko" else en
    return value.format(**fields) if fields else value


def _finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and not isinstance(value, bool) else None


def ready(result):
    """True for a usable score: status ready, a score in 0-100 and 1-5 stars."""
    if not isinstance(result, dict) or result.get("status") != "ready":
        return False
    score, stars = _finite(result.get("score")), result.get("stars")
    return (score is not None and 0 <= score <= 100 and isinstance(stars, int) and not isinstance(stars, bool)
            and 1 <= stars <= 5)


def shown_score(result):
    """The score as this screen prints it: whole points, cut (not rounded) so it agrees with the stars
    (the engine gives 5 stars from 80, so 79.96 reads 79 next to 4 stars)."""
    return int(math.floor(float(result["score"]) + 1e-9))


def part_score(result, key):
    part = (result.get("components") or {}).get(key) or {}
    return _finite(part.get("score"))


def part_raw(result, key):
    part = (result.get("components") or {}).get(key) or {}
    return _finite(part.get("raw"))


def part_weight(result, key):
    part = (result.get("components") or {}).get(key) or {}
    return _finite(part.get("weight"))


def tech_level(result):
    """'strong', 'middle' or 'weak', on the signal engine's own stance edges (composite ±15)."""
    raw = part_raw(result, "technical")
    if raw is None:
        score = part_score(result, "technical")
        raw = None if score is None else score * 2 - 100
    if raw is None:
        return "middle"
    return "strong" if raw >= 15 else "weak" if raw <= -15 else "middle"


def part_points(score):
    """A part's score as the card prints it (whole points, cut like the total), or None."""
    return None if score is None else int(math.floor(score + 1e-9))


def risk_level(score):
    """'low', 'usual' or 'high' risk for a drawdown or tail-loss part score (a higher score is a smaller loss), on
    the points the card prints: 70 and up low (a fall of at most 12% from a high, a worst-days loss of at most
    2.4%), under 40 high (more than 24%, more than 4.8%)."""
    points = part_points(score)
    if points is None:
        return "usual"
    return "low" if points >= 70 else "high" if points < 40 else "usual"


def reading(result, lang):
    """One short sentence of what the parts say ('기술 신호가 강한 편이고 하락 위험은 낮은 편이에요'); '' without a score.
    The risk clause names the worse of the two risk parts, or '하락' when they are at the same level."""
    if not ready(result):
        return ""
    tech = tech_level(result)
    levels = {key: risk_level(part_score(result, key)) for key in ("drawdown", "tail_loss")}
    order = {"low": 0, "usual": 1, "high": 2}
    worst = max(levels.values(), key=order.get)
    if levels["drawdown"] == levels["tail_loss"]:
        what = "qs_risk_both"
    else:
        what = "qs_risk_drawdown" if levels["drawdown"] == worst else "qs_risk_tail"
    contrast = (tech == "strong" and worst == "high") or (tech == "weak" and worst == "low")
    first = _t(lang, f"qs_tech_{tech}_but" if contrast else f"qs_tech_{tech}")
    second = _t(lang, f"qs_risk_{worst}", what=_t(lang, what))
    joined = first + _t(lang, "qs_but" if contrast else "qs_and") + second
    return joined


def reason(result, lang, *, state=""):
    """(why, what would give a score) in plain words for a result that is not a score, or for the screen's own
    state ('waiting' for the daily history, 'loading' it, 'computing')."""
    if state in ("waiting", "loading", "computing") and not isinstance(result, dict):
        fix = _t(lang, "qs_fix_waiting") if state == "waiting" else ""
        return _t(lang, f"qs_why_{state}"), fix
    result = result if isinstance(result, dict) else {}
    code = str(result.get("reason") or "")
    if result.get("status") == "insufficient_data" and not code:
        code = "insufficient_history"
    group = _REASON_GROUPS.get(code, code)
    if code == "insufficient_history":
        sessions = result.get("sessions") or 0
        return (_t(lang, "qs_why_insufficient_history", sessions=sessions),
                _t(lang, "qs_fix_insufficient_history", needed=MIN_SESSIONS))
    if group in _REASONS or group in ("bad_dates", "engine", "quote"):
        return _t(lang, f"qs_why_{group}"), _t(lang, f"qs_fix_{group}")
    return _t(lang, "qs_why_other"), _t(lang, "qs_needs")


def _month_day(day, lang):
    months = TEXT["months"][1 if lang == "ko" else 0]
    return _t(lang, "qs_date", month=months[day.month - 1], day=day.day)


def as_of_text(result, lang):
    """When the score's prices are from: '11월 10일 기준' for daily prices, '14:32 체결 반영 · 실시간' with a live trade."""
    value = str((result or {}).get("as_of") or "")
    if not value:
        return ""
    try:
        if len(value) == 10:
            return _t(lang, "qs_as_of_day", date=_month_day(date.fromisoformat(value), lang))
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return ""
        local = stamp.astimezone(_KST)
    except ValueError:
        return ""
    clock = local.strftime("%H:%M")
    if result.get("live"):
        return _t(lang, "qs_as_of_trade", time=clock)
    return _t(lang, "qs_as_of_time", date=_month_day(local.date(), lang), time=clock)


def badge_text(result, lang, *, state="", short=False):
    """The toolbar badge: 'Q 72 ★★★★' (short: 'Q 72'), 'Q –' without a score, 'Q …' while it is on its way."""
    if ready(result):
        score = shown_score(result)
        if short:
            return _t(lang, "qs_badge_short", score=score)
        return _t(lang, "qs_badge", score=score, stars="★" * int(result["stars"]))
    if not isinstance(result, dict) and state in ("loading", "computing"):
        return _t(lang, "qs_badge_wait")
    return _t(lang, "qs_badge_none")


def _moment(result):
    value = str(result.get("as_of") or "")
    try:
        if len(value) == 10:
            day = date.fromisoformat(value)
            if result.get("asset") == "overseas_stock":
                return datetime(day.year, day.month, day.day, 16, 0, tzinfo=ZoneInfo("America/New_York"))
            return datetime(day.year, day.month, day.day, 15, 30, tzinfo=_KST)
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is not None:
            return stamp
    except ValueError:
        pass
    return datetime.min.replace(tzinfo=timezone.utc)


def pick(own, feed):
    """The score to show: a ready score beats a refusal; of two ready scores the one with the later prices (a live
    trade after a daily close), then the later calculation; without a ready score, the screen's own answer first."""
    scores = [s for s in (own, feed) if isinstance(s, dict)]
    good = [s for s in scores if ready(s)]
    if good:
        return max(good, key=lambda s: (_moment(s), str(s.get("computed_at") or "")))
    return scores[0] if scores else None


def _signed(value, digits=1):
    return f"{value:+.{digits}f}".replace("-", "−")


def _percent(value, digits=1):
    return f"{value * 100:.{digits}f}%".replace("-", "−")


def figures_line(result, lang):
    """The raw numbers behind the three parts, for the '자세히' fold."""
    if not ready(result):
        return ""
    technical, drawdown, tail = (part_raw(result, key) for key in PARTS)
    if None in (technical, drawdown, tail):
        return ""
    return _t(lang, "qs_figures", technical=_signed(technical), drawdown=_percent(drawdown),
              tail=_percent(-abs(tail)))


def part_tip(result, key, lang):
    raw = part_raw(result, key)
    if raw is None:
        return ""
    sessions = result.get("sessions") or 0
    if key == "technical":
        return _t(lang, "qs_part_technical_tip", raw=_signed(raw))
    if key == "drawdown":
        return _t(lang, "qs_part_drawdown_tip", raw=_percent(raw), sessions=sessions)
    return _t(lang, "qs_part_tail_loss_tip", raw=_percent(-abs(raw)))


def methodology(lang):
    """core.research.qscore.q_score_help in the screen's register (해요체), one paragraph per item."""
    return tuple(part.strip() for part in polite(q_score_help(lang), lang).split("\n\n") if part.strip())


# Widgets ------------------------------------------------------------------------------------------------
class ScoreBar(QWidget):
    """One part's score, 0-100, as a short filled track."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(14)
        self.setMinimumWidth(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.value, self.colors = None, ("#E2E3DB", "#194C40")

    def set_value(self, value, colors):
        self.value, self.colors = value, colors
        self.update()

    def sizeHint(self):
        return QSize(120, 14)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track, fill = (QColor(c) for c in self.colors)
        y, h = (self.height() - 6) / 2, 6
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, y, self.width(), h), h / 2, h / 2)
        if self.value is not None:
            width = max(h, min(1.0, max(0.0, self.value / 100)) * self.width())
            p.setBrush(fill)
            p.drawRoundedRect(QRectF(0, y, width, h), h / 2, h / 2)
        p.end()


class QScoreCard(QFrame):
    """The Q-SCORE card (guide-card style, UI-D9): title and as-of, the score and stars, one reading, the three
    parts with their weights, the disclaimer and the methodology behind '자세히 ›'. Without a score: why, and what
    would give one."""
    more_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setObjectName("sdQScore")
        self.setProperty("sd", "guideCard")
        self.language = "ko"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        self.title = label("qsTitle")
        self.title.setText("Q-SCORE")
        head.addWidget(self.title, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addStretch(1)
        self.as_of = numbers(label("qsAsOf"))
        head.addWidget(self.as_of, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)
        self.score_row = QWidget()
        figures = QHBoxLayout(self.score_row)
        figures.setContentsMargins(0, 0, 0, 0)
        figures.setSpacing(6)
        self.score = numbers(label("qsScore", selectable=True))
        figures.addWidget(self.score, 0, Qt.AlignmentFlag.AlignBottom)
        self.out_of = numbers(label("qsOutOf"))
        figures.addWidget(self.out_of, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addSpacing(8)
        self.stars = QLabel()
        self.stars.setProperty("sd", "qsStars")
        self.stars.setProperty("qg_literal", True)
        self.stars.setTextFormat(Qt.TextFormat.RichText)
        figures.addWidget(self.stars, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addStretch(1)
        layout.addWidget(self.score_row)
        self.headline = label("qsReading", wrap=True)
        layout.addWidget(self.headline)
        self.fix = label("guideOne", wrap=True)
        layout.addWidget(self.fix)
        self.parts_box = QWidget()
        grid = QGridLayout(self.parts_box)
        grid.setContentsMargins(0, 2, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(2, 1)
        self.parts = {}
        for row, key in enumerate(PARTS):
            name = label("qsPart")
            weight = numbers(label("qsWeight"))
            bar = ScoreBar()
            value = numbers(label("qsValue"))
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value.setMinimumWidth(26)
            for column, widget in enumerate((name, weight, bar, value)):
                grid.addWidget(widget, row, column, Qt.AlignmentFlag.AlignVCenter)
            self.parts[key] = (name, weight, bar, value)
        self.bars_note = label("guideCaution", wrap=True)
        grid.addWidget(self.bars_note, len(PARTS), 0, 1, 4)
        layout.addWidget(self.parts_box)
        # Too short a history: how far it is from the 200 sessions the engine needs.
        self.progress_box = QWidget()
        progress = QHBoxLayout(self.progress_box)
        progress.setContentsMargins(0, 0, 0, 0)
        progress.setSpacing(10)
        self.progress_name = label("qsPart")
        self.progress_bar = ScoreBar()
        self.progress_value = numbers(label("qsValue"))
        progress.addWidget(self.progress_name)
        progress.addWidget(self.progress_bar, 1)
        progress.addWidget(self.progress_value)
        self.progress_box.hide()
        layout.addWidget(self.progress_box)
        self.disclaimer = label("guideCaution", wrap=True)
        layout.addWidget(self.disclaimer)
        self.more = QPushButton()
        self.more.setProperty("sd", "link")
        self.more.setProperty("qg_literal", True)
        self.more.setCheckable(True)
        self.more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more.toggled.connect(self._more_toggled)
        layout.addWidget(self.more, 0, Qt.AlignmentFlag.AlignLeft)
        self.details = QWidget()
        details = QVBoxLayout(self.details)
        details.setContentsMargins(0, 2, 0, 0)
        details.setSpacing(10)
        self.detail_labels = []
        self.details_layout = details
        self.details.hide()
        layout.addWidget(self.details)
        self.result, self.state = None, ""

    def _more_toggled(self, on):
        self.details.setVisible(on)
        self.more.setText(_t(self.language, "guide_less" if on else "guide_more"))
        self.more_toggled.emit(on)

    def _set_details(self, paragraphs):
        from .indicator_picker import paragraph
        while len(self.detail_labels) < len(paragraphs):
            part = QLabel()
            part.setTextFormat(Qt.TextFormat.RichText)
            part.setWordWrap(True)
            part.setProperty("sd", "guideLong")
            part.setProperty("qg_literal", True)
            part.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            self.details_layout.addWidget(part)
            self.detail_labels.append(part)
        for index, part in enumerate(self.detail_labels):
            value = paragraphs[index] if index < len(paragraphs) else ""
            part.setText(paragraph(value) if value else "")
            part.setVisible(bool(value))

    def show_score(self, result, *, language, state="", colors=None):
        """Fill the card from a compute_q_score result (or None while `state` is 'waiting', 'loading' or
        'computing'). colors: track, fill, empty star and filled star colours."""
        self.language = lang = language
        self.result, self.state = result, state
        track, fill, star_off, star_on = colors or ("#E2E3DB", "#194C40", "#D5D8CF", "#194C40")
        self.title.setText(_t(lang, "qs_title"))
        good = ready(result)
        self.score_row.setVisible(good)
        self.parts_box.setVisible(good)
        if good:
            score, stars = shown_score(result), int(result["stars"])
            self.score.setText(str(score))
            self.score.setToolTip(_t(lang, "qs_exact", score=f"{float(result['score']):.2f}"))
            self.out_of.setText(_t(lang, "qs_out_of"))
            self.stars.setText(f'<span style="color:{star_on}">{"★" * stars}</span>'
                               f'<span style="color:{star_off}">{"★" * (5 - stars)}</span>')
            self.stars.setAccessibleName(_t(lang, "qs_stars_name", stars=stars))
            self.stars.setToolTip(self.stars.accessibleName())
            self.headline.setText(reading(result, lang))
            self.fix.setText(_t(lang, "qs_feed_paused") if result.get("feed_state") in ("stale", "stopped", "error")
                             and len(str(result.get("as_of") or "")) > 10 else "")
            for key, (name, weight, bar, value) in self.parts.items():
                points = part_score(result, key)
                share = part_weight(result, key)
                name.setText(_t(lang, f"qs_part_{key}"))
                weight.setText(_t(lang, "qs_weight", pct=f"{share * 100:.0f}") if share is not None else "")
                bar.set_value(points, (track, fill))
                value.setText("—" if points is None else str(part_points(points)))
                tip = part_tip(result, key, lang)
                for widget in (name, weight, bar, value):
                    widget.setToolTip(tip)
            self.bars_note.setText(_t(lang, "qs_bars_note"))
            self.as_of.setText(as_of_text(result, lang) + " · " + str(result.get("source") or "") +
                               (" · 수정 일별" if lang == "ko" else " · adjusted daily"))
            start, end = result.get("history_start"), result.get("history_end")
            self.as_of.setToolTip(_t(lang, "qs_as_of_tip", sessions=result.get("sessions") or 0, start=start or "—",
                                     end=end or "—", method=result.get("methodology") or "") if start else "")
        else:
            why, fix = reason(result, lang, state=state)
            self.headline.setText(why)
            self.fix.setText(fix)
            self.as_of.setText("")
            self.as_of.setToolTip("")
        sessions = (result or {}).get("sessions") if isinstance(result, dict) else None
        short = (not good and isinstance(result, dict) and result.get("reason") == "insufficient_history"
                 and isinstance(sessions, int) and 0 < sessions < MIN_SESSIONS)
        self.progress_box.setVisible(short)
        if short:
            self.progress_name.setText(_t(lang, "qs_sessions"))
            self.progress_bar.set_value(sessions / MIN_SESSIONS * 100, (track, fill))
            self.progress_value.setText(_t(lang, "qs_sessions_value", sessions=sessions, needed=MIN_SESSIONS))
        self.fix.setVisible(bool(self.fix.text()))
        self.as_of.setVisible(bool(self.as_of.text()))
        self.disclaimer.setText(_t(lang, "qs_disclaimer"))
        figures = figures_line(result, lang)
        self._set_details(((figures,) if figures else ()) + methodology(lang))
        self.more.setText(_t(lang, "guide_less" if self.more.isChecked() else "guide_more"))
        self.more.setAccessibleName(_t(lang, "guide_more_name", name="Q-SCORE"))
        self.setAccessibleName(" · ".join(t for t in (_t(lang, "qs_title"), self.score.text() if good else "",
                                                      self.headline.text()) if t))


# The score runner -----------------------------------------------------------------------------------------
class StockScore(QObject):
    """The open stock's own Q-SCORE: one engine run per loaded daily history, live trades at most every
    LIVE_SECONDS, results of another stock or history dropped. `state`: 'idle', 'waiting' (a domestic stock whose
    daily history has not arrived) or 'computing' (the first run for this history). `runs` counts engine runs."""
    changed = pyqtSignal()
    LIVE_SECONDS = 5.0

    def __init__(self, parent=None, *, now=None):
        super().__init__(parent)
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.instrument = None
        self.history = None
        self.result = None
        self.state = "idle"
        self.runs = 0
        self._epoch = 0
        self._scored_history = None   # the history the current daily result was computed from
        self._tick = None             # the latest trade not yet scored
        self._running = None          # (epoch, history, tick) of the run in the job runner
        self._last_live = None        # time.monotonic() of the last trade run
        self._last_scored = None      # as_of of the last scored trade: an older trade is refused by the engine
        self._feed_live = False
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._done)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._run_tick)

    def _refusal(self, reason_code):
        result = compute_q_score(None, now=self.now(), symbol=getattr(self.instrument, "code", ""))
        result["reason"] = reason_code
        return result

    def _supported(self):
        return self.instrument is not None and (self.instrument.asset == "domestic_stock" or (
            self.instrument.asset == "overseas_stock" and self.instrument.exchange in ("NAS", "NYS", "AMS")))

    def open(self, instrument):
        """A stock was opened: forget the last one (its running result will be dropped)."""
        self._epoch += 1
        self.instrument = instrument
        self.history = self.result = self._scored_history = self._tick = None
        self._last_live = self._last_scored = None
        self.timer.stop()
        self._feed_live = False
        if instrument is None:
            self.state = "idle"
        elif not self._supported():
            self.state = "idle"
            self.result = self._refusal("unsupported_instrument")
        else:
            self.state = "waiting"
        self.changed.emit()

    def set_history(self, snapshot, reason_code="history_unavailable"):
        """The daily history the screen loaded for the open stock (StockProfile.daily_snapshot), or None with the
        reason there is none."""
        if not self._supported():
            return False
        if snapshot is None:
            self.history = self._scored_history = self._tick = None
            self.timer.stop()
            self.result = self._refusal(reason_code)
            self.state = "idle"
            self.changed.emit()
            return False
        if snapshot.request.instrument != self.instrument:
            return False
        if snapshot is self.history:
            return False
        self.history = snapshot
        self._last_scored = None
        if self.result is None:
            self.state = "computing"
            self.changed.emit()
        self._pump()
        return True

    def accept_tick(self, tick):
        """A KIS live trade of the open stock: scored with the daily history at most every LIVE_SECONDS."""
        if (not self._supported() or not isinstance(tick, MarketTick) or tick.source != "KIS WebSocket"
                or tick.instrument != self.instrument):
            return False
        self._tick = tick
        self._schedule()
        return True

    def set_feed(self, mode):
        """The chart's feed mode: once it is not live, the last score stops saying it is live."""
        self._feed_live = str(mode) in LIVE_STATES
        if self._feed_live:
            return
        self._tick = None
        self.timer.stop()
        if isinstance(self.result, dict) and self.result.get("live"):
            self.result = dict(self.result, live=False, feed_state="stopped")
            self.changed.emit()

    def stop(self):
        self._epoch += 1
        self._tick = None
        self.timer.stop()
        self.set_feed("stopped")
        if self.state == "computing":
            self.state = "waiting" if self.result is None and self._supported() else "idle"
        self.history = self._scored_history = None

    def _schedule(self):
        if self.history is None or self._tick is None or self.timer.isActive():
            return
        wait = 0.0 if self._last_live is None else self.LIVE_SECONDS - (time.monotonic() - self._last_live)
        if wait <= 0:
            self._run_tick()
        else:
            self.timer.start(int(wait * 1000) + 1)

    def _run_tick(self):
        if self.jobs.busy or self.history is None or self._tick is None or self._scored_history is not self.history:
            return  # _busy() comes back here when the runner is free
        tick, self._tick = self._tick, None
        self._last_live = time.monotonic()
        self._launch(tick)

    def _pump(self):
        if self.jobs.busy or self.history is None:
            return
        if self._scored_history is not self.history:
            self._launch(None)
        elif self._tick is not None:
            self._schedule()

    def _launch(self, tick):
        token = (self._epoch, self.history, tick)
        history, now, previous = self.history, self.now(), self._last_scored

        def run():
            if tick is None:
                return token, compute_q_score(history, now=now)
            return token, compute_q_score(history, latest_price=tick.price, as_of=tick.timestamp,
                                          previous_as_of=previous, now=now)

        if self.jobs.start(run):
            self._running = token
            self.runs += 1

    @pyqtSlot(object)
    def _done(self, payload):
        (epoch, history, tick), result = payload
        if epoch != self._epoch or history is not self.history:
            return   # another stock or a newer history: this result is stale
        if tick is None:
            self._scored_history = history
            self.result = result
        elif result.get("status") == "ready":
            self._last_scored = result.get("as_of")
            self.result = result if self._feed_live else dict(result, live=False, feed_state="stopped")
        else:
            return   # a refused trade (late, out of order, another price basis) leaves the score as it was
        self.state = "idle"
        self.changed.emit()

    @pyqtSlot(str)
    def _failed(self, _code):
        if self._running is None:
            return
        epoch, history, tick = self._running
        if epoch != self._epoch or history is not self.history or tick is not None:
            return
        self._scored_history = history
        self.result = self._refusal("engine_unavailable")
        self.state = "idle"
        self.changed.emit()

    @pyqtSlot(bool)
    def _busy(self, busy):
        if not busy:
            self._running = None
            self._pump()


__all__ = ["StockScore", "QScoreCard", "ScoreBar", "reading", "reason", "as_of_text", "badge_text", "pick",
           "ready", "shown_score", "figures_line", "methodology", "MIN_SESSIONS"]
