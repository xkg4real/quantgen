"""Native market watchlist and read-only detail views; no provider calls."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import re
from babel.dates import format_date

from PyQt6.QtCore import QEvent, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QScrollArea, QSizePolicy, QTableWidget,
    QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.i18n import LocaleContext
from core.numfmt import compact_large_number
from core.theme import LIGHT
from .company_identity import CompanyMark
from .typography import scaled_font, tone_colors, tone_for

ROW_HEIGHT = 44
DETAIL_COLUMN = 8
SCORE_COLUMN = 9
# Owner issue 05 (2026-11-10, "오와 열 맞추고 글씨 조정"): one inset for every header label and cell
# text, numbers right-aligned on their digits with the unit in a fixed slot after them, one body size.
CELL_PADDING = 10
UNIT_GAP = 4
BODY_PX = 13
NUMERIC_COLUMNS = (1, 2, 3, 4, 5, 6)
UNIT_COLUMNS = (1, 2, 3, 4)
_NUMBER_UNIT = re.compile(r"([+\-−]?\d[\d,]*(?:\.\d+)?)(\s*)(\S.*)?")
_KST = timezone(timedelta(hours=9))
_SECTORS_EN = {"전기전자": "Electronics", "전기,전자": "Electronics", "전기·전자": "Electronics",
               "운수장비": "Transport equipment", "금융업": "Financials", "의약품": "Pharmaceuticals",
               "서비스업": "Services", "기계": "Machinery", "화학": "Chemicals"}


_NAMES = {
    "005930": ("삼성전자", "Samsung Electronics"),
    "000660": ("SK하이닉스", "SK hynix"),
    "005380": ("현대차", "Hyundai Motor"),
    "105560": ("KB금융", "KB Financial"),
    "373220": ("LG에너지솔루션", "LG Energy Solution"),
    "207940": ("삼성바이오로직스", "Samsung Biologics"),
    "^GSPC": ("S&P 500", "S&P 500"),
    "^KS11": ("KOSPI", "KOSPI"),
    "DEXKOUS": ("USD / KRW", "USD / KRW"),
    "DGS10": ("미국 10년 금리", "US 10-year yield"),
    "VIXCLS": ("VIX", "VIX"),
    "BTC-USD": ("비트코인", "Bitcoin"),
}
_BADGES = {"^GSPC": "SPX", "^KS11": "KOSPI", "DEXKOUS": "USDKRW",
           "DGS10": "US10Y", "VIXCLS": "VIX", "BTC-USD": "BTC"}
_STATUS = {
    "NOT_LOADED": ("조회 전", "Not loaded"),
    "LOADING": ("조회 중", "Loading"),
    "UNAVAILABLE": ("조회 불가", "Unavailable"),
    "STALE": ("오래된 자료", "Stale"),
    "OBSERVED": ("정상 관측", "Daily observation"),
    "SNAPSHOT": ("조회 시세", "Quote snapshot"),
    "STREAMING": ("실시간 체결", "Live trades"),
}
_LIVE_STATUS = {
    "idle": ("실시간 연결 전", "Live connection idle"),
    "loading": ("과거 자료 준비 중", "Preparing historical data"),
    "connecting": ("실시간 서버 연결 중", "Connecting to live feed"),
    "subscribed": ("구독 완료 · 첫 체결 대기", "Subscribed · awaiting first trade"),
    "streaming": ("실시간 체결 수신 중", "Receiving live trades"),
    "stale": ("수신 지연 · 마지막 값 유지", "Feed stale · retaining last values"),
    "stopped": ("실시간 연결 종료", "Live connection stopped"),
    "error": ("실시간 연결 실패", "Live connection failed"),
}


def _text(ctx, ko, en):
    return ko if ctx.language == "ko" else en


def _label(text=""):
    label = QLabel(str(text))
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _name(row, ctx):
    names = _NAMES.get(str(row.get("symbol", "")))
    return _text(ctx, *names) if names else str(row.get("label") or row.get("symbol") or "—")


def _number(value, ctx, digits=2):
    return ctx.number(_finite(value), digits)


def _compact(value, ctx):
    """Use one magnitude scale for volume/cap across every UI language."""
    return compact_large_number(value, str(ctx.locale))


def _metric(value, ctx):
    value = _finite(value)
    return "—" if value is None else ctx.number(value, 0 if value.is_integer() else 2)


def _cap_value(row):
    value = _finite(row.get("market_cap"))
    return value if row.get("market_cap_unit") == "KRW" and value is not None and value > 0 else None


def _sector(row, ctx, *, compact=False):
    raw = row.get("sector")
    if not raw:
        return "—"
    if ctx.language == "ko":
        return str(raw)
    translated = _SECTORS_EN.get(str(raw), "Untranslated")
    if compact:
        return {"Transport equipment": "Transport eq.", "Pharmaceuticals": "Pharma"}.get(translated, translated)
    return translated


def _fundamental_tooltip(row, ctx, field):
    if row.get("kind") != "domestic_stock":
        return _text(ctx, "이 시장지표에는 종목 재무 항목이 적용되지 않습니다.", "Stock fundamentals do not apply to this market indicator.")
    value = row.get(field)
    if field == "market_cap":
        cap = _cap_value(row)
        description = (_number(cap, ctx, 0) + " KRW" if cap is not None else
                       _text(ctx, "시가총액 확인 안 됨 · 가격 조회 상태와 별개입니다.", "Market cap unconfirmed · independent of price availability."))
        if cap is not None and row.get("market_cap_basis") == "price_x_listed_shares":
            description += "\n" + _text(ctx, "산출값: 가격 × 상장 주식 수", "Calculated: price × listed shares")
        description += "\n" + _text(ctx, "시가총액 기준 시각: ", "Market cap data as of: ") + _timestamp(row.get("market_cap_as_of"), ctx)
        if not row.get("market_cap_as_of"):
            description += "\n" + _text(ctx, "조회 시세로 계산한 스냅샷입니다. 실제 가격 관측 시각은 제공되지 않았습니다.",
                                        "Calculated from a quote snapshot; the actual price observation time was not supplied.")
    elif field == "sector":
        description = _sector(row, ctx) + "\n" + _text(ctx, "공급처 업종 원문: ", "Provider sector text: ") + str(value or "—")
    else:
        description = field.upper() + ": " + _number(value, ctx)
        description += "\n" + _text(ctx, "KIS 제공값 · 회계 기준과 기준일은 확인되지 않았습니다. EPS 단위·희석 여부도 확인되지 않았습니다.",
                                    "KIS-provided value. Accounting basis and reference date are unconfirmed; EPS unit and dilution basis are also unconfirmed.")
    description += "\n" + _text(ctx, "재무 항목 수신: ", "Fundamentals received: ") + _timestamp(row.get("fundamentals_received_at"), ctx)
    description += "\n" + (_text(ctx, "공급처 기준일: ", "Provider reference date: ") + _date(row.get("fundamentals_as_of"), ctx)
                            if row.get("fundamentals_as_of") else _text(ctx, "공급처 기준일 미제공", "Provider reference date not supplied"))
    return description


def _refresh_cap_from_tick(row, price, market_time):
    """Reuse shares only within their received KST session; never refresh EPS/PER clocks."""
    if row.get("kind") != "domestic_stock" or row.get("provider") != "KIS" or row.get("unit") != "KRW":
        return
    shares = _finite(row.get("listed_shares"))
    if shares is None or not 0 < shares <= 2**53 - 1 or not shares.is_integer():
        return
    try:
        received = row.get("fundamentals_received_at")
        received = datetime.fromisoformat(received.replace("Z", "+00:00")) if isinstance(received, str) else received
        trade = datetime.fromisoformat(market_time.replace("Z", "+00:00")) if isinstance(market_time, str) else market_time
        if (not isinstance(received, datetime) or not isinstance(trade, datetime)
                or received.tzinfo is None or trade.tzinfo is None
                or received.astimezone(_KST).date() != trade.astimezone(_KST).date()):
            return
        cap = _finite(price * shares)
        if cap is not None and cap > 0:
            row.update(market_cap=cap, market_cap_unit="KRW", market_cap_basis="price_x_listed_shares", market_cap_as_of=trade.isoformat())
    except (TypeError, ValueError, OverflowError):
        return


def _price(row, ctx):
    value = _finite(row.get("value"))
    if value is None:
        return "—"
    unit = str(row.get("unit") or "")
    digits = 0 if unit == "KRW" else 2
    return f"{ctx.number(value, digits)} {unit}".strip()


def _change(row, ctx):
    value = _finite(row.get("change"))
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return sign + (ctx.number(value, 2) + " bp" if row.get("unit") == "%"
                   else ctx.percent(value / 100, 2))


def _date(value, ctx):
    try:
        return ctx.date(value) if value else "—"
    except (TypeError, ValueError):
        return "—"


def _timestamp(value, ctx, *, compact=False):
    try:
        if not value:
            return "—"
        moment = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
        if not isinstance(moment, datetime) or moment.tzinfo is None:
            return "—"
        utc = moment.astimezone(timezone.utc)
        if compact:
            return format_date(utc.date(), format="short", locale=ctx.locale) + utc.strftime(" %H:%M:%S UTC")
        return ctx.timestamp(utc) + " UTC"
    except (TypeError, ValueError):
        return "—"


def _status(row, ctx):
    if row.get("status") == "UNAVAILABLE":
        reasons = {
            "no_observations": ("자료 없음", "No data"),
            "insufficient_observations": ("자료 부족", "Too little data"),
            "rate_limited": ("요청 제한", "Rate limited"),
            "network_timeout": ("응답 지연", "Timed out"),
            "network_error": ("연결 확인", "Connection"),
            "certificate_error": ("인증서 확인", "Certificate"),
            "access_denied": ("권한 확인", "Access denied"),
            "dependency_missing": ("설치 확인", "Missing package"),
            "dependency_incompatible": ("버전 확인", "Version issue"),
            "connection_not_configured": ("설정 필요", "Setup needed"),
            "invalid_response": ("응답 확인", "Invalid response"),
        }
        if row.get("reason_code") in reasons:
            return _text(ctx, *reasons[row["reason_code"]])
    if row.get("status") == "STALE" and row.get("quote_time_kind") == "trade":
        if row.get("feed_state") == "stopped":
            return _text(ctx, "연결 종료", "Disconnected")
        if row.get("feed_state") == "error":
            return _text(ctx, "연결 오류", "Connection error")
        return _text(ctx, "수신 지연", "Feed stale")
    return _text(ctx, *_STATUS.get(row.get("status"), ("확인 필요", "Unconfirmed")))


def _score_text(score, ctx):
    score = score if isinstance(score, dict) else {}
    points, stars = _finite(score.get("score")), score.get("stars")
    if (score.get("status") == "ready" and points is not None and 0 <= points <= 100
            and isinstance(stars, int) and not isinstance(stars, bool) and 1 <= stars <= 5):
        text = "★" * stars + "☆" * (5 - stars) + "  " + ctx.number(points, 2)
        if score.get("feed_state") in ("stale", "stopped", "error"):
            text += _text(ctx, "\n중지됨 · 마지막 점수", "\nPaused · last score")
        return text
    if score.get("status") == "insufficient_data":
        return _text(ctx, "자료 부족", "Insufficient data")
    if score.get("status") == "unavailable":
        return _text(ctx, "산정 불가", "Unavailable")
    return _text(ctx, "산정 전", "Not scored")


def _score_tooltip(score, ctx):
    score = score if isinstance(score, dict) else {}
    return (_text(ctx, "가격 흐름과 위험을 함께 비교하는 연구 점수입니다. 표 제목 옆 ?에서 Q-SCORE 소개를 확인하세요.",
                  "Compare price behavior and risk with this research score. Open ? beside the column title to learn about Q-SCORE.")
            + "\n" + _text(ctx, "점수 기준: ", "Score data as of: ") + _score_as_of(score, ctx))


def _score_as_of(score, ctx):
    score = score if isinstance(score, dict) else {}
    value = score.get("as_of")
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return _date(value, ctx) + _text(ctx, " · 일별 자료", " · daily data")
    return _timestamp(value, ctx)


def _score_help_summary(ctx):
    return (_text(ctx,
                  "QUANTGEN의 기술신호·위험분석 엔진이 추세·모멘텀·변동성·하락 위험을 함께 살펴 정리한 연구 별점입니다.",
                  "A research rating from QUANTGEN's technical-signal and risk engines, bringing together trend, momentum, volatility and downside risk.") + "\n\n"
            + _text(ctx, "클릭하거나 Enter·Space를 누르면 활용 방법과 해석 시 유의점을 확인할 수 있습니다.",
                    "Click or press Enter/Space to explore its uses and interpretation limits."))


def _can_chart(row):
    return row.get("kind") == "domestic_stock" and bool(re.fullmatch(r"\d{6}", str(row.get("symbol", ""))))


def _provider(row, ctx):
    provider = str(row.get("provider") or "").upper()
    return provider if provider in ("YFINANCE", "FRED", "KIS") else _text(ctx, "확인 안 됨", "Unconfirmed")


def _source_time(row, ctx, *, compact=False):
    source = _provider(row, ctx)
    if row.get("quote_time_kind") == "trade":
        source += _text(ctx, " · 체결", " · traded")
        detail = _timestamp(row.get("market_time"), ctx, compact=compact)
    elif row.get("kind") == "domestic_stock":
        received = row.get("received_at")
        source += _text(ctx, " · 수신", " · received")
        detail = _timestamp(received, ctx, compact=compact) if received else _text(ctx, "수신 시각 없음", "No receipt time")
    else:
        source += _text(ctx, " · 관측", " · observed")
        detail = _date(row.get("observation_date"), ctx)
    return source + "\n" + detail


def _price_tooltip(row, ctx):
    return (" · ".join((_name(row, ctx), _price(row, ctx), _status(row, ctx))) + "\n"
            + _source_time(row, ctx) + "\n"
            + _text(ctx, "앱 수신: ", "App received: ") + _timestamp(row.get("received_at"), ctx)
            + "\n" + _reason(row, ctx)
            + "\n" + _text(ctx, "상태 코드: ", "Status code: ") + str(row.get('status') or '—'))


def _reason(row, ctx):
    reason = row.get("reason_code") or row.get("error_code")
    provider_reasons = {
        "no_observations": ("공급처가 관측값을 반환하지 않았습니다. 연결과 조회 종목을 확인한 뒤 다시 조회하세요.",
                            "The provider returned no observations. Check the connection and instrument, then refresh."),
        "insufficient_observations": ("변화를 계산할 관측값이 부족합니다. 나중에 다시 조회하세요.",
                                      "There are too few observations to calculate a change. Refresh later."),
        "rate_limited": ("공급처의 요청 한도에 도달했습니다. 잠시 기다린 뒤 새로고침하세요.",
                         "The provider's request limit was reached. Wait briefly, then refresh."),
        "network_timeout": ("공급처 응답 시간이 초과되었습니다. 인터넷 연결을 확인한 뒤 다시 조회하세요.",
                            "The provider response timed out. Check the internet connection, then refresh."),
        "network_error": ("공급처에 연결하지 못했습니다. 인터넷 연결과 프록시 설정을 확인한 뒤 다시 조회하세요.",
                          "The provider could not be reached. Check the internet connection and proxy settings, then refresh."),
        "certificate_error": ("공급처의 인증서를 확인하지 못했습니다. PC 시각과 네트워크 인증서 설정을 확인하세요.",
                              "The provider certificate could not be verified. Check the PC clock and network certificate settings."),
        "access_denied": ("공급처가 조회를 허용하지 않았습니다. 해당 공급처의 접근 권한과 이용 조건을 확인하세요.",
                          "The provider denied access. Check its access permissions and service terms."),
        "dependency_incompatible": ("시세 라이브러리 버전이 호환되지 않습니다. 앱의 의존성을 업데이트한 뒤 다시 조회하세요.",
                                    "The quote-library version is incompatible. Update the app dependencies, then refresh."),
    }
    if reason in provider_reasons:
        return _text(ctx, *provider_reasons[reason])
    if reason in ("connection_not_configured", "missing_credentials", "KISUnavailable", "MISSING_CREDENTIALS", "NOT_CONFIGURED"):
        return _text(ctx, "KIS 연결 설정을 확인하세요. API 키와 시크릿이 필요합니다.",
                     "Check KIS connection settings. An API key and secret are required.")
    if reason == "dependency_missing":
        return _text(ctx, "시세 조회에 필요한 패키지가 설치되지 않았습니다. 앱의 의존성을 업데이트한 뒤 다시 조회하세요.",
                     "A quote dependency is missing. Update the app dependencies, then refresh.")
    if reason == "invalid_response":
        return _text(ctx, "공급처 응답의 종목·단위·값을 검증하지 못했습니다. 값을 표시하지 않고 다시 조회할 수 있도록 유지했습니다.",
                     "The provider response could not be validated for this instrument, unit or value. Refresh to try again.")
    if row.get("status") == "NOT_LOADED":
        return _text(ctx, "새로고침을 누르면 등록된 공급처에 조회합니다.",
                     "Refresh to query the configured data providers.")
    if row.get("status") == "UNAVAILABLE":
        return _text(ctx, "공급처에서 사용할 수 있는 값을 받지 못했습니다. 연결 설정과 제공 범위를 확인한 뒤 다시 조회하세요.",
                     "No usable value was received. Check connectivity and provider coverage, then refresh.")
    if row.get("quote_time_kind") == "trade":
        if row.get("status") == "STALE":
            return _text(ctx, "실시간 체결 수신이 지연되거나 종료되었습니다. 마지막 체결값과 시각을 표시합니다. 별점은 마지막 산정값이며 현재 재계산되지 않습니다.",
                         "Trade reception is stale or stopped. The last trade, timestamp and calculated rating remain visible; the rating is paused.")
        return _text(ctx, "KIS에서 받은 실시간 체결입니다. 체결 시각과 앱의 수신 시각을 구분해 표시합니다.",
                     "A live trade received from KIS. The exchange trade time and app receipt time are shown separately.")
    if row.get("status") == "STALE":
        # Owner, 2026-11-04: no observation-date row; a stale value names its date here instead.
        observed = _date(row.get("observation_date"), ctx) if row.get("observation_date") else "—"
        return _text(ctx, f"마지막 일별 관측({observed})이 오래되었습니다. 표시된 값은 최신이 아닙니다.",
                     f"The last daily observation ({observed}) is old. The value shown is not current.")
    if row.get("kind") == "domestic_stock":
        return _text(ctx, "조회 시점에 받은 시세입니다. 수신 시각은 시장 체결 시각을 뜻하지 않습니다. 실시간 체결은 차트에서 별도로 연결합니다.",
                     "This is a quote snapshot. Receipt time is not the exchange trade time. Connect trade streaming separately in the chart.")
    return _text(ctx, "공급처의 일별 관측입니다. 실시간 체결 자료와 갱신 주기가 다릅니다.",
                 "This is a daily provider observation, with a different update schedule from live trades.")


def _split_number(text):
    """'1,387.50 KRW/USD' -> ('1,387.50', 'KRW/USD', True); '+1.45%' -> ('+1.45', '%', False);
    '—' -> ('—', '', False). The flag says whether the text had a space before its unit."""
    match = _NUMBER_UNIT.fullmatch(str(text).strip())
    return (match.group(1), match.group(3) or "", bool(match.group(2))) if match else (str(text), "", False)


class _CellDelegate(QStyledItemDelegate):
    """Draws watchlist cells at the header's inset (owner issue 05).

    Numeric columns put the number's last digit on one edge and the unit in a slot after it, so
    digits line up down the column whatever the unit (pt, %, KRW, KRW/USD). The item text, tooltip
    and accessible text are unchanged; only where the text is drawn changes.
    """

    def __init__(self, panel):
        super().__init__(panel.table)
        self.panel = panel
        self.unit_widths = {}

    @staticmethod
    def unit_font(font):
        return scaled_font(font, font.pixelSize() if font.pixelSize() > 0 else BODY_PX, 400)

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = opt.text
        opt.text = ""
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        if not text:
            return
        rect = option.rect.adjusted(CELL_PADDING, 0, -CELL_PADDING, 0)
        brush = index.data(Qt.ItemDataRole.ForegroundRole)
        color = brush.color() if isinstance(brush, QBrush) else opt.palette.color(QPalette.ColorRole.Text)
        painter.save()
        painter.setFont(opt.font)
        painter.setPen(color)
        column = index.column()
        if column in NUMERIC_COLUMNS:
            from .font_policy import number_font
            opt.font = number_font(opt.font)  # owner UI-D5: figures keep the number face
            painter.setFont(opt.font)
            number, unit, spaced = _split_number(text)
            slot = self.unit_widths.get(column, 0)
            right = rect.right() - (slot + UNIT_GAP if slot else 0)
            box = QRect(rect.left(), rect.top(), max(0, right - rect.left() + 1), rect.height())
            number = QFontMetrics(opt.font).elidedText(number, Qt.TextElideMode.ElideLeft, box.width())
            painter.drawText(box, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)
            if unit and slot:
                painter.setFont(self.unit_font(opt.font))
                if column != 2:  # a change keeps its rise/fall colour on its unit too
                    painter.setPen(QColor(self.panel.colors.muted))
                # '+1.45%', '21.35M' and '1,155T KRW' keep their unit against the digits; '4.31 %' its space.
                start = right + (UNIT_GAP if spaced else 1)
                painter.drawText(QRect(start, rect.top(), slot + UNIT_GAP, rect.height()),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, unit)
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        painter.restore()


class _WatchlistTable(QTableWidget):
    detail_activated = pyqtSignal(int)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.currentRow() >= 0:
            self.detail_activated.emit(self.currentRow())
            event.accept()
            return
        super().keyPressEvent(event)


class _IdentityDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Keep the item's name for accessibility and legacy consumers, while
        # the ticker/name widget owns visible text. Otherwise both are drawn.
        option.text = ""


class _CompanyName(QLabel):
    """One crisp text line, with the full name available to assistive tools."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("watchlistCompany")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setAccessibleName(text)
        self.setToolTip(text)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        painter.end()


class _HeaderHelpButton(QPushButton):
    def focusInEvent(self, event):
        self.parentWidget().parentWidget().ensure_score_visible()
        super().focusInEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            event.accept()
            return
        super().keyPressEvent(event)


class _WatchlistHeader(QHeaderView):
    """An actual focusable help button travels with the Q-SCORE section."""
    @property
    def score_column(self):
        return self.table.columnCount() - 1

    def __init__(self, table):
        super().__init__(Qt.Orientation.Horizontal, table)
        self.table = table
        self.colors = LIGHT
        self.help_button = _HeaderHelpButton("?", self.viewport())
        self.help_button.setObjectName("qScoreHeaderHelp")
        self.help_button.setFixedSize(22, 22)
        self.help_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedHeight(38)
        self.sectionResized.connect(self._section_resized)
        self.sectionMoved.connect(self._position_help)
        self.geometriesChanged.connect(self._position_help)
        table.horizontalScrollBar().valueChanged.connect(self._position_help)

    def _section_resized(self, logical, previous, size):
        if logical == self.score_column and size < 128:
            self.resizeSection(logical, 128)
        self._position_help()

    def title_font(self):
        """The section header font (12px / 600), shared with the other header labels."""
        return scaled_font(self.font(), 12, 600)

    def _group_geometry(self):
        # Left-aligned at the cell inset, over the score values; it used to be centred in the wide
        # last column, to the right of every value (owner issue 05).
        title_width = QFontMetrics(self.title_font()).horizontalAdvance("Q-SCORE") + 1
        left = self.sectionViewportPosition(self.score_column) + CELL_PADDING
        return left, title_width

    def _position_help(self, *args):
        if not hasattr(self, "help_button"):
            return
        if self.count() <= self.score_column:
            self.help_button.hide()
            return
        self.help_button.setVisible(not self.isSectionHidden(self.score_column))
        left, title_width = self._group_geometry()
        self.help_button.move(left + title_width + 6, (self.viewport().height() - self.help_button.height()) // 2)
        self.help_button.raise_()

    def ensure_score_visible(self):
        # A keyboard focus on the clipped button must also reveal its section.
        left = self.sectionViewportPosition(self.score_column)
        right = left + self.sectionSize(self.score_column)
        bar = self.table.horizontalScrollBar()
        if left < 0:
            bar.setValue(bar.value() + left)
        elif right > self.viewport().width():
            bar.setValue(bar.value() + right - self.viewport().width())
        self._position_help()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_help()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._position_help()
            self.viewport().update()

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self._position_help()

    def paintSection(self, painter, rect, logical_index):
        # Every title is drawn at the same inset as its cells (`_CellDelegate`): a number column and its
        # title share a right edge, text columns a left edge, and the details title sits over its buttons.
        painter.save()
        painter.setClipRect(rect)
        painter.fillRect(rect, QColor(self.colors.surface_2))
        painter.setPen(QColor(self.colors.muted))
        painter.setFont(self.title_font())
        if logical_index == self.score_column:
            left, title_width = self._group_geometry()
            painter.drawText(QRect(left, rect.y(), title_width, rect.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Q-SCORE")
        else:
            text = str(self.model().headerData(logical_index, Qt.Orientation.Horizontal) or "")
            inner = rect.adjusted(CELL_PADDING, 0, -CELL_PADDING, 0)
            side = (Qt.AlignmentFlag.AlignRight if logical_index in NUMERIC_COLUMNS else
                    Qt.AlignmentFlag.AlignHCenter if logical_index == DETAIL_COLUMN else Qt.AlignmentFlag.AlignLeft)
            text = QFontMetrics(self.title_font()).elidedText(text, Qt.TextElideMode.ElideRight, inner.width())
            painter.drawText(inner, side | Qt.AlignmentFlag.AlignVCenter, text)
        painter.restore()


class MarketDetailDialog(QDialog):
    chart_requested = pyqtSignal(str)

    def __init__(self, row, *, locale=None, palette=LIGHT, parent=None):
        super().__init__(parent)
        self.ctx = locale or LocaleContext("ko_KR")
        self.colors = palette
        self.row = deepcopy(row)
        self.setMinimumWidth(420)
        self.resize(560, 660)
        outer = QVBoxLayout(self)
        outer.setSpacing(16)
        outer.setContentsMargins(24, 24, 24, 24)
        self.title = _label()
        self.title.setObjectName("watchlistDetailTitle")
        outer.addWidget(self.title)
        self.price = _label()
        self.price.setObjectName("watchlistDetailPrice")
        outer.addWidget(self.price)
        self.notice = _label()
        outer.addWidget(self.notice)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        self.form = QFormLayout(body)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.setVerticalSpacing(12)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        self.rights = _label()
        outer.addWidget(self.rights)
        actions = QHBoxLayout()
        self.chart_button = QPushButton()
        self.chart_button.setProperty("primary", True)
        self.chart_button.clicked.connect(self.open_chart)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.chart_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        outer.addLayout(actions)
        self.set_theme(palette)
        self.set_locale(self.ctx)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.setWindowTitle(_text(ctx, "시장 상세보기", "Market details"))
        self.title.setText(_name(self.row, ctx) + " · " + str(self.row.get("symbol", "—")))
        self.price.setText(_price(self.row, ctx) + "   " + _change(self.row, ctx))
        self.notice.setText(_reason(self.row, ctx))
        while self.form.rowCount():
            self.form.removeRow(0)
        row = self.row
        unknown = _text(ctx, "확인 안 됨", "Unconfirmed")
        cap_verified = _cap_value(row) is not None
        pairs = [
            (("상태", "Status"), _status(row, ctx)),
            (("Q-SCORE", "Q-SCORE"), _score_text(row.get("q_score"), ctx)),
            (("점수 기준 시각", "Score data as of"), _score_as_of(row.get("q_score"), ctx)),
            (("단위", "Unit"), str(row.get("unit") or "—")),
            (("체결 시각", "Trade time"), _timestamp(row.get("market_time"), ctx)),
            (("수신 시각", "Received at"), _timestamp(row.get("received_at"), ctx)),
            (("조회 시각", "Queried at"), _timestamp(row.get("loaded_at"), ctx)),
            (("거래량", "Volume"), _number(row.get("volume"), ctx, 0)),
            (("시가", "Open"), _number(row.get("open"), ctx)),
            (("고가", "High"), _number(row.get("high"), ctx)),
            (("저가", "Low"), _number(row.get("low"), ctx)),
            (("시가총액", "Market cap"), _number(row.get("market_cap"), ctx, 0) + " KRW" if cap_verified else unknown),
            (("시가총액 산출 기준", "Market cap basis"), _text(ctx, "가격 × 상장 주식 수", "Price × listed shares")
             if cap_verified and row.get("market_cap_basis") == "price_x_listed_shares" else unknown),
            (("시가총액 기준 시각", "Market cap data as of"), _timestamp(row.get("market_cap_as_of"), ctx)),
            (("상장 주식 수", "Listed shares"), _number(row.get("listed_shares"), ctx, 0)),
            (("PER · 공급처 제공값", "PER · provider value"), _number(row.get("per"), ctx)),
            (("EPS · 공급처 제공값", "EPS · provider value"), _metric(row.get("eps"), ctx)),
            (("업종", "Sector"), _sector(row, ctx)),
            (("재무 항목 수신 시각", "Fundamentals received at"), _timestamp(row.get("fundamentals_received_at"), ctx)),
            (("재무 항목 기준일", "Financial reference date"), _date(row.get("fundamentals_as_of"), ctx) if row.get("fundamentals_as_of")
             else _text(ctx, "공급처 미제공", "Not supplied by provider")),
        ]
        if ctx.language != "ko" and row.get("sector") and str(row["sector"]) not in _SECTORS_EN:
            pairs.append((("공급처 업종 원문", "Provider sector text"), str(row["sector"])))
        for labels, value in pairs:
            self.form.addRow(_label(_text(ctx, *labels)), _label(value))
        if row.get("kind") == "domestic_stock":
            self.rights.setText(_text(ctx,
                "시가총액의 계산 근거와 기준 시각을 확인하세요. PER·EPS의 회계 기준과 기준일, EPS 단위·희석 여부는 확인되지 않았습니다. 자료 이용 조건은 공급처별 확인이 필요합니다.",
                "Review the market-cap calculation basis and timestamp. PER/EPS accounting basis and date, and EPS unit/dilution basis, are unconfirmed. Data-use rights require provider-specific review."))
        else:
            self.rights.setText(_text(ctx, "자료 이용 조건은 공급처별 확인이 필요합니다. 확인되지 않은 값은 —로 표시합니다.",
                                     "Data-use rights require provider-specific review. Unconfirmed values are shown as —."))
        self.chart_button.setText(_text(ctx, "종목 차트 열기", "Open instrument chart"))
        self.chart_button.setVisible(_can_chart(row))
        self.close_button.setText(_text(ctx, "닫기", "Close"))

    def set_theme(self, palette):
        self.colors = palette
        p = palette
        self.setStyleSheet(f"""
            QDialog, QWidget {{ background: {p.surface}; color: {p.text}; }}
            QLabel {{ background: transparent; }}
            QLabel#watchlistDetailTitle {{ font-size: 20px; font-weight: 600; }}
            QLabel#watchlistDetailPrice {{ font-size: 24px; font-weight: 600; }}
            QPushButton {{ padding: 9px 14px; border: 1px solid {p.border}; border-radius: 8px; background: {p.surface}; }}
            QPushButton:hover {{ background: {p.accent_soft}; }}
            QPushButton:focus {{ border: 2px solid {p.accent}; }}
            QPushButton[primary='true'] {{ background: {p.accent}; color: {p.on_accent}; }}
        """)

    def open_chart(self):
        if _can_chart(self.row):
            self.chart_requested.emit(str(self.row["symbol"]))
            self.accept()


class ScoreHelpDialog(QDialog):
    def __init__(self, *, locale, palette, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(380)
        self.resize(560, 440)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)
        self.heading = _label("Q-SCORE")
        self.heading.setObjectName("scoreHelpHeading")
        self.eyebrow = _label("QUANTGEN")
        self.eyebrow.setObjectName("scoreHelpBrand")
        self.body = _label()
        self.body.setObjectName("scoreHelpBody")
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        outer.addWidget(self.eyebrow)
        outer.addWidget(self.heading)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 12, 0)
        content_layout.addWidget(self.body)
        content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        outer.addWidget(self.close_button)
        self.set_theme(palette)
        self.set_locale(locale)

    def set_locale(self, ctx):
        self.setWindowTitle(_text(ctx, "Q-SCORE 소개", "About Q-SCORE"))
        # The core owns the product explanation, keeping both views in sync.
        from core.research.qscore import q_score_help
        self.body.setText(q_score_help(ctx.language))
        self.close_button.setText(_text(ctx, "닫기", "Close"))

    def set_theme(self, p):
        self.setStyleSheet(f"""
            QWidget {{ background: {p.surface}; color: {p.text}; }}
            QLabel {{ color: {p.text}; background: transparent; }}
            QLabel#scoreHelpBrand {{ color: {p.accent}; font-size: 12px; font-weight: 600; letter-spacing: 1px; }}
            QLabel#scoreHelpHeading {{ font-size: 25px; font-weight: 600; }}
            QLabel#scoreHelpBody {{ font-size: 14px; }}
            QPushButton {{ color: {p.text}; background: {p.surface}; border: 1px solid {p.border}; border-radius: 8px; padding: 9px 14px; }}
            QPushButton:hover {{ background: {p.accent_soft}; }}
            QPushButton:focus {{ border: 2px solid {p.accent}; }}
        """)


class WatchlistPanel(QWidget):
    refresh_requested = pyqtSignal()
    chart_requested = pyqtSignal(str)
    detail_requested = pyqtSignal(object)
    live_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, *, locale=None, parent=None):
        super().__init__(parent)
        self.setObjectName("marketWatchlistPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.ctx = locale or LocaleContext("ko_KR")
        self.colors = LIGHT
        self.rows = []
        self.detail_dialog = None
        self.score_help_dialog = None
        self.busy = False
        self.live_state = "idle"
        self.live_detail = ""
        self._rendering = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)
        header = QHBoxLayout()
        self.title = _label()
        self.title.setObjectName("watchlistTitle")
        header.addWidget(self.title, 1)
        self.refresh = QPushButton()
        self.refresh.clicked.connect(self.refresh_requested.emit)
        header.addWidget(self.refresh)
        outer.addLayout(header)
        self.caption = _label()
        self.caption.setObjectName("watchlistCaption")
        outer.addWidget(self.caption)
        live_controls = QHBoxLayout()
        self.live_button = QPushButton()
        self.stop_button = QPushButton()
        self.live_status = _label()
        self.live_button.clicked.connect(self.live_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        live_controls.addWidget(self.live_button)
        live_controls.addWidget(self.stop_button)
        live_controls.addWidget(self.live_status, 1)
        outer.addLayout(live_controls)
        self.table = _WatchlistTable(0, 10)
        self.detail_column, self.score_column = DETAIL_COLUMN, SCORE_COLUMN
        self.table.setHorizontalHeader(_WatchlistHeader(self.table))
        self.score_help = self.table.horizontalHeader().help_button
        self.score_help.clicked.connect(self.open_score_help)
        self.table.setItemDelegateForColumn(0, _IdentityDelegate(self.table))
        self.cell_delegate = _CellDelegate(self)
        for column in (*NUMERIC_COLUMNS, 7, SCORE_COLUMN):
            self.table.setItemDelegateForColumn(column, self.cell_delegate)
        self.table.setAccessibleName("Market watchlist")
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(64)
        for column, width in enumerate((260, 134, 78, 72, 100, 66, 68, 79, 68, 136)):
            self.table.setColumnWidth(column, width)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalScrollBar().rangeChanged.connect(self._sync_table_height)
        self.table.cellDoubleClicked.connect(lambda row, column: self.open_detail(row))
        self.table.detail_activated.connect(self.open_detail)
        outer.addWidget(self.table)
        QWidget.setTabOrder(self.stop_button, self.score_help)
        QWidget.setTabOrder(self.score_help, self.table)
        self.set_locale(self.ctx)
        self.set_theme(LIGHT)

    def set_rows(self, rows):
        self.rows = deepcopy(list(rows))
        self._render_rows()
        if self.detail_dialog is not None:
            for row in self.rows:
                self._sync_detail(row)

    def update_score(self, symbol, score):
        """Apply an engine result; scoring and provider I/O belong to the controller."""
        for index, row in enumerate(self.rows):
            if row.get("symbol") == symbol:
                row["q_score"] = deepcopy(score) if isinstance(score, dict) else None
                self._update_row_items(index)
                self._sync_detail(row)
                return True
        return False

    def update_quote(self, symbol, price, change_pct, received_at, **optional):
        """Update an existing row without fetching or treating receipt time as trade time."""
        value = _finite(price)
        if value is None or value <= 0:
            return False
        if optional.get("status") == "STREAMING" and _timestamp(optional.get("market_time"), self.ctx) == "—":
            return False
        for index, row in enumerate(self.rows):
            if row.get("symbol") == symbol:
                row.update(value=value, change=_finite(change_pct), received_at=received_at)
                for field in ("volume", "open", "high", "low", "absolute_change"):
                    if field in optional:
                        row[field] = _finite(optional[field])
                if optional.get("status") in ("STREAMING", "STALE"):
                    row.update(status=optional["status"], quote_time_kind="trade", error_code=None, reason_code=None)
                    row["feed_state"] = "streaming" if optional["status"] == "STREAMING" else "stale"
                if "market_time" in optional:
                    row["market_time"] = optional["market_time"]
                if optional.get("source") in ("KIS", "KIS WebSocket"):
                    row["stream_source"] = optional["source"]
                if optional.get("status") == "STREAMING":
                    _refresh_cap_from_tick(row, value, optional.get("market_time"))
                self._update_row_items(index)
                self._sync_detail(row)
                return True
        return False

    def _sync_detail(self, row):
        if self.detail_dialog is not None and self.detail_dialog.row.get("symbol") == row.get("symbol"):
            self.detail_dialog.row = deepcopy(row)
            self.detail_dialog.set_locale(self.ctx)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.title.setText(_text(ctx, "주요 시장 · 국내 주요 종목", "Markets and Korean stocks"))
        self.caption.setText(_text(ctx,
            "시장지표는 일별 관측, 국내 종목은 조회 시세입니다. 가격에 마우스를 올리거나 상세를 열면 출처·시각·상태를 확인할 수 있습니다.",
            "Indicators are daily observations; stocks start with quote snapshots. Hover a price or open Details for source, timing and status."))
        self.refresh.setText(_text(ctx, "조회 중…", "Loading…") if self.busy else _text(ctx, "새로고침", "Refresh"))
        self.score_help.setAccessibleName(_text(ctx, "Q-SCORE 소개 열기", "About Q-SCORE"))
        self.score_help.setToolTip(_score_help_summary(ctx))
        self.live_button.setText(_text(ctx, "실시간 목록 연결", "Connect live watchlist"))
        self.stop_button.setText(_text(ctx, "연결 중지", "Stop"))
        self.set_live_state(self.live_state, self.live_detail)
        self.table.setAccessibleName(_text(ctx, "주요 시장과 국내 종목 목록", "Markets and Korean stocks watchlist"))
        self.table.setHorizontalHeaderLabels([_text(ctx, ko, en) for ko, en in (
            ("종목 · 지표", "Instrument"), ("현재가", "Price"), ("변동", "Change"),
            ("거래량", "Volume"), ("시가총액", "Market cap"), ("PER", "PER"), ("EPS", "EPS"),
            ("업종", "Sector"), ("상세", "Details"), ("Q-SCORE", "Q-SCORE"))])
        for column in range(self.table.columnCount()):
            alignment = Qt.AlignmentFlag.AlignRight if column in (1, 2, 3, 4, 5, 6) else Qt.AlignmentFlag.AlignLeft
            self.table.horizontalHeaderItem(column).setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(self.score_column).setToolTip(self.score_help.toolTip())
        self.table.horizontalHeaderItem(4).setToolTip(_text(ctx, "KRW · 가격 × 상장 주식 수로 산출, 기준 시각은 상세에서 확인", "KRW · calculated from price × listed shares; open Details for timing"))
        for column in (5, 6):
            self.table.horizontalHeaderItem(column).setToolTip(_text(ctx, "KIS 제공값 · 회계 기준·기준일 및 EPS 단위는 미확인", "KIS-provided value · accounting basis/date and EPS unit unconfirmed"))
        self._render_rows()
        if self.detail_dialog is not None:
            self.detail_dialog.set_locale(ctx)
        if self.score_help_dialog is not None:
            self.score_help_dialog.set_locale(ctx)

    def set_theme(self, palette):
        self.colors = palette
        p = palette
        self.setStyleSheet(f"""
            QWidget#marketWatchlistPanel {{ background: {p.bg}; color: {p.text}; }}
            QLabel {{ color: {p.text}; }}
            QLabel#watchlistTitle {{ font-size: 18px; font-weight: 600; color: {p.text}; }}
            QLabel#watchlistCaption {{ font-size: 14px; font-weight: 500; color: {p.text}; }}
            QTableWidget {{ background: {p.surface}; alternate-background-color: {p.surface_2}; border: 1px solid {p.border}; border-radius: 10px; selection-background-color: {p.accent_soft}; selection-color: {p.text}; color: {p.text}; }}
            QTableWidget::item {{ padding: 1px 8px; border-bottom: 1px solid {p.border}; }}
            QTableWidget::item:hover {{ background: {p.surface_2}; }}
            QTableWidget::item:selected {{ background: {p.accent_soft}; color: {p.text}; }}
            QHeaderView::section {{ background: {p.surface_2}; color: {p.muted}; padding: 6px 8px; border: 0; font-size: 12px; font-weight: 600; }}
            QWidget#watchlistIdentity {{ background: transparent; }}
            QWidget#watchlistIdentity QLabel {{ background: transparent; color: {p.text}; font-size: {BODY_PX}px; font-weight: 500; }}
            QWidget#watchlistIdentity QLabel#watchlistTicker {{ background: {p.surface_2}; color: {p.text}; border-radius: 7px; padding: 3px 4px; font-size: 12px; font-weight: 600; }}
            QPushButton {{ background: {p.surface}; color: {p.text}; border: 1px solid {p.border}; border-radius: 8px; padding: 7px 10px; }}
            QPushButton:hover {{ background: {p.accent_soft}; }}
            QPushButton:focus {{ border: 2px solid {p.accent}; }}
            QPushButton[watchlistDetail='true'] {{ margin: 6px 1px; padding: 0 3px; border-radius: 6px; }}
            QPushButton#qScoreHeaderHelp {{ color: {p.muted}; background: {p.surface}; border: 1px solid {p.border}; border-radius: 11px; padding: 0; margin: 0; font-size: 12px; font-weight: 600; }}
            QPushButton#qScoreHeaderHelp:hover {{ color: {p.accent}; background: {p.accent_soft}; }}
            QPushButton#qScoreHeaderHelp:focus {{ color: {p.accent}; border: 2px solid {p.accent}; }}
        """)
        self.table.horizontalHeader().colors = palette
        self.table.horizontalHeader().viewport().update()
        self._render_rows()
        if self.detail_dialog is not None:
            self.detail_dialog.set_theme(palette)
        if self.score_help_dialog is not None:
            self.score_help_dialog.set_theme(palette)

    def set_busy(self, busy):
        self.busy = bool(busy)
        self.refresh.setEnabled(not self.busy)
        self.refresh.setText(_text(self.ctx, "조회 중…", "Loading…") if self.busy else _text(self.ctx, "새로고침", "Refresh"))

    def set_live_state(self, status, detail=""):
        self.live_state = status if status in _LIVE_STATUS else "error"
        self.live_detail = detail
        self.live_status.setText(_text(self.ctx, *_LIVE_STATUS[self.live_state]))
        known_reason = detail if detail in ("connection_not_configured", "dependency_missing", "invalid_response", "provider_unavailable") else None
        self.live_status.setToolTip(_reason({"reason_code": known_reason, "status": "UNAVAILABLE"}, self.ctx) if self.live_state == "error" else self.live_status.text())
        active = self.live_state in ("loading", "connecting", "subscribed", "streaming")
        self.live_button.setEnabled(not active)
        self.stop_button.setEnabled(active or self.live_state == "stale")
        if self.live_state in ("stale", "stopped", "error"):
            for index, row in enumerate(self.rows):
                if row.get("status") == "STREAMING":
                    row["status"] = "STALE"
                    row["feed_state"] = self.live_state
                    score = row.get("q_score")
                    if isinstance(score, dict):
                        row["q_score"] = {**score, "live": False, "feed_state": self.live_state}
                    self._update_row_items(index)
                    self._sync_detail(row)

    def _render_rows(self):
        if not hasattr(self, "table"):
            return
        selected = self.table.currentRow()
        self.table.setRowCount(len(self.rows))
        self._rendering = True
        for index, row in enumerate(self.rows):
            name = _name(row, self.ctx)
            self._update_row_items(index)
            for column in (0, self.detail_column):
                previous = self.table.cellWidget(index, column)
                if previous is not None:
                    previous.hide()
            identity = QWidget()
            identity.setObjectName("watchlistIdentity")
            identity.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            identity_layout = QHBoxLayout(identity)
            identity_layout.setContentsMargins(10, 1, 10, 1)
            identity_layout.setSpacing(8)
            symbol = str(row.get("symbol") or "—")
            mark = CompanyMark(symbol, name, palette=self.colors, size=28)
            identity_layout.addWidget(mark)
            badge = _label(_BADGES.get(symbol, symbol))
            badge.setObjectName("watchlistTicker")
            badge.setFixedWidth(62)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setWordWrap(False)
            identity_layout.addWidget(badge)
            company = _CompanyName(name)
            identity_layout.addWidget(company, 1)
            identity.setToolTip(f"{name} · {symbol}")
            self.table.setCellWidget(index, 0, identity)
            button = QPushButton(_text(self.ctx, "상세", "Details"))
            button.setProperty("watchlistDetail", True)
            button.setAccessibleName(_text(self.ctx, name + " 상세보기", "Details for " + name))
            button.clicked.connect(lambda checked=False, row_index=index: self.open_detail(row_index))
            self.table.setCellWidget(index, self.detail_column, button)
            self.table.setRowHeight(index, ROW_HEIGHT)
        self._rendering = False
        if self.rows:
            self.table.setCurrentCell(min(max(selected, 0), len(self.rows) - 1), 0)
        self._fit_columns()
        self._sync_table_height()

    def _fit_columns(self):
        """Unit slots and widths from the shown text (owner issue 05).

        A column grows to fit its widest number, unit and title instead of eliding them
        ('1,387.50 KRW/USD' was cut to 'KRW…', volumes to '987.6…'). It never shrinks below
        the default widths, and a width the user dragged wider stays.
        """
        if not hasattr(self, "cell_delegate"):
            return
        title = QFontMetrics(self.table.horizontalHeader().title_font())
        for column in (*NUMERIC_COLUMNS, 7):
            numbers, units = [0], [0]
            for row in range(self.table.rowCount()):
                item = self.table.item(row, column)
                if item is None or not item.text():
                    continue
                number, unit, _ = _split_number(item.text()) if column in NUMERIC_COLUMNS else (item.text(), "", False)
                numbers.append(QFontMetrics(item.font()).horizontalAdvance(number))
                if unit and column in UNIT_COLUMNS:
                    units.append(QFontMetrics(_CellDelegate.unit_font(item.font())).horizontalAdvance(unit) + 1)
            slot = max(units)
            self.cell_delegate.unit_widths[column] = slot
            label = self.table.horizontalHeaderItem(column)
            needed = max(max(numbers) + (slot + UNIT_GAP if slot else 0),
                         title.horizontalAdvance(label.text() if label else "")) + 2 * CELL_PADDING + 1
            if self.table.columnWidth(column) < needed:
                self.table.setColumnWidth(column, needed)
        self.table.viewport().update()

    def _sync_table_height(self, *args):
        # Outer-page vertical scrolling; reserve scrollbar space only when used.
        scrollbar = self.table.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent) if self.table.horizontalScrollBar().maximum() else 0
        height = self.table.horizontalHeader().height() + len(self.rows) * ROW_HEIGHT + 2 * self.table.frameWidth() + scrollbar
        if self.table.height() != height:
            self.table.setFixedHeight(height)

    def _update_row_items(self, index):
        row = self.rows[index]
        cap = _cap_value(row)
        contents = [_name(row, self.ctx), _price(row, self.ctx), _change(row, self.ctx),
                    _compact(row.get("volume"), self.ctx), _compact(cap, self.ctx) + " KRW" if cap is not None else "—",
                    _number(row.get("per"), self.ctx), _metric(row.get("eps"), self.ctx), _sector(row, self.ctx, compact=True),
                    "", _score_text(row.get("q_score"), self.ctx)]
        for column, value in enumerate(contents):
            item = self.table.item(index, column)
            if item is None:
                item = QTableWidgetItem()
                self.table.setItem(index, column, item)
            item.setText(value)
            # One body size for every cell (owner issue 05); the price leads by weight, not by size.
            font = scaled_font(self.table.font(), BODY_PX, 600 if column == 1 else 500 if column in (0, 2) else 400)
            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, row.get("symbol"))
            tooltip = f"{value} · {row.get('symbol', '')}" if column == 0 else value
            if column == 1:
                tooltip = _price_tooltip(row, self.ctx)
            elif column == 3:
                tooltip = _number(row.get("volume"), self.ctx, 0)
            elif column in (4, 5, 6, 7):
                tooltip = _fundamental_tooltip(row, self.ctx, ("market_cap", "per", "eps", "sector")[column - 4])
            elif column == self.score_column:
                tooltip = _score_tooltip(row.get("q_score"), self.ctx)
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, tooltip)
            item.setTextAlignment((Qt.AlignmentFlag.AlignRight if column in (1, 2, 3, 4, 5, 6) else Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter)
            color = self.colors.text
            if column == 2 and _finite(row.get("change")) is not None:
                # Korean market convention (owner 2026-11-04): rise red, fall blue, AA on both themes.
                color = tone_colors(self.colors)[tone_for(_finite(row["change"]))]
            if column == 1 and row.get("status") in ("STALE", "UNAVAILABLE"):
                color = self.colors.warning
            if column == self.score_column:
                color = self.colors.accent if "★" in value else self.colors.muted
            item.setForeground(QBrush(QColor(color)))
        if not self._rendering:
            self._fit_columns()  # a live quote can widen a column; the unit slots follow it

    def open_score_help(self):
        if self.score_help_dialog is None:
            self.score_help_dialog = ScoreHelpDialog(locale=self.ctx, palette=self.colors, parent=self)
        self.score_help_dialog.show()
        self.score_help_dialog.raise_()
        return self.score_help_dialog

    def open_detail(self, row_index):
        if not 0 <= row_index < len(self.rows):
            return None
        if self.detail_dialog is not None:
            self.detail_dialog.close()
            self.detail_dialog.deleteLater()
        row = self.rows[row_index]
        self.detail_requested.emit(deepcopy(row))
        self.detail_dialog = MarketDetailDialog(row, locale=self.ctx, palette=self.colors, parent=self)
        self.detail_dialog.chart_requested.connect(self.chart_requested.emit)
        self.detail_dialog.show()
        self.detail_dialog.raise_()
        return self.detail_dialog
