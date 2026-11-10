"""Charts for the version-3 surfaces (Derivatives, ETF, Crypto, Strategy Lab),
rendered with the same matplotlib-to-data-URI path as `qcharts`."""
from __future__ import annotations

import re
from typing import Optional, Sequence

import numpy as np
import flet as ft

from core.theme import active
from ui.qcharts import _fig, _ko, _localized, _reading, _thin_dates, _to_image, plt


def lines_chart(dates: Sequence[str], series: dict[str, np.ndarray], *, title: str = "", ylabel: str = "",
                hlines: Optional[dict[str, float]] = None, height: float = 3.2, pct: bool = False) -> ft.Control:
    pal = active()
    fig, ax = _fig(9.5, height, pal)
    colours = [pal.accent, pal.text, pal.success, pal.error, pal.muted]
    x = np.arange(len(dates))
    for i, (label, y) in enumerate(series.items()):
        y = np.asarray(y, dtype=float)
        ax.plot(x[-y.size:], y, color=colours[i % len(colours)], linewidth=1.2, label=label)
    for label, v in (hlines or {}).items():
        ax.axhline(v, color=pal.muted, linewidth=0.8, linestyle="--")
        ax.text(x[0] if len(x) else 0, v, f" {label}", color=pal.muted, fontsize=7, va="bottom")
    idx, labels = _thin_dates(list(dates))
    ax.set_xticks(idx); ax.set_xticklabels(labels, rotation=0)
    if pct:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
    ax.set_title(title, fontsize=10, loc="left"); ax.set_ylabel(ylabel, fontsize=8)
    ax.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=pal.text)
    return _to_image(fig)


def smile_chart(points, fit=None, F: float = 0.0, *, title: str = "Implied volatility") -> ft.Control:
    """App IV (Black-76 inversion) vs the exchange's IV per strike, with the SVI curve."""
    from core.ficc.equity_deriv import svi_vol
    pal = active()
    fig, ax = _fig(9.5, 3.4, pal)
    ks = np.array([p.strike for p in points])
    ax.scatter(ks, [p.iv * 100 for p in points], s=14, color=pal.accent, label="app (Black-76 on mids)", zorder=3)
    ex = [(p.strike, p.iv_exchange * 100) for p in points if p.iv_exchange]
    if ex:
        ax.scatter([e[0] for e in ex], [e[1] for e in ex], s=14, marker="x", color=pal.text, label="exchange IV", zorder=3)
    if fit is not None and F > 0 and ks.size:
        grid = np.linspace(ks.min(), ks.max(), 120)
        ax.plot(grid, svi_vol(fit, np.log(grid / F)) * 100, color=pal.success, linewidth=1.3,
                label=f"SVI (ρ {fit.rho:+.2f}, RMSE {fit.rmse_volpts:.2f} pts)")
    if F > 0:
        ax.axvline(F, color=pal.muted, linewidth=0.8, linestyle="--")
        ax.text(F, ax.get_ylim()[1], " F", color=pal.muted, fontsize=7, va="top")
    ax.set_title(title, fontsize=10, loc="left"); ax.set_xlabel("strike", fontsize=8); ax.set_ylabel("vol (%)", fontsize=8)
    ax.legend(loc="upper right", fontsize=7, frameon=False, labelcolor=pal.text)
    return _to_image(fig)


def density_chart(rnd: dict, *, p_samples: Optional[np.ndarray] = None, title: str = "Risk-neutral density") -> ft.Control:
    pal = active()
    fig, ax = _fig(9.5, 3.0, pal)
    K, f = rnd["strikes"], rnd["density"]
    ax.plot(K, f, color=pal.accent, linewidth=1.3, label=f"f_Q (∫ = {rnd['integral']:.3f})")
    ax.axvline(rnd["F"], color=pal.muted, linewidth=0.8, linestyle="--")
    if p_samples is not None and len(p_samples) > 50:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(np.asarray(p_samples, dtype=float))
        ax.plot(K, kde(K), color=pal.success, linewidth=1.1, linestyle="-", label="f_P (GARCH-t terminal)")
    ax.set_title(title, fontsize=10, loc="left"); ax.set_xlabel("terminal level", fontsize=8)
    ax.legend(loc="upper right", fontsize=7, frameon=False, labelcolor=pal.text)
    return _to_image(fig)


_EQUITY_TITLES_KO = (   # English title the callers pass -> Korean title (callers may also pass title_ko)
    (re.compile(r"^(?P<name>.+): out-of-sample equity$"), "{name}: 표본 외(OOS) 누적 성과"),
    (re.compile(r"^10-month trend switch vs buy-and-hold \((?P<bp>[\d.]+) bp per side\)$"),
     "10개월 추세 전환 전략과 매수 후 보유 비교 (편도 비용 {bp}bp)"),
    (re.compile(r"^Equity$"), "누적 성과"),
)


def _equity_title_ko(title: str) -> str:
    for pattern, korean in _EQUITY_TITLES_KO:
        m = pattern.match(title)
        if m:
            return korean.format(**m.groupdict())
    return title


EQUITY_READING = {
    "meaning": ("처음에 1을 넣었다면 전략(진한 선)과 비교 기준(회색 선)이 각각 얼마가 되었는지를 날짜별로 보여 줍니다. "
                "Strategy Lab에서는 전략을 정하는 데 쓰지 않은 기간(표본 외, OOS)의 성과입니다.",
                "What 1 invested at the start became, day by day, for the strategy (dark line) and the benchmark "
                "(grey line). In the Strategy Lab this is the out-of-sample period, not used to choose the strategy."),
    "look": ("오른쪽 끝에서 두 선의 높이를 비교하고, 중간에 크게 떨어진 구간(낙폭)이 어디였는지 보세요. 점선 1.0이 "
             "출발점입니다.",
             "Compare the two lines at the right end, and find the deep dips along the way (drawdowns). The dashed "
             "1.0 line is the starting point."),
    "interpret": ("진한 선이 회색 선보다 위에서 끝나면 같은 기간 비교 기준보다 성과가 좋았습니다. 1.2는 20% 이익, "
                  "0.9는 10% 손실입니다. 선이 덜 출렁일수록 위험이 작았습니다.",
                  "Ending above the grey line means the strategy beat the benchmark over the period. 1.2 is a 20% "
                  "gain, 0.9 a 10% loss. A smoother line means less risk taken."),
    "limit": ("과거 데이터로 다시 계산한 결과이며 미래 성과를 보장하지 않습니다. 좋은 전략인지는 이 선 하나가 아니라 "
              "검증 판정(PASS / REVISE / REJECT)과 함께 판단하세요.",
              "Recomputed on past data; it guarantees no future result. Judge the strategy with its validation "
              "verdict (PASS / REVISE / REJECT), not this line alone."),
}


def equity_chart(dates: Sequence[str], equity: np.ndarray, bench: Optional[np.ndarray] = None, *,
                 title: str = "Equity", labels: tuple[str, str] = ("strategy", "benchmark"),
                 title_ko: Optional[str] = None, labels_ko: Optional[tuple[str, str]] = None) -> ft.Control:
    """Strategy vs benchmark growth of 1. `title_ko` / `labels_ko` give the Korean wording; without
    them the known caller titles and the default labels are translated, anything else is shown as given."""
    eq = np.asarray(equity, dtype=float)
    b = np.asarray(bench, dtype=float) if bench is not None else None
    if labels_ko is None:
        labels_ko = ("전략", "비교 기준") if tuple(labels) == ("strategy", "benchmark") else tuple(labels)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        names = labels_ko if ko else labels
        fig, ax = _fig(9.5, 3.2, pal)
        x = np.arange(len(dates))
        ax.axhline(1.0, color=pal.border, linewidth=0.8, linestyle="--")
        ax.plot(x[-eq.size:], eq, color=pal.accent, linewidth=1.3, label=names[0])
        if b is not None:
            ax.plot(x[-b.size:], b, color=pal.muted, linewidth=1.0, label=names[1])
        idx, lab = _thin_dates(list(dates))
        ax.set_xticks(idx); ax.set_xticklabels(lab)
        ax.set_ylabel("1에서 시작한 누적 성과" if ko else "Growth of 1", fontsize=8)
        ax.set_title((title_ko or _equity_title_ko(title)) if ko else title, fontsize=10, loc="left")
        ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=pal.text)
        _reading(fig, **EQUITY_READING)
        return fig

    return _localized(build)
def bars_chart(labels: Sequence[str], values: Sequence[float], *, title: str = "", vmax: float = 100.0,
               annotate: Optional[Sequence[str]] = None) -> ft.Control:
    pal = active()
    fig, ax = _fig(9.5, 0.45 * len(labels) + 0.8, pal)
    y = np.arange(len(labels))
    vals = [0.0 if v is None or not np.isfinite(v) else float(v) for v in values]
    colours = [pal.success if v >= 70 else pal.accent if v >= 40 else pal.error for v in vals]
    ax.barh(y, vals, color=colours, height=0.6)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8, color=pal.text)
    ax.set_xlim(0, vmax); ax.invert_yaxis()
    if annotate:
        for i, txt in enumerate(annotate):
            ax.text(min(vals[i] + 1, vmax * 0.98), i, txt, va="center", fontsize=7, color=pal.muted,
                    ha="left" if vals[i] < vmax * 0.6 else "right")
    ax.set_title(title, fontsize=10, loc="left")
    return _to_image(fig)


def premium_chart(dates: Sequence[str], price: np.ndarray, nav: np.ndarray, premium_pct: np.ndarray,
                  *, title: str = "Price vs NAV") -> ft.Control:
    pal = active()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 4.2), dpi=110, sharex=True,
                                 gridspec_kw={"height_ratios": [2, 1]})
    fig.patch.set_facecolor(pal.surface)
    from ui.qcharts import _style
    for ax in (a1, a2):
        _style(ax, pal)
    x = np.arange(len(dates))
    a1.plot(x, price, color=pal.accent, linewidth=1.2, label="price")
    a1.plot(x, nav, color=pal.text, linewidth=0.9, linestyle="--", label="NAV")
    a1.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=pal.text)
    a1.set_title(title, fontsize=10, loc="left")
    a2.bar(x, premium_pct, color=[pal.success if v >= 0 else pal.error for v in premium_pct], width=1.0)
    a2.axhline(0, color=pal.muted, linewidth=0.6)
    a2.set_ylabel("premium %", fontsize=8)
    idx, lab = _thin_dates(list(dates))
    a2.set_xticks(idx); a2.set_xticklabels(lab)
    return _to_image(fig)
