"""Execution status dashboard (§4) — what the machine is doing right now.

Layout follows the order the operator asks questions in a real session:

  1. Am I armed?              engine state banner, with the stop button in it
  2. What is live?            active rule count, today's fired / rejected tally
  3. What is outstanding?     open simulated orders, fillable from here
  4. Why did nothing happen?  the decision feed, including skips

Point 4 is the one most status screens omit. A rule that quietly did not fire
is the hardest thing to debug, so skipped decisions are shown with the same
weight as fired ones and carry the evaluator's own explanation verbatim.

The emergency stop is rendered in every state, including DISARMED, because a
control that appears only when you need it is one you have to find under
pressure. When there is nothing to stop it is disabled with a tooltip saying so.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

import flet as ft

from core.engine.evaluator import Outcome
from core.engine.state import EngineMode
from core.theme import RADII, active
from ui.components import card, chip, empty_state, notice, section
# Owner UI review (2026-11-10): Korean captions. This file is add-only against the pre-v2 backup
# (tests/macro_m5_integration.py), so fixed English strings are translated by the page catalogue
# (core/ui_page_messages/build_pages.py) and sentences with numbers by the patterns below, applied
# to each composed view by `localize_tree`. No existing line changes.
from ui.build_widgets import localize_tree
from core.i18n import LocaleContext

_MODE_KO = {"DISARMED": "작동 해제", "ARMED": "작동 중", "HALTED": "긴급 정지됨"}   # the code stays visible
_VENUE_KO = {"open": "개장", "closed": "휴장", "unknown": "알 수 없음", "holiday": "공휴일 휴장"}
TRADING_KO = (
    (r"(DISARMED|ARMED|HALTED)", lambda m: f"{_MODE_KO[m[1]]} · {m[1]}"),
    (r"Stopped because of (.+?)\. (.*)", "정지 사유: {1}. {2}"),
    (r"Evaluating every (\d+)s · last pass (.+)", "{1}초마다 평가 · 마지막 평가 {2}"),
    (r"No quote for (\S+) on (\d+) recent pass\(es\)(: .*)?\. Its rules are not being evaluated; the engine halts "
     r"once a rule that needs it has missed more than (.+)\.",
     "최근 {2}번의 평가에서 {1} 시세를 받지 못했습니다{3}. 이 종목의 규칙은 평가하지 않으며, 이 시세가 필요한 "
     "규칙이 {4}회를 넘게 놓치면 엔진이 정지합니다."),
    (r"of (\d+) saved", "저장된 규칙 {1}개 중"),
    (r"(\d+) open · (\d+) filled", "미체결 {1} · 체결 {2}"),
    (r"(\S+) (open|closed|unknown|holiday) · (\d+) rules?",
     lambda m: f"{m[1]} {_VENUE_KO[m[2]]} · 규칙 {m[3]}개"),
    (r"Open simulated orders \((\d+)\)", "모의 미체결 주문 ({1}건)"),
    (r"(.+) · (\w+) · triggered at (.+)", "{1} · {2} · 발동 가격 {3}"),
    (r"(\d+)s open", "{1}초째 미체결"),
    (r"(\d+) rule\(s\) saved, but none is active\. Confirm and activate a rule before arming\.",
     "저장된 규칙 {1}개 중 활성화된 규칙이 없습니다. 작동을 시작하기 전에 규칙을 확인하고 활성화하세요."),
    (r"Exchange calendar data has expired for (.+)\. Holidays are no longer recognised on those venues\.",
     "{1} 거래소 휴장일 자료가 만료되었습니다. 이 시장들의 휴장일을 더 이상 인식하지 못합니다."),
    (r"Exchange calendar data runs out in (\d+) days \((\S+) first\)\. Regenerate with "
     r"pkg_tools/generate_calendars\.py\.",
     "거래소 휴장일 자료가 {1}일 뒤 끝납니다 ({2}부터). pkg_tools/generate_calendars.py로 다시 만드세요."),
    (r"Evaluated (\d+) decision\(s\)\.", "판단 {1}건을 평가했습니다."),
    (r"Acknowledge the halt \((.+)\) before arming\. This program never re-arms itself\.",
     "작동을 시작하기 전에 정지({1})를 확인하세요. 이 프로그램은 스스로 다시 작동하지 않습니다."),
    (r"Filled at (.+)\.", "{1}에 체결 처리했습니다."),
    (r"Order is already (\w+)\.", "이미 {1} 상태인 주문입니다."),
)


def _toast_text(page, message: str) -> str:
    """The SnackBar is shown outside the localized view tree, so its text is localized here."""
    text = ft.Text(message)
    localize_tree(text, TRADING_KO)
    ctx = getattr(page, "qg_locale", None) or LocaleContext("en_US")
    if callable(getattr(text, "render_locale", None)):
        text.render_locale(ctx)
        return text.value
    return ctx.text(message)

MODE_STYLE: dict[EngineMode, tuple[str, str, str]] = {
    EngineMode.DISARMED: ("DISARMED", "muted", ft.Icons.PAUSE_CIRCLE_OUTLINE),
    EngineMode.ARMED:    ("ARMED", "success", ft.Icons.PLAY_CIRCLE_OUTLINE),
    EngineMode.HALTED:   ("HALTED", "error", ft.Icons.REPORT_PROBLEM_OUTLINED),
}

OUTCOME_STYLE: dict[Outcome, tuple[str, str]] = {
    Outcome.FIRED:    ("Fired", "success"),
    Outcome.REJECTED: ("Rejected", "error"),
    Outcome.SKIPPED:  ("Skipped", "muted"),
    Outcome.HALTED:   ("Halted", "error"),
    Outcome.BLOCKED:  ("Blocked", "accent"),     # v2 (M5): new entry inside an R-10 window or the R-31 step
}


def _clock(value) -> str:
    return value.astimezone().strftime("%H:%M:%S") if value else "—"


def _money(value: Optional[Decimal]) -> str:
    return f"{value:,.0f}" if value is not None else "—"


def build_trading_page(page: ft.Page, runtime, *,
                       on_open_rules: Optional[Callable[[], None]] = None,
                       on_open_settings: Optional[Callable[[], None]] = None
                       ) -> ft.Control:
    pal = active()
    body = ft.Column(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def refresh(_e=None) -> None:
        body.controls = _compose()
        localize_tree(body, TRADING_KO)
        try:
            page.update()
        except Exception:
            pass          # the page may be detached during a rebuild

    # Repaint whenever the engine does anything. Without this the dashboard is
    # a snapshot from whenever it was last opened: the loop ticks every few
    # seconds on its own thread, and the operator watching an armed engine sees
    # a decision log that never moves. Called from the engine thread, so it is
    # wrapped in the same try/except as any other repaint.
    runtime.on_update = refresh

    # -- actions -------------------------------------------------------------
    def toast(message: str, token: str = "accent") -> None:
        message = _toast_text(page, message)
        page.show_dialog(ft.SnackBar(ft.Text(message, color=pal.text),
                              bgcolor=pal.surface_2))

    def do_arm(_e) -> None:
        ok, message = runtime.arm()
        toast(message, "success" if ok else "error")
        refresh()

    def do_disarm(_e) -> None:
        runtime.disarm()
        toast("Disarmed. No rule will be evaluated.")
        refresh()

    def do_halt(_e) -> None:
        runtime.halt()
        toast("Emergency stop. Open orders are kept; new orders are blocked.",
              "error")
        refresh()

    def do_acknowledge(_e) -> None:
        runtime.acknowledge()
        toast("Halt acknowledged. The engine is disarmed — arm it when ready.")
        refresh()

    def do_tick(_e) -> None:
        produced = runtime.tick()
        toast(f"Evaluated {len(produced)} decision(s)."
              if produced else "Nothing to evaluate.")
        refresh()

    def fill_order(order_id: str, price: Decimal) -> Callable:
        def handler(_e):
            ok, message = runtime.book.fill(order_id, price)
            toast(message or f"Filled at {price:,}.",
                  "success" if ok else "error")
            runtime._persist()
            refresh()
        return handler

    def cancel_order(order_id: str) -> Callable:
        def handler(_e):
            ok, message = runtime.book.cancel(order_id)
            toast(message or "Cancelled.", "muted" if ok else "error")
            runtime._persist()
            refresh()
        return handler

    # -- pieces --------------------------------------------------------------
    def state_banner(data: dict) -> ft.Control:
        mode = data["mode"]
        label, token, icon = MODE_STYLE[mode]
        colour = getattr(pal, token)

        controls: list[ft.Control] = []
        if data["needs_ack"]:
            controls.append(ft.Button(
                "Acknowledge halt", icon=ft.Icons.CHECK,
                on_click=do_acknowledge,
                style=ft.ButtonStyle(bgcolor=pal.accent, color=pal.on_accent)))
        elif mode is EngineMode.ARMED:
            controls.append(ft.Button("Disarm", icon=ft.Icons.PAUSE,
                                      on_click=do_disarm))
        else:
            controls.append(ft.Button(
                "Arm", icon=ft.Icons.PLAY_ARROW, on_click=do_arm,
                style=ft.ButtonStyle(bgcolor=pal.accent, color=pal.on_accent)))

        # Always present. Disabled rather than hidden when there is nothing to
        # stop, so its position never moves.
        stoppable = mode is EngineMode.ARMED
        controls.append(ft.Button(
            "Emergency stop", icon=ft.Icons.STOP_CIRCLE_OUTLINED,
            on_click=do_halt, disabled=not stoppable,
            tooltip="Stops new orders immediately and keeps open ones."
                    if stoppable else "Nothing is running to stop.",
            style=ft.ButtonStyle(color=pal.error if stoppable else pal.muted)))

        lines = [
            ft.Row([
                ft.Icon(icon, size=26, color=colour),
                ft.Text(label, size=22, weight=ft.FontWeight.BOLD, color=colour),
                ft.Container(expand=True),
                ft.Row(controls, spacing=8),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ]
        if mode is EngineMode.HALTED:
            reason = data["halt_reason"].value if data["halt_reason"] else "unknown"
            detail = data["halt_detail"] or "No further detail was recorded."
            lines.append(ft.Text(
                f"Stopped because of {reason.replace('_', ' ')}. {detail}",
                size=13, color=pal.text, selectable=True))
            lines.append(ft.Text(
                "This program never re-arms itself. Acknowledge the halt, "
                "check the cause, then arm again when you are ready.",
                size=12, color=pal.muted))
        elif mode is EngineMode.DISARMED:
            lines.append(ft.Text(
                "No rule is being evaluated and no market request is being made.",
                size=12, color=pal.muted))
        else:
            lines.append(ft.Text(
                f"Evaluating every {runtime.tick_seconds:.0f}s · "
                f"last pass {_clock(data['last_tick'])}",
                size=12, color=pal.muted))
            # Armed but blind: say so here, not only in the decision log.
            for symbol, misses, why in data.get("degraded", []):
                lines.append(ft.Text(
                    f"No quote for {symbol} on {misses} recent pass(es)"
                    + (f": {why}" if why else "")
                    + ". Its rules are not being evaluated; the engine halts "
                      f"once a rule that needs it has missed more than "
                      f"{runtime.no_data_grace}.",
                    size=13, color=pal.error, selectable=True))

        return ft.Container(
            content=ft.Column(lines, spacing=8), padding=18,
            bgcolor=pal.surface, border=ft.Border.all(1, colour),
            border_radius=RADII["lg"],
        )

    def tile(label: str, value: str, *, token: str = "text",
             hint: str = "") -> ft.Container:
        return card(ft.Column([
            ft.Text(label, size=11, color=pal.muted),
            ft.Text(value, size=24, weight=ft.FontWeight.BOLD,
                    color=getattr(pal, token)),
            ft.Text(hint or " ", size=10, color=pal.muted),
        ], spacing=2), col={"xs": 6, "md": 3})

    def counters(data: dict) -> ft.Control:
        orders = data["orders_today"]
        return ft.ResponsiveRow([
            tile("Active rules", str(data["active_rules"]),
                 hint=f"of {data['total_rules']} saved"),
            tile("Fired today", str(data["fired_today"]),
                 token="success" if data["fired_today"] else "text"),
            tile("Rejected today", str(data["rejected_today"]),
                 token="error" if data["rejected_today"] else "text",
                 hint="blocked by your caps"),
            tile("Committed today", _money(data["notional_today"]),
                 hint=f"{orders.get('OPEN', 0)} open · "
                      f"{orders.get('FILLED', 0)} filled"),
        ], spacing=12, run_spacing=12)

    def venues(data: dict) -> Optional[ft.Control]:
        rows = data.get("venues") or []
        if not rows:
            return None
        chips = []
        for entry in rows:
            state = entry["open"]
            token = "success" if state else ("muted" if state is False else "error")
            word = "open" if state else ("closed" if state is False else "unknown")
            why = entry.get("why", "")
            # Name a holiday on the chip itself: "US closed" during New York
            # hours is confusing until you know why.
            if not state and "holiday" in why:
                word = "holiday"
            chips.append(chip(
                f"{entry['code']} {word} · {entry['rules']} rule"
                f"{'s' if entry['rules'] != 1 else ''}",
                token, tooltip=entry["describe"]))
        closed = [e for e in rows if e["open"] is False]
        note = ("" if not closed else
                "Rules on a closed venue are skipped, not stopped. They resume "
                "when the market opens.")
        content = [ft.Row([
            ft.Text("Venues", size=13, weight=ft.FontWeight.W_600, color=pal.text),
            ft.Row(chips, spacing=6, wrap=True, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)]
        if note:
            content.append(ft.Text(note, size=11, color=pal.muted))
        return card(ft.Column(content, spacing=6))

    def open_orders(data: dict) -> ft.Control:
        orders = data["open_orders"]
        if not orders:
            return card(ft.Column([
                ft.Text("Open simulated orders", size=15,
                        weight=ft.FontWeight.W_600, color=pal.text),
                ft.Text("Nothing outstanding. Orders placed by a rule rest here "
                        "until you fill or cancel them.",
                        size=12, color=pal.muted),
            ], spacing=6))

        rows = []
        for order in orders:
            price = (order.limit_price if order.limit_price is not None
                     else order.trigger_price)
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"{order.side.value} {order.quantity:,} "
                                f"{order.symbol}", size=13,
                                weight=ft.FontWeight.W_600, color=pal.text),
                        ft.Text(f"{order.rule_name} · {order.kind.value.lower()}"
                                f" · triggered at {order.trigger_price:,}",
                                size=11, color=pal.muted),
                    ], spacing=2, expand=True),
                    chip(f"{order.age_seconds:.0f}s open", "accent"),
                    ft.Button("Fill", icon=ft.Icons.CHECK,
                              on_click=fill_order(order.id, price),
                              tooltip=f"Record a fill at {price:,}"),
                    ft.Button("Cancel", icon=ft.Icons.CLOSE,
                              on_click=cancel_order(order.id)),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(0, 8, 0, 8),
                border=ft.Border(bottom=ft.BorderSide(1, pal.border)),
            ))
        return card(ft.Column(
            [ft.Text(f"Open simulated orders ({len(orders)})", size=15,
                     weight=ft.FontWeight.W_600, color=pal.text),
             ft.Text("These do not fill by themselves — that is the decision "
                     "you are practising.", size=11, color=pal.muted)] + rows,
            spacing=6))

    def decision_feed() -> ft.Control:
        decisions = runtime.decisions(limit=40)
        if not decisions:
            return card(ft.Column([
                ft.Text("Decision log", size=15, weight=ft.FontWeight.W_600,
                        color=pal.text),
                ft.Text("Empty. Every evaluation appears here — including the "
                        "ones that did nothing, with the reason.",
                        size=12, color=pal.muted),
            ], spacing=6))

        rows = []
        for decision in decisions:
            label, token = OUTCOME_STYLE.get(decision.outcome,
                                             (decision.outcome.value, "muted"))
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Text(_clock(decision.at), size=11, color=pal.muted,
                            width=64),
                    ft.Container(chip(label, token), width=90),
                    ft.Column([
                        ft.Text(decision.rule_name or decision.rule_id, size=12,
                                weight=ft.FontWeight.W_500, color=pal.text),
                        ft.Text(decision.reason, size=11, color=pal.muted,
                                selectable=True),
                    ], spacing=1, expand=True),
                    ft.Text(f"{decision.quote_price:,}"
                            if decision.quote_price is not None else "—",
                            size=11, color=pal.muted, width=80,
                            text_align=ft.TextAlign.RIGHT),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding(0, 7, 0, 7),
                border=ft.Border(bottom=ft.BorderSide(1, pal.border)),
            ))
        return card(ft.Column(
            [ft.Row([
                ft.Text("Decision log", size=15, weight=ft.FontWeight.W_600,
                        color=pal.text),
                ft.Container(expand=True),
                ft.Text("newest first", size=11, color=pal.muted),
            ])] + rows, spacing=6))

    # -- compose -------------------------------------------------------------
    def _compose() -> list[ft.Control]:
        data = runtime.dashboard()
        blocks: list[ft.Control] = [
            ft.Row([
                section("Execution",
                        subtitle="Simulated order flow from rules you wrote."),
                ft.Container(expand=True),
                ft.Button("Evaluate now", icon=ft.Icons.BOLT,
                          on_click=do_tick,
                          tooltip="Run one pass immediately instead of waiting "
                                  "for the next interval."),
                ft.IconButton(ft.Icons.REFRESH, on_click=refresh,
                              tooltip="Refresh this view"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            state_banner(data),
        ]

        if data["total_rules"] == 0:
            blocks.append(empty_state(
                "No rules yet",
                "The engine executes rules you write. Nothing here is suggested "
                "for you — every condition, size and limit is yours.",
                icon=ft.Icons.RULE_FOLDER_OUTLINED,
                action=ft.Button("Write a rule", icon=ft.Icons.ADD,
                                 on_click=lambda _e: on_open_rules and on_open_rules(),
                                 style=ft.ButtonStyle(bgcolor=pal.accent,
                                                      color=pal.on_accent))))
            return blocks

        if data["active_rules"] == 0:
            blocks.append(notice(
                f"{data['total_rules']} rule(s) saved, but none is active. "
                f"Confirm and activate a rule before arming.",
                "accent",
                action=ft.Button("Open rules",
                                 on_click=lambda _e: on_open_rules and on_open_rules())))

        blocks.append(counters(data))
        stale = data.get("calendar_stale") or []
        if stale:
            expired = [row for row in stale if row["expired"]]
            worst = min(stale, key=lambda r: r["days_remaining"])
            blocks.append(notice(
                (f"Exchange calendar data has expired for "
                 f"{', '.join(r['market'] for r in expired)}. Holidays are no "
                 f"longer recognised on those venues."
                 if expired else
                 f"Exchange calendar data runs out in "
                 f"{worst['days_remaining']} days ({worst['market']} first). "
                 f"Regenerate with pkg_tools/generate_calendars.py."),
                "error" if expired else "accent",
                icon=ft.Icons.EVENT_BUSY_OUTLINED))
        venue_card = venues(data)
        if venue_card is not None:
            blocks.append(venue_card)
        blocks.extend([open_orders(data), decision_feed()])
        return blocks

    refresh()
    return body
