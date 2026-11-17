"""Display text for Portfolio & Risk and Quant Lab's Monte Carlo panel (owner UI review, 2026-11-10).

Ported from Claude's Flet fix (PR #98: ui/portfolio_page.py, ui/signals_page.py, ui/quant_lab_page.py)
for the owner's issues 13 (the portfolio result), 04/12 (no data-source selector), 14 (Korean and English
mixed on one screen) and 11 (a wall of text). Pure Python, no Qt.

Display only. Every function reads a result that already exists and returns its English and Korean
display text; numbers are the result's own fields in the formats the screens already use, ids stay in
the exports, and an engine or provider note with no reviewed Korean reading is shown as written.
"""
from __future__ import annotations

import re

# Objective, strategy and model ids -> English display names. The Korean names come from the shared
# catalogue (quantgen_desktop.translations, owner_ui_language.risk), the Flet wording.
OBJECTIVE_LABELS = {"max_sharpe": "Max Sharpe", "min_vol": "Minimum volatility",
                    "risk_parity": "Risk parity", "equal_weight": "Equal weight"}
STRATEGY_LABELS = {"ma_cross": "MA crossover", "momentum": "Momentum", "rsi_revert": "RSI mean reversion"}
MC_MODEL_LABELS = {"garch_t": "GARCH(1,1)-t", "gbm": "GBM", "jump": "Jump diffusion",
                   "bootstrap": "Block bootstrap"}
# The provider that answered, as Flet's provenance chips name it (ui/build_widgets.provenance_chips).
SOURCE_NAMES = {"SYNTHETIC": ("synthetic data", "합성 데이터"), "YFINANCE": ("Yahoo", "Yahoo"),
                "FMP": ("FMP", "FMP"), "KIS": ("KIS", "KIS"), "CRYPTO": ("crypto venue", "가상자산 거래소")}
# Status codes stay visible next to their Korean meaning (quantgen_desktop.status_language).
STATUS_KO = {"NOT_RUN": "미실행", "PARTIAL": "부분", "PASS": "통과", "FAIL": "실패", "SYNTHETIC": "합성 데이터"}


def ko(text):
    """The catalogue's Korean for an English display string (the string itself when there is none)."""
    from .translations import translate
    from core.i18n import LocaleContext
    out = translate(text, "ko")
    return out if out != text else LocaleContext("ko_KR").text(text)


def status_ko(code):
    code = str(code)
    return f"{STATUS_KO[code]}({code})" if code in STATUS_KO else code


def source_name(source, language):
    en, kr = SOURCE_NAMES.get(str(source).upper(), (str(source), str(source)))
    return kr if language == "ko" else en


def provenance_line(histories, language):
    """'Data from: AAPL · Yahoo, TLT · synthetic data' — which provider actually answered."""
    parts = []
    for h in histories:
        cached = "cached" in (h.note or "")
        parts.append(f"{h.symbol} · {source_name(h.source, language)}"
                     + ((" · 캐시" if language == "ko" else " · cached") if cached else ""))
    return ("데이터 출처: " if language == "ko" else "Data from: ") + ", ".join(parts)


def synthetic_line(histories, language):
    """The simulated-data warning for the SYNTHETIC series among `histories`, or ''."""
    names = ", ".join(h.symbol for h in histories if str(h.source).upper() == "SYNTHETIC")
    if not names:
        return ""
    if language == "ko":
        return (f"합성 데이터({names}): 실제 시세가 아닌 모의 가격 경로로 계산했습니다. "
                "아래 결과는 화면 시연용이며 실제 시장 판단 근거가 아닙니다.")
    return (f"Synthetic data ({names}): computed on simulated price paths, not market prices. "
            "The results below are a demonstration, not a market read.")


# --------------------------------------------------------------------------- portfolio
def portfolio_summary(out, language):
    """Verdict first (Flet `build_portfolio_page`): the selected objective's portfolio in one sentence."""
    p = out.portfolios[out.request.objective]
    name = OBJECTIVE_LABELS.get(p.objective, p.objective)
    top = ", ".join(f"{s} {w * 100:.0f}%" for s, w in sorted(zip(p.symbols, p.weights), key=lambda x: -x[1])[:3])
    sessions = out.stats.sessions
    if language == "ko":
        title = f"{ko(name)} 포트폴리오"
        text = (f"비중이 큰 종목은 {top}입니다. 과거 {sessions:,}개 공통 거래일로 추정하면 "
                f"연 기대수익률 {p.ann_return * 100:+.1f}%, 연 변동성 {p.ann_vol * 100:.1f}%, "
                f"샤프 지수 {p.sharpe:.2f}입니다. 기대수익률은 표본 기간에 가장 민감한 추정치입니다.")
        if not p.converged:
            text += " 최적화 계산이 수렴했다고 보고하지 않았으므로 비중은 근사치로만 보세요."
    else:
        title = f"{name} portfolio"
        text = (f"Largest weights: {top}. Estimated on {sessions:,} shared sessions: expected return "
                f"{p.ann_return * 100:+.1f}%/yr, volatility {p.ann_vol * 100:.1f}%, Sharpe {p.sharpe:.2f}. "
                "The expected return is the least stable estimate here.")
        if not p.converged:
            text += " The solver did not report convergence; treat the weights as approximate."
    return title, text


def portfolio_sections(out):
    """Headed bullets for the portfolio read in both languages (owner issue 11).

    The read is `out.narrative` (English) and its reviewed Korean twin; the data, convention and
    per-objective notes follow under their own headings, from the same lines the full notes hold."""
    from ui.narrative_sections import korean, organise
    from .bonds_portfolio_narrative import convention_korean, model_note_korean, portfolio_korean
    from core.quant.insights import narrate_portfolio
    chosen = out.portfolios[out.request.objective]
    # The Korean twin only reads the locally generated narrative; any other text is shown as written.
    read_ko = korean(portfolio_korean, chosen) if out.narrative == narrate_portfolio(chosen) else None
    variants = {}
    for language in ("en", "ko"):
        k = language == "ko"
        sections = organise((read_ko or out.narrative) if k else out.narrative, language)
        # The synthetic-data warning is the summary card's; the bullets list the dates and the convention.
        data = [(f"과거 {out.stats.sessions:,}개 공통 거래일" if k else f"{out.stats.sessions:,} shared sessions"),
                *[f"{h.symbol} · {source_name(h.source, language)} · {h.first_date} → {h.last_date}"
                  for h in out.histories],
                korean(convention_korean, out) if k else out.convention_warning]
        sections.append(("데이터" if k else "Data", [x for x in data if x]))
        notes = [f"{ko(OBJECTIVE_LABELS.get(o, o))}: {model_note_korean(p.note)}" if k
                 else f"{OBJECTIVE_LABELS.get(o, o)}: {p.note}"
                 for o, p in out.portfolios.items() if p.note]
        if notes:
            from ui.narrative_sections import ko_terms
            sections.append(("목적함수별 메모" if k else "Objective notes",
                             [ko_terms(n) for n in notes] if k else notes))
        variants[language] = sections
    return variants


# --------------------------------------------------------------------------- signals
def signals_summary(out, language):
    """Verdict first (Flet `signals_page._summary`): the composite in words, then whether the costed
    strategy beat buy-and-hold over the same history. Beating buy-and-hold is a comparison, not a gain."""
    r, b, h = out.report, out.backtest, out.history
    strategy = STRATEGY_LABELS.get(b.strategy, b.strategy)
    beat = bool(b.beat_benchmark)
    if language == "ko":
        title = f"{r.symbol} 기술적 관측"
        text = (f"종합 점수 {r.composite:+.0f}점(−100~+100)은 '{ko(r.stance)}'입니다. 같은 기간 "
                f"{ko(strategy)} 전략은 거래비용을 빼고 {b.total_return * 100:+.1f}%, 매수 후 보유는 "
                f"{b.bench_return * 100:+.1f}%로, 전략이 매수 후 보유보다 {'나았습니다' if beat else '못했습니다'}.")
        period = (f"기간: {h.first_date} ~ {h.last_date}. "
                  "한 구간의 과거 백테스트이며 통계 검정이나 표본 외 검증이 아닙니다.")
    else:
        title = f"{r.symbol} technical read"
        text = (f"The composite of {r.composite:+.0f} (−100 to +100) reads '{r.stance}'. Over the same "
                f"history the {strategy} strategy returned {b.total_return * 100:+.1f}% after costs against "
                f"{b.bench_return * 100:+.1f}% for buy-and-hold: it {'beat' if beat else 'did not beat'} "
                "buy-and-hold.")
        period = (f"Period: {h.first_date} to {h.last_date}. "
                  "One historical backtest; not a statistical test or out-of-sample validation.")
    return title, text, period


def parameters_text(params):
    """The backtest parameters as words ('Fast 20 · slow 50'); None for an unknown shape."""
    keys = set(params or {})
    g = lambda v: f"{v:g}" if isinstance(v, (int, float)) else str(v)
    if keys == {"fast", "slow"}:
        return f"Fast {g(params['fast'])} · slow {g(params['slow'])}"
    if keys == {"lookback"}:
        return f"Lookback {g(params['lookback'])} sessions"
    if keys == {"period", "buy_below", "exit_above"}:
        return (f"RSI period {g(params['period'])} · buy below {g(params['buy_below'])} · "
                f"exit above {g(params['exit_above'])}")
    return None


# --------------------------------------------------------------------------- Monte Carlo evidence notes
MC_GROUPS = (("data", "Data", "데이터"), ("assumptions", "Assumptions", "가정"),
             ("volatility", "Volatility and target", "변동성·목표 가격"), ("garch", "GARCH fit", "GARCH 적합"))
_PARAM_KO = {"alpha": "알파", "beta": "베타", "persistence": "지속성", "nu": "nu", "omega": "오메가",
             "eta": "eta", "stationarity": "정상성"}


def _funding_ko(note):
    m = re.fullmatch(r"rf (\S+) · FRED DGS3MO (\S+)", note)
    if m:
        return f"무위험 금리 {m[1]} · FRED DGS3MO {m[2]}"
    m = re.fullmatch(r"rf (\S+) · KRW 3m · FRED (\S+) · monthly", note)
    if m:
        return f"무위험 금리 {m[1]} · 원화 3개월 · FRED {m[2]} · 월별"
    m = re.fullmatch(r"rf (\S+) assumed · FRED unavailable", note)
    if m:
        return f"무위험 금리 {m[1]} 가정 · FRED 연결 불가"
    if note == "Funding rate not applied for this drift":
        return "이 추세 가정에는 무위험 금리를 쓰지 않습니다"
    return None


def _flag_ko(flag):
    from core.ui_legacy_messages import static_text
    fixed = {"solver did not converge": "수치 해법 미수렴",
             "near-integrated (alpha+beta > 0.995)": "IGARCH형에 가까움(알파+베타 > 0.995)",
             "nu at lower bound: tails heavier than the model allows": "nu 하한: 꼬리가 모형 허용 범위보다 두꺼움",
             "normal innovations (eta = 0)": "정규분포 충격(eta = 0)",
             "omega at bound: unconditional vol undefined": "오메가 경계값: 장기 평균 변동성 정의 불가",
             "persistence interval reaches 1": "지속성 신뢰구간이 1에 닿음",
             "no guardrail hit": "안전장치 경고 없음"}
    if flag in fixed:
        return fixed[flag]
    m = re.fullmatch(r"normal innovations \(nu = (\S+) > (\S+)\)", flag)
    if m:
        return f"정규분포에 가까운 충격(nu = {m[1]} > {m[2]})"
    m = re.fullmatch(r"(alpha|beta) at bound", flag)
    if m:
        return f"{_PARAM_KO[m[1]]} 경계값"
    m = re.fullmatch(r"standard errors undefined: (.+)", flag)
    if m:
        reason = static_text(m[1], "ko")
        return None if reason == m[1] else f"표준오차 계산 불가: {reason}"
    m = re.fullmatch(r"95% interval reaches a bound: (.+)", flag)
    if m:
        return "95% 신뢰구간이 경계에 닿음: " + ", ".join(_PARAM_KO.get(x, x) for x in m[1].split(", "))
    return None


def _garch_note_ko(note):
    """`GarchFit.note` (core.quant.garch.fit_garch) in Korean, or None when any part is unfamiliar."""
    m = re.fullmatch(r"GARCH\(1,1\)-(\w+) on (\d+) sessions, mu fixed at (\S+)%/day: (.+?); (.+)\.", note)
    if not m:
        return None
    params = (m[4].replace("alpha=", "알파=").replace("beta=", "베타=").replace("persistence=", "지속성=")
              .replace(" to normal)", "~정규분포)"))
    params = re.sub(r"\((\S+) to (\S+)\)", r"(\1~\2)", params)
    flags = [_flag_ko(f) for f in m[5].split("; ")]
    if any(f is None for f in flags):
        return None
    return (f"GARCH(1,1)-{m[1]}, {m[2]}거래일, 평균 수익률은 하루 {m[3]}%로 고정: {params}; "
            + "; ".join(flags) + ".")


def mc_note_ko(group, text, *, result=None):
    """The Korean reading of one Monte Carlo evidence line, or the line as written."""
    from ui.narrative_sections import _bound_note_korean, _jump_note_korean, drift_note_korean
    from core.ui_legacy_messages import static_text
    known = ko(text)
    if known != text:
        return known
    candidates = (_funding_ko(text), drift_note_korean(text, strict=False))
    for value in candidates:
        if value:
            return value
    if result is not None:
        if text == getattr(result, "bound_note", None):
            return _bound_note_korean(text) or text
        if text == getattr(result, "jump_note", None):
            return _jump_note_korean(text) or text
    m = re.fullmatch(r"Horizon-average volatility: sqrt\(mean forecast daily variance\) \* sqrt\(252\), "
                     r"using the engine innovation convention", text)
    if m:
        return "기간 평균 변동성: sqrt(일별 예측 분산의 평균) × sqrt(252), 엔진의 충격 분포 기준"
    m = re.fullmatch(r"Target probability: final price >= (\S+) after (\d+) sessions\. "
                     r"Only the final session is used\.", text)
    if m:
        return f"목표 가격 확률: {m[2]}거래일 뒤 최종 가격이 {m[1]} 이상일 확률입니다. 마지막 거래일 가격만 씁니다."
    m = re.fullmatch(r"GARCH fit: alpha=(\S+), beta=(\S+), nu=(\S+)", text)
    if m:
        return f"GARCH 적합: 알파={m[1]}, 베타={m[2]}, nu={m[3]}"
    m = re.fullmatch(r"converged=(True|False) · persistence=(\S+) · half-life=(\S+) sessions", text)
    if m:
        return f"수렴={'예' if m[1] == 'True' else '아니오'} · 지속성={m[2]} · 반감기={m[3]}거래일"
    m = re.fullmatch(r"(at_bound|interval_at_bound): \((.*)\)", text)
    if m:
        names = [x.strip().strip("'\"") for x in m[2].split(",") if x.strip()]
        head = "경계값에 닿은 모수" if m[1] == "at_bound" else "신뢰구간이 경계에 닿은 모수"
        return f"{head}: " + ", ".join(_PARAM_KO.get(n, n) for n in names)
    m = re.fullmatch(r"note: (.+)", text, re.S)
    if m:
        garch = _garch_note_ko(m[1])
        return f"적합 메모: {garch}" if garch else text
    m = re.fullmatch(r"se_note: (.+)", text, re.S)
    if m:
        reason = static_text(m[1], "ko")
        return text if reason == m[1] else f"표준오차 메모: {reason}"
    m = re.fullmatch(r"(alpha|beta|persistence) 95% Wald interval: (.+)", text)
    if m:
        return f"{_PARAM_KO[m[1]]} 95% Wald 신뢰구간: {m[2]}"
    m = re.fullmatch(r"eta 95% profile interval: (.+)", text)
    if m:
        return f"eta 95% 프로파일 우도 신뢰구간: {m[1]}"
    return text


def mc_data_line_ko(history):
    if str(history.source).upper() == "SYNTHETIC":
        return f"합성 데이터 · {history.first_date} → {history.last_date}"
    return f"{source_name(history.source, 'ko')} · {history.first_date} → {history.last_date}"


def grouped_notes(entries, language, *, result=None, history=None):
    """Evidence lines under short headings, bullets in reading order: '데이터' then '• ...'.

    `entries` are (group, English line) pairs in the order the source text holds them."""
    out = []
    for key, en_head, ko_head in MC_GROUPS:
        lines = []
        for index, (group, text) in enumerate(entries):
            if group != key or not text:
                continue
            first = index == 0 and history is not None and group == "data"
            if language == "ko":
                text = mc_data_line_ko(history) if first else mc_note_ko(group, str(text), result=result)
            elif first:
                text = (("Synthetic data · " if str(history.source).upper() == "SYNTHETIC" else "")
                        + f"{history.source} · {history.first_date} → {history.last_date}")
            lines.append("• " + str(text))
        if lines:
            out.append((ko_head if language == "ko" else en_head) + "\n" + "\n".join(lines))
    return "\n\n".join(out)
