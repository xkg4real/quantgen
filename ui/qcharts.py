"""Quant charts, rendered by matplotlib into base64 data-URI images.

Flet 0.85 ships no chart controls (`ft.LineChart` and `ft.BarChart` are gone
from this build — probed, not assumed), and the container-bar technique that
draws NEXTGEN's score bars cannot draw a percentile fan or a scatter cloud.
matplotlib can, deterministically, and `ft.Image` renders the PNG. `src`
accepts a data URI in 0.85; `src_base64` was removed.

Every figure is painted with the active QUANTGEN palette so the charts sit in
the app instead of on top of it. The Agg backend is forced before pyplot is
imported: this module runs inside worker threads, and a GUI backend would
try to touch the main thread and die.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

import flet as ft

from core.quant.backtest import BacktestResult
from core.quant.garch import TRADING_DAYS, GarchFit
from core.quant.history import History
from core.quant.montecarlo import MCResult
from core.quant.optimize import Frontier, OptimizedPortfolio
from core.theme import active

DPI = 110
_FONT_FILES = ("qg-interface.ttf", "qg-interface-medium.ttf", "qg-interface-semibold.ttf")


def _register_fonts() -> str:
    """Register the bundled QG Interface faces (Regular/Medium/SemiBold) with matplotlib once.

    matplotlib's default DejaVu Sans has no Hangul, so Korean chart text drew as boxes. The
    chart font becomes QG Interface with DejaVu Sans as the per-glyph fallback, so symbols
    the bundled face lacks still render. Nothing is downloaded or installed in the OS.
    """
    from core.app_paths import assets_directory
    folder = Path(assets_directory()) / "fonts"
    family = ""
    for name in _FONT_FILES:
        path = folder / name
        if not path.is_file():
            continue
        font_manager.fontManager.addfont(str(path))
        family = family or font_manager.FontProperties(fname=str(path)).get_name()
    if family:
        matplotlib.rcParams["font.family"] = [family, "DejaVu Sans"]
    return family or "DejaVu Sans"


CHART_FONT = _register_fonts()


def _ko(ctx) -> bool:
    """True when the chart text should be Korean (the page language of `ctx`)."""
    return getattr(ctx, "language", "en") == "ko"


def _reading(fig, **pairs: tuple[str, str]) -> None:
    """Chart-specific reading guidance for the side panel: meaning/look/interpret/limit = (Korean, English)."""
    fig._qg_reading = dict(pairs)


def _style(ax, pal, *, grid: bool = True) -> None:
    ax.set_facecolor(pal.surface)
    for spine in ax.spines.values():
        spine.set_color(pal.border)
    ax.tick_params(colors=pal.muted, labelsize=8)
    if grid:
        ax.grid(True, color=pal.border, alpha=0.35, linewidth=0.6)
    for title in (ax.title, ax._left_title, ax._right_title):   # loc="left" titles are separate Text objects
        title.set_color(pal.text)
    ax.xaxis.label.set_color(pal.muted)
    ax.yaxis.label.set_color(pal.muted)


def _fig(w: float, h: float, pal):
    fig, ax = plt.subplots(figsize=(w, h), dpi=DPI)
    fig._qg_palette = pal
    fig.patch.set_facecolor(pal.surface)
    _style(ax, pal)
    return fig, ax


def _to_image(fig, *, expand: bool = True, factory=None) -> ft.Control:
    from ui.chart_study import FigureStudy
    result = FigureStudy(fig, expand=expand, factory=factory)
    plt.close(fig)
    return result


def _localized(build, *, expand: bool = True) -> ft.Control:
    """`build(ctx) -> figure` drawn now in the default (Korean) page language and redrawn by
    `FigureStudy` when the page switches language, so chart text follows the KO/EN setting."""
    from core.i18n import LocaleContext
    ctx = LocaleContext()
    fig = build(ctx)
    fig._qg_language = "ko" if _ko(ctx) else "en"
    def factory(c):
        f = build(c)
        f._qg_language = "ko" if _ko(c) else "en"
        return f
    return _to_image(fig, expand=expand, factory=factory)


def _thin_dates(dates, n_ticks: int = 6):
    if not dates:
        return [], []
    idx = np.linspace(0, len(dates) - 1, min(n_ticks, len(dates))).astype(int)
    return idx, [dates[i] for i in idx]


# --------------------------------------------------------------------------- #
# Each chart draws the same data as before; `build(ctx)` only picks the language
# of its text, and `_reading` adds the side panel's chart-specific guidance.
# --------------------------------------------------------------------------- #
def _legend(ax, pal, loc: str = "upper left") -> None:
    ax.legend(loc=loc, fontsize=8, facecolor=pal.surface_2, edgecolor=pal.border, labelcolor=pal.text)


def price_chart(history: History, *, sma_windows: tuple[int, ...] = (50, 200)) -> ft.Control:
    px = history.prices()

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        x = np.arange(px.size)
        ax.plot(x, px, color=pal.accent, linewidth=1.4, label="종가" if ko else "Close")
        from core.quant.signals import sma
        for n, style in zip(sma_windows, ("--", ":")):
            if px.size >= n:
                ax.plot(x, sma(px, n), style, color=pal.muted, linewidth=1.0,
                        label=f"{n}일 이동평균 (SMA{n})" if ko else f"SMA{n}")
        idx, labels = _thin_dates(history.dates)
        ax.set_xticks(idx)
        ax.set_xticklabels(labels, rotation=0)
        _legend(ax, pal)
        ax.set_title(f"{history.symbol} 종가와 이동평균 — {len(history)}거래일 ({history.source})" if ko else
                     f"{history.symbol} — {len(history)} sessions ({history.source})", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("일별 종가(실선)와 50일·200일 단순이동평균(점선)을 함께 그린 가격 흐름입니다.",
                          "Daily closes (solid line) with the 50- and 200-session simple moving averages "
                          "(dashed and dotted)."),
                 look=("종가가 이동평균선 위에 있는지 아래에 있는지, 짧은 평균(50일)이 긴 평균(200일) 위에 있는지를 "
                       "보세요. 제목 괄호 안은 데이터 출처입니다.",
                       "Whether the close is above or below the averages, and whether the 50-session average is "
                       "above the 200-session one. The data source is in brackets in the title."),
                 interpret=("종가가 이동평균 위에 있으면 최근 가격이 그 기간 평균보다 높다는 뜻입니다. 50일선이 200일선을 "
                            "넘어서는 것은 이미 일어난 상승을 요약할 뿐입니다.",
                            "A close above an average means recent prices exceed that period's mean. A 50-over-200 "
                            "cross summarises a rise that has already happened."),
                 limit=("지나간 가격만 보여 주며 앞으로의 방향을 예측하지 않습니다. 출처가 SYNTHETIC이면 실제 시장 "
                        "가격이 아닙니다.",
                        "Past prices only, not a forecast. A SYNTHETIC source means these are not market prices."))
        return fig

    return _localized(build)


def fan_chart(history: History, mc: MCResult, *, tail_sessions: int = 90) -> ft.Control:
    px = history.prices()[-tail_sessions:]

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.2, pal)
        hx = np.arange(-px.size + 1, 1)
        fx = np.arange(0, mc.horizon_days + 1)
        ax.plot(hx, px, color=pal.text, linewidth=1.3)
        # Sample paths: faint spaghetti behind the fan.
        if mc.sample_paths is not None:
            for row in mc.sample_paths:
                ax.plot(fx, row, color=pal.muted, linewidth=0.35, alpha=0.25)
        ax.fill_between(fx, mc.fan[5], mc.fan[95], color=pal.accent, alpha=0.16,
                        label="경로 90% 범위 (5–95%)" if ko else "5–95%")
        ax.fill_between(fx, mc.fan[25], mc.fan[75], color=pal.accent, alpha=0.30,
                        label="경로 50% 범위 (25–75%)" if ko else "25–75%")
        ax.plot(fx, mc.fan[50], color=pal.accent, linewidth=1.6, label="중앙값" if ko else "Median")
        if mc.target:
            ax.axhline(mc.target, color=pal.success, linewidth=1.0, linestyle="--",
                       label=f"목표가 {mc.target:,.0f}" if ko else f"Target {mc.target:,.0f}")
        ax.axvline(0, color=pal.border, linewidth=0.8)
        _legend(ax, pal)
        ax.set_title(f"{mc.symbol} 가격 시뮬레이션 — {mc.model.upper()} 경로 {mc.n_paths:,}개, {mc.horizon_days}거래일"
                     if ko else f"{mc.symbol} — {mc.n_paths:,} {mc.model.upper()} paths, {mc.horizon_days} sessions",
                     fontsize=10, loc="left")
        ax.set_xlabel("오늘(0)부터의 거래일" if ko else "Sessions from today")
        _reading(fig,
                 meaning=("0 왼쪽은 최근 실제 가격, 오른쪽은 모형이 만든 미래 가격 경로들의 분포입니다. 옅은 띠는 경로의 "
                          "90%, 진한 띠는 50%가 지나간 범위입니다.",
                          "Left of 0 is the recent actual price; right of 0 is the spread of simulated future paths. "
                          "The light band holds 90% of the paths, the dark band 50%."),
                 look=("0(오늘) 이후 띠의 폭과 가운데 선(중앙값)을 보세요. 목표가 점선이 있으면 띠 안에 있는지 "
                       "확인하세요.",
                       "Look at the width of the bands after 0 (today) and the middle line (median). If a target "
                       "line is drawn, see whether it falls inside the bands."),
                 interpret=("띠가 넓을수록 모형이 예상하는 가격 변동이 큽니다. 중앙값은 '가장 그럴듯한 가격 하나'가 아니라 "
                            "경로들의 가운데 값입니다.",
                            "Wider bands mean the model expects larger price swings. The median is the middle of "
                            "the paths, not the single most likely price."),
                 limit=("과거 수익률로 추정한 모형의 시뮬레이션이며 미래 가격이나 확률을 보장하지 않습니다. 모형 가정이 "
                        "틀리면 범위도 틀립니다.",
                        "A simulation from a model fitted to past returns; it guarantees no price or probability. "
                        "If the model's assumptions are wrong, so are the bands."))
        return fig

    return _localized(build)


def terminal_histogram(mc: MCResult) -> ft.Control:
    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.6, pal)
        ax.hist(mc.terminal, bins=60, color=pal.accent, alpha=0.85, edgecolor=pal.surface)
        ax.axvline(mc.spot, color=pal.text, linewidth=1.2,
                   label=f"현재가 {mc.spot:,.0f}" if ko else f"Spot {mc.spot:,.0f}")
        var_price = mc.spot * (1 - mc.var_pct)
        ax.axvline(var_price, color=pal.error, linewidth=1.2, linestyle="--",
                   label=f"VaR{mc.var_level * 100:.0f} {var_price:,.0f}")
        if mc.target:
            ax.axvline(mc.target, color=pal.success, linewidth=1.2, linestyle="--",
                       label=f"목표가 {mc.target:,.0f}" if ko else f"Target {mc.target:,.0f}")
        _legend(ax, pal, "upper right")
        ax.set_title("기간 끝 가격 분포 (시뮬레이션)" if ko else "Terminal price distribution",
                     fontsize=10, loc="left")
        _reading(fig,
                 meaning=("시뮬레이션한 모든 경로가 기간 끝에 도달한 가격을 막대로 모은 분포입니다.",
                          "Where every simulated path ends, collected into a histogram."),
                 look=("현재가 실선, VaR 점선(손실 기준선), 목표가 점선의 위치와 막대가 몰린 곳을 비교하세요.",
                       "Compare the spot line, the VaR line (loss threshold) and the target line with where the "
                       "bars cluster."),
                 interpret=("VaR 점선 왼쪽 막대가 많을수록 모형상 큰 손실 경로가 많습니다. 목표가 오른쪽 막대의 비중이 "
                            "모형상 목표 도달 경로의 비중입니다.",
                            "More bars left of the VaR line mean more large-loss paths in the model; the share right "
                            "of the target is the model's share of paths reaching it."),
                 limit=("모형 시뮬레이션 결과이며 실제 확률이나 수익을 보장하지 않습니다.",
                        "A model simulation; it guarantees no actual probability or return."))
        return fig

    return _localized(build)


def equity_chart(bt: BacktestResult) -> ft.Control:
    x = np.arange(bt.equity.size)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.0, pal)
        ax.plot(x, bt.bench_equity, color=pal.muted, linewidth=1.1,
                label="매수 후 보유 (비교 기준)" if ko else "Buy & hold")
        ax.plot(x, bt.equity, color=pal.accent, linewidth=1.5, label=f"{bt.strategy}")
        # Shade the periods the strategy is in the market.
        inmkt = bt.position > 0
        ax.fill_between(x, 0, 1, where=inmkt, transform=ax.get_xaxis_transform(),
                        color=pal.success, alpha=0.06)
        idx, labels = _thin_dates(bt.dates)
        ax.set_xticks(idx)
        ax.set_xticklabels(labels)
        _legend(ax, pal)
        ax.set_title(f"{bt.symbol} — 1.0에서 시작한 누적 성과 (음영: 보유 구간)" if ko else
                     f"{bt.symbol} — growth of 1.0 (shaded: in market)", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("1.0을 투자했다면 전략(진한 선)과 단순히 사서 보유(회색 선)했을 때 금액이 어떻게 변했는지를 "
                          "보여 줍니다. 음영은 전략이 주식을 보유한 기간입니다.",
                          "What 1.0 invested would have become with the strategy (dark line) and with simple buy "
                          "and hold (grey line). Shading marks the periods the strategy was in the market."),
                 look=("마지막 지점에서 두 선의 높이를 비교하고, 중간에 크게 떨어진 구간(낙폭)을 확인하세요.",
                       "Compare the two lines at the end, and look for deep dips along the way (drawdowns)."),
                 interpret=("전략 선이 회색 선보다 위에 있으면 같은 기간 단순 보유보다 성과가 좋았다는 뜻입니다. 1.2는 "
                            "20% 이익, 0.9는 10% 손실입니다.",
                            "The strategy line above the grey one means it beat buy and hold over the period. 1.2 is "
                            "a 20% gain, 0.9 a 10% loss."),
                 limit=("과거 데이터로 다시 계산한 결과(백테스트)이며 미래 성과를 보장하지 않습니다. 비용·세금·체결 "
                        "차이가 실제 결과를 바꿀 수 있습니다.",
                        "A backtest on past data; it guarantees no future result. Costs, taxes and execution can "
                        "change the real outcome."))
        return fig

    return _localized(build)


_OBJECTIVE_KO = {"max_sharpe": "최대 샤프 지수", "min_vol": "최소 변동성", "risk_parity": "위험 균형",
                 "equal_weight": "동일 비중"}


def frontier_chart(frontier: Frontier,
                   marked: list[OptimizedPortfolio] | None = None) -> ft.Control:
    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.4, pal)
        sc = ax.scatter(frontier.cloud_vols * 100, frontier.cloud_rets * 100,
                        c=frontier.cloud_sharpes, cmap="viridis", s=6, alpha=0.5)
        cbar = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
        cbar.set_label("샤프 지수" if ko else "Sharpe", color=pal.muted, fontsize=8)
        cbar.ax.tick_params(colors=pal.muted, labelsize=7)
        cbar.outline.set_edgecolor(pal.border)
        if frontier.vols.size:
            ax.plot(frontier.vols * 100, frontier.rets * 100, color=pal.text,
                    linewidth=1.6, label="효율적 투자선" if ko else "Efficient frontier")
        markers = {"max_sharpe": ("*", pal.success, 180),
                   "min_vol": ("D", pal.accent, 60),
                   "risk_parity": ("s", pal.error, 60),
                   "equal_weight": ("o", pal.muted, 60)}
        for p in marked or []:
            m, c, s = markers.get(p.objective, ("o", pal.text, 60))
            ax.scatter([p.ann_vol * 100], [p.ann_return * 100], marker=m, s=s,
                       color=c, edgecolors=pal.surface, zorder=5,
                       label=_OBJECTIVE_KO.get(p.objective, p.objective) if ko else p.objective.replace("_", " "))
        ax.set_xlabel("연 변동성 (%)" if ko else "Annualized volatility (%)")
        ax.set_ylabel("연 수익률 (%)" if ko else "Annualized return (%)")
        _legend(ax, pal, "lower right")
        ax.set_title("위험과 수익 — 무작위 포트폴리오와 효율적 투자선" if ko else
                     "Risk / return — random portfolios and the frontier", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("점 하나가 무작위로 비중을 정한 포트폴리오 하나입니다. 가로는 위험(연 변동성), 세로는 과거 연 "
                          "수익률, 점 색은 샤프 지수(위험 대비 수익)입니다.",
                          "Each dot is one randomly weighted portfolio: across is risk (annual volatility), up is "
                          "past annual return, dot colour is the Sharpe ratio (return per unit of risk)."),
                 look=("검은 선(효율적 투자선)과 별·마름모 등 표시된 최적화 결과의 위치를 보세요.",
                       "Look at the dark line (efficient frontier) and where the marked optimised portfolios sit."),
                 interpret=("같은 위험이라면 위쪽 점이, 같은 수익이라면 왼쪽 점이 과거 기준으로 더 효율적이었습니다. 선 "
                            "위의 점은 그 위험에서 가장 높았던 수익입니다.",
                            "At the same risk a higher dot, at the same return a dot further left, was more efficient "
                            "in the past. Points on the line had the best return for their risk."),
                 limit=("과거 수익률·상관관계로 계산한 결과이며, 미래에는 위치가 크게 달라질 수 있습니다. 투자 권유가 "
                        "아닙니다.",
                        "Computed from past returns and correlations; positions can move a lot in the future. Not "
                        "a recommendation."))
        return fig

    return _localized(build)


def corr_heatmap(corr: np.ndarray, symbols: tuple[str, ...]) -> ft.Control:
    n = len(symbols)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(max(3.4, 0.65 * n + 1.6), max(2.8, 0.55 * n + 1.2), pal)
        ax.grid(False)
        im = ax.imshow(corr, cmap="RdYlGn_r", vmin=-1, vmax=1)
        ax.set_xticks(range(n)); ax.set_xticklabels(symbols, rotation=45, ha="right")
        ax.set_yticks(range(n)); ax.set_yticklabels(symbols)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                        fontsize=8, color="#111111")
        cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
        cbar.ax.tick_params(colors=pal.muted, labelsize=7)
        cbar.outline.set_edgecolor(pal.border)
        ax.set_title("수익률 상관계수" if ko else "Return correlation", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("두 종목의 일별 수익률이 얼마나 함께 움직였는지를 −1에서 +1 사이 숫자로 보여 줍니다.",
                          "How closely the daily returns of each pair moved together, from −1 to +1."),
                 look=("칸 안의 숫자와 색을 보세요. 대각선은 자기 자신이라 항상 1입니다.",
                       "Read the number and colour in each cell. The diagonal is each asset with itself, always 1."),
                 interpret=("+1에 가까우면 함께 오르내렸고, 0 근처면 관계가 약했으며, −1에 가까우면 반대로 움직였습니다. "
                            "상관이 낮은 자산을 섞을수록 분산 효과가 큽니다.",
                            "Near +1 they moved together, near 0 barely related, near −1 in opposite directions. "
                            "Mixing low-correlation assets diversifies more."),
                 limit=("과거 기간의 상관이며 앞으로도 같다고 보장하지 않습니다. 시장이 급변할 때는 상관이 갑자기 "
                        "높아지는 경우가 많습니다.",
                        "Correlation over the past window, with no guarantee it holds; in market stress "
                        "correlations often jump."))
        return fig

    return _localized(build, expand=False)


def cond_vol_chart(history: History, fit: GarchFit, *, window: int = 20) -> ft.Control:
    """Annualised GARCH conditional vol against rolling realised vol, with the
    unconditional level dashed. Both series are aligned on the return dates."""
    ann = np.sqrt(TRADING_DAYS)
    cond = np.asarray(fit.cond_vol, dtype=float) * ann * 100
    r = history.log_returns()[-cond.size:]

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        x = np.arange(cond.size)
        if r.size >= window:
            real = np.lib.stride_tricks.sliding_window_view(r, window).std(axis=1, ddof=1) * ann * 100
            ax.plot(x[window - 1:], real, color=pal.muted, linewidth=1.0,
                    label=f"실현 변동성 {window}일" if ko else f"Realised {window}d")
        ax.plot(x, cond, color=pal.accent, linewidth=1.4,
                label="GARCH 조건부 변동성" if ko else "GARCH conditional")
        if np.isfinite(fit.uncond_vol):
            ax.axhline(fit.uncond_vol * 100, color=pal.text, linewidth=1.0, linestyle="--",
                       label=(f"장기 평균 {fit.uncond_vol * 100:.1f}%" if ko else
                              f"Unconditional {fit.uncond_vol * 100:.1f}%"))
        idx, labels = _thin_dates(list(history.dates[-cond.size:]))
        ax.set_xticks(idx)
        ax.set_xticklabels(labels)
        ax.set_ylabel("연환산 변동성 (%)" if ko else "Annualised vol (%)")
        _legend(ax, pal)
        half = f"{fit.half_life:.0f}" if np.isfinite(fit.half_life) else "inf"
        ax.set_title(f"{history.symbol} — GARCH(1,1)-{fit.dist} 조건부 변동성, 지속성 {fit.persistence:.3f}, "
                     f"반감기 {half}거래일" if ko else
                     f"{history.symbol} — GARCH(1,1)-{fit.dist} conditional vol, "
                     f"persistence {fit.persistence:.3f}, half-life {half} sessions", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("GARCH 모형이 추정한 그날그날의 변동성(진한 선)과 최근 실제로 나타난 변동성(회색 선), 모형의 "
                          "장기 평균(점선)을 연 단위로 비교합니다.",
                          "The day-by-day volatility the GARCH model estimates (dark line), the recently realised "
                          "volatility (grey line) and the model's long-run level (dashed), all annualised."),
                 look=("진한 선이 점선 위인지 아래인지, 그리고 회색 선과 얼마나 붙어 움직이는지를 보세요.",
                       "Whether the dark line is above or below the dashed level, and how closely it tracks the "
                       "grey line."),
                 interpret=("점선 위면 지금 변동성이 평소보다 높다는 뜻이며, 반감기는 그 차이가 절반으로 줄어드는 데 걸리는 "
                            "거래일 수입니다.",
                            "Above the dashed line, volatility is higher than usual; the half-life is how many "
                            "sessions it takes for that gap to halve."),
                 limit=("모형 추정치이며 앞으로의 변동성을 보장하지 않습니다. 급격한 사건은 모형이 늦게 반영합니다.",
                        "A model estimate, not a guarantee of future volatility; sudden events reach it late."))
        return fig

    return _localized(build)
