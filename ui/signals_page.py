"""Signals — the technical read on one instrument, and the backtest that
keeps it honest.

Top half: the composite signal with its components drawn as signed bars
(bullish fills right in green, bearish fills left in red — the sign is
spatial, not just chromatic). Bottom half: the selected rule strategy run
against the same history with costs, next to buy-and-hold, because a signal
whose strategy loses to its own underlying should have to say so on the same
screen that painted it green.

The data source is chosen by the app (owner UI review, 2026-11-10): the
selector stays in the tree for tests but is hidden, and every load asks
`load_history(..., source="best")`. The provider that answered is shown as a
small chip under the summary.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

import flet as ft

from core.i18n import LocaleContext
from core.quant.backtest import STRATEGIES, run_backtest
from core.research.signals_analysis import PENDING_LABELS, trade_statistics, trade_statistics_labels
from core.quant.history import HistoryError, load_history
from core.quant.signals import SignalReport, compute_signals
from core.quant import insights
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.narrative_sections import korean, localized
from quantgen_desktop.model_narrative_language import signals_korean
from ui.build_widgets import provenance_chips, synthetic_banner
from ui.components import LocalText, card, chip, empty_state, notice, section, stat
import ui.qcharts as qcharts

# "best" is the app's own routing (keyless Yahoo before a synthetic fallback). The
# selector is hidden; the other keys stay valid so scripts and tests can still pick one.
_SOURCES = [("best", "Auto"), ("auto", "Auto (keyed providers only)"), ("fmp", "FMP"),
            ("kis", "KIS (KRX)"), ("synthetic", "Synthetic demo")]
SIGNALS_NOTICE = "Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book."
_STRAT_LABELS = {"ma_cross": "MA cross (fast/slow)",
                 "momentum": "Momentum (lookback)",
                 "rsi_revert": "RSI mean reversion"}
_KO = LocaleContext("ko_KR").text          # the reviewed Korean caption of a static English string

# Korean readings of the component reasons written by core.quant.signals. Display
# only: the English sentence stays the source; an unmatched reason shows as is.
_DIR = {"above": "위", "below": "아래"}
_REASONS_KO = (
    (r"Price is ([\d.]+)% (above|below) its 50-day average\.",
     lambda m: f"가격이 50일 이동평균보다 {m[1]}% {_DIR[m[2]]}에 있습니다."),
    (r"Price is ([\d.]+)% (above|below) its 200-day average — the long trend is (up|down)\.",
     lambda m: f"가격이 200일 이동평균보다 {m[1]}% {_DIR[m[2]]}에 있습니다. 장기 추세는 "
               f"{'상승' if m[3] == 'up' else '하락'}입니다."),
    (r"Price moved ([+-]?[\d.]+)% over the last 63 sessions\.",
     lambda m: f"최근 63거래일 동안 가격이 {m[1]}% 움직였습니다."),
    (r"RSI (\d+) is overbought — stretched to the upside\.",
     lambda m: f"RSI {m[1]}: 과매수 구간으로, 위쪽으로 과열되어 있습니다."),
    (r"RSI (\d+) is oversold — stretched to the downside\.",
     lambda m: f"RSI {m[1]}: 과매도 구간으로, 아래쪽으로 과하게 밀려 있습니다."),
    (r"RSI (\d+) is in the neutral band\.",
     lambda m: f"RSI {m[1]}: 중립 구간입니다."),
    (r"MACD line is (above|below) its signal line by ([\d.]+)\.",
     lambda m: f"MACD 선이 시그널 선보다 {m[2]}만큼 {_DIR[m[1]]}에 있습니다."),
    (r"20-day volatility is ([\d.]+)× its 100-day level — (compressed|elevated|normal)\.",
     lambda m: f"20일 변동성이 100일 변동성의 {m[1]}배로, "
               f"{ {'compressed': '평소보다 낮은', 'elevated': '평소보다 높은', 'normal': '평소 수준인'}[m[2]] } "
               f"상태입니다."),
)


def _reason_ko(reason: str) -> str:
    for pattern, render in _REASONS_KO:
        m = re.fullmatch(pattern, reason or "")
        if m:
            return render(m)
    return reason


def _signed_bar(score: float) -> ft.Control:
    """A bar centered at zero: [-100..0] fills leftward red, [0..100] rightward
    green. Both halves are 100 expand-units wide, so scale is identical."""
    pal = active()
    s = max(-100.0, min(100.0, score))
    left_fill = int(round(-s)) if s < 0 else 0
    right_fill = int(round(s)) if s > 0 else 0
    left = ft.Row([
        ft.Container(expand=100 - left_fill),
        ft.Container(expand=left_fill, bgcolor=pal.error,
                     border_radius=RADII["sm"]) if left_fill else ft.Container(),
    ], spacing=0, expand=True)
    right = ft.Row([
        ft.Container(expand=right_fill, bgcolor=pal.success,
                     border_radius=RADII["sm"]) if right_fill else ft.Container(),
        ft.Container(expand=100 - right_fill),
    ], spacing=0, expand=True)
    return ft.Container(
        ft.Row([left,
                ft.Container(width=2, bgcolor=pal.border),
                right], spacing=0),
        height=14, bgcolor=pal.surface_2, border=ft.Border.all(1, pal.border),
        border_radius=RADII["sm"], expand=True)


def _stance_token(score: float) -> str:
    return "success" if score > 15 else "error" if score < -15 else "muted"


def _signal_block(report: SignalReport) -> ft.Control:
    pal = active()
    stance_token = _stance_token(report.composite)
    rows: list[ft.Control] = [
        ft.Text("Indicator readings", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        LocalText("막대는 0을 기준으로 오른쪽(초록)이 상승 쪽, 왼쪽(빨강)이 하락 쪽 관측입니다. "
                  "오른쪽 숫자는 점수(−100~+100)와 종합 점수 안에서의 가중치입니다.",
                  "Bars start at zero: right (green) reads bullish, left (red) bearish. "
                  "The numbers are the score (−100 to +100) and its weight in the composite.",
                  size=12, color=pal.muted),
        ft.Row([
            ft.Text("Composite", size=13, color=pal.text, width=170,
                    weight=ft.FontWeight.W_600),
            _signed_bar(report.composite),
            ft.Text(f"{report.composite:+.0f}", size=13, width=44,
                    color=getattr(pal, stance_token), weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT),
            ft.Container(chip(report.stance, stance_token), width=120,
                         alignment=ft.Alignment.CENTER_LEFT),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Divider(color=pal.border, height=9)]
    for c in report.components:
        rows.append(ft.Column([
            ft.Row([
                ft.Text(c.label, size=12, color=pal.text, width=170,
                        max_lines=2, tooltip=c.value or c.label),
                _signed_bar(c.score),
                ft.Text(f"{c.score:+.0f}", size=12, width=44,
                        color=pal.success if c.score > 0 else
                        (pal.error if c.score < 0 else pal.muted),
                        weight=ft.FontWeight.W_600,
                        text_align=ft.TextAlign.RIGHT),
                ft.Text(f"{c.weight * 100:.0f}%", size=11, color=pal.muted,
                        width=120, text_align=ft.TextAlign.LEFT,
                        tooltip="Weight in the composite"),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Container(width=170),
                    LocalText(_reason_ko(c.reason), c.reason, size=12, color=pal.muted,
                              expand=True, max_lines=2)], spacing=8),
        ], spacing=2))
    return ft.Column(rows, spacing=8)


def _trade_statistics_block(bt):
    """Separate labels from values so locale switching preserves statistics."""
    pal = active()
    count_label, win_label, count_note = trade_statistics_labels(bt)
    rows = [
        (count_label, str(bt.n_trades)),
        ('Completed round trips', str(bt.completed_round_trips) if bt.completed_round_trips is not None else '—'),
        ('Final-close signal', PENDING_LABELS.get(bt.pending_last_signal, bt.pending_last_signal)),
        (win_label, f'{bt.win_rate * 100:.0f}%' if bt.win_rate is not None else '—'),
    ]
    return card(ft.Column(
        [ft.Text("Trade statistics", size=15, weight=ft.FontWeight.W_600, color=pal.text)]
        + [ft.Row([ft.Text(label, size=12, color=pal.muted, width=240),
                   ft.Text(value, size=13, color=pal.text, weight=ft.FontWeight.W_600)],
                  spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
           for label, value in rows]
        + [ft.Text(count_note, size=12, color=pal.muted)], spacing=8))


def _sign_token(x: float) -> str:
    """A return tile reads by its own sign: green only for a gain, red only for a loss."""
    return "success" if x > 0 else "error" if x < 0 else "text"


def _summary(report: SignalReport, bt, hist) -> ft.Control:
    """Verdict first: the composite in words, then whether the costed strategy beat buy-and-hold.

    Beating buy-and-hold is a comparison, not a gain (both can be losses), so its chip is neutral and
    the strategy-return tile takes the colour of its own sign. The period and the one-backtest caveat
    sit under the sentence (owner UI review, 2026-11-10)."""
    pal = active()
    token = _stance_token(report.composite)
    strat_en = _STRAT_LABELS[bt.strategy]
    beat = bt.beat_benchmark
    sentence = LocalText(
        f"종합 점수 {report.composite:+.0f}점(−100~+100)은 '{_KO(report.stance)}'입니다. 같은 기간 "
        f"{_KO(strat_en)} 전략은 거래비용을 빼고 {bt.total_return * 100:+.1f}%, 매수 후 보유는 "
        f"{bt.bench_return * 100:+.1f}%로, 전략이 매수 후 보유보다 {'나았습니다' if beat else '못했습니다'}.",
        f"The composite of {report.composite:+.0f} (−100 to +100) reads '{report.stance}'. Over the same "
        f"history the {strat_en} strategy returned {bt.total_return * 100:+.1f}% after costs against "
        f"{bt.bench_return * 100:+.1f}% for buy-and-hold: it {'beat' if beat else 'did not beat'} buy-and-hold.",
        size=13, color=pal.text)
    return card(ft.Column([
        ft.Row([
            LocalText(f"{report.symbol} 기술적 관측", f"{report.symbol} technical read",
                      size=16, weight=ft.FontWeight.W_600, color=pal.text),
            chip(report.stance, token),
            chip("beats buy & hold" if beat else "trails buy & hold", "muted"),
        ], spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        sentence,
        LocalText(f"기간: {hist.first_date} ~ {hist.last_date}. "
                  "한 구간의 과거 백테스트이며 통계 검정이나 표본 외 검증이 아닙니다.",
                  f"Period: {hist.first_date} to {hist.last_date}. "
                  "One historical backtest; not a statistical test or out-of-sample validation.",
                  size=12, color=pal.muted),
        ft.Row([
            stat("Strategy return", f"{bt.total_return * 100:+.1f}%",
                 token=_sign_token(bt.total_return)),
            stat("Buy & hold", f"{bt.bench_return * 100:+.1f}%"),
            stat("Sharpe", f"{bt.sharpe:.2f}"),
            stat("Max drawdown", f"{bt.max_drawdown * 100:.1f}%"),
            stat("Time in market", f"{bt.exposure * 100:.0f}%"),
            stat("Cost (bps)", f"{bt.cost_bps:g}"),
        ], spacing=8, wrap=True),
        provenance_chips([hist]),
    ], spacing=12))


def build_signals_page(page: ft.Page,
                       on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()

    symbol = ft.TextField(label="Symbol", hint_text="AAPL or 005930", width=160,
                          border_radius=RADII["md"], value="AAPL")
    source = ft.Dropdown(label="Data source", width=180, value="best", visible=False,
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    strategy = ft.Dropdown(label="Backtest strategy", width=250, value="ma_cross",
                           options=[ft.dropdown.Option(s, _STRAT_LABELS[s])
                                    for s in STRATEGIES])
    p_fast = ft.TextField(label="Fast/lookback", width=140, value="20",
                          border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT,
                          tooltip="ma_cross: fast SMA · momentum: lookback · "
                                  "rsi_revert: RSI period")
    p_slow = ft.TextField(label="Slow/exit", width=140, value="50",
                          border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT,
                          tooltip="ma_cross: slow SMA · rsi_revert: exit-above "
                                  "RSI level · momentum: unused")
    cost = ft.TextField(label="Cost (bps)", width=130, value="10",
                        border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _params(strat: str) -> dict:
        a = float(p_fast.value or "20")
        b = float(p_slow.value or "50")
        if strat == "ma_cross":
            return {"fast": int(a), "slow": int(b)}
        if strat == "momentum":
            return {"lookback": int(a)}
        return {"period": int(a), "buy_below": 30.0, "exit_above": b}

    def run(e=None) -> None:
        busy.visible = True
        result_host.controls = []
        page.update()

        def worker():
            try:
                strat = strategy.value or "ma_cross"
                hist = load_history(symbol.value, source=source.value or "best")
                report = compute_signals(hist)
                bt = run_backtest(hist, strategy=strat, params=_params(strat),
                                  cost_bps=float(cost.value or "10"))
            except (HistoryError, ValueError) as exc:
                result_host.controls = [notice(str(exc), "error",
                                               icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False
                page.update()
                return
            except Exception as exc:
                result_host.controls = [notice(f"{type(exc).__name__}: {exc}",
                                               "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False
                page.update()
                return

            blocks: list[ft.Control] = []
            banner = synthetic_banner([hist])
            if banner is not None:
                blocks.append(banner)
            blocks.append(_summary(report, bt, hist))
            blocks.append(card(qcharts.price_chart(hist)))
            blocks.append(card(_signal_block(report)))
            blocks.append(_trade_statistics_block(bt))
            blocks.append(card(qcharts.equity_chart(bt)))
            from .indicator_guide import IndicatorGuide
            blocks.append(card(IndicatorGuide(page, history=hist)))

            payload = {
                "symbol": report.symbol, "data_source": hist.source,
                "last_price": report.last_price,
                "composite": report.composite, "stance": report.stance,
                "components": [{"label": c.label, "score": c.score,
                                "weight": c.weight, "reason": c.reason}
                               for c in report.components],
                "backtest": {
                    "strategy": bt.strategy, "params": bt.params,
                    "total_return": bt.total_return,
                    "benchmark_return": bt.bench_return,
                    "ann_vol": bt.ann_vol, "sharpe": bt.sharpe,
                    "max_drawdown": bt.max_drawdown,
                    "benchmark_max_drawdown": bt.bench_max_drawdown,
                    "exposure": bt.exposure, "cost_bps": bt.cost_bps,
                    **trade_statistics(bt),
                },
            }
            narrative = (insights.narrate_signals(report) + " " +
                         insights.narrate_backtest(bt))
            blocks.append(analysis_panel(page, kind="signals_and_backtest",
                                         narrative=narrative,
                                         payload_fn=lambda p=payload: p,
                                         sections=localized(narrative, korean(signals_korean, report, bt))))
            result_host.controls = blocks
            busy.visible = False
            page.update()

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Read a chart, then make the read prove itself",
        "The composite signal and its components render above the backtest of "
        "the same idea on the same history, with costs.",
        icon=ft.Icons.CANDLESTICK_CHART_OUTLINED)]

    return ft.Column([
        section("Signals", subtitle="Technical composite with dissent shown, and a "
                                    "costed backtest against buy-and-hold."),
        notice(SIGNALS_NOTICE, "accent", icon=ft.Icons.LOCK_OUTLINE),
        ft.Row([symbol, source, strategy, p_fast, p_slow, cost,
                ft.Button("Analyze", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run),
                busy], spacing=12, run_spacing=12, wrap=True,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)

