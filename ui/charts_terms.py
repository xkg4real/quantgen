"""Plain-language names for the macro sheet and small locale-aware chips (owner UI review, 2026-11-10).

The Macro page and the macro z-score chart share these names so a row reads the same in the
chart, the tiles and the table. Each entry is (Korean, English); the indicator code stays in
parentheses so the provider series can still be recognised. Nothing here computes a value:
the regime words describe the rule-based read of `core.ficc.macro` (descriptive read, not a
regime model, P19) and `regime_evidence` only re-reads the numbers the core already printed in
`Regime.summary`.
"""
from __future__ import annotations

import re

import flet as ft

from core.theme import active
from quantgen_desktop.rates_narrative import REGIMES
from ui.components import LocalText, chip, notice

# Indicator id -> (Korean name (code), English name (code)).
INDICATOR_NAMES: dict[str, tuple[str, str]] = {
    "DGS2": ("미 국채 2년 금리 (UST 2y)", "US Treasury 2-year yield (UST 2y)"),
    "DGS10": ("미 국채 10년 금리 (UST 10y)", "US Treasury 10-year yield (UST 10y)"),
    "DGS30": ("미 국채 30년 금리 (UST 30y)", "US Treasury 30-year yield (UST 30y)"),
    "T10Y2Y": ("장단기 금리차 10년−2년 (2s10s)", "10y minus 2y yield gap (2s10s)"),
    "DFII10": ("10년 실질금리 (TIPS)", "10-year real yield (TIPS)"),
    "T10YIE": ("10년 기대인플레이션 (BEI)", "10-year breakeven inflation (BEI)"),
    "SOFR": ("담보부 익일물 금리 (SOFR)", "Secured overnight rate (SOFR)"),
    "DFF": ("미 연방기금금리 (Fed funds)", "Fed funds rate (Fed funds)"),
    "BAMLC0A0CM": ("투자등급 회사채 스프레드 (IG OAS)", "Investment-grade credit spread (IG OAS)"),
    "BAMLH0A0HYM2": ("하이일드 스프레드 (HY OAS)", "High-yield credit spread (HY OAS)"),
    "DTWEXBGS": ("달러 지수 (Broad USD)", "Broad dollar index (Broad USD)"),
    "DEXUSEU": ("유로/달러 환율 (EUR/USD)", "Euro in dollars (EUR/USD)"),
    "DEXJPUS": ("달러/엔 환율 (USD/JPY)", "Dollar in yen (USD/JPY)"),
    "DEXKOUS": ("달러/원 환율 (USD/KRW)", "Dollar in won (USD/KRW)"),
    "VIXCLS": ("미국 주식 변동성 지수 (VIX)", "US equity volatility index (VIX)"),
    "DCOILWTICO": ("서부텍사스유 가격 (WTI)", "WTI crude oil (WTI)"),
    "ZN=F": ("미 10년 국채선물 (ZN)", "10-year Treasury note future (ZN)"),
    "GC=F": ("금 선물 가격 (Gold)", "Gold futures price (Gold)"),
}

# Short names for the headline tiles.
SHORT_NAMES: dict[str, tuple[str, str]] = {
    "DGS2": ("미 국채 2년", "UST 2y"), "DGS10": ("미 국채 10년", "UST 10y"),
    "DGS30": ("미 국채 30년", "UST 30y"), "T10Y2Y": ("장단기 금리차 (10년−2년)", "2s10s"),
    "DFII10": ("10년 실질금리", "10y real (TIPS)"), "T10YIE": ("10년 기대인플레이션", "10y breakeven"),
    "VIXCLS": ("변동성 지수 (VIX)", "VIX"), "BAMLH0A0HYM2": ("하이일드 스프레드", "HY OAS"),
    "DTWEXBGS": ("달러 지수", "Broad USD"),
}

# Indicator group -> (Korean, English). The chart legend and the table use these.
GROUP_NAMES: dict[str, tuple[str, str]] = {
    "rates": ("금리", "Rates"),
    "credit": ("신용", "Credit"),
    "fx": ("외환", "FX"),
    "risk": ("위험선호", "Risk appetite"),
}

# Regime word -> (Korean word, Korean meaning, English meaning). The English word is the core's own; the
# Korean curve words are the one shared vocabulary (quantgen_desktop.rates_narrative.REGIMES, the reviewed
# native words), so the Macro page, the Rates page and every chart say the same thing.
CURVE_WORDS: dict[str, tuple[str, str, str]] = {
    "bull steepener": (REGIMES["bull steepener"],
                       "금리가 내리는 가운데 단기 금리가 더 많이 내려 장단기 금리차가 벌어졌습니다.",
                       "Yields fell and the short end fell more, so the 10y-2y gap widened."),
    "bear steepener": (REGIMES["bear steepener"],
                       "금리가 오르는 가운데 장기 금리가 더 많이 올라 장단기 금리차가 벌어졌습니다.",
                       "Yields rose and the long end rose more, so the 10y-2y gap widened."),
    "bull flattener": (REGIMES["bull flattener"],
                       "금리가 내리는 가운데 장기 금리가 더 많이 내려 장단기 금리차가 줄었습니다.",
                       "Yields fell and the long end fell more, so the 10y-2y gap narrowed."),
    "bear flattener": (REGIMES["bear flattener"],
                       "금리가 오르는 가운데 단기 금리가 더 많이 올라 장단기 금리차가 줄었습니다.",
                       "Yields rose and the short end rose more, so the 10y-2y gap narrowed."),
    "parallel up": (REGIMES["parallel up"], "장단기 금리가 비슷한 폭으로 올랐습니다.",
                    "Short and long yields rose by similar amounts."),
    "parallel down": (REGIMES["parallel down"], "장단기 금리가 비슷한 폭으로 내렸습니다.",
                      "Short and long yields fell by similar amounts."),
    "unchanged": (REGIMES["unchanged"], "20거래일 동안 10년 금리와 장단기 금리차가 5bp 미만으로 움직였습니다.",
                  "The 10y yield and the 10y-2y gap moved less than 5bp over 20 sessions."),
}
# The rule of core/ficc/macro.py: the average of the VIX and high-yield spread 1-year z-scores, risk-off above
# +0.75, risk-on below -0.5, neutral in between.
RISK_WORDS: dict[str, tuple[str, str, str]] = {
    "risk-on": ("위험 선호", "VIX와 하이일드 스프레드의 1년 z-점수 평균이 -0.5보다 낮습니다(위험을 감수하는 쪽).",
                "The average of the VIX and high-yield spread 1-year z-scores is below -0.5 (leaning toward "
                "taking risk)."),
    "risk-off": ("위험 회피", "VIX와 하이일드 스프레드의 1년 z-점수 평균이 +0.75보다 높습니다(위험을 피하는 쪽).",
                 "The average of the VIX and high-yield spread 1-year z-scores is above +0.75 (leaning toward "
                 "avoiding risk)."),
    "neutral": ("중립", "VIX와 하이일드 스프레드의 1년 z-점수 평균이 -0.5와 +0.75 사이입니다(어느 쪽으로도 뚜렷하게 "
                "기울지 않음).",
                "The average of the VIX and high-yield spread 1-year z-scores is between -0.5 and +0.75 (no clear "
                "lean)."),
}
DOLLAR_WORDS: dict[str, tuple[str, str, str]] = {
    "strong": ("강세", "달러 지수가 한 달 동안 1.5% 넘게 올랐습니다.", "The broad dollar rose more than 1.5% in a month."),
    "weak": ("약세", "달러 지수가 한 달 동안 1.5% 넘게 내렸습니다.", "The broad dollar fell more than 1.5% in a month."),
    "range": ("횡보", "달러 지수의 한 달 변화가 ±1.5% 안에 머물렀습니다.",
              "The broad dollar stayed within ±1.5% over a month."),
}
INFLATION_WORDS: dict[str, tuple[str, str, str]] = {
    "rising": ("상승", "시장이 예상하는 10년 물가상승률이 한 달 동안 0.10%p 넘게 올랐습니다.",
               "Market-implied 10-year inflation rose more than 10bp in a month."),
    "falling": ("하락", "시장이 예상하는 10년 물가상승률이 한 달 동안 0.10%p 넘게 내렸습니다.",
                "Market-implied 10-year inflation fell more than 10bp in a month."),
    "stable": ("안정", "시장이 예상하는 10년 물가상승률의 한 달 변화가 0.10%p 미만입니다.",
               "Market-implied 10-year inflation moved less than 10bp in a month."),
}
REAL_WORDS: dict[str, tuple[str, str, str]] = {
    "rising": ("상승", "물가를 뺀 10년 실질금리가 한 달 동안 0.15%p 넘게 올랐습니다.",
               "The 10-year real yield rose more than 15bp in a month."),
    "falling": ("하락", "물가를 뺀 10년 실질금리가 한 달 동안 0.15%p 넘게 내렸습니다.",
                "The 10-year real yield fell more than 15bp in a month."),
    "stable": ("안정", "물가를 뺀 10년 실질금리의 한 달 변화가 0.15%p 미만입니다.",
               "The 10-year real yield moved less than 15bp in a month."),
}

_SUMMARY = re.compile(
    r"\(10y (?P<d10>[+-]\d+)bp, 2s10s (?P<slope>[+-]\d+)bp over (?P<n>\d+) sessions\).*?"
    r"\(VIX/HY z (?P<risk>[+-][\d.]+)\).*?\((?P<usd>[+-][\d.]+)% 1m\).*?"
    r"\(1m (?P<bei>[+-]\d+)bp / (?P<real>[+-]\d+)bp\)", re.DOTALL)


def name(table: dict[str, tuple[str, str]], key: str, fallback: str) -> tuple[str, str]:
    """(Korean, English) for a known key; an unknown key shows its own text in both languages."""
    return table.get(key, (fallback, fallback))


def regime_evidence(summary: str) -> dict[str, tuple[str, str]]:
    """The numbers the core printed in `Regime.summary`, as short (Korean, English) evidence lines.

    Returns {} when the summary does not have the core's format; the caller then shows the raw
    summary only. Nothing is recomputed.
    """
    m = _SUMMARY.search(summary or "")
    if not m:
        return {}
    g = m.groupdict()
    return {
        "curve": (f"{g['n']}거래일: 10년 금리 {g['d10']}bp, 장단기 금리차 {g['slope']}bp",
                  f"{g['n']} sessions: 10y {g['d10']}bp, 2s10s {g['slope']}bp"),
        "risk": (f"VIX·하이일드 평균 z-점수 {g['risk']}", f"VIX/HY average z {g['risk']}"),
        "dollar": (f"1개월 변화 {g['usd']}%", f"1-month change {g['usd']}%"),
        "inflation": (f"1개월 변화 {g['bei']}bp", f"1-month change {g['bei']}bp"),
        "real": (f"1개월 변화 {g['real']}bp", f"1-month change {g['real']}bp"),
    }


class LocalTip(ft.Container):
    """A Container whose tooltip follows the page language (translate_controls calls render_locale)."""

    def __init__(self, *args, tips: tuple[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.qg_tips = tips
        if tips:
            self.tooltip = tips[1]

    def render_locale(self, ctx) -> None:
        self.ctx = ctx
        if self.qg_tips:
            self.tooltip = self.qg_tips[0] if getattr(ctx, "language", "en") == "ko" else self.qg_tips[1]


def local_chip(ko: str, en: str, token: str = "muted", *, tooltip: str = "",
               tips: tuple[str, str] | None = None) -> ft.Container:
    """`components.chip` with authored Korean and English wording (for chips that carry numbers).

    `tips` = (Korean, English) gives a tooltip that follows the page language as well."""
    out = chip(en, token, tooltip=tooltip)
    old = out.content
    text = LocalText(ko, en, size=old.size, color=old.color, weight=old.weight)
    if tips:
        return LocalTip(text, padding=out.padding, bgcolor=out.bgcolor, border=out.border,
                        border_radius=out.border_radius, tips=tips)
    out.content = text
    return out


def local_notice(ko: str, en: str, token: str = "accent", *, icon=ft.Icons.INFO_OUTLINE) -> ft.Container:
    """`components.notice` with authored Korean and English wording (for notices that carry numbers)."""
    out = notice(en, token, icon=icon)
    row = out.content
    row.controls[1] = LocalText(ko, en, size=13, color=active().text, expand=True, selectable=True)
    return out
