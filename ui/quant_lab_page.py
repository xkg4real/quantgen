"""Quant Lab — Monte Carlo simulation of a single instrument.

The operator names a symbol, a model, and a horizon; the lab calibrates on
daily history, draws the paths, and answers with the fan, the terminal
distribution, the risk numbers, and a written read of all three. Every result
states its data source — a SYNTHETIC series is flagged loudly, because a
simulation calibrated on simulated data is a toy and must look like one.

The drift defaults to the risk-premium view (rf + ERP, less each model's own
convexity correction): the out-of-sample study found the sample mean has no
forecasting power over one year. rf comes from FRED (DGS3MO) when reachable
and is assumed 3% otherwise; either way the chip row says which.
"""
from __future__ import annotations

from core.research.runs import session_for, new_run, completed, failed, utc_now
from core.research.provenance import code_evidence, runtime_evidence
from core.research.mc_disclosure import bootstrap_disclosure, volatility_disclosure

import json
import re
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from core.ficc import data as ficc_data
from core.i18n import LocaleContext
from core.quant.garch import LR_5PCT, NU_NORMAL
from core.quant.history import HistoryError, _looks_krx, load_history
from core.quant.montecarlo import MODELS, run_monte_carlo
from core.quant import insights
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.build_widgets import local_chip, local_notice, local_stat, provenance_chips
from ui.components import LocalText, card, chip, empty_state, notice, number_field, section, stat as _stat
import ui.qcharts as qcharts

# "best" is the app's own routing (keyless Yahoo before a synthetic fallback). The selector is
# hidden (owner UI review, 2026-11-10); the other keys stay valid for scripts and tests.
_SOURCES = [("best", "Auto"), ("auto", "Auto (KIS for 6-digit, else FMP)"), ("fmp", "FMP"),
            ("kis", "KIS (KRX)"), ("synthetic", "Synthetic demo")]
_MODEL_LABELS = {"garch_t": "GARCH(1,1)-t (default)", "gbm": "GBM (lognormal)",
                 "jump": "Jump diffusion (Merton)",
                 "bootstrap": "Block bootstrap (empirical)"}
_DRIFTS = [("premium", "Risk premium: rf + ERP, less convexity (default)"),
           ("zero", "Zero (stress view)"),
           ("rf", "Risk-neutral: rf, less convexity"),
           ("sample", "Sample mean (noisy)")]
_DRIFT_LABELS = dict(_DRIFTS)
_DRIFT_SHORT = {"premium": "risk premium", "zero": "zero", "rf": "risk-neutral",
                "sample": "sample mean"}          # chip text; the dropdown carries the formula
_DRIFT_SHORT_KO = {"premium": "위험프리미엄", "zero": "0 (스트레스 관점)", "rf": "위험중립",
                   "sample": "표본 평균"}
_KO = LocaleContext("ko_KR").text          # the reviewed Korean caption of a static English string
_RF_ASSUMED = 0.03
FIT_CAPTION = ("Fit window: the last 504 daily closes (the history default); descriptive, not an R-16 graded fit. "
               "The graded lab line is the expanding-window grading (docs/quant_lab), shown below when stored.")
_GRADES = Path(__file__).resolve().parents[1] / "docs" / "quant_lab"
_GRADE_FILE = {"069500": "KODEX200", "069500.KS": "KODEX200", "^KS11": "KOSPI"}   # docs/quant_lab_grading.py names
_GRADE_STYLE = {"PASS": ("PASS", "success"), "FAIL": ("FAIL", "error"), "NOT_RUN": ("NOT RUN", "muted")}
_BASEL_TOKEN = {"green": "success", "yellow": "warning", "red": "error"}
_WORD_KO = {"PASS": "통과 · PASS", "FAIL": "불합격 · FAIL", "NOT RUN": "미실행 · NOT RUN"}   # codes stay visible
_DECISION_KO = {"PASS": "통과 · PASS", "REVISE": "보완 필요 · REVISE", "REJECT": "기각 · REJECT",
                "INSUFFICIENT_DATA": "자료 부족 · INSUFFICIENT_DATA"}
_ZONE_KO = {"green": "녹색 · green", "yellow": "황색 · yellow", "red": "적색 · red", "NOT RUN": "미실행 · NOT RUN"}
SMOKE_CHIP = "SMOKE · vendor data, not an official close, not a card run · gates nothing"   # rulings section 1
_GRADE_LINES = (("var99_kupiec_p", "var99_kupiec_p_min", "Kupiec 99% VaR"),
                ("var99_cc_p", "var99_cc_p_min", "Christoffersen CC 99%"),
                ("es975_z2_p", "es975_z2_reject_level", "ES 97.5% Z2"),
                ("fan_pit_h21_chi2_p", "fan_pit_h21_chi2_p_min", "Fan PIT h21"))


# Korean readings of the engine's drift note (core.quant.montecarlo._drift_note). Display only:
# the English note stays the source and the payload; an unmatched note is shown as is.
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


def _how_ko(how: str) -> str:
    for pattern, render in _HOW_KO:
        m = re.fullmatch(pattern, how)
        if m:
            return render(m)
    return how


def _drift_note_ko(note: str) -> str:
    m = re.fullmatch(r"risk premium: rf (\S+) \+ ERP (\S+) = expected \(arithmetic\) return (\S+); log drift = "
                     r"that - convexity correction (\S+) \((.*?)\) = (\S+?)"
                     r"( - the median sits below spot only because the variance is large; "
                     r"the mean path still earns the premium)?", note or "")
    if m:
        return (f"위험프리미엄 방식: 무위험 금리 {m[1]} + 주식 위험프리미엄 {m[2]} = 기대(산술) 수익률 {m[3]}. "
                f"로그 드리프트 = 여기서 볼록성 보정 {m[4]}({_how_ko(m[5])})을 뺀 {m[6]}"
                + (". 중앙값이 현재가보다 낮은 것은 분산이 크기 때문일 뿐, 평균 경로는 프리미엄을 얻습니다"
                   if m[7] else ""))
    m = re.fullmatch(r"risk-neutral: rf (\S+) - convexity correction (\S+) \((.*?)\) = (\S+); "
                     r"a pricing measure, not a forecast", note or "")
    if m:
        return (f"위험중립 방식: 무위험 금리 {m[1]} - 볼록성 보정 {m[2]}({_how_ko(m[3])}) = {m[4]}. "
                "가격 평가용 기준이며 예측이 아닙니다")
    if note == "zero: the cone centres on spot (stress view)":
        return "0 드리프트: 분포가 현재가를 중심으로 퍼집니다 (스트레스 관점)"
    m = re.fullmatch(r"sample mean (\S+): noisy, standard error about (\S+) on two years of data", note or "")
    if m:
        return f"표본 평균 방식 {m[1]}: 잡음이 크며, 2년치 자료로는 표준오차가 약 {m[2]}입니다"
    return note


def _fmt_sessions(x: float) -> str:
    return "inf" if x == float("inf") else f"{x:.0f}"


def _fmt_pct(x: float) -> str:
    return "n/a" if x != x else f"{x * 100:.1f}%"


def _fmt_nu(x: float) -> str:
    """An end of the nu interval: 'normal' when it reaches eta = 0, '>100' beyond
    the nu the sampler already treats as normal."""
    return "normal" if x == float("inf") else (f">{NU_NORMAL:.0f}" if x > NU_NORMAL else f"{x:.1f}")


def _with_interval(fit, name: str, value: str, fmt) -> str:
    """'value (low to high)': the tile's value with its 95 % Wald interval when
    the fit has one (B2), the value alone otherwise."""
    iv = fit.interval(name)
    return value if iv is None else f"{value} ({fmt(iv[0])} to {fmt(iv[1])})"


def _risk_free(symbol: str = "") -> tuple[float, ft.Control]:
    """The funding rate for the drift, as a decimal, plus the chip that says
    where it came from: the US 3-month bill (FRED DGS3MO) for everything except
    KRX codes, which get the KRW 3-month rate (FRED, monthly) - a USD bill on a
    KRW stock would be the wrong currency. Never raises: any failure, or a
    SYNTHETIC fallback, is the assumed 3% with an error-toned chip."""
    try:
        if _looks_krx(symbol):
            s = ficc_data.load_short_rate("KRW", source="auto")
            if s.source == "FRED":
                return s.last, local_chip(
                    f"무위험 금리 {s.last * 100:.2f}% (원화 3개월, FRED {s.last_date}, 월별)",
                    f"rf {s.last * 100:.2f}% (KRW 3m, FRED {s.last_date}, monthly)")
        else:
            s = ficc_data.load_series("DGS3MO", source="auto", days=30)
            if s.source == "FRED":
                rf = s.last / 100.0                     # FRED yields are percent
                return rf, local_chip(f"무위험 금리 {rf * 100:.2f}% (FRED DGS3MO {s.last_date})",
                                      f"rf {rf * 100:.2f}% (FRED DGS3MO {s.last_date})")
    except Exception:
        pass
    return _RF_ASSUMED, local_chip(f"무위험 금리 {_RF_ASSUMED * 100:.2f}% 가정 (FRED 연결 불가)",
                                   f"rf {_RF_ASSUMED * 100:.2f}% assumed (FRED unreachable)", "error")


def _garch_blocks(fit, horizon_vol: float) -> list[ft.Control]:
    """Second stat strip + one chip per guardrail flag. Every flag is visible:
    the operator cannot judge a silent failure."""
    ab = set(fit.at_bound)
    wald = "95% Wald interval from the observed information (B2)"
    f3, f4 = (lambda x: f"{x:.3f}"), (lambda x: f"{x:.4f}")
    nu_txt = "normal" if fit.effectively_normal else f"{fit.nu:.1f}"
    if fit.nu_interval is not None:
        nu_txt += f" ({_fmt_nu(fit.nu_interval[0])} ~ {_fmt_nu(fit.nu_interval[1])})"
    hl_txt = _fmt_sessions(fit.half_life)
    if fit.half_life_interval is not None:
        hl_txt += " ({} ~ {})".format(*(_fmt_sessions(x) for x in fit.half_life_interval))
    words_ko = (lambda t: re.sub(r"\binf\b", "무한", re.sub(r"\bnormal\b", "정규분포", t)))
    strip = ft.Row([
        _stat("GARCH alpha", _with_interval(fit, "alpha", f"{fit.alpha:.3f}", f3),
              token="error" if "alpha" in ab else "text", tooltip=wald),
        _stat("GARCH beta", _with_interval(fit, "beta", f"{fit.beta:.3f}", f3),
              token="error" if "beta" in ab else "text", tooltip=wald),
        _stat("GARCH alpha+beta", _with_interval(fit, "persistence", f"{fit.persistence:.4f}", f4),
              token="error" if "stationarity" in ab else "text",
              tooltip=wald + ", delta method"),
        local_stat("Half-life (sessions)", words_ko(hl_txt), hl_txt,
                   tooltip="the persistence interval mapped through the half-life"),
        local_stat("nu (tail)", words_ko(nu_txt), nu_txt,
                   token="error" if "nu" in ab else ("muted" if "alpha" in ab else "text"),
                   tooltip=("95% profile-likelihood interval: cut 1.92 inside, 1.35 at the normal "
                       "(the boundary null of the LR tile); 'normal' means the interval includes eta = 0"
                       + ("; greyed: alpha at its bound, the reference distribution is indicative only"
                          if "alpha" in ab else ""))),
        _stat("Next-session vol (ann.)", _fmt_pct(fit.cond_vol_last)),
        _stat("Uncond vol (ann.)", _fmt_pct(fit.uncond_vol),
              token="error" if "omega" in ab else "text",
              tooltip="no interval: the delta method covers 42% to 100% depending on persistence (B2)"),
        _stat("Horizon-average vol (ann.)", _fmt_pct(horizon_vol),
              tooltip="Annualized forecast RMS across the simulated horizon; 252 sessions/year, using the engine innovation convention."),
        _stat("LR t vs normal", f"{fit.lr_t_vs_normal:.1f}",
              token="success" if (fit.lr_t_vs_normal > LR_5PCT and "alpha" not in ab) else "muted",
              tooltip=(f"5% point of the boundary null (half delta-0, half chi-square(1)): {LR_5PCT}"
                       + ("; greyed: alpha at its bound, reference distribution indicative only"
                          if "alpha" in ab else ""))),
        _stat("dAIC vs GBM", f"{fit.delta_aic_vs_gbm:+.1f}",
              token="success" if fit.delta_aic_vs_gbm > 0 else "muted"),
    ], spacing=8, run_spacing=8, wrap=True)
    chips = [local_chip(f"경계값에 닿음: {name}", f"at bound: {name}", "error") for name in fit.at_bound]
    if not fit.converged:
        chips.append(chip("solver did not converge", "error"))
    if not fit.se:
        chips.append(chip("SE undefined", "error", tooltip=fit.se_note))
    at_bound_iv = [n for n in fit.interval_at_bound if n != "persistence"]
    if at_bound_iv:
        chips.append(local_chip("신뢰구간이 경계에 닿음: " + ", ".join(at_bound_iv),
                                "interval touches a bound: " + ", ".join(at_bound_iv), "error",
                                tooltip="a 95% interval crosses a guardrail (0 or the cap for alpha and beta, "
                                        "nu = 2.5); a symmetric interval there is indicative only"))
    if not chips:                                        # same rule as the note's "no guardrail hit"
        chips.append(chip("GARCH guardrails clear", "success"))
    if fit.dist == "t" and fit.effectively_normal:      # eta = 0 is an answer, not a failure
        chips.append(chip("normal innovations", "muted",
                          tooltip="the t fit found no heavier tail than the normal (eta = 1/nu at 0)"))
    if "persistence" in fit.interval_at_bound:           # true of most two-year samples: muted, not an error
        chips.append(chip("persistence interval reaches 1", "muted",
                          tooltip="an integrated variance is not excluded at 95%: the sample "
                                  "cannot pin down where vol settles"))
    chips.extend(_study_chips())
    return [ft.Text("GARCH fit", size=15, weight=ft.FontWeight.W_600, color=active().text),
            strip, ft.Row(chips, spacing=6, run_spacing=6, wrap=True)]


def _study_chips() -> list[ft.Control]:
    """What the asset-expansion study found about this fan out of sample
    (docs/asset_expansion/cards): the rolling one-day 5 % VaR breach rate on
    SPY and KODEX 200 and the verdict of the skewed-t challenger, so the
    operator sees the known miss next to the fit."""
    try:
        from core.quant.validate import load_cards
        from pathlib import Path
        cards = {c["card_id"]: c for c in load_cards(Path(__file__).resolve().parents[1] / "docs" / "asset_expansion" / "cards")}
    except Exception:
        return []
    out = []
    for cid, label in (("D_Q_garch_spy", "SPY"), ("D_Q_garch_kodex200", "KODEX 200")):
        c = cards.get(cid)
        if c and isinstance(c.get("stats", {}).get("exceed95"), (int, float)):
            rate = c['stats']['exceed95']
            out.append(local_chip(f"검증 연구 {label}: 5% VaR 초과 {rate:.1%}일 → {_DECISION_KO.get(c['decision'], c['decision'])}",
                                  f"study {label}: 5 % VaR breached {rate:.1%} of days → {c['decision']}",
                                  "muted" if c["decision"] == "PASS" else "error",
                                  tooltip=(c.get("lines") or [""])[0]))
    for cid, label, ko in (("D_Q_skewt_spy", "skew-t on SPY", "SPY 대상 skew-t 모형"),
                           ("D_Q_skewt_kodex200", "skew-t on KODEX 200", "KODEX 200 대상 skew-t 모형")):
        c = cards.get(cid)
        if c:
            out.append(local_chip(f"{ko}: {_DECISION_KO.get(c['decision'], c['decision'])}", f"{label}: {c['decision']}",
                                  "success" if c["decision"] == "PASS" else "muted",
                                  tooltip=c.get("decision_reason", "")))
    return out


def _lab_grade(symbol: str) -> Optional[dict]:
    """The stored R-16 grading report for `symbol` (`docs/quant_lab/<name>.json`, `lab.grade_to_json`), else None."""
    s = (symbol or "").strip().upper()
    name = _GRADE_FILE.get(s, s)
    if not re.fullmatch(r"[A-Z0-9]+", name):
        return None
    try:
        return json.loads((_GRADES / f"{name}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _grade_blocks(g) -> list[ft.Control]:
    """PASS / FAIL / NOT RUN chips for the M9 gate and its four statistics, from a `lab.LabGrade` or its JSON;
    [] when there is no grade. The words come from the report's own p-values and thresholds."""
    if g is None:
        return []
    gate = g.get("gate") if isinstance(g, dict) else getattr(g, "gate", None)
    if not isinstance(gate, dict) or not gate.get("status"):
        return []
    lines, th = gate.get("lines") or {}, gate.get("thresholds") or {}
    rep = g if isinstance(g, dict) else (getattr(g, "report", None) or {})
    note = rep.get("label")
    smoke = str(note or "").startswith("SMOKE")          # vendor data: gates nothing, so no chip may read as a pass
    tone = (lambda t: "muted") if smoke else (lambda t: t)
    label, tok = _GRADE_STYLE.get(gate["status"], (str(gate["status"]), "muted"))
    chips = [chip(SMOKE_CHIP, "error", tooltip=str(note))] if smoke else []
    chips.append(local_chip(f"M9 검증 관문: {_WORD_KO.get(label, label)}", f"M9 gate: {label}", tone(tok),
                            tooltip=str(gate.get("reason") or f"period {gate.get('period')}, n {gate.get('n')}")))
    zone = ((((rep.get("periods") or {}).get(gate.get("period")) or {}).get("basel") or {}).get("last_250"))
    for key, tkey, name in _GRADE_LINES:
        if key == "fan_pit_h21_chi2_p":                    # 02_ui_design order: ..., ES Z2, Basel zone, fan PIT
            zone_en = zone or "NOT RUN"
            chips.append(local_chip(f"바젤 구간 (최근 250일): {_ZONE_KO.get(zone_en, zone_en)}",
                                    f"Basel last 250: {zone_en}", tone(_BASEL_TOKEN.get(zone, "muted"))))
        p, t = lines.get(key), th.get(tkey)
        if isinstance(p, (int, float)) and isinstance(t, (int, float)):
            word, tok = _GRADE_STYLE["PASS" if p >= t else "FAIL"]
            chips.append(local_chip(f"{name}: {_WORD_KO[word]} (p값 {p:.3f}, 기준 {t:g} 이상)",
                                    f"{name}: {word} (p {p:.3f}, min {t:g})", tone(tok)))
        else:
            chips.append(local_chip(f"{name}: {_WORD_KO['NOT RUN']}", f"{name}: NOT RUN", "muted"))
    out: list[ft.Control] = [ft.Row(chips, spacing=6, run_spacing=6, wrap=True)]
    if note:
        out.append(ft.Text(str(note), size=12, color=active().muted, selectable=True))
    report_lines = g.get("lines") if isinstance(g, dict) else getattr(g, "lines", ())
    details = [ft.Text(f"• {s}", size=12, color=active().muted, selectable=True)   # incl. 'reported, not gated' and 1-day VaR
               for s in report_lines or () if s != note]
    if details:                                          # long report text: one click away, never deleted
        out.append(ft.ExpansionTile(
            title=ft.Text("Grading report details", size=13, weight=ft.FontWeight.W_600, color=active().text),
            controls=[ft.Container(ft.Column(details, spacing=4), padding=ft.Padding(16, 0, 16, 12))],
            expanded=False))
    return out


def build_quant_lab_page(page: ft.Page,
                         on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()

    symbol = ft.TextField(label="Symbol", hint_text="AAPL or 005930", width=150,
                          border_radius=RADII["md"], value="AAPL")
    source = ft.Dropdown(label="Data source", width=250, value="best", visible=False,
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    model = ft.Dropdown(label="Model", width=230, value="garch_t",
                        options=[ft.dropdown.Option(m, _MODEL_LABELS[m]) for m in MODELS])
    # The guidance used to be a helper line under the box, which pushed this one field off the
    # row's baseline; it is the tooltip now.
    erp = ft.TextField(label="ERP %", value="4.0", width=140, text_align=ft.TextAlign.RIGHT,
                       tooltip="equity 4 / bonds-gold 1 / FX 0",
                       border_radius=RADII["md"])

    def on_drift(e=None) -> None:
        erp.visible = drift.value == "premium"
        page.update()

    drift = ft.Dropdown(label="Drift", width=240, value="premium", on_select=on_drift,
                        options=[ft.dropdown.Option(k, v) for k, v in _DRIFTS])
    horizon = ft.TextField(label="Horizon (sessions)", width=130, value="126",
                           border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT)
    paths = number_field("Paths", "5000", width=120)
    target = number_field("Target price (optional)", "", width=150)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _plain(text):
        """A grouped entry ('5,000') as the plain number string the run record stores."""
        return text.replace(",", "").strip() if isinstance(text, str) else text

    def run(e=None) -> None:
        # Capture UI inputs before starting a background task.
        inputs = dict(symbol=symbol.value, source_requested=source.value or "best", model=model.value or "garch_t",
                      horizon_days=horizon.value or "126", n_paths=_plain(paths.value) or "5000",
                      target=_plain(target.value), drift=drift.value or "premium", erp=erp.value or "0", seed=7)
        research = session_for(page)
        run_record = new_run(inputs, code=code_evidence(), environment=runtime_evidence())
        research.put(run_record)
        busy.visible = True
        result_host.controls = []
        page.update()

        def worker():
            try:
                hz = int(float(inputs["horizon_days"]))
                np_ = int(float(inputs["n_paths"]))
                tgt = float(inputs["target"]) if (inputs["target"] or "").strip() else None
                mode = inputs["drift"]
                erp_dec = 0.0
                if mode == "premium":
                    try:
                        erp_dec = float(inputs["erp"]) / 100.0
                    except ValueError:
                        raise ValueError(f"ERP % is not a number: {erp.value!r}")
                rf, rf_chip = (_risk_free(inputs["symbol"] or "") if mode in ("premium", "rf")
                               else (0.0, None))
                hist = load_history(inputs["symbol"], source=inputs["source_requested"])
                loaded_at = utc_now()
                mc = run_monte_carlo(hist, model=inputs["model"],
                                     n_paths=np_, horizon_days=hz, target=tgt,
                                     drift=mode, rf_rate=rf, erp=erp_dec, seed=inputs["seed"])
                run_record["parameters"]["target"] = tgt
                research.put(completed(run_record, hist, mc, loaded_at=loaded_at))
            except (HistoryError, ValueError) as exc:
                research.put(failed(run_record, type(exc).__name__))
                result_host.controls = [notice(str(exc), "error",
                                               icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False
                page.update()
                return
            except Exception as exc:
                research.put(failed(run_record, type(exc).__name__))
                result_host.controls = [notice(f"{type(exc).__name__}: {exc}",
                                               "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False
                page.update()
                return

            vol_info = volatility_disclosure(mc)
            blocks: list[ft.Control] = []
            if hist.source == "SYNTHETIC":
                blocks.append(local_notice(
                    "합성 데이터입니다. 시세 제공자가 응답하지 않아 모의 가격 경로로 보정했으므로, 아래 분포는 "
                    "화면 시연용이며 실제 시장에 대한 판단 근거가 아닙니다. 자세한 원인은 이 안내 위에 마우스를 "
                    "올리면 표시됩니다.",
                    "Synthetic data: " + hist.note, "error", icon=ft.Icons.SCIENCE_OUTLINED,
                    tooltip=hist.note))
            model_en = _MODEL_LABELS[mc.model]
            drift_short = _DRIFT_SHORT.get(mc.drift_mode, mc.drift_mode)
            resampling = bootstrap_disclosure(mc.model)   # None for every model but bootstrap
            # Summary first: the distribution in one sentence, then the tiles, then how it was made.
            blocks.append(card(ft.Column([
                ft.Row([
                    LocalText(f"{mc.symbol} 가격 분포 (모의실험)", f"{mc.symbol} simulated price distribution",
                              size=16, weight=ft.FontWeight.W_600, color=pal.text),
                    chip(model_en, "accent"),
                ], spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                LocalText(f"{_KO(model_en)} 모형으로 {mc.n_paths:,}개 경로, {mc.horizon_days}거래일 뒤를 모의실험한 "
                          f"결과, 만기 가격 중앙값은 {mc.median_terminal:,.2f}(현재 {mc.spot:,.2f})이고 90% 범위는 "
                          f"{mc.p05:,.0f}~{mc.p95:,.0f}, 손실 확률은 {mc.prob_loss * 100:.0f}%입니다.",
                          f"{mc.n_paths:,} paths of {model_en} over {mc.horizon_days} sessions: median terminal "
                          f"{mc.median_terminal:,.2f} (spot {mc.spot:,.2f}), 90% range {mc.p05:,.0f} to "
                          f"{mc.p95:,.0f}, probability of a loss {mc.prob_loss * 100:.0f}%.",
                          size=13, color=pal.text),
                ft.Row([
                    _stat("Spot", f"{mc.spot:,.2f}"),
                    _stat("Median terminal", f"{mc.median_terminal:,.2f}"),
                    _stat("90% range", f"{mc.p05:,.0f} – {mc.p95:,.0f}"),
                    _stat("P(loss)", f"{mc.prob_loss * 100:.0f}%",
                          token="error" if mc.prob_loss > 0.5 else "text"),
                    _stat(f"VaR {mc.var_level * 100:.0f}", f"{mc.var_pct * 100:.1f}%"),
                    _stat("CVaR", f"{mc.cvar_pct * 100:.1f}%"),
                    _stat("Drift (ann.)", f"{mc.mu_annual * 100:+.1f}%"),
                    _stat(vol_info["label"], f"{mc.sigma_annual * 100:.1f}%",
                          tooltip=vol_info["description"]),
                ] + ([_stat("P(terminal ≥ target)", f"{mc.prob_target * 100:.0f}%",
                            token="success")] if mc.prob_target is not None else []),
                    spacing=8, run_spacing=8, wrap=True),
                LocalText(_drift_note_ko(mc.drift_note), mc.drift_note, size=12, color=pal.muted),
            ] + ([ft.Text(resampling["description"], size=12, color=pal.muted)] if resampling is not None else []) + [
                provenance_chips([hist]),
                ft.Row([
                    chip(f"{hist.first_date} → {hist.last_date}"),
                    local_chip(f"경로 {mc.n_paths:,}개", f"{mc.n_paths:,} paths"),
                    local_chip(f"드리프트: {_DRIFT_SHORT_KO.get(mc.drift_mode, drift_short)}",
                               f"drift: {drift_short}", "accent"),
                ] + ([rf_chip] if rf_chip is not None else []), spacing=6, run_spacing=6, wrap=True),
            ], spacing=12)))
            fit = getattr(mc, "garch", None)
            blocks.append(card(ft.Column(
                [ft.Text("Validation record", size=15, weight=ft.FontWeight.W_600, color=pal.text),
                 ft.Text(FIT_CAPTION, size=12, color=pal.muted)]
                + _grade_blocks(_lab_grade(symbol.value or ""))
                + (_garch_blocks(fit, mc.garch_horizon_vol) if fit is not None else []),
                spacing=10)))
            if fit is not None:
                blocks.append(card(qcharts.cond_vol_chart(hist, fit)))
            blocks.append(card(qcharts.fan_chart(hist, mc)))
            blocks.append(card(qcharts.terminal_histogram(mc)))
            payload = {
                "symbol": mc.symbol, "data_source": hist.source,
                "model": mc.model, "n_paths": mc.n_paths,
                "horizon_days": mc.horizon_days, "spot": mc.spot,
                "drift_annual": mc.mu_annual, "vol_annual": mc.sigma_annual,
                "volatility_definition": vol_info,
                "median_terminal": mc.median_terminal,
                "mean_terminal": mc.mean_terminal,
                "p05": mc.p05, "p95": mc.p95, "prob_loss": mc.prob_loss,
                "prob_target": mc.prob_target, "target": mc.target,
                "prob_target_basis": "terminal_price >= target at horizon_days; not first-touch probability" if mc.prob_target is not None else None,
                "var_level": mc.var_level, "var_pct": mc.var_pct,
                "cvar_pct": mc.cvar_pct, "jump_note": mc.jump_note,
                "drift_mode": mc.drift_mode, "drift_note": mc.drift_note,
                "rf_rate": mc.rf_rate, "erp": mc.erp,
                "convexity_correction_annual": mc.correction_annual, "z_bound": mc.z_bound,
                "bound_note": mc.bound_note, "resampling_definition": resampling,
            }
            if fit is not None:
                payload["garch"] = {
                    "dist": fit.dist, "omega": fit.omega, "alpha": fit.alpha,
                    "beta": fit.beta, "nu": fit.nu, "persistence": fit.persistence,
                    "half_life_sessions": fit.half_life,
                    "cond_vol_annual": fit.cond_vol_last,
                    "uncond_vol_annual": fit.uncond_vol,
                    "horizon_vol_annual": mc.garch_horizon_vol,
                    "loglik": fit.loglik, "loglik_normal": fit.loglik_normal,
                    "loglik_gbm": fit.loglik_gbm, "aic": fit.aic, "bic": fit.bic,
                    "lr_t_vs_normal": fit.lr_t_vs_normal,
                    "delta_aic_vs_gbm": fit.delta_aic_vs_gbm,
                    "converged": fit.converged, "at_bound": list(fit.at_bound),
                    "note": fit.note,
                    "se": fit.se, "se_note": fit.se_note,
                    "nu_interval_95": fit.nu_interval,
                    "half_life_interval_95": fit.half_life_interval,
                    "interval_at_bound": list(fit.interval_at_bound),
                }
            blocks.append(analysis_panel(page, kind="monte_carlo",
                                         narrative=insights.narrate_monte_carlo(mc),
                                         payload_fn=lambda p=payload: p))
            result_host.controls = blocks
            busy.visible = False
            page.update()

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Calibrate and simulate",
        "Pick a symbol and a model — GARCH(1,1)-t is the default, so volatility "
        "clustering and fat tails are in the fan from the first run. The drift "
        "defaults to the risk-premium view (rf + ERP, less each model's convexity correction): in the "
        "out-of-sample study the trailing sample mean had no forecasting power "
        "over one year, so it is offered only for transparency. Without API "
        "keys the lab runs on a clearly labeled synthetic series, so every control "
        "here works immediately.",
        icon=ft.Icons.TROUBLESHOOT_OUTLINED)]

    return ft.Column([
        section("Quant Lab", subtitle="Monte Carlo simulation — calibrated on daily "
                                      "history, seeded and reproducible."),
        ft.Row([symbol, source, model, drift, erp, horizon, paths, target,
                ft.Button("Simulate", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run),
                busy], spacing=12, run_spacing=12, wrap=True,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)


if __name__ == "__main__":
    # Headless driver: no network. FRED is forced off so the "assumed" chip path runs.
    from types import SimpleNamespace

    def _boom(*a, **k):
        raise RuntimeError("network off in driver")
    ficc_data.load_series = _boom

    def walk(c):
        yield c
        for attr in ("controls", "rows", "cells", "columns"):
            children = getattr(c, attr, None)
            if isinstance(children, (list, tuple)):     # ResponsiveRow.columns is its grid width, an int
                for child in children:
                    yield from walk(child)
        for attr in ("content", "label"):
            child = getattr(c, attr, None)
            if child is not None and not isinstance(child, str):
                yield from walk(child)

    fake = SimpleNamespace(run_thread=lambda fn: fn(), update=lambda: None)
    root = build_quant_lab_page(fake)
    controls = list(walk(root))
    dd = {d.label: d for d in controls if isinstance(d, ft.Dropdown)}
    tf = {t.label: t for t in controls if isinstance(t, ft.TextField)}
    run_btn = next(b for b in controls if isinstance(b, ft.Button))
    dd["Data source"].value = "synthetic"
    tf["Paths"].value = "500"

    def texts() -> list[str]:
        return [t.value for t in walk(root) if isinstance(t, ft.Text) and t.value]

    assert dd["Drift"].value == "premium" and tf["ERP %"].visible
    for mode, needs_rf in (("premium", True), ("zero", False), ("sample", False)):
        dd["Drift"].value = mode
        dd["Drift"].on_select(None)
        assert tf["ERP %"].visible == (mode == "premium"), mode
        run_btn.on_click(None)
        found = texts()
        assert not any(t.startswith(("ValueError", "RuntimeError", "TypeError")) for t in found), \
            (mode, found[:3])
        assert f"drift: {_DRIFT_SHORT[mode]}" in found, (mode, found)
        assert any(t.startswith(("risk premium:", "zero:", "sample mean")) for t in found), mode
        assert any("assumed (FRED unreachable)" in t for t in found) == needs_rf, mode
        print(f"{mode}: ok")

    dd["Drift"].value = "premium"
    tf["ERP %"].value = "abc"
    run_btn.on_click(None)
    assert any("ERP % is not a number" in t for t in texts())
    print("driver ok")
