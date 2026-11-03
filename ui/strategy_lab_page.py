"""Strategy Lab — the validation scorecard and a live run of any strategy
family through the same gate.

Section one reads the model cards the study wrote (`docs/asset_expansion/
cards/*.json`) and shows every verdict with its plain-language lines, so what
the app offers and what it refuses is visible in one table. Section two runs a
family (trend switch, vol target, cross-sectional momentum, TSMOM, crypto
trend, risk parity, pairs) on symbols the operator names, through the purged
walk-forward and the full gate, and shows the equity curve, the statistics and
the decision. N trials equals the grid size; the card ledger says so.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Optional

import flet as ft
import numpy as np

from core.quant import insights
from core.quant import strategies as S
from core.quant import validate as V
from core.quant.history import HistoryError, convention_warning, load_history
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import card, chip, empty_state, notice, section, stat
import ui.xcharts as xc
from core.research.strategy_workflow import FAMILIES, FAMILY_ID, _MARKET, register_trials, narrative, payload, _study_card
from core.research.strategy_workflow import run_family as _run_family
from core.research.strategy_exposure import EXPOSURE_HELP, exposure_lines

ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = ROOT / "docs" / "asset_expansion" / "cards"
_TOKEN = {"PASS": "success", "REVISE": "accent", "REJECT": "error", "INSUFFICIENT_DATA": "muted"}


# Card family of each Lab family (docs/asset_expansion/cards S_<family>_*), the trial ledger's family id.


def run_family(family: str, symbols: list[str], *, source: str = "auto", cost_bps: Optional[float] = None,
               days: int = 5000, bootstrap_B: int = 1000) -> dict:
    return _run_family(family, symbols, source=source, cost_bps=cost_bps, days=days,
                       bootstrap_B=bootstrap_B, history_loader=load_history, trial_registrar=register_trials)

def build_strategy_lab_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    cards = load_cards()
    # ---- section 1: scorecard --------------------------------------------------
    picker = ft.Dropdown(label="Card", width=360, value=cards[0]["card_id"] if cards else None,
                         options=[ft.dropdown.Option(c["card_id"], f"{c['card_id']} — {c['decision']}") for c in cards])
    detail = ft.Column(spacing=6)

    def show_card(e=None) -> None:
        c = next((x for x in cards if x["card_id"] == picker.value), None)
        detail.controls = []
        if c:
            detail.controls = [
                ft.Row([chip(c["decision"], _TOKEN.get(c["decision"], "muted")), chip(c["kind"]), chip(f"seed {c.get('seed')}"),
                        chip(f"results md5 {str(c.get('results_md5', ''))[:8]}")], spacing=6, wrap=True),
                ft.Text(c["hypothesis"], size=12, color=pal.text, italic=True, selectable=True),
                ft.Text(f"Decision: {c['decision_reason']}" + (f" → {c['revise_target']}" if c.get("revise_target") else ""),
                        size=12, color=pal.text, selectable=True),
            ] + [ft.Text("• " + ln, size=12, color=pal.text, selectable=True) for ln in c.get("lines", [])] + \
                [ft.Text("Sources: " + "; ".join(c.get("citations", [])), size=11, color=pal.muted, selectable=True)]
        page.update()

    picker.on_select = show_card
    counts = {}
    for c in cards:
        counts[c["decision"]] = counts.get(c["decision"], 0) + 1
    rows = []
    for c in cards:
        st = c.get("stats", {})
        key = (f"SR {st.get('sr_oos', float('nan')):.2f} · DSR {st.get('dsr', float('nan')):.2f} · PBO {st.get('pbo', float('nan')):.2f}"
               if isinstance(st.get("sr_oos"), (int, float)) else
               "; ".join(f"{k} {v:.3g}" for k, v in list(c.get("tests", {}).items())[:3] if isinstance(v, (int, float))))
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(c["card_id"], size=11, color=pal.text)),
            ft.DataCell(ft.Text(c["kind"], size=11, color=pal.muted)),
            ft.DataCell(chip(c["decision"], _TOKEN.get(c["decision"], "muted"))),
            ft.DataCell(ft.Text(c["decision_reason"][:70], size=11, color=pal.text)),
            ft.DataCell(ft.Text(key, size=11, color=pal.muted)),
        ]))
    table = ft.DataTable(columns=[ft.DataColumn(ft.Text(h, size=11, color=pal.muted)) for h in ("Card", "Kind", "Decision", "Reason", "Key numbers")],
                         rows=rows, column_spacing=14, heading_row_height=32, data_row_max_height=34) if rows else None
    scorecard = ft.Column([
        ft.Text("Validation scorecard", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        notice("v2 macro model cards (CARD-O / CARD-P) are under Macro → Model cards; this scorecard lists the "
               "asset-expansion study cards only.", "accent"),
        ft.Row([chip(f"{k}: {v}", _TOKEN.get(k, "muted")) for k, v in sorted(counts.items())] +
               [chip(f"{len(cards)} cards from docs/asset_expansion/cards")], spacing=6, wrap=True),
        ft.Text("PASS is offered by default; REVISE is offered with its revise target shown; REJECT and INSUFFICIENT_DATA are "
                "listed so the refusal is visible. Every line states the number, the threshold and the sample behind it.",
                size=11, color=pal.muted),
        ft.Row([table], scroll=ft.ScrollMode.AUTO) if table else notice("No cards yet: run python docs/asset_expansion_study.py", "accent"),
        ft.Row([picker], spacing=10), detail,
    ], spacing=10)
    if cards:
        show_card()

    # ---- section 2: run a family ------------------------------------------------
    family = ft.Dropdown(label="Family", width=330, value="trend_switch",
                         options=[ft.dropdown.Option(k, v[0]) for k, v in FAMILIES.items()])
    symbols = ft.TextField(label="Symbols (comma)", value="SPY, QQQ, TLT, GLD", width=340, border_radius=RADII["md"],
                           hint_text="069500, 152380 · BTC-USD · KRW-BTC · 005935.KS, 005930.KS")
    source = ft.Dropdown(label="Source", width=180, value="auto",
                         options=[ft.dropdown.Option(k, k) for k in ("auto", "yfinance", "kis", "fmp", "crypto", "synthetic")])
    cost = ft.TextField(label="Cost bp/side", value="", hint_text="table", width=110, border_radius=RADII["md"],
                        tooltip="Blank charges QUANTGEN's table rate. A lower cost runs as a sensitivity with no verdict.")
    days = ft.TextField(label="Sessions", value="5000", width=100, border_radius=RADII["md"])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=14)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def worker():
            try:
                syms = [s.strip() for s in (symbols.value or "").split(",") if s.strip()]
                r = run_family(family.value or "trend_switch", syms, source=source.value or "auto",
                               cost_bps=float(cost.value) if (cost.value or "").strip() else None,
                               days=int(float(days.value or "5000")))
            except (HistoryError, ValueError) as exc:
                host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]; busy.visible = False; page.update(); return
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            sc = r["score"]
            blocks: list[ft.Control] = []
            blocks.extend(notice(line, "accent") for line in exposure_lines(r.get("exposure")))
            if "SYNTHETIC" in r["sources"]:
                blocks.append(notice("Synthetic data in the panel: the verdict below is a toy.", "error", icon=ft.Icons.SCIENCE_OUTLINED))
            if r.get("convention"):
                blocks.append(notice(r["convention"], "error", icon=ft.Icons.ERROR_OUTLINE))
            if r["withheld"]:
                blocks.append(notice(r["withheld"], "error", icon=ft.Icons.ERROR_OUTLINE))
            verdict = ([chip("NO VERDICT", "muted"), chip(f"{r['cost_bps']:g} bp < table {r['cost_floor']:g} bp"
                                                          if r["cost_floor"] is not None else "no cost row")]
                       if r["withheld"] else [chip(sc.decision, _TOKEN.get(sc.decision, "muted")), chip(sc.reason[:80])])
            blocks.append(ft.Row(verdict + [
                                  chip(r["wf"].note, "muted")]
                                 + ([chip(f"{FAMILY_ID[r['family']]} ledger: {r['ledger_n']} configurations", "muted",
                                          tooltip="Every configuration ever run in this family. The deflated Sharpe "
                                                  "above counts only this run's grid.")]
                                    if r.get("ledger_n") else []) + [chip(f"{s}: {src}" + (" · cached" if "cached" in note else ""),
                                                                       "success" if src != "SYNTHETIC" else "muted", tooltip=note)
                                                                  for s, src, note in zip(r["symbols"], r["sources"], r["notes"])],
                                 spacing=6, wrap=True))
            blocks.append(ft.Row([
                stat("OOS Sharpe", f"{sc.sr_oos:.2f}", token="success" if sc.ci90[0] > 0 else "error",
                     tooltip=f"90 % block-bootstrap interval {sc.ci90[0]:.2f} to {sc.ci90[1]:.2f}"),
                stat("Deflated Sharpe", f"{sc.dsr:.2f}", token="success" if sc.dsr >= 0.95 else "error"),
                stat("PBO", f"{sc.pbo:.2f}", token="success" if sc.pbo <= 0.05 else "muted"),
                stat("OOS / IS", f"{sc.oos_is:.2f}"), stat("2× costs", f"{sc.sr_stress:.2f}", token="success" if sc.sr_stress > 0 else "error"),
                stat("Years positive", f"{sc.years_positive:.0%}"), stat("Plateau", f"{sc.plateau:.0%}{' (edge)' if sc.edge else ''}"),
                stat("Trades", f"{sc.n_trades}"), stat("Max DD", f"{sc.max_drawdown:.0%}"),
                stat("Benchmark SR", f"{sc.bench_sr:.2f}" if math.isfinite(sc.bench_sr) else "n/a",
                     tooltip=f"difference {sc.bench_diff:+.2f}, one-sided p {sc.bench_p:.2f}" if math.isfinite(sc.bench_p) else ""),
                stat("Haircut SR", f"{sc.haircut_sr:.2f}"),
            ], spacing=10, wrap=True))
            # equity_curve includes initial wealth 1 before the first OOS return.
            # Give that point its preceding price date; never drop an OOS return.
            first = r["panel"].dates.index(r["wf"].dates[0])
            equity_dates = (r["panel"].dates[first - 1], *r["wf"].dates)
            blocks.append(card(xc.equity_chart(equity_dates, r["equity"], r["bench_equity"], title=f"{r['label']}: out-of-sample equity")))
            blocks.append(card(ft.Column([ft.Text("• " + ln, size=12, color=pal.text, selectable=True) for ln in sc.lines], spacing=4)))
            blocks.append(analysis_panel(page, kind="strategy_gate", narrative=narrative(r),
                                         payload_fn=lambda p=payload(r): p, deep_fn=insights.deep_analysis))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    lab = ft.Column([
        ft.Text("Run a family through the gate", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        notice(EXPOSURE_HELP, "accent"),
        ft.Row([family, symbols, source, cost, days, ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy],
               spacing=10, wrap=True),
        host,
    ], spacing=10)
    host.controls = [empty_state("Pick a family and symbols", "Purged walk-forward (IS 756 / OOS 126), block-bootstrap Sharpe interval, "
                                 "deflated Sharpe, PBO, 2× costs, plateau, benchmark test — the same gate the study applied.",
                                 icon=ft.Icons.SCIENCE_OUTLINED)]
    return ft.Column([
        section("Strategy Lab", subtitle="What the validation study admitted, and a live run of any family through the same gate."),
        ft.Column([scorecard, ft.Divider(color=pal.border), lab], scroll=ft.ScrollMode.AUTO, expand=True, spacing=14),
    ], spacing=14, expand=True)


def load_cards() -> list[dict]:
    cards = [_study_card(c) for c in V.load_cards(CARDS_DIR) if isinstance(c, dict)]
    return sorted(cards, key=lambda c: ({"PASS": 0, "REVISE": 1, "REJECT": 2}.get(c["decision"], 3), c["card_id"]))


if __name__ == "__main__":
    r = run_family("trend_switch", ["AAA", "BBB", "CCC"], source="synthetic", cost_bps=5.0, days=1500, bootstrap_B=200)
    assert r["score"].decision in V.DECISIONS and r["equity"].size > 100 and len(r["score"].lines) >= 8
    assert "decision" in narrative(r) and payload(r)["grid_size"] == 12
    assert r["withheld"] and payload(r)["decision"] == "WITHHELD", "5 bp is below the 50 bp US row: no verdict"
    assert "decision" not in payload(r)["stats"] and payload(r)["revise_target"] is None, "no verdict in the payload"
    t = run_family("trend_switch", ["AAA", "BBB", "CCC"], source="synthetic", days=1500, bootstrap_B=200)
    assert t["cost_bps"] == 50.0 and not t["withheld"], "blank cost charges the table rate and keeps the verdict"
    p = run_family("pairs", ["AAA", "BBB"], source="synthetic", cost_bps=5.0, days=1500, bootstrap_B=200)
    assert p["bench_equity"] is None and p["score"].decision in V.DECISIONS
    print("ok", r["score"].decision, p["score"].decision)
