"""FICC charts, rendered by matplotlib into base64 data-URI `ft.Image`s.

Same machinery as `ui/qcharts.py` — Agg backend, palette from `core.theme`,
and `_fig/_style/_localized/_reading/_thin_dates` imported from there rather
than copied. Every function takes a `core.ficc` result object and returns one
`FigureStudy` (chart plus reading panel) drawn in the page language; the pages
wrap it in `card()`.

This is the one place the FICC core's decimals get scaled for humans: rates
in percent, spreads in bp, P&L in currency. Tenor axes are log-scaled so
1m/3m/6m do not collapse onto the 30y end. `payoff_chart` is duck-typed on
`ProductReport.payoff_grid` so this module imports without
`core.ficc.structured`.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional, Sequence

import numpy as np
from matplotlib.ticker import FuncFormatter

import flet as ft

from core.ficc.bonds import Bond, modified_duration, price_from_yield
from core.ficc.common import BP, tenor_label
from core.ficc.curves import CurveReport, PCAResult, nelson_siegel, svensson
from core.theme import active
from ui.qcharts import _fig, _ko, _localized, _reading, _style, _thin_dates

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


def _legend_below(fig, pal, *axes) -> None:
    """The legend of `axes` under the plot, so it never covers a line or bar: frameless, in as
    many columns as fit the figure width (Korean labels are longer, so they may take two rows)."""
    handles, labels = [], []
    for a in axes:
        h, l = a.get_legend_handles_labels()
        handles += h
        labels += l
    fig.set_layout_engine("constrained")
    renderer = fig.canvas.get_renderer()
    for ncol in range(len(labels), 0, -1):
        legend = fig.legend(handles, labels, loc="outside lower center", ncol=ncol, frameon=False,
                            fontsize=8, labelcolor=pal.text, handlelength=1.8, columnspacing=1.4)
        if ncol == 1 or legend.get_window_extent(renderer).width <= 0.96 * fig.bbox.width:
            return
        legend.remove()


def _tenor_axis(ax, tenors: Sequence[float], ko: bool = False) -> None:
    ax.set_xscale("log")
    ax.set_xticks(list(tenors))
    ax.set_xticklabels([_tenor_tick(tenor_label(t), ko) for t in tenors])
    ax.minorticks_off()


def _tenor_tick(label: str, ko: bool) -> str:
    """Axis tick for a tenor: '2y' -> '2년', '3m' -> '3개월' in Korean; tenor_label's spelling in English."""
    return _tenor_ko(label).removesuffix("물") if ko else label


def _catalogue_ko(text: str) -> str:
    """The reviewed Korean caption of an exact English name (method, product); the name itself if none."""
    from core.ui_legacy_messages import static_text
    return static_text(text, "ko")


# Same Korean words as the Rates page (ui/rates_page.py) and the native app.
_SHAPES_KO = {"normal": "정상 우상향", "inverted": "역전", "humped": "중간 만기 돌출", "flat": "평탄"}
_REGIMES_KO = {"bull steepener": "금리 하락·기울기 확대", "bull flattener": "금리 하락·기울기 축소",
               "bear steepener": "금리 상승·기울기 확대", "bear flattener": "금리 상승·기울기 축소",
               "parallel up": "평행 상승", "parallel down": "평행 하락", "unchanged": "변화 없음"}
_RATE_MODELS = {"vasicek": "Vasicek", "cir": "CIR", "hull_white": "Hull-White"}


def _date_axis(ax, dates) -> None:
    idx, labels = _thin_dates(dates)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)


# --------------------------------------------------------------------------- #
# Curves
# --------------------------------------------------------------------------- #
def curve_chart(report: CurveReport) -> ft.Control:
    """Par, zero and 1y-forward curves off the constructed `YieldCurve`, the
    parametric fit dotted (the method's own, else the Nelson-Siegel reference),
    and the snapshot's par yields as markers."""
    snap, curve = report.snapshot, report.curve
    lo, hi = min(snap.tenors), max(snap.tenors)
    t = np.geomspace(lo, hi, 160)
    # Par only on the semi-annual coupon grid (plus the money-market tenors):
    # the stub-free schedule T - k/2 saw-tooths between those points.
    tp = np.array(sorted({x for x in snap.tenors if x < 1.0} | set(np.arange(1.0, hi + 0.5, 0.5))))
    tp = tp[tp <= hi]
    par = np.array([curve.par_rate(x, 2) if x >= 1.0 else (1.0 / curve.df(x) - 1.0) / x
                    for x in tp])
    tf = t[t + 1.0 <= hi + 1e-9]          # a 1y forward must end inside the quotes (no extrapolation)
    fwd = np.array([curve.fwd(x, x + 1.0) for x in tf])
    from core.ficc.curves import METHOD_NAMES, parametric_function   # the fit's own yield function
    fn = parametric_function(report.ns.method)
    zero, fitted = curve.zero(t) * 100, fn(t, *report.ns.params) * 100
    method = METHOD_NAMES.get(curve.method, curve.method)
    fit_name = METHOD_NAMES.get(report.ns.method, report.ns.method)
    rmse = report.ns.rmse / BP

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.2, pal)
        ax.plot(tp, par * 100, color=pal.accent, linewidth=1.6,
                label="파 수익률 (반기 복리)" if ko else "Par (semi-annual)")
        ax.plot(t, zero, color=pal.text, linewidth=1.2, label="제로 금리 (연속 복리)" if ko else "Zero (cont.)")
        ax.plot(tf, fwd * 100, "--", color=pal.success, linewidth=1.1, label="1년 선도금리" if ko else "1y forward")
        ax.plot(t, fitted, ":", color=pal.muted, linewidth=1.2,
                label=(f"{_catalogue_ko(fit_name)} 적합, 오차 RMSE {rmse:.1f}bp" if ko else
                       f"{fit_name} fit, rmse {rmse:.1f}bp"))
        ax.scatter(snap.tenors, np.asarray(snap.par_yields) * 100, color=pal.accent, s=18,
                   zorder=5)
        _tenor_axis(ax, snap.tenors, ko)
        ax.set_xlabel("만기" if ko else "Maturity")
        ax.set_ylabel("금리 (%)" if ko else "Rate (%)")
        _legend_below(fig, pal, ax)
        ax.set_title((f"{snap.date} {snap.source} 수익률 곡선 ({_catalogue_ko(method)}) — "
                      f"{_SHAPES_KO.get(report.shape, report.shape)}, 최근 {report.lookback}거래일 "
                      f"{_REGIMES_KO.get(report.regime, report.regime)}") if ko else
                     (f"{snap.date} {snap.source} {method} curve — {report.shape}, {report.regime} "
                      f"over {report.lookback} sessions"), fontsize=10, loc="left")
        _reading(fig,
                 meaning=("고시된 국채 금리(점)로 만든 수익률 곡선입니다. 파 수익률(액면가에 거래되는 채권의 수익률), "
                          "제로 금리(만기에 한 번 받는 돈의 할인율), 1년 선도금리(그 만기부터 1년 동안 적용되는 금리)를 "
                          "함께 그리고, 점선은 매끄러운 모수 모형으로 맞춘 곡선입니다.",
                          "The yield curve built from the quoted Treasury yields (dots): par yields (the yield of a "
                          "bond priced at par), zero rates (the discount rate of one payment at maturity) and 1-year "
                          "forward rates (the rate for the year starting at that maturity). The dotted line is a "
                          "smooth parametric fit."),
                 look=("가로축은 만기(로그 눈금)입니다. 왼쪽 단기에서 오른쪽 장기로 곡선이 오르는지 내리는지, 점선이 "
                       "점들을 얼마나 가깝게 지나는지 보세요. 제목에 곡선 형태와 최근 변화가 적혀 있습니다.",
                       "Across is maturity on a log scale. See whether the curve rises or falls from the short end "
                       "(left) to the long end (right), and how closely the dotted fit passes the dots. The title "
                       "names the curve shape and the recent move."),
                 interpret=("장기 금리가 단기보다 높으면 정상(우상향), 낮으면 역전된 곡선입니다. 1년 선도금리가 같은 "
                            "만기의 제로 금리보다 높으면 그 뒤 구간에서 곡선이 오른다는 뜻입니다. 범례의 오차(RMSE)가 "
                            "작을수록 모수 모형이 고시 금리를 잘 따라갑니다.",
                            "Long yields above short ones is a normal (upward) curve; below is inverted. A 1-year "
                            "forward above the zero rate of the same maturity means the curve rises after it. The "
                            "smaller the fit error (RMSE) in the legend, the closer the model follows the quotes."),
                 limit=("선도금리는 오늘 곡선에서 계산한 값이며 미래 금리 전망이 아닙니다. 구축 방법에 따라 고시 금리 "
                        "사이의 모양이 달라집니다. 출처가 SYNTHETIC이면 실제 금리가 아닙니다.",
                        "Forward rates are arithmetic on today's curve, not a forecast. The construction method "
                        "changes the shape between quotes. A SYNTHETIC source means these are not market yields."))
        return fig

    return _localized(build)


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


_PCA_FACTORS_KO = {"level": "수준", "slope": "기울기", "curvature": "곡률"}


def _pca_factor_ko(label: str) -> str:
    """'level' -> '수준', 'pc4' -> '주성분 4'; anything else unchanged."""
    if label in _PCA_FACTORS_KO:
        return _PCA_FACTORS_KO[label]
    return f"주성분 {label[2:]}" if re.fullmatch(r"pc\d+", label) else label


def pca_chart(pca: PCAResult) -> ft.Control:
    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        colours = (pal.accent, pal.success, pal.error, pal.muted)
        for j, label in enumerate(pca.labels):
            ax.plot(pca.tenors, pca.loadings[:, j], marker="o", markersize=3, linewidth=1.3,
                    color=colours[j % len(colours)],
                    label=f"{_pca_factor_ko(label) if ko else label} ({pca.explained[j] * 100:.0f}%)")
        ax.axhline(0, color=pal.border, linewidth=0.8)
        _tenor_axis(ax, pca.tenors, ko)
        ax.set_ylabel("요인 적재값" if ko else "Loading")
        _legend_below(fig, pal, ax)
        total = pca.explained.sum() * 100
        ax.set_title(f"일별 금리 변화의 주성분 분석(PCA) — 요인 {len(pca.labels)}개가 변동의 {total:.0f}% 설명" if ko else
                     f"PCA of daily curve changes — {total:.0f}% explained by {len(pca.labels)} factors",
                     fontsize=10, loc="left")
        _reading(fig,
                 meaning=("매일의 금리 곡선 변화를 서로 겹치지 않는 몇 가지 움직임(주성분)으로 나눈 결과입니다. 선 하나가 "
                          "한 요인이 만기별 금리를 얼마나 움직이는지(적재값)를 보여 줍니다.",
                          "The daily changes of the yield curve split into a few independent movements (principal "
                          "components). Each line shows how much one factor moves the yield at each maturity (its "
                          "loadings)."),
                 look=("범례 괄호 안의 비율(그 요인이 설명하는 변동의 몫)과 각 선의 모양을 보세요. 가로선 0을 기준으로 "
                       "선이 위인지 아래인지 비교하세요.",
                       "Read the share in brackets in the legend (how much of the variation that factor explains) "
                       "and the shape of each line against the zero line."),
                 interpret=("모든 만기에서 같은 부호로 비슷하면 곡선 전체가 함께 오르내리는 '수준' 요인, 단기와 장기의 "
                            "부호가 반대면 '기울기' 요인, 중간 만기만 반대면 '곡률' 요인입니다. 첫 요인의 비율이 클수록 "
                            "곡선이 대부분 평행하게 움직였다는 뜻입니다.",
                            "Same sign and similar size at every maturity is the 'level' factor (the whole curve "
                            "moves together); opposite signs at the short and long ends is 'slope'; only the middle "
                            "moving the other way is 'curvature'. A large first share means the curve mostly moved "
                            "in parallel."),
                 limit=("관측 기간의 변화로 계산한 통계적 분해이며, 기간이 바뀌면 요인 모양과 비율도 바뀝니다. 앞으로의 "
                        "금리 움직임을 예측하지 않습니다.",
                        "A statistical split of the changes in the observed window; another window gives other "
                        "shapes and shares. It does not forecast rate moves."))
        return fig

    return _localized(build)


# --------------------------------------------------------------------------- #
# Bonds & swaps
# --------------------------------------------------------------------------- #
def _swap_ko(label: str) -> str:
    """`Swap.label` ('5y payer', '1y5y receiver') -> '5년 고정금리 지급 스왑', '1년 후 시작 5년 고정금리 수취 스왑'."""
    m = re.fullmatch(r"(?P<start>[\d.]+[mywd])?(?P<tenor>[\d.]+[mywd]) (?P<side>payer|receiver)", label)
    if not m:
        return label
    side = "고정금리 지급" if m["side"] == "payer" else "고정금리 수취"
    start = f"{_tenor_tick(m['start'], True)} 후 시작 " if m["start"] else ""
    return f"{start}{_tenor_tick(m['tenor'], True)} {side} 스왑"


def _krd_title_ko(title: str) -> str:
    """The Korean of the titles the Rates and Bonds pages pass; anything else is shown as given."""
    if title == "Key-rate DV01":
        return "만기별 DV01"
    if title == "Bond KRD":
        return "채권 만기별 DV01"
    m = re.fullmatch(r"Key-rate DV01 — (?P<swap>.+)", title)
    if m:
        return f"만기별 DV01 — {_swap_ko(m['swap'])}"
    m = re.fullmatch(r"Key-rate DV01, z-spread (?P<z>.+) held", title)
    if m:
        return f"만기별 DV01 (z-스프레드 {m['z']} 고정)"
    return title


def krd_chart(krd: dict[float, float], title: str = "Key-rate DV01", *,
              title_ko: Optional[str] = None) -> ft.Control:
    """Key-rate DV01 bars. `title_ko` gives the Korean title; without it the titles the pages pass
    are translated and anything else is shown as given."""
    tenors = sorted(krd)
    vals = np.array([krd[t] for t in tenors], dtype=float)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.7, pal)
        ax.bar(range(len(tenors)), vals, color=[pal.accent if v >= 0 else pal.error for v in vals],
               edgecolor=pal.surface)
        ax.set_xticks(range(len(tenors)))
        ax.set_xticklabels([_tenor_tick(tenor_label(t), ko) for t in tenors])
        ax.axhline(0, color=pal.border, linewidth=0.8)
        ax.set_ylabel("1bp당 가치 변화" if ko else "per bp")
        head = title_ko or _krd_title_ko(title)
        ax.set_title(f"{head}{', ' if ' — ' in head else ' — '}합계 {vals.sum():,.0f} (1bp당)" if ko else
                     f"{title} — total {vals.sum():,.0f} per bp", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("각 만기(2년, 5년, 10년 등)의 금리만 1bp(0.01%p) 움직였을 때 가치가 얼마나 바뀌는지를 만기별 "
                          "막대로 나눠 보여 줍니다. 막대를 모두 더하면 제목의 합계(전체 DV01)와 거의 같습니다.",
                          "How much the value changes when only the yield at one maturity (2, 5, 10 years...) moves "
                          "by 1bp (0.01 percentage point), one bar per maturity. The bars add up to about the total "
                          "in the title (the overall DV01)."),
                 look=("가장 긴 막대가 어느 만기에 있는지, 그리고 0 위(양수)와 아래(빨간 막대, 음수)로 나뉜 방향을 "
                       "보세요.",
                       "Find the maturity with the longest bar, and which bars point above zero (positive) or "
                       "below it (red, negative)."),
                 interpret=("막대가 길수록 그 만기 금리 변화에 민감합니다. 부호의 기준은 화면마다 다릅니다: 채권은 금리가 "
                            "1bp 내릴 때의 가격 상승분(양수면 금리가 오를 때 손실), 스왑은 금리가 1bp 오를 때의 손익(고정금리 "
                            "지급 스왑은 양수)입니다.",
                            "A longer bar means more sensitivity to that maturity's yield. The sign convention "
                            "depends on the screen: for a bond it is the price gain when yields fall 1bp (positive "
                            "means a loss when yields rise); for a swap it is the P&L when yields rise 1bp (a "
                            "pay-fixed swap is positive)."),
                 limit=("한 만기만 따로 1bp 움직인다고 본 선형 근사이므로, 금리가 크게 움직이거나 곡선 모양이 바뀌면 실제 "
                        "손익과 다를 수 있습니다. 금리 방향을 예측하지 않습니다.",
                        "A linear approximation with one maturity moved at a time; large moves or a change in the "
                        "curve's shape can give a different P&L. It does not forecast rates."))
        return fig

    return _localized(build)


_SCENARIOS_KO = {"bear steepener": "금리 상승·기울기 확대", "bull steepener": "금리 하락·기울기 확대",
                 "bear flattener": "금리 상승·기울기 축소", "bull flattener": "금리 하락·기울기 축소",
                 "2y-5y-10y fly": "2년-5년-10년 버터플라이"}


def _scenario_ko(name: str) -> str:
    """'+25bp parallel' -> '+25bp 평행 이동', 'bear steepener' -> '금리 상승·기울기 확대'; else unchanged."""
    m = re.fullmatch(r"([+-]?[\d.]+bp) parallel", name)
    return f"{m[1]} 평행 이동" if m else _SCENARIOS_KO.get(name, name)


def scenario_chart(rows: Sequence[ScenarioRow]) -> ft.Control:
    pnl = np.array([r.pnl for r in rows], dtype=float)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, max(2.4, 0.32 * len(rows) + 1.0), pal)
        y = np.arange(len(rows))
        ax.barh(y, pnl, color=[pal.success if v >= 0 else pal.error for v in pnl],
                edgecolor=pal.surface)
        ax.set_yticks(y)
        ax.set_yticklabels([_scenario_ko(r.name) if ko else r.name for r in rows], fontsize=8)
        ax.invert_yaxis()
        ax.axvline(0, color=pal.border, linewidth=0.8)
        for yi, r in zip(y, rows):
            ax.text(r.pnl, yi, f" {r.pnl:,.0f} ({r.pnl_pct * 100:+.2f}%) ", va="center",
                    ha="left" if r.pnl >= 0 else "right", fontsize=7, color=pal.text)
        ax.margins(x=0.3)
        ax.set_xlabel("명목금액 기준 손익" if ko else "P&L on notional")
        ax.set_title("시나리오별 손익 — 전체 재평가, z-스프레드 고정" if ko else
                     "Scenario P&L — full revaluation, z-spread held", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("금리 곡선에 정해 둔 충격(평행 이동, 기울기 변화, 버터플라이)을 주고 채권 가격을 처음부터 다시 "
                          "계산했을 때의 손익입니다. 막대 끝 숫자는 손익 금액과 현재 가격 대비 비율입니다.",
                          "The P&L when a fixed shock (parallel shift, slope change, butterfly) is applied to the "
                          "yield curve and the bond is fully repriced. The numbers at the bar ends are the P&L and "
                          "its percentage of today's price."),
                 look=("초록 막대(이익)와 빨간 막대(손실)의 길이를 비교하고, 가장 긴 빨간 막대가 어떤 시나리오인지 "
                       "보세요.",
                       "Compare the green (gain) and red (loss) bars, and find the scenario with the longest red "
                       "bar."),
                 interpret=("금리 상승 시나리오의 손실이 클수록 금리 위험에 많이 노출된 것입니다. 같은 크기의 금리 하락에서 "
                            "얻는 이익이 상승에서 잃는 손실보다 크면 그 차이가 볼록성(컨벡시티) 효과입니다.",
                            "Larger losses in the rising-rate scenarios mean more exposure to rate risk. When the "
                            "gain from a fall is bigger than the loss from a rise of the same size, the difference "
                            "is convexity."),
                 limit=("미리 정한 가상 충격의 결과일 뿐 금리 예측이 아니며, 그 시나리오가 일어날 가능성도 말하지 "
                        "않습니다. 신용 스프레드(z-스프레드)는 그대로라고 가정합니다.",
                        "Results of hypothetical shocks chosen in advance, not a rate forecast; they say nothing "
                        "about how likely a scenario is. The credit spread (z-spread) is held constant."))
        return fig

    return _localized(build)


def _bond_name_ko(name: str) -> str:
    """'4.00% 10y' -> '쿠폰 4.00% · 10년 만기 채권'; any other bond name is shown as given."""
    m = re.fullmatch(r"(?P<coupon>[\d.]+%) (?P<maturity>[\d.]+)y", name)
    return f"쿠폰 {m['coupon']} · {m['maturity']}년 만기 채권" if m else name


def price_yield_chart(bond: Bond, ytm: float) -> ft.Control:
    """Price against yield ±300bp with the duration tangent at `ytm`; the gap
    between curve and tangent is the convexity."""
    ys = np.linspace(ytm - 0.03, ytm + 0.03, 121)
    ys = ys[1.0 + ys / bond.freq > 0]
    p0, mdur = price_from_yield(bond, ytm), modified_duration(bond, ytm)
    prices = np.array([price_from_yield(bond, y) for y in ys])
    name = bond.name or f"{bond.coupon * 100:.2f}% {bond.maturity:g}y"

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        ax.plot(ys * 100, prices, color=pal.accent, linewidth=1.6, label="가격" if ko else "Price")
        ax.plot(ys * 100, p0 * (1.0 - mdur * (ys - ytm)), "--", color=pal.muted, linewidth=1.0,
                label=f"듀레이션 접선 (수정 듀레이션 {mdur:.2f})" if ko else
                f"Duration tangent (mod. dur. {mdur:.2f})")
        ax.scatter([ytm * 100], [p0], color=pal.text, s=30, zorder=5,
                   label=f"현재 {ytm * 100:.2f}% → {p0:.3f}" if ko else f"{ytm * 100:.2f}% -> {p0:.3f}")
        ax.set_xlabel("수익률 (%)" if ko else "Yield (%)")
        ax.set_ylabel(f"액면 {bond.face:g}당 가격" if ko else f"Price per {bond.face:g}")
        _legend(ax, pal, "upper right")
        ax.set_title(f"{_bond_name_ko(name)} — 가격과 수익률" if ko else f"{name} — price / yield",
                     fontsize=10, loc="left")
        _reading(fig,
                 meaning=("수익률이 지금보다 ±3%p 범위에서 바뀔 때 채권 가격이 어떻게 변하는지(실선)와, 현재 수익률에서 "
                          "듀레이션으로 그은 직선 근사(점선)를 함께 보여 줍니다. 점이 현재 수익률과 가격입니다.",
                          "How the bond price changes as the yield moves up to ±3 percentage points from today "
                          "(solid line), with the straight-line duration approximation at today's yield (dashed). "
                          "The dot is today's yield and price."),
                 look=("점에서 실선과 점선이 맞닿는 모습과, 점에서 멀어질수록 두 선이 벌어지는 정도를 보세요.",
                       "Look at where the solid and dashed lines touch at the dot, and how far apart they get "
                       "away from it."),
                 interpret=("수익률이 오르면 가격이 내립니다. 선이 가파를수록 금리 위험이 큽니다. 실선이 점선보다 위에 있는 "
                            "만큼이 볼록성(컨벡시티)으로, 금리가 크게 움직일 때 듀레이션만으로 계산한 것보다 가격이 덜 "
                            "떨어지고 더 오른다는 뜻입니다.",
                            "Price falls as yield rises; a steeper line means more rate risk. The gap by which the "
                            "solid line sits above the dashed one is convexity: for large moves the price falls less "
                            "and rises more than duration alone says."),
                 limit=("수익률 하나로 모든 현금흐름을 할인한 이론 가격이며 실제 시장 가격·유동성·신용 위험은 반영하지 "
                        "않습니다. 수익률 방향을 예측하지 않습니다.",
                        "A theoretical price discounting every cash flow at one yield; market prices, liquidity "
                        "and credit risk are not included. It does not forecast yields."))
        return fig

    return _localized(build)


_OPTION_MODELS_KO = {"bachelier": "Bachelier 정규 모형", "black": "Black-76"}


def caplet_chart(report: CapFloorReport) -> ft.Control:
    c = np.asarray(report.caplets, dtype=float).reshape(-1, 4)
    starts, ends, fwds, prem = c.T

    def build(ctx):
        ko, pal = _ko(ctx), active()
        if ko:
            kind = "캡렛" if report.cap else "플로어렛"
        else:
            kind = "Caplet" if report.cap else "Floorlet"
        fig, ax = _fig(7.5, 2.9, pal)
        ax.bar(starts, prem, width=(ends - starts) * 0.8, align="edge", color=pal.accent,
               alpha=0.85, edgecolor=pal.surface, label=f"{kind} 프리미엄" if ko else f"{kind} premium")
        ax.set_xlabel("이자기간 시작 시점 (년)" if ko else "Period start (years)")
        ax.set_ylabel("프리미엄" if ko else "Premium")
        ax2 = ax.twinx()
        _style(ax2, pal, grid=False)
        ax2.plot((starts + ends) / 2, fwds * 100, color=pal.text, marker="o", markersize=3,
                 linewidth=1.1, label="선도금리 (%)" if ko else "Forward (%)")
        ax2.axhline(report.strike * 100, color=pal.error, linestyle="--", linewidth=1.0,
                    label=f"행사금리 {report.strike * 100:.2f}%" if ko else f"Strike {report.strike * 100:.2f}%")
        ax2.axhline(report.atm_strike * 100, color=pal.muted, linestyle=":", linewidth=1.0,
                    label=(f"등가격(ATM) 금리 {report.atm_strike * 100:.2f}%" if ko else
                           f"ATM {report.atm_strike * 100:.2f}%"))
        ax2.set_ylabel("금리 (%)" if ko else "%")
        _legend_below(fig, pal, ax, ax2)
        if ko:
            title = (f"{'캡' if report.cap else '플로어'} — {len(c)}개 기간, "
                     f"{_OPTION_MODELS_KO.get(report.model, report.model)}, "
                     f"프리미엄 {report.premium:,.0f} ({report.premium_bp:.1f}bp)")
        else:
            title = (f"{'Cap' if report.cap else 'Floor'} — {len(c)} periods, {report.model}, "
                     f"premium {report.premium:,.0f} ({report.premium_bp:.1f}bp)")
        ax.set_title(title, fontsize=10, loc="left")
        _reading(fig,
                 meaning=("캡(또는 플로어)을 이자기간마다의 옵션(캡렛·플로어렛)으로 나눠, 기간별 프리미엄(막대, 왼쪽 축)과 "
                          "그 기간의 선도금리(점을 이은 선, 오른쪽 축)를 함께 보여 줍니다.",
                          "The cap (or floor) split into one option per interest period (caplets or floorlets): "
                          "the premium of each period (bars, left axis) and that period's forward rate (dotted "
                          "line with markers, right axis)."),
                 look=("막대 높이가 기간에 따라 어떻게 바뀌는지, 선도금리 선이 빨간 점선(행사금리)보다 위인지 아래인지 "
                       "보세요. 회색 점선은 등가격(ATM) 금리입니다.",
                       "See how the bar heights change across periods, and whether the forward line is above or "
                       "below the red dashed strike. The grey dotted line is the at-the-money (ATM) rate."),
                 interpret=("캡렛은 선도금리가 행사금리보다 높을수록, 시작 시점이 멀수록(불확실성이 클수록) 비쌉니다. "
                            "플로어렛은 선도금리가 행사금리보다 낮을수록 비쌉니다. 막대를 모두 더하면 제목의 전체 "
                            "프리미엄입니다.",
                            "A caplet costs more the further the forward is above the strike and the later it "
                            "starts (more uncertainty); a floorlet costs more the further the forward is below the "
                            "strike. The bars add up to the total premium in the title."),
                 limit=("입력한 변동성 하나와 단일 곡선으로 계산한 모형 가격이며, 시장 호가도 금리 예측도 "
                        "아닙니다.",
                        "A model price from one input volatility and a single curve; it is not a market quote "
                        "and not a rate forecast."))
        return fig

    return _localized(build)


# --------------------------------------------------------------------------- #
# FX
# --------------------------------------------------------------------------- #
_SMILE_POINTS_KO = {"25d put": "25델타 풋", "ATM": "등가격(ATM)", "25d call": "25델타 콜"}


def smile_chart(strikes, vols, points: Sequence[SmilePoint], forward: float) -> ft.Control:
    ks, vs = np.asarray(strikes, dtype=float), np.asarray(vols, dtype=float) * 100

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        ax.plot(ks, vs, color=pal.accent, linewidth=1.5, label="SABR 적합 곡선" if ko else "SABR")
        for p in points:
            ax.scatter([p.strike], [p.vol * 100], color=pal.text, s=28, zorder=5)
            ax.annotate(f"{_SMILE_POINTS_KO.get(p.label, p.label) if ko else p.label} {p.vol * 100:.2f}%",
                        (p.strike, p.vol * 100), textcoords="offset points", xytext=(0, 7), ha="center",
                        fontsize=7, color=pal.text)
        ax.axvline(forward, color=pal.muted, linestyle="--", linewidth=1.0,
                   label=f"선도환율 {forward:.4f}" if ko else f"Forward {forward:.4f}")
        ax.set_xlabel("행사가격" if ko else "Strike")
        ax.set_ylabel("변동성 (%)" if ko else "Vol (%)")
        _legend_below(fig, pal, ax)
        ax.set_title("변동성 스마일 — 시장 호가 점과 SABR 적합" if ko else
                     "Volatility smile — market points and SABR fit", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("행사가격마다 통화옵션 시장이 매기는 내재변동성입니다. 점은 시장 호가(등가격·25델타 리스크리버설·"
                          "버터플라이)에서 계산한 값이고, 선은 그 점들에 맞춘 SABR 모형 곡선입니다.",
                          "The implied volatility the FX option market sets at each strike. The dots come from the "
                          "market quotes (at-the-money, 25-delta risk reversal and butterfly); the line is the SABR "
                          "model fitted to them."),
                 look=("곡선의 가장 낮은 지점, 양쪽 끝이 올라가는 정도, 회색 점선(선도환율)을 기준으로 왼쪽과 오른쪽의 "
                       "높이 차이를 보세요.",
                       "Look at the lowest point of the curve, how much the ends lift, and the difference between "
                       "the left and right of the grey dashed forward."),
                 interpret=("양쪽 끝이 높을수록 큰 환율 변동에 대비한 옵션이 비싸게 매겨졌다는 뜻입니다. 한쪽이 더 높으면 "
                            "시장이 그 방향의 급변을 더 비싸게 보험하고 있다는 뜻입니다.",
                            "Higher ends mean options against large FX moves are priced dearer. One side higher "
                            "than the other means the market pays more to insure a sharp move that way."),
                 limit=("한 시점의 호가에 맞춘 모형 곡선이며 환율 방향이나 미래 변동성을 예측하지 않습니다. 호가 사이와 "
                        "바깥의 행사가격은 모형이 채운 값입니다.",
                        "A model curve fitted to quotes at one moment; it does not forecast the rate or future "
                        "volatility. Strikes between and beyond the quotes are filled in by the model."))
        return fig

    return _localized(build)


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
_UNDERLYINGS_KO = {"FX": "외환", "EQ": "주식", "CMS 10y-2y": "CMS 10년-2년"}


def _product_ko(name: str) -> str:
    """Korean name of a `ProductReport.product` ('Principal-protected note (FX)' -> '원금보장형 노트 (외환)');
    product kinds come from the reviewed page catalogue, anything unknown is shown as given."""
    m = re.fullmatch(r"(?P<kind>.+?) \((?P<underlying>[^()]+)\)", name)
    if m and _catalogue_ko(m["kind"]) != m["kind"]:
        return f"{_catalogue_ko(m['kind'])} ({_UNDERLYINGS_KO.get(m['underlying'], m['underlying'])})"
    m = re.fullmatch(r"Dual-currency deposit (?P<pair>\S+) K=(?P<strike>\S+)", name)
    if m:
        return f"{_catalogue_ko('Dual-currency deposit')} {m['pair']} (행사가격 {m['strike']})"
    if name == "CMS 10y-2y steepener note":
        return "CMS 10년-2년 스티프너 노트"
    if name == "Structured note":
        return "구조화 노트"
    return _catalogue_ko(name)


def payoff_chart(product) -> ft.Control:
    """Duck-typed on ProductReport: `payoff_grid` of (underlying level, payoff
    per 100), plus `product`, `issue_price` and `fair_value` when present."""
    grid = np.asarray(product.payoff_grid, dtype=float).reshape(-1, 2)
    if grid.size == 0:
        raise ValueError("payoff_grid is empty.")
    x, y = grid[:, 0], grid[:, 1]
    issue = float(getattr(product, "issue_price", 100.0))
    name = str(getattr(product, "product", "Structured note"))
    fair = getattr(product, "fair_value", None)
    spread = getattr(product, "underlying", "") == "CMS 10y-2y"     # the page plots this grid in bp

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.9, pal)
        ax.plot(x, y, color=pal.accent, linewidth=1.7,
                label="만기 지급액 (액면 100당)" if ko else "Payoff at maturity (per 100)")
        ax.axhline(issue, color=pal.muted, linestyle="--", linewidth=1.0,
                   label=f"발행가 {issue:g}" if ko else f"Issue price {issue:g}")
        ax.fill_between(x, issue, y, where=y >= issue, color=pal.success, alpha=0.15,
                        interpolate=True)
        ax.fill_between(x, issue, y, where=y < issue, color=pal.error, alpha=0.15,
                        interpolate=True)
        if ko:
            ax.set_xlabel("실현 10년-2년 금리 스프레드 (bp)" if spread else "만기 시 기초자산 가격")
        else:
            ax.set_xlabel("Underlying at maturity")
        ax.set_ylabel("액면 100당" if ko else "per 100")
        _legend(ax, pal)
        if ko:
            title = _product_ko(name) + (f" — 공정가치 {fair:.2f} / 발행가 {issue:g}" if fair is not None else "")
        else:
            title = name + (f" — fair {fair:.2f} vs issue {issue:g}" if fair is not None else "")
        ax.set_title(title, fontsize=10, loc="left")
        _reading(fig,
                 meaning=("만기에 기초자산이 어느 수준일 때 액면 100당 얼마를 돌려받는지(실선)를 발행가(점선)와 비교합니다.",
                          "What the note pays at maturity per 100 of face (solid line) for each level of the "
                          "underlying, against the issue price (dashed line)."),
                 look=("실선이 발행가 점선 위에 있는 구간(초록 음영)과 아래에 있는 구간(빨간 음영), 그리고 선이 꺾이는 "
                       "지점(행사가격)을 보세요. 제목에는 모형 공정가치와 발행가가 있습니다.",
                       "Find where the solid line is above the issue price (green shading) and below it (red "
                       "shading), and where the line bends (the strike). The title gives the model fair value "
                       "and the issue price."),
                 interpret=("초록 음영 구간에서 만기를 맞으면 발행가보다 많이, 빨간 음영 구간이면 적게 돌려받습니다. "
                            "공정가치가 발행가보다 낮은 만큼은 이 모형 기준으로 투자자가 발행 시점에 부담하는 몫(발행 마진 "
                            "등)입니다.",
                            "Ending in the green zone pays back more than the issue price, in the red zone less. "
                            "The amount by which fair value is below the issue price is, on this model, what the "
                            "buyer gives up at issue (margin and costs)."),
                 limit=("만기 시점의 지급 구조만 보여 주며, 그 수준에 도달할 확률이나 중도 매도 가격은 알려 주지 않습니다. "
                        "발행사 신용 위험은 반영하지 않았습니다. 수익 전망이 아닙니다.",
                        "Only the payoff at maturity: it does not tell how likely each level is or what the note "
                        "would sell for before maturity. Issuer credit risk is not included. Not a return "
                        "forecast."))
        return fig

    return _localized(build)


def rate_fan_chart(sim: RateSimResult) -> ft.Control:
    t = sim.times
    name = _RATE_MODELS.get(sim.model, sim.model)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 3.0, pal)
        ax.fill_between(t, sim.fan[5] * 100, sim.fan[95] * 100, color=pal.accent, alpha=0.16,
                        label="경로 90% 범위 (5–95%)" if ko else "5–95%")
        ax.fill_between(t, sim.fan[25] * 100, sim.fan[75] * 100, color=pal.accent, alpha=0.30,
                        label="경로 50% 범위 (25–75%)" if ko else "25–75%")
        ax.plot(t, sim.fan[50] * 100, color=pal.accent, linewidth=1.6, label="중앙값" if ko else "Median")
        if sim.model != "hull_white":          # HW's theta is a regression mean, not a level
            ax.axhline(sim.params.theta * 100, color=pal.muted, linestyle=":", linewidth=1.0,
                       label=(f"장기 평균 {sim.params.theta * 100:.2f}%" if ko else
                              f"Long-run mean {sim.params.theta * 100:.2f}%"))
        if sim.threshold is not None:
            ax.axhline(sim.threshold * 100, color=pal.error, linestyle="--", linewidth=1.0,
                       label=(f"기준 금리 {sim.threshold * 100:.2f}% (기간 끝 초과 비율 {sim.prob_above * 100:.0f}%)"
                              if ko else f"Threshold {sim.threshold * 100:.2f}% "
                                         f"(P above {sim.prob_above * 100:.0f}%)"))
        ax.set_xlabel("경과 기간 (년)" if ko else "Years")
        ax.set_ylabel("단기금리 (%)" if ko else "%")
        _legend_below(fig, pal, ax)
        if ko:
            title = (f"{name} 단기금리 시뮬레이션 — 경로 {sim.n_paths:,}개, {sim.horizon:g}년, 기간 끝 평균 "
                     f"{sim.mean_terminal * 100:.2f}% [{sim.p05 * 100:.2f}%, {sim.p95 * 100:.2f}%]")
        else:
            title = (f"{sim.model} — {sim.n_paths:,} paths, {sim.horizon:g}y; terminal mean "
                     f"{sim.mean_terminal * 100:.2f}% [{sim.p05 * 100:.2f}%, {sim.p95 * 100:.2f}%]")
        ax.set_title(title, fontsize=10, loc="left")
        _reading(fig,
                 meaning=("과거 단기금리로 추정한 모형이 만든 미래 단기금리 경로들의 분포입니다. 옅은 띠에 경로의 90%, "
                          "진한 띠에 50%가 들어가고 가운데 선은 중앙값입니다. 제목의 대괄호는 기간 끝 금리의 5%·95% "
                          "분위수입니다.",
                          "The spread of future short-rate paths from a model fitted to past short rates. The "
                          "light band holds 90% of the paths, the dark band 50%, and the middle line is the median. "
                          "The square brackets in the title are the 5th and 95th percentiles of the final rate."),
                 look=("시간이 지나면서 띠가 얼마나 넓어지는지, 중앙값이 장기 평균 점선 쪽으로 다가가는지, 빨간 점선(기준 "
                       "금리)이 띠의 어디에 있는지 보세요.",
                       "See how fast the bands widen, whether the median drifts toward the dotted long-run mean, "
                       "and where the red dashed threshold sits within the bands."),
                 interpret=("띠가 넓을수록 모형이 보는 금리의 불확실성이 큽니다. 범례의 초과 비율은 기간 끝에 기준 금리를 "
                            "넘은 경로의 비율로, 모형 안에서만 의미가 있습니다.",
                            "Wider bands mean more rate uncertainty in the model. The share above the threshold in "
                            "the legend is the fraction of paths ending above it, meaningful only inside the "
                            "model."),
                 limit=("과거 데이터로 추정한 모형의 시뮬레이션이며 금리 전망이 아닙니다. 모형이나 추정 기간이 바뀌면 범위와 "
                        "비율도 바뀝니다.",
                        "A simulation from a model fitted to past data, not a rate forecast. Another model or "
                        "fitting window gives other bands and shares."))
        return fig

    return _localized(build)


def horizon_pv_hist(hpv: HorizonPV) -> ft.Control:
    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(7.5, 2.6, pal)
        ax.hist(hpv.pvs, bins=40, color=pal.accent, alpha=0.85, edgecolor=pal.surface)
        ax.axvline(hpv.mean, color=pal.text, linewidth=1.2,
                   label=f"평균 {hpv.mean:,.0f}" if ko else f"Mean {hpv.mean:,.0f}")
        ax.axvline(hpv.p05, color=pal.error, linewidth=1.2, linestyle="--",
                   label=f"5% 분위수 {hpv.p05:,.0f}" if ko else f"p05 {hpv.p05:,.0f}")
        ax.axvline(hpv.p95, color=pal.success, linewidth=1.2, linestyle="--",
                   label=f"95% 분위수 {hpv.p95:,.0f}" if ko else f"p95 {hpv.p95:,.0f}")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))   # grouped values, no 1e6 offset
        _legend_below(fig, pal, ax)
        ax.set_title(f"보유기간 끝 평가가치 분포 — 경로 {hpv.pvs.size}개, VaR95 {hpv.var95:,.0f}, "
                     f"CVaR95 {hpv.cvar95:,.0f}" if ko else
                     f"Horizon PV over {hpv.pvs.size} paths — VaR95 {hpv.var95:,.0f}, "
                     f"CVaR95 {hpv.cvar95:,.0f}", fontsize=10, loc="left")
        _reading(fig,
                 meaning=("금리 시뮬레이션의 경로마다 보유기간 끝에서 상품(채권·스왑)을 다시 평가한 가치를 모은 "
                          "분포입니다.",
                          "The value of the instrument (bond or swap) revalued at the end of the horizon on every "
                          "simulated rate path, collected into a histogram."),
                 look=("평균 실선과 5%·95% 분위수 점선의 위치, 그리고 막대가 왼쪽(낮은 가치)으로 길게 늘어지는지 "
                       "보세요.",
                       "Look at the mean line, the 5th and 95th percentile dashed lines, and whether the bars "
                       "trail off to the left (low values)."),
                 interpret=("5% 분위수가 낮을수록 나쁜 금리 경로에서 가치가 많이 줄어듭니다. 제목의 VaR95는 오늘 가치 대비 "
                            "95% 수준의 손실, CVaR95는 그보다 나쁜 5% 경로의 평균 손실입니다.",
                            "The lower the 5th percentile, the more value is lost on bad rate paths. VaR95 in the "
                            "title is the loss against today's value at the 95% level; CVaR95 is the average loss "
                            "on the worst 5% of paths."),
                 limit=("단기금리 모형의 시뮬레이션에서 나온 분포이며 실제 손실 한도나 확률을 보장하지 않습니다. 모형에 "
                        "없는 위험(신용·유동성)은 빠져 있습니다.",
                        "A distribution from a short-rate model simulation; it guarantees no actual loss limit or "
                        "probability. Risks outside the model (credit, liquidity) are left out."))
        return fig

    return _localized(build)


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
        product="Principal-protected note (FX)", issue_price=100.0, fair_value=98.5,
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
