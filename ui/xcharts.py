"""Charts for the version-3 surfaces (Derivatives, ETF, Crypto, Strategy Lab),
rendered with the same matplotlib-to-data-URI path as `qcharts`. Every chart is
drawn in the page language (`_localized`) and carries its own reading guidance
(`_reading`); the data, scales and palette are the same in Korean and English."""
from __future__ import annotations

import re
from typing import Optional, Sequence

import numpy as np
import flet as ft

from core.theme import active
from ui.qcharts import _fig, _ko, _localized, _reading, _thin_dates, plt


def _title_ko(title: str, patterns) -> str:
    """Korean title for an English caller title: the first matching (regex, Korean format) wins;
    an unknown title is shown as given."""
    for pattern, korean in patterns:
        m = pattern.fullmatch(title)
        if m:
            return korean.format(**m.groupdict())
    return title


# Titles and series names the pages pass (ui/crypto_page.py) -> Korean; callers may also pass
# title_ko / labels_ko / ylabel_ko. Tickers (BTCUSDT) stay as they are.
_LINES_TITLES_KO = (
    (re.compile(r"Kimchi premium \(Upbit KRW-BTC vs Binance × USD/KRW\)"),
     "김치 프리미엄 (업비트 KRW-BTC 대 바이낸스 × 달러/원 환율)"),
    (re.compile(r"Perpetual funding, 7-day mean annualised"), "무기한 선물 펀딩비 — 7일 평균, 연율 환산"),
    (re.compile(r"(?P<ticker>\S+) with 50/200-day averages"), "{ticker}와 50일·200일 이동평균"),
)
_LINES_LABELS_KO = {"kimchi premium %": "김치 프리미엄 (%)", "funding (ann. %)": "펀딩비 (연율 %)",
                    "SMA50": "50일 이동평균 (SMA50)", "SMA200": "200일 이동평균 (SMA200)"}

LINES_READING = {
    "meaning": ("날짜별 값을 선으로 그린 시계열입니다. 범례의 이름이 각 선입니다.",
                "Values over time, one line per series named in the legend."),
    "look": ("오른쪽 끝(가장 최근)의 값과, 점선 기준선이 있으면 그 위인지 아래인지를 보세요.",
             "Look at the right end (the latest value) and, where a dashed reference line is drawn, whether "
             "the line is above or below it."),
    "interpret": ("선이 기준선보다 위면 그 값보다 크고 아래면 작습니다. 여러 선은 같은 축에서 비교합니다.",
                  "Above the reference line the value is larger, below it smaller. Several lines share one "
                  "axis."),
    "limit": ("관측된 과거 값이며 앞으로를 예측하지 않습니다. 차트가 수익 전망이나 검증 통과를 뜻하지 않습니다.",
              "Observed past values, not a forecast. A chart is not a return forecast or a validation pass."),
}
_LINES_READINGS = {
    "Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)": {
        "meaning": ("업비트의 원화 비트코인 가격이 바이낸스 달러 가격을 원화로 환산한 값보다 몇 % 비싼지(김치 프리미엄)를 "
                    "날짜별로 보여 줍니다.",
                    "How many percent the won price of bitcoin on Upbit is above the Binance dollar price converted "
                    "into won (the kimchi premium), day by day."),
        "look": ("선이 0 점선 위인지 아래인지, 최근 값이 지난 범위에 비해 높은지 낮은지를 보세요.",
                 "Whether the line is above or below the dashed 0, and whether the latest value is high or low "
                 "against the past range."),
        "interpret": ("0보다 위면 국내 가격이 해외보다 비싸고, 아래면 쌉니다(역프리미엄). 프리미엄이 벌어졌다가 0 쪽으로 "
                      "돌아오는 속도는 화면의 반감기 수치로 확인하세요.",
                      "Above 0 the domestic price is dearer than abroad, below 0 cheaper (a reverse premium). How "
                      "fast a gap closes back toward 0 is the half-life shown on the page."),
        "limit": ("국내외 거래소 종가와 환율로 계산한 값이며 수수료·송금 제한·세금은 빠져 있습니다. 가격 예측이나 차익거래 "
                  "기회를 뜻하지 않습니다.",
                  "Computed from exchange closes and the exchange rate; fees, transfer limits and taxes are left "
                  "out. It is not a forecast or an arbitrage opportunity."),
    },
    "Perpetual funding, 7-day mean annualised": {
        "meaning": ("바이낸스 비트코인 무기한 선물의 펀딩비를 7일 평균으로 고르게 한 뒤 연율로 환산한 값입니다.",
                    "The funding rate of the Binance bitcoin perpetual future, smoothed over 7 days and annualised."),
        "look": ("선이 0 점선 위인지 아래인지와 최근 급등·급락 구간을 보세요.",
                 "Whether the line is above or below the dashed 0, and recent spikes or drops."),
        "interpret": ("양수면 매수(롱) 포지션이 매도(숏) 포지션에 펀딩비를 내고 있다는 뜻으로 선물 매수 수요가 많다는 "
                      "신호이고, 음수면 그 반대입니다.",
                      "Positive means long positions pay shorts, a sign of strong demand to be long the future; "
                      "negative is the reverse."),
        "limit": ("과거 펀딩비이며 앞으로의 펀딩비나 가격을 예측하지 않습니다. 실제 캐리 수익은 거래 비용과 가격 변동에 "
                  "따라 달라집니다.",
                  "Past funding only, not a forecast of funding or price. Any real carry depends on trading "
                  "costs and price moves."),
    },
}
_SMA_READING = {
    "meaning": ("일별 종가(실선)와 50일·200일 단순이동평균을 함께 그린 가격 흐름입니다.",
                "Daily closes with the 50- and 200-day simple moving averages."),
    "look": ("가격이 이동평균선 위에 있는지 아래에 있는지, 50일선이 200일선 위에 있는지를 보세요.",
             "Whether the price is above or below the averages, and whether the 50-day average is above the "
             "200-day one."),
    "interpret": ("가격이 이동평균 위에 있으면 최근 가격이 그 기간 평균보다 높다는 뜻입니다. 50일선이 200일선을 넘어서는 "
                  "것은 이미 일어난 상승을 요약할 뿐입니다.",
                  "A price above an average means recent prices exceed that period's mean. A 50-over-200 cross "
                  "summarises a rise that has already happened."),
    "limit": ("지나간 가격만 보여 주며 앞으로의 방향을 예측하지 않습니다. 합성 데이터이면 실제 시세가 아닙니다.",
              "Past prices only, not a forecast. Synthetic data means these are not market prices."),
}


def _lines_reading(title: str) -> dict:
    if title in _LINES_READINGS:
        return _LINES_READINGS[title]
    return _SMA_READING if title.endswith("with 50/200-day averages") else LINES_READING


def lines_chart(dates: Sequence[str], series: dict[str, np.ndarray], *, title: str = "", ylabel: str = "",
                hlines: Optional[dict[str, float]] = None, height: float = 3.2, pct: bool = False,
                title_ko: Optional[str] = None, ylabel_ko: Optional[str] = None,
                labels_ko: Optional[dict[str, str]] = None, reading: Optional[dict] = None) -> ft.Control:
    """Date-indexed lines. The Korean wording comes from `title_ko` / `ylabel_ko` / `labels_ko`
    ({English series or reference-line name: Korean}); without them the titles and names the pages
    pass are translated and anything else is shown as given. `reading` overrides the side-panel
    guidance ({'meaning'|'look'|'interpret'|'limit': (Korean, English)})."""
    names_ko = {**_LINES_LABELS_KO, **(labels_ko or {})}
    guidance = reading or _lines_reading(title)
    x = np.arange(len(dates))
    lines = [(label, np.asarray(y, dtype=float)) for label, y in series.items()]

    def build(ctx):
        ko, pal = _ko(ctx), active()
        word = (lambda s: names_ko.get(s, s)) if ko else (lambda s: s)
        fig, ax = _fig(9.5, height, pal)
        colours = [pal.accent, pal.text, pal.success, pal.error, pal.muted]
        for i, (label, y) in enumerate(lines):
            ax.plot(x[-y.size:], y, color=colours[i % len(colours)], linewidth=1.2, label=word(label))
        for label, v in (hlines or {}).items():
            ax.axhline(v, color=pal.muted, linewidth=0.8, linestyle="--")
            ax.text(x[0] if len(x) else 0, v, f" {word(label)}", color=pal.muted, fontsize=7, va="bottom")
        idx, labels = _thin_dates(list(dates))
        ax.set_xticks(idx); ax.set_xticklabels(labels, rotation=0)
        if pct:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
        ax.set_title((title_ko or _title_ko(title, _LINES_TITLES_KO)) if ko else title, fontsize=10, loc="left")
        ax.set_ylabel((ylabel_ko or word(ylabel)) if ko else ylabel, fontsize=8)
        ax.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=pal.text)
        _reading(fig, **guidance)
        return fig

    return _localized(build)


_SMILE_TITLES_KO = (
    (re.compile(r"Implied volatility"), "내재변동성"),
    (re.compile(r"(?P<underlying>.+) (?P<expiry>\S+) smile"), "{underlying} {expiry} 변동성 스마일"),
)
SMILE_READING = {
    "meaning": ("행사가격별 옵션 내재변동성입니다. 점은 앱이 중간호가에서 Black-76으로 역산한 값, x 표시는 거래소가 발표한 "
                "값, 선은 그 점들에 맞춘 SVI 곡선입니다.",
                "Implied volatility by strike. Dots are the app's Black-76 inversion of the mid quotes, crosses the "
                "exchange's published values, and the line is the SVI curve fitted to them."),
    "look": ("점과 x 표시가 서로 가까운지, SVI 선이 점들을 잘 따라가는지, F 점선(선도가격) 왼쪽과 오른쪽의 높이 차이를 "
             "보세요. 범례의 RMSE는 적합 오차입니다.",
             "Whether dots and crosses sit close together, how well the SVI line follows the dots, and the height "
             "difference left and right of the dashed F (the forward). RMSE in the legend is the fit error."),
    "interpret": ("왼쪽(낮은 행사가격)이 높게 올라가면 하락에 대비하는 풋옵션이 비싸게 거래된다는 뜻으로 주가지수 옵션에서 "
                  "흔한 모양입니다. 앱 값과 거래소 값이 크게 다르면 호가가 얇거나 오래된 행사가격일 수 있습니다.",
                  "A left side (low strikes) rising high means puts that insure against a fall trade dear, the "
                  "usual shape for index options. A large gap between app and exchange values can mean thin or "
                  "stale quotes at that strike."),
    "limit": ("한 시점의 호가로 계산한 값이며 지수 방향이나 미래 변동성을 예측하지 않습니다. 합성 보드이면 시장 호가가 "
              "아닙니다.",
              "Computed from quotes at one moment; it does not forecast the index or future volatility. A "
              "synthetic board is not market quotes."),
}


def smile_chart(points, fit=None, F: float = 0.0, *, title: str = "Implied volatility",
                title_ko: Optional[str] = None) -> ft.Control:
    """App IV (Black-76 inversion) vs the exchange's IV per strike, with the SVI curve."""
    from core.ficc.equity_deriv import svi_vol
    ks = np.array([p.strike for p in points])
    ivs = [p.iv * 100 for p in points]
    ex = [(p.strike, p.iv_exchange * 100) for p in points if p.iv_exchange]
    curve = None
    if fit is not None and F > 0 and ks.size:
        grid = np.linspace(ks.min(), ks.max(), 120)
        curve = (grid, svi_vol(fit, np.log(grid / F)) * 100)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(9.5, 3.4, pal)
        ax.scatter(ks, ivs, s=14, color=pal.accent, zorder=3,
                   label="앱 계산 (중간호가에 Black-76)" if ko else "app (Black-76 on mids)")
        if ex:
            ax.scatter([e[0] for e in ex], [e[1] for e in ex], s=14, marker="x", color=pal.text, zorder=3,
                       label="거래소 내재변동성" if ko else "exchange IV")
        if curve is not None:
            ax.plot(*curve, color=pal.success, linewidth=1.3,
                    label=(f"SVI 적합 (ρ {fit.rho:+.2f}, 오차 RMSE {fit.rmse_volpts:.2f}%p)" if ko else
                           f"SVI (ρ {fit.rho:+.2f}, RMSE {fit.rmse_volpts:.2f} pts)"))
        if F > 0:
            ax.axvline(F, color=pal.muted, linewidth=0.8, linestyle="--")
            ax.text(F, ax.get_ylim()[1], " F (선도가격)" if ko else " F", color=pal.muted, fontsize=7, va="top")
        ax.set_title((title_ko or _title_ko(title, _SMILE_TITLES_KO)) if ko else title, fontsize=10, loc="left")
        ax.set_xlabel("행사가격" if ko else "strike", fontsize=8)
        ax.set_ylabel("변동성 (%)" if ko else "vol (%)", fontsize=8)
        ax.legend(loc="upper right", fontsize=7, frameon=False, labelcolor=pal.text)
        _reading(fig, **SMILE_READING)
        return fig

    return _localized(build)


DENSITY_READING = {
    "meaning": ("옵션 가격(SVI 스마일)에서 거꾸로 계산한, 만기 때 기초자산 수준에 대한 위험중립 확률밀도(f_Q)입니다. 범례에 "
                "f_P가 있으면 과거 수익률로 추정한 GARCH-t 모형이 만든 만기 분포입니다.",
                "The risk-neutral density (f_Q) of the underlying's level at expiry, backed out of option prices "
                "(the SVI smile). Where the legend shows f_P, that is the expiry distribution of a GARCH-t model "
                "fitted to past returns."),
    "look": ("봉우리의 위치와 왼쪽 꼬리의 두께를 보세요. 점선은 선도가격 F입니다. 범례의 적분 값이 1에 가까워야 밀도가 "
             "제대로 계산된 것입니다.",
             "Look at where the peak sits and how fat the left tail is. The dashed line is the forward F. The "
             "integral in the legend should be close to 1 for a well-formed density."),
    "interpret": ("f_Q의 왼쪽 꼬리가 f_P보다 두꺼우면 옵션 시장이 하락 위험에 보험료를 더 얹어 가격을 매기고 있다는 "
                  "뜻입니다.",
                  "A left tail of f_Q fatter than f_P means option prices carry an extra premium for downside "
                  "risk."),
    "limit": ("위험중립 밀도는 시장이 믿는 실제 확률이 아니라 위험 프리미엄이 섞인 가격의 표현이며, 지수 방향을 예측하지 "
              "않습니다.",
              "A risk-neutral density is not the market's real-world probability but prices with risk premia "
              "mixed in; it does not forecast the index."),
}


def density_chart(rnd: dict, *, p_samples: Optional[np.ndarray] = None, title: str = "Risk-neutral density",
                  title_ko: Optional[str] = None) -> ft.Control:
    K, f = rnd["strikes"], rnd["density"]
    f_p = None
    if p_samples is not None and len(p_samples) > 50:
        from scipy.stats import gaussian_kde
        f_p = gaussian_kde(np.asarray(p_samples, dtype=float))(K)

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, ax = _fig(9.5, 3.0, pal)
        ax.plot(K, f, color=pal.accent, linewidth=1.3,
                label=(f"위험중립 밀도 f_Q (적분 {rnd['integral']:.3f})" if ko else
                       f"f_Q (∫ = {rnd['integral']:.3f})"))
        ax.axvline(rnd["F"], color=pal.muted, linewidth=0.8, linestyle="--")
        if f_p is not None:
            ax.plot(K, f_p, color=pal.success, linewidth=1.1, linestyle="-",
                    label="GARCH-t 모형 만기 분포 f_P" if ko else "f_P (GARCH-t terminal)")
        default = title == "Risk-neutral density"
        ax.set_title((title_ko or ("위험중립 확률밀도" if default else title)) if ko else title,
                     fontsize=10, loc="left")
        ax.set_xlabel("만기 시 기초자산 수준" if ko else "terminal level", fontsize=8)
        ax.legend(loc="upper right", fontsize=7, frameon=False, labelcolor=pal.text)
        _reading(fig, **DENSITY_READING)
        return fig

    return _localized(build)


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
                "전략 실험실에서는 전략을 정하는 데 쓰지 않은 기간(표본 외, OOS)의 성과입니다.",
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
                 title_ko: Optional[str] = None, labels_ko: Optional[tuple[str, str]] = None,
                 reading: Optional[dict] = None) -> ft.Control:
    """Strategy vs benchmark growth of 1. `title_ko` / `labels_ko` give the Korean wording; without
    them the known caller titles and the default labels are translated, anything else is shown as given.
    `reading` replaces the side-panel guidance ({'meaning'|'look'|'interpret'|'limit': (Korean, English)});
    the default describes the Strategy Lab's out-of-sample equity."""
    guidance = reading or EQUITY_READING
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
        _reading(fig, **guidance)
        return fig

    return _localized(build)


def _bars_reading(vmax: float) -> dict:
    return {
        "meaning": (f"항목마다 0부터 {vmax:g}까지의 점수를 가로 막대로 비교합니다.",
                    f"Each item's score on a 0 to {vmax:g} scale, as horizontal bars."),
        "look": ("막대 길이와 색을 보세요. 초록은 70 이상, 중간색은 40 이상 70 미만, 빨강은 40 미만입니다. 막대 옆 글자는 "
                 "보조 설명입니다.",
                 "Read the bar lengths and colours: green is 70 or more, the middle colour 40 to under 70, red under "
                 "40. Text beside a bar is a supporting note."),
        "interpret": ("막대가 길수록 점수가 높습니다. 같은 축에서 항목끼리 비교하세요.",
                      "A longer bar is a higher score; compare items on the same axis."),
        "limit": ("점수는 정해진 규칙으로 계산한 요약 값이며 수익 전망이나 검증 통과를 뜻하지 않습니다.",
                  "A score is a rule-based summary; it is not a return forecast or a validation pass."),
    }


def bars_chart(labels: Sequence[str], values: Sequence[float], *, title: str = "", vmax: float = 100.0,
               annotate: Optional[Sequence[str]] = None, title_ko: Optional[str] = None,
               labels_ko: Optional[Sequence[str]] = None, annotate_ko: Optional[Sequence[str]] = None) -> ft.Control:
    """Score bars on 0..vmax. `title_ko` / `labels_ko` / `annotate_ko` give the Korean wording; without
    them the English text is shown as given."""
    vals = [0.0 if v is None or not np.isfinite(v) else float(v) for v in values]

    def build(ctx):
        ko, pal = _ko(ctx), active()
        names = list(labels_ko) if ko and labels_ko else list(labels)
        notes = annotate_ko if ko and annotate_ko else annotate
        fig, ax = _fig(9.5, 0.45 * len(labels) + 0.8, pal)
        y = np.arange(len(labels))
        colours = [pal.success if v >= 70 else pal.accent if v >= 40 else pal.error for v in vals]
        ax.barh(y, vals, color=colours, height=0.6)
        ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8, color=pal.text)
        ax.set_xlim(0, vmax); ax.invert_yaxis()
        if notes:
            for i, txt in enumerate(notes):
                ax.text(min(vals[i] + 1, vmax * 0.98), i, txt, va="center", fontsize=7, color=pal.muted,
                        ha="left" if vals[i] < vmax * 0.6 else "right")
        ax.set_title((title_ko or title) if ko else title, fontsize=10, loc="left")
        _reading(fig, **_bars_reading(vmax))
        return fig

    return _localized(build)


_PREMIUM_TITLES_KO = (
    (re.compile(r"Price vs NAV"), "시장가격과 순자산가치(NAV)"),
    (re.compile(r"(?P<code>.+) price vs NAV"), "{code} 시장가격과 순자산가치(NAV)"),
)
PREMIUM_READING = {
    "meaning": ("위 그림은 ETF의 시장 거래가격(실선)과 1주당 순자산가치(NAV, 점선), 아래 그림은 둘의 차이인 괴리율(%)입니다.",
                "Top: the ETF's market price (solid) and its net asset value per share (NAV, dashed). Bottom: the "
                "gap between them, the premium (%)."),
    "look": ("아래 막대가 0 위(초록, 할증)인지 아래(빨강, 할인)인지와 막대가 커지는 구간을 보세요.",
             "Whether the bottom bars are above 0 (green, premium) or below it (red, discount), and where they "
             "grow."),
    "interpret": ("괴리율이 양수면 ETF가 보유 자산 가치보다 비싸게, 음수면 싸게 거래된 것입니다. 0 근처에서 작게 움직일수록 "
                  "가격이 순자산가치를 잘 따라간 것입니다.",
                  "A positive premium means the ETF traded above the value of its holdings, a negative one below "
                  "it. Small moves around 0 mean the price tracked the NAV closely."),
    "limit": ("일별 종가 기준이며 장중 괴리율과 다를 수 있습니다. 괴리율이 줄어든다는 예측이나 매매 신호가 아닙니다.",
              "Based on daily closes; the intraday premium can differ. It is not a forecast that the gap will "
              "close or a trading signal."),
}


def premium_chart(dates: Sequence[str], price: np.ndarray, nav: np.ndarray, premium_pct: np.ndarray,
                  *, title: str = "Price vs NAV", title_ko: Optional[str] = None) -> ft.Control:
    from ui.qcharts import _style
    x = np.arange(len(dates))

    def build(ctx):
        ko, pal = _ko(ctx), active()
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 4.2), dpi=110, sharex=True,
                                     gridspec_kw={"height_ratios": [2, 1]})
        fig._qg_palette = pal
        fig.patch.set_facecolor(pal.surface)
        for ax in (a1, a2):
            _style(ax, pal)
        a1.plot(x, price, color=pal.accent, linewidth=1.2, label="시장가격" if ko else "price")
        a1.plot(x, nav, color=pal.text, linewidth=0.9, linestyle="--", label="순자산가치 (NAV)" if ko else "NAV")
        a1.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=pal.text)
        a1.set_title((title_ko or _title_ko(title, _PREMIUM_TITLES_KO)) if ko else title, fontsize=10, loc="left")
        a2.bar(x, premium_pct, color=[pal.success if v >= 0 else pal.error for v in premium_pct], width=1.0)
        a2.axhline(0, color=pal.muted, linewidth=0.6)
        a2.set_ylabel("괴리율 (%)" if ko else "premium %", fontsize=8)
        idx, lab = _thin_dates(list(dates))
        a2.set_xticks(idx); a2.set_xticklabels(lab)
        _reading(fig, **PREMIUM_READING)
        return fig

    return _localized(build)
