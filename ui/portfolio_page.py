"""Portfolio — Markowitz optimization, risk parity, and basket risk.

The operator lists symbols; the page aligns their histories, computes the
joint return statistics, solves all four objectives (so the frontier chart can
mark them against each other), and details the one selected: weights, risk
contributions, correlation structure, and the written read.

Weight and risk-contribution bars are drawn with the container technique the
rest of the app uses — a weight is a proportion, and `expand` weights render
proportions exactly at any pane width.

Layout rule (owner UI review, 2026-11-10): no child of a `wrap=True` Row may
carry `expand` — Flutter cannot lay out an Expanded inside a Wrap and paints a
grey box instead of the page. Inputs in the wrapping row have fixed widths.
The data source is chosen by the app (`source="best"`); the hidden selector
stays in the tree for tests, and the provider that answered is a small chip.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

import flet as ft
import numpy as np

from core.i18n import LocaleContext
from core.quant.history import HistoryError, convention_warning, load_history
from core.quant.optimize import OBJECTIVES, efficient_frontier, optimize_portfolio
from core.quant.risk import align_histories
from core.quant import insights
from core.research.portfolio_disclosure import cap_label, portfolio_disclosure
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.narrative_sections import korean, localized
from quantgen_desktop.bonds_portfolio_narrative import portfolio_korean, portfolio_scope_korean
from ui.build_widgets import local_notice, provenance_chips, synthetic_banner
from ui.components import LocalText, card, chip, data_table, empty_state, notice, section, stat
import ui.qcharts as qcharts

_OBJ_LABELS = {"max_sharpe": "Max Sharpe", "min_vol": "Minimum volatility",
               "risk_parity": "Risk parity", "equal_weight": "Equal weight"}
_SOURCES = [("best", "Auto"), ("auto", "Auto (keyed providers only)"), ("fmp", "FMP"),
            ("kis", "KIS (KRX)"), ("yfinance", "Yahoo (total return)"), ("synthetic", "Synthetic demo")]
_KO = LocaleContext("ko_KR").text          # the reviewed Korean caption of a static English string

# Korean readings of the optimizer's notes (core.quant.optimize). Display only.
_NOTES_KO = (
    ("Weights equalize each asset's contribution to portfolio risk.",
     "각 자산이 포트폴리오 위험에 같은 몫을 기여하도록 비중을 정했습니다."),
    ("No asset has positive estimated excess return over the risk-free rate. Maximizing a non-positive "
     "Sharpe can favor higher volatility; these weights are not evidence of an attractive or low-risk "
     "allocation.",
     "무위험 금리보다 높은 기대 초과수익을 가진 자산이 없습니다. 0 이하인 샤프 지수를 최대화하면 변동성이 "
     "큰 쪽이 선택될 수 있으므로, 이 비중은 매력적이거나 위험이 낮은 배분이라는 근거가 아닙니다."),
    ("Solver did not report convergence; treat weights as approximate.",
     "최적화 계산이 수렴했다고 보고하지 않았습니다. 비중은 근사치로만 보세요."),
)
_CAP_ADJUSTED = re.compile(r"Requested per-asset cap (\S+) was adjusted to (\S+) by the existing "
                           r"fully-invested feasibility bound \(1/N \+ 1e-9, at most 1\)\.")


def _note_ko(note: str) -> str:
    out = note
    for en, ko in _NOTES_KO:
        out = out.replace(en, ko)
    return _CAP_ADJUSTED.sub(lambda m: f"요청한 종목당 상한 {m[1]}은(는) 전액 투자가 가능한 최소 한도"
                                       f"(1/N + 1e-9, 최대 1)에 맞춰 {m[2]}로 조정되었습니다.", out)


def _cap_ko(p) -> str:
    requested, effective = p.requested_max_weight, p.effective_max_weight
    if requested != effective:
        return f"{requested:.2%} 요청 → {effective:.8%} 적용"
    return f"{effective:.2%}"


def _scope_ko(ports, selected: str) -> str:
    """Korean twin of `portfolio_disclosure(...)["summary"]`, same facts in the same order. The last
    sentence is conditional, as in English ("With different caps, ..."): with the default cap 1.0 every
    row uses the same 100% bound and the comparison is like for like."""
    return (f"선택한 목적함수({_KO(_OBJ_LABELS[selected])})의 종목당 상한은 {_cap_ko(ports[selected])}입니다. "
            "요청한 상한은 선택한 목적함수에만 적용되고, 다른 목적함수 행과 효율적 프런티어·무작위 포트폴리오 "
            "점은 종목당 100% 상한으로 계산합니다. 모두 공매도 없이 전액 투자하며, 동일 비중은 각 비중을 "
            "1/N으로 고정합니다. 상한이 서로 다르면 효율적 프런티어와 같은 조건의 비교가 아닙니다.")


def _bar(fraction: float, token: str) -> ft.Control:
    pal = active()
    filled = max(0, min(100, int(round(fraction * 100))))
    parts: list[ft.Control] = []
    if filled:
        parts.append(ft.Container(expand=filled,
                                  bgcolor=getattr(pal, token, pal.accent),
                                  border_radius=RADII["sm"]))
    if 100 - filled:
        parts.append(ft.Container(expand=100 - filled))
    return ft.Container(ft.Row(parts, spacing=0), height=14,
                        bgcolor=pal.surface_2,
                        border=ft.Border.all(1, pal.border),
                        border_radius=RADII["sm"], expand=True)


def _weight_rows(symbols, weights, risk_contrib) -> ft.Control:
    pal = active()
    rows: list[ft.Control] = [
        ft.Text("Weights and risk contributions", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        LocalText("비중은 투자 금액에서 그 종목이 차지하는 몫, 위험 기여도는 포트폴리오 전체 변동성에서 "
                  "그 종목이 차지하는 몫입니다. 막대 길이가 0~100%를 나타냅니다.",
                  "Weight is the share of the money in the asset; risk contribution is its share of the "
                  "portfolio's total volatility. Bar length is 0 to 100%.",
                  size=12, color=pal.muted),
        ft.Row([
            ft.Container(width=80),
            ft.Text("Weight", size=12, color=pal.muted, expand=True),
            ft.Container(width=52),
            ft.Text("Risk contribution", size=12, color=pal.muted, expand=True),
            ft.Container(width=52),
        ], spacing=8)]
    order = np.argsort(-np.asarray(weights))
    for i in order:
        w, rc = float(weights[i]), float(risk_contrib[i])
        rows.append(ft.Row([
            ft.Text(symbols[i], size=13, color=pal.text, width=80,
                    weight=ft.FontWeight.W_600),
            _bar(w, "accent"),
            ft.Text(f"{w * 100:.1f}%", size=12, color=pal.text, width=52,
                    text_align=ft.TextAlign.RIGHT),
            _bar(rc, "error"),
            ft.Text(f"{rc * 100:.1f}%", size=12, color=pal.text, width=52,
                    text_align=ft.TextAlign.RIGHT),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return ft.Column(rows, spacing=8)


def _comparison_table(ports, chosen_objective: str) -> ft.Control:
    """All four objectives side by side; text columns first, numbers right-aligned."""
    pal = active()

    def cell(value, em):
        if isinstance(value, ft.Text):
            value.size, value.color, value.weight = 12, pal.text, em
            return value
        return ft.Text(value, size=12, color=pal.text, weight=em)

    rows = []
    for o in OBJECTIVES:
        p = ports[o]
        selected = o == chosen_objective
        em = ft.FontWeight.W_600 if selected else ft.FontWeight.W_400
        rows.append([cell(_OBJ_LABELS[o], em),
                     cell(LocalText("선택" if selected else "비교용",
                                    "selected" if selected else "comparison"), em),
                     cell(LocalText(_cap_ko(p), cap_label(p)), em),
                     cell(f"{p.ann_return * 100:+.1f}%", em),
                     cell(f"{p.ann_vol * 100:.1f}%", em),
                     cell(f"{p.sharpe:.2f}", em)])
    table = data_table(["Objective", "Role", "Per-asset cap", "Expected return (ann.)",
                        "Volatility (ann.)", "Sharpe"], rows, numeric_from=2)
    return ft.Column([
        ft.Text("All four objectives compared", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        ft.Row([table], scroll=ft.ScrollMode.AUTO),
    ], spacing=8)


def build_portfolio_page(page: ft.Page,
                         on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()

    symbols = ft.TextField(label="Symbols (comma separated)",
                           hint_text="AAPL, MSFT, NVDA, TLT, GLD",
                           value="AAPL, MSFT, NVDA, TLT", width=340,
                           border_radius=RADII["md"])
    source = ft.Dropdown(label="Data source", width=180, value="best", visible=False,
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    objective = ft.Dropdown(label="Objective", width=230, value="max_sharpe",
                            options=[ft.dropdown.Option(o, _OBJ_LABELS[o])
                                     for o in OBJECTIVES])
    max_w = ft.TextField(label="Max weight/asset", width=170, value="1.0",
                         border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT,
                         tooltip="Per-asset weight cap for the selected objective, 0 to 1 (1.0 = no cap).")
    rf = ft.TextField(label="Risk-free %", width=140, value="3.0",
                      border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def run(e=None) -> None:
        busy.visible = True
        result_host.controls = []
        page.update()

        def worker():
            try:
                syms = [s.strip().upper() for s in (symbols.value or "").split(",")
                        if s.strip()]
                if len(syms) < 2:
                    raise ValueError("List at least two symbols, comma separated.")
                if len(syms) > 15:
                    raise ValueError("At most 15 symbols — the covariance of more "
                                     "is not estimable on two years of dailies.")
                rf_rate = float(rf.value or "3.0") / 100.0
                cap = float(max_w.value or "1.0")
                hists = [load_history(s, source=source.value or "best") for s in syms]
                stats = align_histories(hists)
                ports = {o: optimize_portfolio(stats, objective=o, rf_rate=rf_rate,
                                               max_weight=cap if o == (objective.value or "max_sharpe") else 1.0)
                         for o in OBJECTIVES}
                chosen = ports[objective.value or "max_sharpe"]
                frontier = efficient_frontier(stats, rf_rate=rf_rate)
                disclosure = portfolio_disclosure(ports, chosen.objective)
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

            synth = [h.symbol for h in hists if h.source == "SYNTHETIC"]
            blocks: list[ft.Control] = []
            banner = synthetic_banner(hists)
            if banner is not None:
                blocks.append(banner)
            mixed = convention_warning(hists)
            if mixed:
                blocks.append(notice(mixed, "error", icon=ft.Icons.ERROR_OUTLINE))

            # Verdict first: what the selected objective produced, in one sentence and four numbers.
            obj_en = _OBJ_LABELS[chosen.objective]
            top = sorted(zip(chosen.symbols, chosen.weights), key=lambda x: -x[1])[:3]
            top_txt = ", ".join(f"{s} {w * 100:.0f}%" for s, w in top)
            blocks.append(card(ft.Column([
                ft.Row([
                    LocalText(f"{_KO(obj_en)} 포트폴리오", f"{obj_en} portfolio",
                              size=16, weight=ft.FontWeight.W_600, color=pal.text),
                    chip(obj_en, "accent"),
                ] + ([chip("solver did not converge", "error")] if not chosen.converged else []),
                    spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                LocalText(f"비중이 큰 종목은 {top_txt}입니다. 과거 {stats.sessions}개 공통 거래일로 추정하면 "
                          f"연 기대수익률 {chosen.ann_return * 100:+.1f}%, 연 변동성 {chosen.ann_vol * 100:.1f}%, "
                          f"샤프 지수 {chosen.sharpe:.2f}입니다. 기대수익률은 표본 기간에 가장 민감한 추정치입니다.",
                          f"Largest weights: {top_txt}. Estimated on {stats.sessions} shared sessions: "
                          f"expected return {chosen.ann_return * 100:+.1f}%/yr, volatility "
                          f"{chosen.ann_vol * 100:.1f}%, Sharpe {chosen.sharpe:.2f}. The expected return is "
                          "the least stable estimate here.",
                          size=13, color=pal.text),
                ft.Row([
                    stat("Expected return (ann.)", f"{chosen.ann_return * 100:+.1f}%"),
                    stat("Volatility (ann.)", f"{chosen.ann_vol * 100:.1f}%"),
                    stat("Sharpe", f"{chosen.sharpe:.2f}",
                         token="success" if chosen.sharpe > 1 else "text"),
                    stat("Shared sessions", f"{stats.sessions:,}"),
                ], spacing=8, wrap=True),
                provenance_chips(hists),
            ], spacing=12)))
            blocks.append(card(_weight_rows(chosen.symbols, chosen.weights,
                                            chosen.risk_contrib)))
            blocks.append(local_notice(_scope_ko(ports, chosen.objective), disclosure["summary"]))
            for o, p in ports.items():
                if p.note:
                    blocks.append(local_notice(f"{_KO(_OBJ_LABELS[o])}: {_note_ko(p.note)}",
                                               f"{_OBJ_LABELS[o]}: {p.note}"))

            blocks.append(card(_comparison_table(ports, chosen.objective)))

            blocks.append(card(ft.Column([
                ft.Text("Efficient frontier", size=15, weight=ft.FontWeight.W_600, color=pal.text),
                ft.Text("Frontier / random cloud: 100% per-asset bound; markers use each row's cap.",
                        size=12, color=pal.muted),
                qcharts.frontier_chart(frontier, list(ports.values())),
            ], spacing=8)))
            blocks.append(card(ft.Column([
                ft.Text("Correlation of daily returns", size=15, weight=ft.FontWeight.W_600, color=pal.text),
                qcharts.corr_heatmap(stats.corr, stats.symbols),
            ], spacing=8)))

            payload = {
                "objective": chosen.objective,
                "symbols": list(chosen.symbols),
                "weights": [round(float(w), 4) for w in chosen.weights],
                "risk_contributions": [round(float(x), 4) for x in chosen.risk_contrib],
                "ann_return": chosen.ann_return, "ann_vol": chosen.ann_vol,
                "sharpe": chosen.sharpe, "converged": chosen.converged,
                "rf_rate": rf_rate, "shared_sessions": stats.sessions,
                "constraint_scope": disclosure,
                "note": chosen.note,
                "correlation": [[round(float(c), 3) for c in row] for row in stats.corr],
                "alternatives": {o: {"return": ports[o].ann_return,
                                     "vol": ports[o].ann_vol,
                                     "sharpe": ports[o].sharpe} for o in OBJECTIVES},
                "synthetic_symbols": synth,
            }
            read = insights.narrate_portfolio(chosen)
            scope = (("제약 조건", "Constraints"),
                     korean(portfolio_scope_korean, ports, chosen.objective), disclosure["summary"])
            blocks.append(analysis_panel(page, kind="portfolio_optimization",
                                         narrative=read + " " + disclosure["summary"],
                                         payload_fn=lambda p=payload: p,
                                         sections=localized(read, korean(portfolio_korean, chosen),
                                                            extra=[scope])))
            result_host.controls = blocks
            busy.visible = False
            page.update()

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Build a portfolio",
        "List symbols and pick an objective. All four objectives are computed "
        "and marked on the frontier so the trade-offs are visible, not implied.",
        icon=ft.Icons.PIE_CHART_OUTLINE)]

    return ft.Column([
        section("Portfolio", subtitle="Mean-variance optimization, risk parity, and the "
                                      "efficient frontier — solved with scipy on aligned "
                                      "daily histories."),
        ft.Row([symbols, source, objective, max_w, rf,
                ft.Button("Optimize", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run),
                busy], spacing=12, run_spacing=12, wrap=True,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)
