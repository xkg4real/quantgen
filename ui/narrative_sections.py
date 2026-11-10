"""Headed sentence bullets for the Analysis panel, in the page's language (owner UI review, 2026-11-10).

The owner reads the app in Korean (`LocaleContext('ko_KR')`) and found every Analysis panel to be one
English paragraph. The native app already has reviewed Korean twins of the local narratives
(`quantgen_desktop/*_narrative*.py`, `*_narrative_language.py`: pure Python, no Qt imports). A page
whose narrative has such a twin passes `sections=localized(english, korean_text)` to
`ui.ai_panel.analysis_panel`: in Korean the panel shows the Korean text, in any other language the
English text, both cut into sentence bullets under the same short headings.

Presentation only:
  * The English narrative stays the panel's `narrative` argument, unchanged: the payload, the deep
    analysis and the tests read it, and it stays available as the full paragraph under the bullets.
  * The Korean text is exactly what the native function returns. This module adds headings; it never
    writes a number or a statement, and it never reorders sentences (headings are inserted between
    them in reading order).
  * When the native function cannot read a result (returns None or raises), the page passes no
    sections and the panel keeps its own English bullets instead of a half-translated read.
  * Raw identifiers the native functions leave in their Korean text (`ma_cross`, `equal_weight`,
    `nelson-siegel`, `SYNTHETIC`, ...) are shown under their Korean display names (`ko_terms`): whole
    tokens only, with the following particle agreeing with the new word. No number or sentence changes.
  * Quant Lab's Monte Carlo has no native Korean narrative; `monte_carlo_korean` is its Korean twin,
    written here from the same `MCResult`/`GarchFit` fields and numbers `core.quant.insights.
    narrate_monte_carlo` states, sentence for sentence, and None for any note it cannot read.
"""
from __future__ import annotations

import math
import re
from types import SimpleNamespace
from typing import Callable, Optional, Sequence, Union


Sections = list[tuple[str, list[str]]]
Body = Union[str, Sequence[str]]
# An extra part: ((Korean heading, English heading), Korean body or None when there is none, English body).
Extra = tuple[tuple[str, str], Optional[Body], Body]

# A sentence ends at . ! ? followed by space and a capital, digit, Hangul or an opening bracket/quote;
# decimals (0.72) and lower-case continuations (e.g. how) do not split. Kept here, free of Flet, so the
# native app (quantgen_desktop.narrative_view) shares it; ui.ai_panel re-exports it.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9가-힣(\"'“‘\[{])")


def split_sentences(text: str) -> list[str]:
    """Sentences of a narrative; joined with single spaces they give the text back (whitespace aside)."""
    parts = [p.strip() for p in _SENTENCE_END.split(str(text or "").strip())]
    return [p for p in parts if p]


HEADINGS = {
    "summary": ("요약", "Summary"),
    "figures": ("핵심 수치", "Key figures"),
    "more": ("세부 수치", "More figures"),
    "limits": ("해석과 한계", "Interpretation and limits"),
}
SHORT = 4            # a narrative of this many sentences or fewer reads under one heading
KEY_FIGURES = 6      # bullets under "Key figures"; the rest follow, in order, under "More figures"

# The trailing run of sentences without a figure (or that state the data status) is the read's
# interpretation, conventions and caveats; a sentence with a digit carries figures.
_DIGIT = re.compile(r"\d")
_STATUS = re.compile(r"SYNTHETIC|NOT_RUN|합성")
# A Korean sentence ends in "다." even when the next one opens with a lower-case model note or a sign
# ("... 반영합니다. nelson-siegel 적합의 ...", "... 입니다. +1bp ..."), which split_sentences keeps together.
_KO_END = re.compile(r"(?<=다\.)\s+(?=\S)")


def _ko(language: str) -> bool:
    return language == "ko"


def sentences(text: str, language: str) -> list[str]:
    """`split_sentences`, plus the Korean "다." ending; joined with spaces they give the text back."""
    parts = split_sentences(text)
    if not _ko(language):
        return parts
    return [s for part in parts for s in (x.strip() for x in _KO_END.split(part)) if s]


def _limit_like(sentence: str) -> bool:
    return not _DIGIT.search(sentence) or bool(_STATUS.search(sentence))


def organise(text: str, language: str) -> Sections:
    """One narrative as sentence bullets under short headings, in reading order.

    Up to SHORT sentences: one heading (Summary). Longer: the first sentence is the summary, the
    trailing run of sentences without figures is "Interpretation and limits", the rest "Key figures"
    (at most KEY_FIGURES bullets; any further ones follow under "More figures")."""
    parts = sentences(text, language)
    if not parts:
        return []
    side = 0 if _ko(language) else 1
    if len(parts) <= SHORT:
        return [(HEADINGS["summary"][side], parts)]
    cut = len(parts)
    while cut > 1 and _limit_like(parts[cut - 1]):
        cut -= 1
    out: Sections = [(HEADINGS["summary"][side], parts[:1])]
    figures = parts[1:cut]
    if figures[:KEY_FIGURES]:
        out.append((HEADINGS["figures"][side], figures[:KEY_FIGURES]))
    if figures[KEY_FIGURES:]:
        out.append((HEADINGS["more"][side], figures[KEY_FIGURES:]))
    if parts[cut:]:
        out.append((HEADINGS["limits"][side], parts[cut:]))
    return out


def _lines(body: Body, language: str) -> list[str]:
    if isinstance(body, str):
        return sentences(body, language)
    return [str(x).strip() for x in body if str(x).strip()]


# --------------------------------------------------------------------------- #
# Raw identifiers in Korean text -> Korean display names (owner UI review, 2026-11-10)
# --------------------------------------------------------------------------- #
# id -> (Korean display name, final sound of that name for the particle: "" vowel, "c" consonant,
# "l" the consonant ㄹ). Strategy, objective and curve-method ids come in both spellings the native
# functions print (`max_sharpe`, and `max-sharpe` from `objective.replace('_', '-')`).
_V, _C, _L = "", "c", "l"
_IDS_KO: dict[str, tuple[str, str]] = {
    "ma_cross": ("이동평균 교차", _V),
    "momentum": ("모멘텀", _C),
    "rsi_revert": ("RSI 평균회귀", _V),
    "equal_weight": ("동일 비중", _C), "equal-weight": ("동일 비중", _C),
    "max_sharpe": ("최대 샤프 지수", _V), "max-sharpe": ("최대 샤프 지수", _V),
    "min_vol": ("최소 변동성", _C), "min-vol": ("최소 변동성", _C),
    "risk_parity": ("리스크 패리티(위험 균등)", _V), "risk-parity": ("리스크 패리티(위험 균등)", _V),
    "bootstrap": ("부트스트랩", _C),
    "cubic_spline": ("자연 3차 스플라인", _V), "cubic-spline": ("자연 3차 스플라인", _V),
    "pchip": ("단조 3차 보간(PCHIP)", _C),
    "monotone_convex": ("단조 볼록 보간(Hagan-West)", _C), "monotone-convex": ("단조 볼록 보간(Hagan-West)", _C),
    "smith_wilson": ("Smith-Wilson", _C), "smith-wilson": ("Smith-Wilson", _C),
    "nelson_siegel": ("Nelson-Siegel", _L), "nelson-siegel": ("Nelson-Siegel", _L),
    "diebold_li": ("Diebold-Li", _V), "diebold-li": ("Diebold-Li", _V),
    "svensson": ("Svensson", _C),
    "bjork_christensen": ("Björk-Christensen", _C), "bjork-christensen": ("Björk-Christensen", _C),
    "normal": ("보통", _C),
    "crowded long": ("롱 쏠림", _C), "crowded short": ("숏 쏠림", _C),
    "SYNTHETIC": ("합성", _C),
}
# Korean wording unified with the agreed vocabulary (the native scope note says 효율적 투자선).
_TERMS_KO: dict[str, tuple[str, str]] = {"효율적 투자선": ("효율적 프런티어", _V)}
_PARTICLE_PAIRS = {"은": ("은", "는"), "는": ("은", "는"), "이": ("이", "가"), "가": ("이", "가"),
                   "을": ("을", "를"), "를": ("을", "를"), "과": ("과", "와"), "와": ("과", "와"),
                   "으로": ("으로", "로"), "로": ("으로", "로")}


def _id_pattern(token: str) -> str:
    rx = re.escape(token)
    if token == "normal":          # 'normal vol' is the Bachelier (normal-model) volatility, not a level
        rx += r"(?!\s+vol)"
    return rx


# Whole tokens only: no ASCII letter, digit, '_' or '-' on either side; the code inside "합성(SYNTHETIC)"
# already has its Korean word next to it. A standalone particle right after the id (은/는, 이/가, ...)
# is re-chosen for the Korean name; 이 before more Hangul (이며, 입니다) is the copula and stays.
_PARTICLE_RX = r"(?:(으로|로|은|는|이|가|을|를|과|와)(?![가-힣]))?"
_ID_RX = re.compile(
    r"(?<![A-Za-z0-9_\-])(?<!합성\()("
    + "|".join(_id_pattern(t) for t in sorted(_IDS_KO, key=len, reverse=True))
    + r")(?![A-Za-z0-9_\-])" + _PARTICLE_RX)
_TERM_RX = re.compile("(" + "|".join(re.escape(t) for t in _TERMS_KO) + ")" + _PARTICLE_RX)


def _particle(particle: str, final: str) -> str:
    consonant_form, vowel_form = _PARTICLE_PAIRS[particle]
    if particle in ("으로", "로"):
        return vowel_form if final in (_V, _L) else consonant_form
    return vowel_form if final == _V else consonant_form


def ko_terms(text: Optional[str]) -> Optional[str]:
    """Korean text with the raw identifiers native functions leave in it shown by their Korean
    display names (`ma_cross` -> 이동평균 교차, `equal_weight는` -> 동일 비중은, ...). Display only:
    whole tokens, nothing else changes; None stays None."""
    if not isinstance(text, str):
        return text

    def swap(table):
        def render(m: re.Match) -> str:
            name, final = table[m[1]]
            return name + (_particle(m[2], final) if m[2] else "")
        return render

    return _TERM_RX.sub(swap(_TERMS_KO), _ID_RX.sub(swap(_IDS_KO), text))


def korean(fn: Callable[..., Optional[str]], *args, **kwargs) -> Optional[str]:
    """The native Korean text for a result (raw identifiers shown by their Korean names, `ko_terms`),
    or None when the reviewed function cannot read it."""
    try:
        text = fn(*args, **kwargs)
    except Exception:            # display only: a failed translation must not take the results down
        return None
    return ko_terms(text) if isinstance(text, str) and text.strip() else None


def localized(english: str, korean_text: Optional[str], *,
              extra: Sequence[Extra] = ()) -> Optional[Callable[[object], Sections]]:
    """`sections=` for `analysis_panel`: `korean_text` organised in Korean, `english` in any other
    language, each followed by the `extra` parts under their own headings. None (the panel's own English
    bullets) when the Korean text, or the Korean body of an extra part, is missing: the two languages
    always show the same parts."""
    if not korean_text or any(body_ko is None for _, body_ko, _ in extra):
        return None
    korean_text = ko_terms(korean_text)
    extra = [(headings, ko_terms(body_ko) if isinstance(body_ko, str) else [ko_terms(str(x)) for x in body_ko],
              body_en) for headings, body_ko, body_en in extra]

    def sections(ctx) -> Sections:
        ko = getattr(ctx, "language", "en") == "ko"
        out = organise(korean_text if ko else english, "ko" if ko else "en")
        for (heading_ko, heading_en), body_ko, body_en in extra:
            lines = _lines(body_ko if ko else body_en, "ko" if ko else "en")
            if lines:
                out.append((heading_ko if ko else heading_en, lines))
        return out
    return sections


# --------------------------------------------------------------------------- #
# Adapters for native functions that read the native workflow's output object
# --------------------------------------------------------------------------- #
def fx_text(tool: str, data: dict) -> Optional[str]:
    """`quantgen_desktop.fx_narrative.fx_korean` reads `out.request.tool` and `out.data` (the dict
    `core.research.fx_analysis.execute_fx` builds); the page passes the same keys it computed."""
    from quantgen_desktop.fx_narrative import fx_korean
    return korean(fx_korean, SimpleNamespace(request=SimpleNamespace(tool=tool), data=data))


def macro_text(sheet, tool: str, narrative: str) -> Optional[str]:
    """`quantgen_desktop.macro_narrative_language.macro_korean` reads `out.sheet`, `out.request.tool`
    ('sheet' | 'daily' | 'weekly') and `out.narrative`, and returns None unless the narrative is the
    current locally generated one."""
    from quantgen_desktop.macro_narrative_language import macro_korean
    return korean(macro_korean, SimpleNamespace(sheet=sheet, request=SimpleNamespace(tool=tool),
                                                narrative=narrative))


# --------------------------------------------------------------------------- #
# Quant Lab: the Korean twin of core.quant.insights.narrate_monte_carlo
# --------------------------------------------------------------------------- #
# Every sentence below mirrors one English sentence of `narrate_monte_carlo` / `_narrate_garch` /
# `_narrate_drift`, from the same fields with the same formats. The engine's own notes (drift,
# innovation cap, jump calibration, standard-error reason) are read by fixed patterns; a note that
# matches none of them makes the whole twin None, so the panel keeps the English read rather than
# showing a half-translated one.
_MC_MODEL_KO = {"garch_t": "GARCH(1,1)-t", "gbm": "GBM", "jump": "점프 확산(Merton)",
                "bootstrap": "블록 부트스트랩"}
_PARAM_KO = {"alpha": "알파", "beta": "베타", "persistence": "지속성", "nu": "nu", "omega": "오메가",
             "eta": "eta"}

# The drift note's "how" (core.quant.montecarlo.run_monte_carlo: where the convexity correction came from).
_HOW_KO = (
    (r"per step from each path's conditional variance, horizon average; t innovations bounded at ±(\S+)",
     lambda m: f"경로별 조건부 분산으로 매 단계 계산한 기간 평균, t 분포 충격은 ±{m[1]}에서 절단"),
    (r"per step from each path's conditional variance, horizon average; normal innovations",
     lambda m: "경로별 조건부 분산으로 매 단계 계산한 기간 평균, 정규분포 충격"),
    (r"half the sample variance, sigma (\S+)", lambda m: f"표본 분산의 절반, 변동성 {m[1]}"),
    (r"half the diffusion variance plus the jump compensator", lambda m: "확산 분산의 절반과 점프 보정항의 합"),
    (r"the empirical block log-MGF of the demeaned sample",
     lambda m: "평균을 뺀 표본의 블록 단위 경험적 로그 적률생성함수"),
)


def _how_korean(how: str) -> Optional[str]:
    for pattern, render in _HOW_KO:
        m = re.fullmatch(pattern, how)
        if m:
            return render(m)
    return None


def drift_note_korean(note: str, *, strict: bool = True) -> Optional[str]:
    """Korean reading of `MCResult.drift_note` (core.quant.montecarlo._drift_note). None when the note
    matches no known form; with `strict=False` an unknown correction source stays in English inside an
    otherwise Korean note (the Quant Lab card's long-standing behaviour)."""
    def how(text: str) -> Optional[str]:
        ko = _how_korean(text)
        return ko if ko is not None or strict else text

    m = re.fullmatch(r"risk premium: rf (\S+) \+ ERP (\S+) = expected \(arithmetic\) return (\S+); log drift = "
                     r"that - convexity correction (\S+) \((.*?)\) = (\S+?)"
                     r"( - the median sits below spot only because the variance is large; "
                     r"the mean path still earns the premium)?", note or "")
    if m and how(m[5]) is not None:
        return (f"위험프리미엄 방식: 무위험 금리 {m[1]} + 주식 위험프리미엄 {m[2]} = 기대(산술) 수익률 {m[3]}. "
                f"로그 드리프트 = 여기서 볼록성 보정 {m[4]}({how(m[5])})을 뺀 {m[6]}"
                + (". 중앙값이 현재가보다 낮은 것은 분산이 크기 때문일 뿐, 평균 경로는 프리미엄을 얻습니다"
                   if m[7] else ""))
    m = re.fullmatch(r"risk-neutral: rf (\S+) - convexity correction (\S+) \((.*?)\) = (\S+); "
                     r"a pricing measure, not a forecast", note or "")
    if m and how(m[3]) is not None:
        return (f"위험중립 방식: 무위험 금리 {m[1]} - 볼록성 보정 {m[2]}({how(m[3])}) = {m[4]}. "
                "가격 평가용 기준이며 예측이 아닙니다")
    if note == "zero: the cone centres on spot (stress view)":
        return "0 드리프트: 분포가 현재가를 중심으로 퍼집니다 (스트레스 관점)"
    m = re.fullmatch(r"sample mean (\S+): noisy, standard error about (\S+) on two years of data", note or "")
    if m:
        return f"표본 평균 방식 {m[1]}: 잡음이 크며, 2년치 자료로는 표준오차가 약 {m[2]}입니다"
    return None


def _bound_note_korean(note: str) -> Optional[str]:
    """`MCResult.bound_note`: what the cap on the t innovations removes (GARCH-t only)."""
    m = re.fullmatch(r"t innovations are capped at ±(\S+): this fit expects a larger day "
                     r"(?:once per (\S+) years|(never in practice)) \(P (\S+) within the horizon\); "
                     r"the cap drops (\S+) of innovation variance, so the fan's vol over this horizon runs "
                     r"(\S+) below the fit's own forecast and VaR/CVaR exclude those days\.", note)
    if m:
        expect = "사실상 나타나지 않을 것으로" if m[3] else f"{m[2]}년에 한 번꼴로"
        return (f"t 분포 충격은 ±{m[1]}에서 절단합니다. 이 적합에서 그보다 큰 하루 변동은 {expect} 예상되며"
                f"(분석 기간 안에 나타날 확률 {m[4]}), 절단으로 충격 분산의 {m[5]}가 빠지므로 이 기간 팬 차트의 "
                f"변동성은 적합 모형 자체의 예측보다 {m[6]} 낮고 VaR/CVaR에는 그런 날이 빠집니다.")
    if note == ("Innovations are effectively normal (the t fit found no heavier tail), so they are drawn "
                "unbounded and no cap applies."):
        return ("충격은 사실상 정규분포이므로(t 분포 적합에서 더 두꺼운 꼬리가 발견되지 않음) 절단 없이 뽑으며 "
                "상한은 적용되지 않습니다.")
    return None


def _jump_note_korean(note: str) -> Optional[str]:
    """`MCResult.jump_note` (core.quant.montecarlo._simulate_jump)."""
    if note == "No >3σ daily moves in the sample — jump model degrades to GBM.":
        return "표본에 3σ를 넘는 하루 변동이 없어 점프 모형이 GBM으로 바뀝니다."
    m = re.fullmatch(r"Calibrated (\d+) jump days out of (\d+) \(λ=(\S+)/yr, mean jump (\S+)\)\.", note)
    if m:
        return f"전체 {m[2]}개 관측 가운데 점프일 {m[1]}일로 보정했습니다 (λ={m[3]}/년, 평균 점프 {m[4]})."
    return None


def _garch_korean(mc) -> Optional[str]:
    """`core.quant.insights._narrate_garch` in Korean: levels, dynamics, tails, precision, every guardrail."""
    from core.quant.garch import LR_5PCT, NU_NORMAL
    from core.ui_legacy_messages import static_text
    g = mc.garch
    v = lambda x: f"{x * 100:.1f}%"
    uncond = v(g.uncond_vol) if math.isfinite(g.uncond_vol) else "정의되지 않음"
    half = (f"분산 충격은 {g.half_life:.0f}거래일 뒤 절반으로 줄어듭니다" if math.isfinite(g.half_life)
            else "분산 충격이 사라지지 않습니다(IGARCH형 분산)")
    out = [
        f"보정(GARCH(1,1)-{g.dist}, {g.n_obs}거래일): 다음 거래일 조건부 변동성(연율)은 {v(g.cond_vol_last)}"
        f"(장기 평균 변동성 {uncond}), {mc.horizon_days}거래일 평균 예측 변동성(연율)은 "
        f"{v(mc.garch_horizon_vol)}입니다.",
        f"알파 {g.alpha:.3f}, 베타 {g.beta:.3f}, 지속성 {g.persistence:.3f}: {half}.",
    ]
    if g.dist == "t":
        tail = ("충격 분포의 꼬리가 정규분포보다 두껍습니다" if g.lr_t_vs_normal > LR_5PCT
                else "이 표본에서는 t 분포 꼬리가 정규분포 GARCH보다 낫지 않았습니다")
        if "alpha" in g.at_bound:
            tail += "; 알파가 경계값이라 LR 기준 분포는 참고용입니다"
        nu_txt = ("정규분포 충격(eta = 0)" if math.isinf(g.nu)
                  else f"nu = {g.nu:.0f}, 사실상 정규분포" if g.effectively_normal
                  else f"nu = {g.nu:.1f}")
        out.append(f"{nu_txt}: {tail} (LR {g.lr_t_vs_normal:.1f}, 기준 {LR_5PCT}).")
    else:
        out.append("충격은 정규분포입니다(꼬리 모수 없음).")
    if g.se:
        iv = lambda n, d=3: "{:.{d}f}~{:.{d}f}".format(*g.interval(n), d=d)
        lo, hi = g.half_life_interval
        half_iv = f"{lo:.0f}거래일~무한" if math.isinf(hi) else f"{lo:.0f}~{hi:.0f}거래일"
        prec = (f"95% 신뢰구간: 알파 {iv('alpha')}, 베타 {iv('beta')}, 지속성 {iv('persistence', 4)} "
                f"(반감기 {half_iv})")
    else:
        reason = static_text(g.se_note, "ko")
        if reason == g.se_note:                  # an unreviewed reason: keep the English read
            return None
        prec = f"표준오차 계산 불가: {reason}"
    if g.nu_interval is not None:
        fmt = lambda x: ("정규분포" if math.isinf(x) else f">{NU_NORMAL:.0f}" if x > NU_NORMAL else f"{x:.1f}")
        prec += (f"; 프로파일 우도로 구한 nu {fmt(g.nu_interval[0])}~{fmt(g.nu_interval[1])}"
                 + ("(알파가 경계값이라 참고용)" if "alpha" in g.at_bound else ""))
    at_bound_iv = [n for n in g.interval_at_bound if n != "persistence"]
    if at_bound_iv:
        prec += ("; " + ", ".join(_PARAM_KO.get(n, n) for n in at_bound_iv)
                 + "의 신뢰구간은 경계에 닿아 참고용입니다")
    if "persistence" in g.interval_at_bound:
        prec += "; 지속성 신뢰구간이 1에 닿으므로 지속성 1(충격이 사라지지 않는 IGARCH형 분산)을 배제할 수 없습니다"
    out.append(prec + ". 장기 평균 변동성에는 설계상 신뢰구간을 붙이지 않습니다.")
    d = g.delta_aic_vs_gbm
    out.append(f"GBM 대비 AIC 차이 {d:+.1f}: "
               + ("GARCH 쪽이 선호됩니다." if d > 0 else "여기서는 GARCH가 GBM보다 낫지 않습니다."))
    flags = []
    if not g.converged:
        flags.append("수치 해법이 수렴하지 않았으므로 보정 결과는 참고용입니다")
    ab = set(g.at_bound)
    if "stationarity" in ab or "beta" in ab:
        flags.append("지속성이 IGARCH형에 가까워 이 표본으로는 변동성이 결국 어디에 자리 잡을지 정할 수 없으므로 "
                     "더 긴 기간의 자료를 쓰세요")
    if "nu" in ab:
        flags.append("꼬리가 모형이 허용하는 범위보다 두껍습니다")
    if "omega" in ab:
        flags.append("장기 평균 변동성을 정의할 수 없습니다")
    if "alpha" in ab:
        flags.append("알파가 0이라 충격에 반응하지 않으므로 베타와 반감기를 식별할 수 없습니다" if g.alpha < 1e-3
                     else "알파가 상한이라 충격 반응이 안전장치 상한으로 제한됩니다")
    if flags:
        out.append("안전장치: " + "; ".join(flags) + ".")
    return " ".join(out)


def monte_carlo_korean(mc) -> Optional[str]:
    """Korean twin of `core.quant.insights.narrate_monte_carlo(mc)`: the same sentences, in the same
    order, from the same fields and numbers. None when a note in the result has no Korean reading."""
    from core.quant.insights import _pct
    from core.research.mc_disclosure import BOOTSTRAP_TEXT_KO, bootstrap_disclosure
    model = _MC_MODEL_KO.get(mc.model)
    if model is None:
        return None
    lines = [
        f"{model} 모형으로 모의실험한 {mc.n_paths:,}개 경로에서 {mc.symbol}의 {mc.horizon_days}거래일 뒤 "
        f"가격 중앙값은 {mc.median_terminal:,.2f}로, 현재가 {mc.spot:,.2f} 대비 "
        f"{_pct(mc.median_terminal / mc.spot - 1)}입니다.",
        f"결과의 가운데 90%는 {mc.p05:,.2f}~{mc.p95:,.2f}이며, 모의실험에서 현재가보다 낮게 끝날 확률은 "
        f"{mc.prob_loss * 100:.0f}%입니다.",
        f"기간 VaR({mc.var_level * 100:.0f})는 포지션 가치의 {mc.var_pct * 100:.1f}%이고, 그 지점을 넘는 "
        f"손실의 기댓값(CVaR)은 {mc.cvar_pct * 100:.1f}%입니다.",
    ]
    if mc.garch is not None:
        garch = _garch_korean(mc)
        if garch is None:
            return None
        lines.append(garch)
    else:
        lines.append(f"보정: 과거 표본 로그수익률 변동성(연율, 252거래일 기준)은 {mc.sigma_annual * 100:.1f}%입니다.")
    if bootstrap_disclosure(mc.model) is not None:
        lines.append(BOOTSTRAP_TEXT_KO)
    if getattr(mc, "bound_note", ""):
        bound = _bound_note_korean(mc.bound_note)
        if bound is None:
            return None
        lines.append(bound)
    note = getattr(mc, "drift_note", "")
    drift = drift_note_korean(note) if note else f"연 {mc.mu_annual * 100:+.1f}%"
    if drift is None:
        return None
    lines.append(f"드리프트(추세 가정) — {drift}.")
    if mc.prob_target is not None and mc.target:
        lines.append(f"{mc.horizon_days}거래일 뒤 {mc.target:,.2f} 이상으로 끝날 확률은 "
                     f"{mc.prob_target * 100:.0f}%입니다.")
    if mc.jump_note:
        jump = _jump_note_korean(mc.jump_note)
        if jump is None:
            return None
        lines.append(jump)
    spread = (mc.p95 - mc.p05) / mc.spot
    if spread > 0.8:
        lines.append("결과 범위가 현재가에 비해 넓습니다. 여기서는 방향보다 포지션 규모가 더 중요합니다.")
    elif spread < 0.25:
        lines.append("결과 범위가 좁습니다. 보정된 변동성이 낮으므로 꼬리 쪽의 큰 충격은 이 분포가 아니라 "
                     "국면 변화에서 나올 것입니다.")
    return " ".join(lines)
