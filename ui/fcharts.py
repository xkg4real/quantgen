"""FICC charts, rendered by matplotlib into base64 data-URI `ft.Image`s.

Same machinery as `ui/qcharts.py` — Agg backend, palette from `core.theme`,
and `_fig/_style/_to_image/_thin_dates` imported from there rather than
copied. Every function takes a `core.ficc` result object and returns one
`ft.Image`; the pages wrap it in `card()`.

This is the one place the FICC core's decimals get scaled for humans: rates
in percent, spreads in bp, P&L in currency. Tenor axes are log-scaled so
1m/3m/6m do not collapse onto the 30y end. `payoff_chart` is duck-typed on
`ProductReport.payoff_grid` so this module imports without
`core.ficc.structured`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import numpy as np

import flet as ft

from core.ficc.bonds import Bond, modified_duration, price_from_yield
from core.ficc.common import BP, tenor_label
from core.ficc.curves import CurveReport, PCAResult, nelson_siegel, svensson
from core.theme import active
from ui.qcharts import _fig, _ko, _localized, _reading, _style, _thin_dates, _to_image

if TYPE_CHECKING:                                    # pragma: no cover
    from core.ficc.bonds import ScenarioRow
    from core.ficc.data import CurvePanel, Series
    from core.ficc.fx import CarryBacktest, CarryRow, SmilePoint
    from core.ficc.macro import MacroSheet
    from core.ficc.ratesim import HorizonPV, RateSimResult
    from core.ficc.swaps import CapFloorReport


def _legend(ax, pal, loc: str = "upper left", *args) -> None:
    ax.legend(*args, loc=loc, fontsize=8, facecolor=pal.surface_2,
              edgecolor=pal.border, labelcolor=pal.text)


def _twin_legend(ax, ax2, pal, loc: str) -> None:
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    _legend(ax, pal, loc, h1 + h2, l1 + l2)


def _tenor_axis(ax, tenors: Sequence[float]) -> None:
    ax.set_xscale("log")
    ax.set_xticks(list(tenors))
    ax.set_xticklabels([tenor_label(t) for t in tenors])
    ax.minorticks_off()


def _date_axis(ax, dates) -> None:
    idx, labels = _thin_dates(dates)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)


# --------------------------------------------------------------------------- #
# Curves
# --------------------------------------------------------------------------- #
def curve_chart(report: CurveReport) -> ft.Control:
    """Par, zero and 1y-forward curves off the fitted `YieldCurve`, the NS/NSS
    fit dotted, and the snapshot's par yields as markers."""
    pal = active()
    snap, curve = report.snapshot, report.curve
    lo, hi = min(snap.tenors), max(snap.tenors)
    t = np.geomspace(lo, hi, 160)
    # Par only on the semi-annual coupon grid (plus the money-market tenors):
    # the stub-free schedule T - k/2 saw-tooths between those points.
    tp = np.array(sorted({x for x in snap.tenors if x < 1.0} | set(np.arange(1.0, hi + 0.5, 0.5))))
    tp = tp[tp <= hi]
    par = np.array([curve.par_rate(x, 2) if x >= 1.0 else (1.0 / curve.df(x) - 1.0) / x
                    for x in tp])
    fwd = np.array([curve.fwd(x, x + 1.0) for x in t])
    fn = svensson if report.ns.method == "svensson" else nelson_siegel
    fig, ax = _fig(7.5, 3.2, pal)
    ax.plot(tp, par * 100, color=pal.accent, linewidth=1.6, label="Par (semi-annual)")
    ax.plot(t, curve.zero(t) * 100, color=pal.text, linewidth=1.2, label="Zero (cont.)")
    ax.plot(t, fwd * 100, "--", color=pal.success, linewidth=1.1, label="1y forward")
    ax.plot(t, fn(t, *report.ns.params) * 100, ":", color=pal.muted, linewidth=1.2,
            label=f"{report.ns.method.replace('_', '-')} fit, rmse {report.ns.rmse / BP:.1f}bp")
    ax.scatter(snap.tenors, np.asarray(snap.par_yields) * 100, color=pal.accent, s=18,
               zorder=5)
    _tenor_axis(ax, snap.tenors)
    ax.set_ylabel("%")
    _legend(ax, pal)
    ax.set_title(f"{snap.date} {snap.source} — {report.shape}, {report.regime} over "
                 f"{report.lookback} sessions", fontsize=10, loc="left")
    return _to_image(fig)


def _tenor_ko(label: str) -> str:
    """'2y' -> '2년물', '3m' -> '3개월물' (tenor_label spelling); anything else unchanged."""
    for suffix, word in (("y", "년물"), ("m", "개월물"), ("w", "주물"), ("d", "일물")):
        if label.endswith(suffix) and label[:-1].replace(".", "", 1).isdigit():
            return label[:-1] + word
    return label


def curve_history_chart(panel: CurvePanel,
                        tenors: Sequence[float] = (2.0, 10.0, 30.0)) -> ft.Control:
    grid = np.asarray(panel.tenors, dtype=float)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        x = np.arange(len(panel))
        for tenor, colour in zip(tenors, (pal.accent, pal.text, pal.success, pal.error, pal.muted)):
            k = int(np.argmin(np.abs(grid - tenor)))
            label = tenor_label(grid[k])
            ax.plot(x, panel.yields[:, k] * 100, color=colour, linewidth=1.3,
                    label=_tenor_ko(label) if ko else label)
        _date_axis(ax, panel.dates)
        ax.set_ylabel("금리 (%)" if ko else "%")
        _legend(ax, pal)
        ax.set_title(f"국채 금리 추이 — {len(panel)}거래일 ({panel.source})" if ko else
                     f"Par yields — {len(panel)} sessions ({panel.source})", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("만기별(예: 2년·10년·30년) 국채 금리가 날짜에 따라 어떻게 움직였는지 보여 줍니다.",
                          "How the par yields of each maturity (e.g. 2, 10 and 30 years) moved over time."),
                 look=("선들의 높이 차이(장단기 금리차)와 최근 방향을 보세요. 오른쪽 끝이 가장 최근입니다.",
                       "Look at the gaps between the lines (the curve slope) and their recent direction; the right "
                       "end is the latest."),
                 interpret=("선들이 함께 오르내리면 금리 수준이 바뀐 것이고, 간격이 바뀌면 곡선 기울기가 바뀐 것입니다. "
                            "단기 금리 선이 장기 금리 선보다 위에 있으면 곡선이 역전된 상태입니다.",
                            "Lines moving together mean the level changed; a changing gap means the slope changed. "
                            "A short-maturity line above a long one means the curve is inverted."),
                 limit=("관측된 금리를 그린 것이며 앞으로의 금리를 예측하지 않습니다. 출처가 SYNTHETIC이면 실제 금리가 "
                        "아닙니다.",
                        "Observed yields only, not a forecast. A SYNTHETIC source means these are not market "
                        "yields."))
        return fig

    return _localized(build)


def pca_chart(pca: PCAResult) -> ft.Control:
    pal = active()
    fig, ax = _fig(7.5, 2.9, pal)
    colours = (pal.accent, pal.success, pal.error, pal.muted)
    for j, label in enumerate(pca.labels):
        ax.plot(pca.tenors, pca.loadings[:, j], marker="o", markersize=3, linewidth=1.3,
                color=colours[j % len(colours)],
                label=f"{label} ({pca.explained[j] * 100:.0f}%)")
    ax.axhline(0, color=pal.border, linewidth=0.8)
    _tenor_axis(ax, pca.tenors)
    ax.set_ylabel("Loading")
    _legend(ax, pal, "upper right")
    ax.set_title(f"PCA of daily curve changes — {pca.explained.sum() * 100:.0f}% explained by "
                 f"{len(pca.labels)} factors", fontsize=10, loc="left")
    return _to_image(fig)


# --------------------------------------------------------------------------- #
# Bonds & swaps
# --------------------------------------------------------------------------- #
def krd_chart(krd: dict[float, float], title: str = "Key-rate DV01") -> ft.Control:
    pal = active()
    tenors = sorted(krd)
    vals = np.array([krd[t] for t in tenors], dtype=float)
    fig, ax = _fig(7.5, 2.7, pal)
    ax.bar(range(len(tenors)), vals, color=[pal.accent if v >= 0 else pal.error for v in vals],
           edgecolor=pal.surface)
    ax.set_xticks(range(len(tenors)))
    ax.set_xticklabels([tenor_label(t) for t in tenors])
    ax.axhline(0, color=pal.border, linewidth=0.8)
    ax.set_ylabel("per bp")
    ax.set_title(f"{title} — total {vals.sum():,.0f} per bp", fontsize=10, loc="left")
    return _to_image(fig)


def scenario_chart(rows: Sequence[ScenarioRow]) -> ft.Control:
    pal = active()
    pnl = np.array([r.pnl for r in rows], dtype=float)
    fig, ax = _fig(7.5, max(2.4, 0.32 * len(rows) + 1.0), pal)
    y = np.arange(len(rows))
    ax.barh(y, pnl, color=[pal.success if v >= 0 else pal.error for v in pnl],
            edgecolor=pal.surface)
    ax.set_yticks(y)
    ax.set_yticklabels([r.name for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0, color=pal.border, linewidth=0.8)
    for yi, r in zip(y, rows):
        ax.text(r.pnl, yi, f" {r.pnl:,.0f} ({r.pnl_pct * 100:+.2f}%) ", va="center",
                ha="left" if r.pnl >= 0 else "right", fontsize=7, color=pal.text)
    ax.margins(x=0.3)
    ax.set_xlabel("P&L on notional")
    ax.set_title("Scenario P&L — full revaluation, z-spread held", fontsize=10, loc="left")
    return _to_image(fig)


def price_yield_chart(bond: Bond, ytm: float) -> ft.Control:
    """Price against yield ±300bp with the duration tangent at `ytm`; the gap
    between curve and tangent is the convexity."""
    pal = active()
    ys = np.linspace(ytm - 0.03, ytm + 0.03, 121)
    ys = ys[1.0 + ys / bond.freq > 0]
    p0, mdur = price_from_yield(bond, ytm), modified_duration(bond, ytm)
    prices = np.array([price_from_yield(bond, y) for y in ys])
    fig, ax = _fig(7.5, 2.9, pal)
    ax.plot(ys * 100, prices, color=pal.accent, linewidth=1.6, label="Price")
    ax.plot(ys * 100, p0 * (1.0 - mdur * (ys - ytm)), "--", color=pal.muted, linewidth=1.0,
            label=f"Duration tangent (mod. dur. {mdur:.2f})")
    ax.scatter([ytm * 100], [p0], color=pal.text, s=30, zorder=5,
               label=f"{ytm * 100:.2f}% -> {p0:.3f}")
    ax.set_xlabel("Yield (%)")
    ax.set_ylabel(f"Price per {bond.face:g}")
    _legend(ax, pal, "upper right")
    name = bond.name or f"{bond.coupon * 100:.2f}% {bond.maturity:g}y"
    ax.set_title(f"{name} — price / yield", fontsize=10, loc="left")
    return _to_image(fig)


def caplet_chart(report: CapFloorReport) -> ft.Control:
    pal = active()
    c = np.asarray(report.caplets, dtype=float).reshape(-1, 4)
    starts, ends, fwds, prem = c.T
    kind = "Caplet" if report.cap else "Floorlet"
    fig, ax = _fig(7.5, 2.9, pal)
    ax.bar(starts, prem, width=(ends - starts) * 0.8, align="edge", color=pal.accent,
           alpha=0.85, edgecolor=pal.surface, label=f"{kind} premium")
    ax.set_xlabel("Period start (years)")
    ax.set_ylabel("Premium")
    ax2 = ax.twinx()
    _style(ax2, pal, grid=False)
    ax2.plot((starts + ends) / 2, fwds * 100, color=pal.text, marker="o", markersize=3,
             linewidth=1.1, label="Forward (%)")
    ax2.axhline(report.strike * 100, color=pal.error, linestyle="--", linewidth=1.0,
                label=f"Strike {report.strike * 100:.2f}%")
    ax2.axhline(report.atm_strike * 100, color=pal.muted, linestyle=":", linewidth=1.0,
                label=f"ATM {report.atm_strike * 100:.2f}%")
    ax2.set_ylabel("%")
    _twin_legend(ax, ax2, pal, "upper left")
    ax.set_title(f"{'Cap' if report.cap else 'Floor'} — {len(c)} periods, {report.model}, "
                 f"premium {report.premium:,.0f} ({report.premium_bp:.1f}bp)",
                 fontsize=10, loc="left")
    return _to_image(fig)


# --------------------------------------------------------------------------- #
# FX
# --------------------------------------------------------------------------- #
def smile_chart(strikes, vols, points: Sequence[SmilePoint], forward: float) -> ft.Control:
    pal = active()
    fig, ax = _fig(7.5, 2.9, pal)
    ax.plot(np.asarray(strikes, dtype=float), np.asarray(vols, dtype=float) * 100,
            color=pal.accent, linewidth=1.5, label="SABR")
    for p in points:
        ax.scatter([p.strike], [p.vol * 100], color=pal.text, s=28, zorder=5)
        ax.annotate(f"{p.label} {p.vol * 100:.2f}%", (p.strike, p.vol * 100),
                    textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7,
                    color=pal.text)
    ax.axvline(forward, color=pal.muted, linestyle="--", linewidth=1.0,
               label=f"Forward {forward:.4f}")
    ax.set_xlabel("Strike")
    ax.set_ylabel("Vol (%)")
    _legend(ax, pal, "upper center")
    ax.set_title("Volatility smile — market points and SABR fit", fontsize=10, loc="left")
    return _to_image(fig)


def fx_spot_chart(series: Series, forward_points_line=None) -> ft.Control:
    """`forward_points_line`: a forward outright (float) drawn as a dashed level,
    or (tenor_years, forward) pairs drawn as the forward curve extending past
    the last spot at 252 sessions per year."""
    px = series.array()

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        ax.plot(np.arange(px.size), px, color=pal.accent, linewidth=1.4, label="현물 환율" if ko else "Spot")
        if forward_points_line is not None:
            if np.isscalar(forward_points_line):
                f = float(forward_points_line)
                ax.axhline(f, color=pal.success, linestyle="--", linewidth=1.0,
                           label=f"선도 환율 {f:.4f}" if ko else f"Forward {f:.4f}")
            else:
                pts = sorted((float(t), float(f)) for t, f in forward_points_line)
                ax.plot([px.size - 1] + [px.size - 1 + t * 252 for t, _ in pts],
                        [px[-1]] + [f for _, f in pts], "--o", color=pal.success,
                        linewidth=1.2, markersize=3, label="선도 환율 곡선" if ko else "Forward curve")
        _date_axis(ax, series.dates)
        _legend(ax, pal)
        ax.set_title(f"{series.label} 환율 — {len(series)}거래일 ({series.source}), 최근 {series.last:.4f}" if ko else
                     f"{series.label} — {len(series)} sessions ({series.source}), last {series.last:.4f}",
                     fontsize=10, loc="left")
        _reading(fig,
                 meaning=("현물 환율의 흐름(실선)과 두 통화의 금리 차이로 계산한 선도 환율(점선)을 함께 보여 줍니다.",
                          "The spot rate over time (solid) with the forward rate implied by the two currencies' "
                          "interest-rate gap (dashed)."),
                 look=("실선의 오른쪽 끝(오늘)과 점선의 차이를 보세요. 제목 괄호 안은 데이터 출처입니다.",
                       "Compare the right end of the solid line (today) with the dashed line. The data source is "
                       "in brackets in the title."),
                 interpret=("선도 환율이 현물보다 높거나 낮은 것은 금리 차이를 반영한 계산 결과입니다. 환율이 그 방향으로 "
                            "움직인다는 뜻은 아닙니다.",
                            "A forward above or below spot reflects the interest-rate gap; it does not mean the rate "
                            "will move that way."),
                 limit=("선도 환율은 전망이 아니라 금리 차이로 계산한 값입니다. 출처가 SYNTHETIC이면 실제 시세가 "
                        "아닙니다.",
                        "The forward is arithmetic on the rate gap, not a forecast. A SYNTHETIC source means these "
                        "are not market quotes."))
        return fig

    return _localized(build)


def carry_equity_chart(bt: CarryBacktest) -> ft.Control:
    x = np.arange(bt.equity.size)
    pos = {d: i for i, d in enumerate(bt.dates)}

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.0, pal)
        ax.plot(x, bt.bench_equity, color=pal.muted, linewidth=1.1,
                label="모든 통화 동일 비중 매수 (비교 기준)" if ko else "Equal-weight long all")
        ax.plot(x, bt.equity, color=pal.accent, linewidth=1.5,
                label=(f"캐리 상위 {bt.top_n}개 매수 / 하위 {bt.top_n}개 매도" if ko else
                       f"Carry top {bt.top_n} / bottom {bt.top_n}"))
        for d, _, _ in bt.positions:
            if d in pos:
                ax.axvline(pos[d], color=pal.border, linewidth=0.5, alpha=0.7)
        _date_axis(ax, bt.dates)
        _legend(ax, pal)
        ax.set_title((f"캐리 바스켓 — 연 {bt.ann_return * 100:+.1f}%, 변동성 {bt.ann_vol * 100:.1f}%, "
                      f"샤프 {bt.sharpe:.2f}, 최대 낙폭 {bt.max_drawdown * 100:.1f}%, 비용 {bt.cost_bps:g}bp "
                      f"(세로선: 재조정)") if ko else
                     (f"Carry basket — {bt.ann_return * 100:+.1f}% p.a., vol {bt.ann_vol * 100:.1f}%, "
                      f"Sharpe {bt.sharpe:.2f}, max DD {bt.max_drawdown * 100:.1f}%, "
                      f"{bt.cost_bps:g}bp cost (lines: rebalances)"), fontsize=10, loc="left")
        _reading(fig,
                 meaning=("금리가 높은 통화를 사고 낮은 통화를 파는 캐리 전략을 과거 데이터로 다시 계산한 누적 성과(1에서 "
                          "시작)입니다. 세로선은 바스켓을 다시 짠 날입니다.",
                          "The carry strategy (long high-yield, short low-yield currencies) recomputed on past data, "
                          "as growth of 1. Vertical lines are rebalance dates."),
                 look=("진한 선(전략)과 회색 선(모든 통화 동일 비중)의 끝 높이와 중간 낙폭을 비교하세요.",
                       "Compare where the dark (strategy) and grey (equal-weight) lines end, and the dips on the "
                       "way."),
                 interpret=("진한 선이 위에 있으면 같은 기간 단순 분산 매수보다 성과가 좋았습니다. 캐리 전략은 평소 꾸준하다가 "
                            "위험 회피 국면에 한꺼번에 크게 잃는 경향이 있습니다.",
                            "Dark above grey means carry beat the simple basket over the period. Carry tends to earn "
                            "steadily and then lose sharply when markets turn risk-off."),
                 limit=("과거 데이터의 백테스트이며 미래 성과를 보장하지 않습니다. 표시한 비용 외의 실제 비용·체결 차이는 "
                        "반영되지 않았습니다.",
                        "A backtest on past data, no guarantee of future results. Real costs beyond the stated cost "
                        "and execution are not included."))
        return fig

    return _localized(build)


def carry_bar_chart(rows: Sequence[CarryRow]) -> ft.Control:
    x = np.arange(len(rows))
    carry = np.array([r.carry for r in rows], dtype=float) * 100

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.8, pal)
        ax.bar(x, carry, color=[pal.success if v >= 0 else pal.error for v in carry],
               edgecolor=pal.surface, label="달러 대비 캐리 (연 %)" if ko else "Carry vs USD (% p.a.)")
        ax.set_xticks(x)
        ax.set_xticklabels([r.ccy for r in rows])
        ax.axhline(0, color=pal.border, linewidth=0.8)
        ax.set_ylabel("캐리 (연 %)" if ko else "Carry (% p.a.)")
        ax2 = ax.twinx()
        _style(ax2, pal, grid=False)
        ax2.plot(x, [r.score for r in rows], color=pal.text, marker="D", markersize=4,
                 linewidth=0, label="점수 (캐리/변동성 + 모멘텀/변동성)" if ko else "Score (carry/vol + mom/vol)")
        ax2.set_ylabel("점수" if ko else "Score")
        _twin_legend(ax, ax2, pal, "upper right")
        ax.set_title("캐리 순위 — 달러 대비 각 통화를 샀을 때" if ko else
                     "Carry ranking — long the currency against USD", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("통화마다 달러 대비로 샀을 때 받는 연간 금리 차이(캐리, 막대)와, 변동성을 감안한 점수(마름모)를 "
                          "보여 줍니다.",
                          "For each currency bought against USD: the yearly rate gap earned (carry, bars) and a "
                          "volatility-adjusted score (diamonds)."),
                 look=("초록 막대는 보유하면 금리 차이를 받는 통화, 빨간 막대는 내야 하는 통화입니다. 마름모가 높을수록 "
                       "점수가 높습니다.",
                       "Green bars earn the rate gap, red bars pay it. Higher diamonds mean higher scores."),
                 interpret=("캐리가 크더라도 변동성이 크면 점수는 낮아집니다. 점수는 순위를 매기기 위한 값입니다.",
                            "A large carry with high volatility still scores low; the score is for ranking only."),
                 limit=("현재 금리 차이와 과거 움직임으로 계산한 순위이며 환율 전망이나 매매 권유가 아닙니다.",
                        "A ranking from today's rate gaps and past moves, not an FX forecast or a recommendation."))
        return fig

    return _localized(build)


# --------------------------------------------------------------------------- #
# Structured, simulation, macro
# --------------------------------------------------------------------------- #
def payoff_chart(product) -> ft.Control:
    """Duck-typed on ProductReport: `payoff_grid` of (underlying level, payoff
    per 100), plus `product`, `issue_price` and `fair_value` when present."""
    pal = active()
    grid = np.asarray(product.payoff_grid, dtype=float).reshape(-1, 2)
    if grid.size == 0:
        raise ValueError("payoff_grid is empty.")
    x, y = grid[:, 0], grid[:, 1]
    issue = float(getattr(product, "issue_price", 100.0))
    fig, ax = _fig(7.5, 2.9, pal)
    ax.plot(x, y, color=pal.accent, linewidth=1.7, label="Payoff at maturity (per 100)")
    ax.axhline(issue, color=pal.muted, linestyle="--", linewidth=1.0,
               label=f"Issue price {issue:g}")
    ax.fill_between(x, issue, y, where=y >= issue, color=pal.success, alpha=0.15,
                    interpolate=True)
    ax.fill_between(x, issue, y, where=y < issue, color=pal.error, alpha=0.15,
                    interpolate=True)
    ax.set_xlabel("Underlying at maturity")
    ax.set_ylabel("per 100")
    _legend(ax, pal)
    title = str(getattr(product, "product", "Structured note"))
    fair = getattr(product, "fair_value", None)
    if fair is not None:
        title += f" — fair {fair:.2f} vs issue {issue:g}"
    ax.set_title(title, fontsize=10, loc="left")
    return _to_image(fig)


def rate_fan_chart(sim: RateSimResult) -> ft.Control:
    pal = active()
    fig, ax = _fig(7.5, 3.0, pal)
    t = sim.times
    ax.fill_between(t, sim.fan[5] * 100, sim.fan[95] * 100, color=pal.accent, alpha=0.16,
                    label="5–95%")
    ax.fill_between(t, sim.fan[25] * 100, sim.fan[75] * 100, color=pal.accent, alpha=0.30,
                    label="25–75%")
    ax.plot(t, sim.fan[50] * 100, color=pal.accent, linewidth=1.6, label="Median")
    if sim.model != "hull_white":          # HW's theta is a regression mean, not a level
        ax.axhline(sim.params.theta * 100, color=pal.muted, linestyle=":", linewidth=1.0,
                   label=f"Long-run mean {sim.params.theta * 100:.2f}%")
    if sim.threshold is not None:
        ax.axhline(sim.threshold * 100, color=pal.error, linestyle="--", linewidth=1.0,
                   label=f"Threshold {sim.threshold * 100:.2f}% "
                         f"(P above {sim.prob_above * 100:.0f}%)")
    ax.set_xlabel("Years")
    ax.set_ylabel("%")
    _legend(ax, pal)
    ax.set_title(f"{sim.model} — {sim.n_paths:,} paths, {sim.horizon:g}y; terminal mean "
                 f"{sim.mean_terminal * 100:.2f}% [{sim.p05 * 100:.2f}%, {sim.p95 * 100:.2f}%]",
                 fontsize=10, loc="left")
    return _to_image(fig)


def horizon_pv_hist(hpv: HorizonPV) -> ft.Control:
    pal = active()
    fig, ax = _fig(7.5, 2.6, pal)
    ax.hist(hpv.pvs, bins=40, color=pal.accent, alpha=0.85, edgecolor=pal.surface)
    ax.axvline(hpv.mean, color=pal.text, linewidth=1.2, label=f"Mean {hpv.mean:,.0f}")
    ax.axvline(hpv.p05, color=pal.error, linewidth=1.2, linestyle="--",
               label=f"p05 {hpv.p05:,.0f}")
    ax.axvline(hpv.p95, color=pal.success, linewidth=1.2, linestyle="--",
               label=f"p95 {hpv.p95:,.0f}")
    _legend(ax, pal, "upper right")
    ax.set_title(f"Horizon PV over {hpv.pvs.size} paths — VaR95 {hpv.var95:,.0f}, "
                 f"CVaR95 {hpv.cvar95:,.0f}", fontsize=10, loc="left")
    return _to_image(fig)


MACRO_READING = {
    "meaning": ("주요 거시 지표 18개가 지금 지난 1년 평균보다 얼마나 높거나 낮은지를 z-점수로 보여 줍니다. "
                "0은 1년 평균과 같다는 뜻이고, +1은 평소 흔들림(표준편차) 1개만큼 높다는 뜻입니다.",
                "How far each of the 18 macro indicators sits above or below its own 1-year average, as a "
                "z-score. 0 means at the 1-year average; +1 means one typical swing (standard deviation) above it."),
    "look": ("막대가 0의 오른쪽이면 1년 평균보다 높고, 왼쪽이면 낮습니다. 옅은 띠(±1) 안은 평소 범위, "
             "점선(±2) 밖은 1년 중 드문 수준입니다. 막대 끝 숫자가 정확한 z-점수입니다.",
             "Bars right of 0 are above the 1-year average, bars left of it below. Inside the shaded band (±1) "
             "is the usual range; beyond the dashed lines (±2) is rare for the past year. The number at each "
             "bar end is the exact z-score."),
    "interpret": ("막대 색은 지표 묶음(금리·신용·외환·위험선호)이며 묶음 사이에 구분선이 있습니다. 빗금 막대는 실제 관측이 "
                  "아닌 합성 데이터입니다. 신용 스프레드와 VIX가 함께 오른쪽이면 시장이 위험을 피하는 분위기입니다. "
                  "차트 위 '시장 요약'은 같은 지표의 최근 변화를 정해진 규칙으로 정리한 것입니다.",
                  "Bar colour is the indicator group (rates, credit, FX, risk appetite), with a rule between groups. "
                  "Hatched bars are synthetic data, not observations. Credit spreads and VIX both to the right "
                  "mean markets are avoiding risk. The market summary above the chart sums up recent changes "
                  "of the same indicators with fixed rules."),
    "limit": ("지금 상태를 설명할 뿐이며 국면 모형이나 예측이 아닙니다(P19). z-점수는 지난 1년만 비교하므로 "
              "1년 내내 이례적이었다면 0이 '정상'을 뜻하지 않습니다. 매매 신호나 투자 권유로 쓰지 마세요.",
              "A descriptive read of the present, not a regime model or a forecast (P19). The z-score compares "
              "with the past year only, so 0 is not 'normal' if the whole year was unusual. Not a trading "
              "signal or a recommendation."),
}


def macro_z_chart(sheet: MacroSheet) -> ft.Control:
    """Horizontal bars of 1y z-scores, coloured by group (with group rules), synthetic rows hatched.

    Same data as before; the text follows the page language (Korean names with the indicator
    code), the usual range |z| < 1 is shaded and |z| = 2 is dashed and labelled, the value is
    printed at each bar end and the legend sits below the plot so it never covers a bar.
    """
    from matplotlib.patches import Patch
    from matplotlib.transforms import offset_copy
    from ui.charts_terms import GROUP_NAMES, INDICATOR_NAMES, name

    rows = list(sheet.rows)
    synthetic = set(sheet.synthetic_ids)

    def build(ctx):
        ko = _ko(ctx)
        pick = (lambda pair: pair[0]) if ko else (lambda pair: pair[1])
        pal = active()
        colours = {"rates": pal.accent, "credit": pal.error, "fx": pal.success, "risk": pal.muted}
        n = len(rows)
        fig, ax = _fig(8.2, 0.38 * n + 2.5, pal)
        ax.grid(False)
        ax.grid(True, axis="x", color=pal.border, alpha=0.5, linewidth=0.6)
        ax.set_axisbelow(True)
        y = np.arange(n)
        z = np.array([r.z_1y for r in rows], dtype=float)
        finite = np.abs(z[np.isfinite(z)])
        lim = max(3.0, float(np.ceil(finite.max() + 0.9))) if finite.size else 3.0
        ax.axvspan(-1, 1, color=pal.accent, alpha=0.07, linewidth=0, zorder=0)
        for v in (-2, 2):
            ax.axvline(v, color=pal.muted, linewidth=0.9, linestyle="--", zorder=1)
        ax.axvline(0, color=pal.text, linewidth=0.9, zorder=2)
        for yi, r in zip(y, rows):
            ax.barh(yi, r.z_1y, height=0.64, color=colours.get(r.group, pal.text), edgecolor=pal.surface,
                    linewidth=0.6, hatch="///" if r.id in synthetic else None, zorder=3)
            if np.isfinite(r.z_1y):
                ax.text(r.z_1y + (0.08 if r.z_1y >= 0 else -0.08), yi, f"{r.z_1y:+.1f}", va="center",
                        ha="left" if r.z_1y >= 0 else "right", fontsize=9.5, color=pal.text, zorder=4,
                        bbox=dict(facecolor=pal.surface, edgecolor="none", pad=0.8))
        for k in range(1, n):                                  # a rule between indicator groups
            if rows[k].group != rows[k - 1].group:
                ax.axhline(k - 0.5, color=pal.border, linewidth=1.0, zorder=1)
        ax.set_yticks(y)
        ax.set_yticklabels([pick(name(INDICATOR_NAMES, r.id, r.label)) for r in rows], fontsize=10)
        ax.tick_params(axis="y", length=0, colors=pal.text)
        ax.tick_params(axis="x", labelsize=9.5)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(n - 0.5, -0.5)
        top = offset_copy(ax.get_xaxis_transform(), fig=fig, y=3, units="points")
        ax.text(0, 1.0, pick(("평소 범위 (±1)", "Usual range (±1)")), transform=top, ha="center", va="bottom",
                fontsize=9.5, color=pal.muted)
        for v in (-2, 2):
            ax.text(v, 1.0, pick(("이례적", "Unusual")), transform=top, ha="center", va="bottom",
                    fontsize=9.5, color=pal.muted)
        ax.set_xlabel(pick(("1년 z-점수 (0 = 1년 평균, ±2 = 이례적)",
                            "1-year z-score (0 = 1-year average, ±2 = unusual)")), fontsize=10)
        ax.set_title(pick(("주요 거시 지표: 1년 평균 대비 현재 위치 (z-점수)",
                           "Key macro indicators against their 1-year average (z-score)")),
                     fontsize=13, fontweight="semibold", loc="left", pad=44)
        ax.text(0, 1.0, pick((f"기준일 {sheet.as_of} · 막대 끝 숫자 = z-점수",
                              f"As of {sheet.as_of} · number at bar end = z-score")),
                transform=offset_copy(ax.transAxes, fig=fig, y=22, units="points"),
                ha="left", va="bottom", fontsize=10, color=pal.muted)
        groups = list(dict.fromkeys(r.group for r in rows))
        handles = [Patch(facecolor=colours.get(g, pal.text), edgecolor=pal.surface,
                         label=pick(name(GROUP_NAMES, g, g))) for g in groups]
        if any(r.id in synthetic for r in rows):
            handles.append(Patch(facecolor=pal.muted, edgecolor=pal.surface, hatch="///",
                                 label=pick(("합성 데이터 · 실제 관측 아님", "Synthetic data · not observed"))))
        fig.set_layout_engine("constrained")
        fig.legend(handles=handles, loc="outside lower center", ncol=len(handles), frameon=False,
                   fontsize=10, labelcolor=pal.text, handlelength=1.4, columnspacing=1.6)
        _reading(fig, **MACRO_READING)
        return fig

    return _localized(build)


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from types import SimpleNamespace

    from core.ficc import data, fx, ratesim, swaps
    from core.ficc.bonds import analyze_bond, scenario_pnl
    from core.ficc.curves import analyze_curve, curve_pca
    from core.ficc.macro import macro_sheet

    panel = data.synthetic_curve_panel(days=120)
    report = analyze_curve(panel, method="nelson_siegel")
    curve = report.curve
    bond = Bond(coupon=0.04, maturity=10.0, name="4% 10y")
    ba = analyze_bond(bond, ytm=0.045, curve=curve)
    pts = fx.smile_from_quotes(fx.SmileQuote(0.5, 0.10, 0.01, 0.003), 1.10, 0.045, 0.03)
    F = fx.forward(1.10, 0.045, 0.03, 0.5)
    fit = fx.calibrate_sabr(F, 0.5, [p.strike for p in pts], [p.vol for p in pts])
    ks = np.linspace(pts[0].strike * 0.97, pts[-1].strike * 1.03, 60)
    params = ratesim.calibrate(data.load_short_rate("USD", source="synthetic", days=300))
    sim = ratesim.simulate(params, horizon=1.0, n_paths=300, threshold=0.05)
    hpv = ratesim.horizon_pv_distribution(sim.params, sim, kind="bond", bond=bond, curve=curve)
    pairs = ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDKRW")
    spots = {p: data.synthetic_fx(p, days=300) for p in pairs}
    rates = {c: data.synthetic_series(f"RATE_{c}", days=300, kind="rate") for c in data.G10_KRW}
    product = SimpleNamespace(
        product="Test PPN", issue_price=100.0, fair_value=98.5,
        payoff_grid=tuple((s, 100.0 + max(s - 100.0, 0.0) * 0.8) for s in range(60, 141, 5)))
    images = [
        curve_chart(report), curve_history_chart(panel), pca_chart(curve_pca(panel)),
        krd_chart(ba.krd, "Bond KRD"), scenario_chart(scenario_pnl(bond, curve, ba.price)),
        price_yield_chart(bond, ba.ytm),
        smile_chart(ks, fx.smile_curve(fit, F, 0.5, ks), pts, F),
        payoff_chart(product), rate_fan_chart(sim), horizon_pv_hist(hpv),
        fx_spot_chart(spots["EURUSD"], ((0.25, 1.105), (1.0, 1.12))),
        fx_spot_chart(spots["USDJPY"], 148.0),
        carry_equity_chart(fx.carry_backtest(spots, rates)),
        carry_bar_chart(fx.carry_table(spots, rates)),
        macro_z_chart(macro_sheet(source="synthetic", days=300)),
        caplet_chart(swaps.price_cap_floor(curve, 5.0, None, vol=0.008)),
    ]
    assert len(images) == 16
    for img in images:
        assert img.src.startswith("data:image/png;base64,"), "chart must inline its PNG"
        assert len(img.src) > 1000, "suspiciously empty chart"
    print("ok")
