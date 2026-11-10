"""Rule list and rule builder (§1, §2).

The form is the product's centre of gravity, so a few decisions are deliberate:

  * **No financial field is pre-selected.** Direction, size, order type, price
    levels and every limit open blank. A pre-filled "BUY" or a default quantity
    would be the program choosing, which the service terms exclude. The one
    dropdown that does carry a default is the AND/OR combinator, which is a
    structural choice about how the operator's own conditions combine, not a
    view about the market.

  * **Errors sit under their own field** (§2 "입력 중 필드별 오류 표시") and
    appear as you type, not on submit. Validation runs on every change and the
    full report is redistributed across the fields it names.

  * **Confirmation shows the rule in plain language, not the form again.**
    Re-reading your own inputs in the same layout you just typed them in
    catches nothing. `Rule.summary()` renders one sentence describing what will
    happen, which is a different enough view to notice a mistake in.

  * **Activation is two steps.** Save produces a DRAFT; confirming produces a
    CONFIRMED rule; activating arms it for evaluation. Editing a decision field
    silently reverts it to DRAFT, and the banner says so.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional

import flet as ft

from core import markets
from core.rules import (CancelCondition, Comparator, Limits, OrderKind,
                        PriceCondition, Rule, RuleStatus, Side, SizeMode,
                        validate)
from core.i18n import LocaleContext
from core.theme import RADII, active
from ui.build_widgets import localize_tree, make_bilingual
from ui.components import LocalText, card, chip, empty_state, group_digits, notice, number_field, section
from ui.localization import translate_controls

STATUS_STYLE: dict[RuleStatus, tuple[str, str]] = {
    RuleStatus.DRAFT:     ("Draft", "muted"),
    RuleStatus.CONFIRMED: ("Confirmed", "accent"),
    RuleStatus.ACTIVE:    ("Active", "success"),
    RuleStatus.PAUSED:    ("Paused", "muted"),
    RuleStatus.EXHAUSTED: ("Exhausted", "muted"),
    RuleStatus.EXPIRED:   ("Expired", "muted"),
    RuleStatus.CANCELLED: ("Cancelled", "muted"),
}

COMPARATOR_LABEL = {
    Comparator.AT_OR_BELOW:  "is at or below",
    Comparator.AT_OR_ABOVE:  "is at or above",
    Comparator.CROSSES_DOWN: "crosses down through",
    Comparator.CROSSES_UP:   "crosses up through",
}

# Korean readings (owner UI review, 2026-11-10). Fixed strings are in the page catalogue
# (core/ui_page_messages/build_pages.py); these cover the sentences that carry the operator's
# own values. Display only: the English sentence stays the source.
COMPARATOR_KO = {
    Comparator.AT_OR_BELOW:  "이하일 때",
    Comparator.AT_OR_ABOVE:  "이상일 때",
    Comparator.CROSSES_DOWN: "아래로 뚫고 내려갈 때",
    Comparator.CROSSES_UP:   "위로 뚫고 올라갈 때",
}
_STATUS_WORD_KO = {"draft": "초안", "confirmed": "확인됨", "active": "활성"}
RULES_KO = (
    (r"rev (\d+)", "개정 {1}"),
    (r"fired (\d+)(/\d+)?", "실행 {1}{2}회"),
    (r"until (.+)", "{1}까지"),
    (r"(\d+) field\(s\) need attention", "입력 항목 {1}개를 확인해야 합니다"),
    (r"Deleted (.+)\.", "{1}을(를) 삭제했습니다."),
    (r"Saved as (\w+)\.", lambda m: f"{_STATUS_WORD_KO.get(m[1], m[1])} 상태로 저장했습니다."),
    (r"(.+) and its edit history will be removed from this machine\.",
     "{1}과(와) 수정 기록을 이 컴퓨터에서 삭제합니다."),
    (r"e\.g\. (.+)", "예: {1}"),
    (r"Will be requested as (\S+) \((\w+)\)\.", "{1}({2})로 시세를 요청합니다."),
    (r"Limits: none set", "한도: 설정 안 함"),
    (r"Limits: (.+)", lambda m: "한도: " + _caps_ko(m[1])),
)


def _caps_ko(text: str) -> str:
    out = []
    for part in text.split("; "):
        part = part.replace("at most ", "최대 ").replace(" time(s)", "회")
        part = part.replace(" per order", " (주문당)").replace(" per day", " (하루)")
        out.append(part)
    return "; ".join(out)


def _summary_ko(rule: Rule) -> str:
    """Korean twin of `Rule.summary()`: the same fields read back, unset parts still bracketed."""
    symbol = rule.symbol or "(종목 없음)"
    if not rule.conditions:
        condition = "(조건 없음)"
    else:
        joiner = " 그리고 " if rule.require_all_conditions else " 또는 "
        condition = joiner.join(f"현재가가 {c.level:,} {COMPARATOR_KO[c.comparator]}" for c in rule.conditions)
    side = {Side.BUY: "매수", Side.SELL: "매도"}.get(rule.side, "(방향 미설정)")
    if rule.size_value is None or rule.size_mode is None:
        size = "(수량 미설정)"
    elif rule.size_mode is SizeMode.QUANTITY:
        size = f"{rule.size_value:,}주"
    else:
        size = f"금액 {rule.size_value:,}어치"
    if rule.order_kind is OrderKind.MARKET:
        kind = "시장가 주문"
    elif rule.order_kind is OrderKind.LIMIT:
        kind = (f"{rule.limit_price:,} 지정가 주문" if rule.limit_price is not None
                else "지정가 주문 (지정가 없음)")
    else:
        kind = "(주문 유형 미설정)"
    return f"{symbol}: {condition}, {kind}으로 {size}를 {side}합니다."


def _summary_text(rule: Rule, **kwargs) -> ft.Text:
    return LocalText(_summary_ko(rule), rule.summary(), **kwargs)


# Sourced from the registry so the operator can never pick a venue the feed
# cannot route. The previous build hard-coded this list and let a rule be saved
# on a market that halted the engine at evaluation time.
MARKETS = markets.codes()


def _decimal(text: str) -> Optional[Decimal]:
    text = (text or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _int(text: str) -> Optional[int]:
    text = (text or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _enum(cls, raw):
    """Coerce a dropdown value to an enum member, or None.

    Flet can deliver a callback with `value=None` (for example when a menu is
    opened and dismissed without a choice). `Comparator(None)` raises, and an
    exception escaping a Flet event handler takes the entire application down
    rather than just the control — so every enum read from the UI goes through
    here.
    """
    if raw in (None, ""):
        return None
    try:
        return cls(raw)
    except ValueError:
        return None


def build_rules_page(page: ft.Page, store, *,
                     on_changed: Optional[Callable[[], None]] = None
                     ) -> ft.Control:
    pal = active()
    editing: dict[str, Optional[Rule]] = {"rule": None}
    body = ft.Column(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def localized(control):
        """Toasts and dialogs open outside the localized view tree: localize them here."""
        localize_tree(control, RULES_KO)
        translate_controls(control, getattr(page, "qg_locale", None) or LocaleContext("en_US"))
        return control

    def toast(message: str) -> None:
        page.show_dialog(ft.SnackBar(localized(ft.Text(message, color=pal.text)),
                              bgcolor=pal.surface_2))

    def refresh() -> None:
        body.controls = (_editor() if editing["rule"] is not None else _list())
        localize_tree(body, RULES_KO)
        try:
            page.update()
        except Exception:
            pass
        if on_changed:
            on_changed()

    # ---------------------------------------------------------------- listing
    def start_new(_e=None) -> None:
        editing["rule"] = Rule()
        refresh()

    def start_edit(rule: Rule) -> Callable:
        def handler(_e):
            editing["rule"] = rule
            refresh()
        return handler

    def set_status(rule: Rule, status: RuleStatus, message: str) -> Callable:
        def handler(_e):
            store.save(rule.with_status(status))
            toast(message)
            refresh()
        return handler

    def confirm_rule(rule: Rule) -> Callable:
        def handler(_e):
            store.save(rule.confirm())
            toast("Confirmed. Activate it when you want the engine to watch it.")
            refresh()
        return handler

    def delete_rule(rule: Rule) -> Callable:
        def handler(_e):
            def yes(_):
                store.delete(rule.id)
                page.pop_dialog()
                toast(f"Deleted {rule.name or rule.id}.")
                refresh()
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete this rule?"),
                content=ft.Text(f"{rule.name or rule.id} and its edit history "
                                f"will be removed from this machine."),
                actions=[ft.Button("Keep it", on_click=lambda _e: page.pop_dialog()),
                         ft.Button("Delete", on_click=yes,
                                   style=ft.ButtonStyle(color=pal.error))],
            )
            page.show_dialog(localized(dialog))
        return handler

    def rule_row(rule: Rule) -> ft.Control:
        label, token = STATUS_STYLE[rule.status]
        actions: list[ft.Control] = []
        report = validate(rule)

        if rule.status is RuleStatus.DRAFT:
            actions.append(ft.Button(
                "Review & confirm", icon=ft.Icons.FACT_CHECK_OUTLINED,
                on_click=confirm_rule(rule), disabled=not report.ok,
                tooltip=("Fix the errors first"
                         if not report.ok else "Read the summary and confirm")))
        elif rule.status is RuleStatus.CONFIRMED:
            actions.append(ft.Button(
                "Activate", icon=ft.Icons.PLAY_ARROW,
                on_click=set_status(rule, RuleStatus.ACTIVE,
                                    "Active. It will be evaluated while the "
                                    "engine is armed."),
                style=ft.ButtonStyle(bgcolor=pal.accent, color=pal.on_accent)))
        elif rule.status is RuleStatus.ACTIVE:
            actions.append(ft.Button(
                "Pause", icon=ft.Icons.PAUSE,
                on_click=set_status(rule, RuleStatus.PAUSED, "Paused.")))
        elif rule.status is RuleStatus.PAUSED:
            actions.append(ft.Button(
                "Resume", icon=ft.Icons.PLAY_ARROW,
                on_click=set_status(rule, RuleStatus.ACTIVE, "Active again.")))

        actions.append(ft.IconButton(ft.Icons.EDIT_OUTLINED,
                                     on_click=start_edit(rule), tooltip="Edit"))
        actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE,
                                     on_click=delete_rule(rule),
                                     tooltip="Delete", icon_color=pal.error))

        meta = [f"rev {rule.revision}"]
        if rule.trigger_count:
            cap = (f"/{rule.limits.max_triggers}"
                   if rule.limits.max_triggers else "")
            meta.append(f"fired {rule.trigger_count}{cap}")
        if rule.valid_to:
            meta.append(f"until {rule.valid_to.astimezone():%Y-%m-%d %H:%M}")

        return card(ft.Column([
            ft.Row([
                ft.Text(rule.name or "(unnamed)", size=15,
                        weight=ft.FontWeight.W_600, color=pal.text),
                chip(label, token),
                ft.Container(expand=True),
                ft.Row(actions, spacing=2),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            _summary_text(rule, size=13, color=pal.text, selectable=True),
            ft.Row([ft.Text(m, size=12, color=pal.muted) for m in meta], spacing=12, wrap=True),
        ] + ([ft.Text(f"{len(report.errors)} field(s) need attention",
                      size=12, color=pal.error)] if not report.ok else []),
            spacing=6))

    def _list() -> list[ft.Control]:
        rules = store.all()
        head = ft.Row([
            section("Rules", subtitle="Your conditions. The program adds none."),
            ft.Container(expand=True),
            ft.Button("New rule", icon=ft.Icons.ADD, on_click=start_new,
                      style=ft.ButtonStyle(bgcolor=pal.accent,
                                           color=pal.on_accent)),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        if not rules:
            return [head, empty_state(
                "No rules yet",
                "A rule says: when this price condition holds, place this order "
                "at this size, within these limits. Every part of that is yours "
                "to write.",
                icon=ft.Icons.RULE_FOLDER_OUTLINED,
                action=ft.Button("Write your first rule", icon=ft.Icons.ADD,
                                 on_click=start_new,
                                 style=ft.ButtonStyle(bgcolor=pal.accent,
                                                      color=pal.on_accent)))]
        return [head] + [rule_row(r) for r in rules]

    # ----------------------------------------------------------------- editor
    def _editor() -> list[ft.Control]:
        draft: dict[str, Rule] = {"rule": editing["rule"]}
        # Conditions are edited as a plain list and rebuilt into the Rule on
        # every change, so add/remove needs no separate diffing.
        conditions: list[dict] = [
            {"comparator": c.comparator, "level": str(c.level)}
            for c in draft["rule"].conditions
        ] or [{"comparator": None, "level": ""}]

        fields: dict[str, ft.Control] = {}
        error_slots: dict[str, ft.Text] = {}
        preview = ft.Text("", size=13, color=pal.text, selectable=True)
        # Shown at authoring time rather than at engine-halt time: FMP answers
        # HTTP 402 for every suffixed symbol on a plan without international
        # coverage, so a rule on these venues can be saved but never evaluated.
        plan_note = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color=pal.error),
                ft.Text("Your FMP plan returns HTTP 402 for this venue. The rule "
                        "can be saved, but the engine cannot quote it until the "
                        "plan covers international exchanges.",
                        size=11, color=pal.text, expand=True),
            ], spacing=8),
            padding=10, bgcolor=pal.surface_2,
            border=ft.Border.all(1, pal.error), border_radius=RADII["sm"],
            visible=False)
        warn_box = ft.Column(spacing=2)
        actions_row = ft.Row(spacing=8)

        def collect() -> Rule:
            base = draft["rule"]
            parsed = tuple(
                PriceCondition(c["comparator"], _decimal(c["level"]))
                for c in conditions
                if c["comparator"] is not None and _decimal(c["level"]) is not None
            )
            changes = dict(
                name=fields["name"].value or "",
                symbol=(fields["symbol"].value or "").strip(),
                market=fields["market"].value or "",
                side=_enum(Side, fields["side"].value),
                size_mode=_enum(SizeMode, fields["size_mode"].value),
                size_value=_decimal(fields["size_value"].value),
                order_kind=_enum(OrderKind, fields["order_kind"].value),
                limit_price=_decimal(fields["limit_price"].value),
                conditions=parsed,
                require_all_conditions=fields["logic"].value != "any",
                limits=Limits(
                    max_triggers=_int(fields["max_triggers"].value),
                    max_order_amount=_decimal(fields["max_order_amount"].value),
                    max_daily_amount=_decimal(fields["max_daily_amount"].value),
                ),
                cancel=CancelCondition(
                    after_seconds=_int(fields["cancel_after"].value)),
            )
            # `edit()` bumps the revision, which is only correct on save. For
            # live preview we build the candidate directly.
            from dataclasses import replace
            return replace(base, **changes)

        def revalidate(_e=None) -> None:
            candidate = collect()
            report = validate(candidate)
            for name, slot in error_slots.items():
                issues = [i for i in report.issues if i.field == name
                          or i.field.startswith(f"{name}[")
                          or i.field.startswith(f"{name}.")]
                slot.value = "  ".join(i.message for i in issues)
                slot.color = (pal.error
                              if any(i.blocking for i in issues) else pal.muted)
                slot.visible = bool(issues)
            chosen = markets.get(candidate.market)
            plan_note.visible = bool(chosen and chosen.needs_intl_plan)
            fields["symbol"].hint_text = (
                f"e.g. {chosen.example}" if chosen else "choose a market first")
            routed = markets.provider_symbol(candidate.market, candidate.symbol)
            error_slots["symbol"].visible = (
                error_slots["symbol"].visible
                or bool(chosen and routed != candidate.symbol))
            if chosen and routed != candidate.symbol and candidate.symbol:
                error_slots["symbol"].value = (
                    f"Will be requested as {routed} ({chosen.currency}).")
                error_slots["symbol"].color = pal.muted
            preview.value = candidate.summary()
            make_bilingual(preview, _summary_ko(candidate))
            preview.render_locale(getattr(page, "qg_locale", None) or LocaleContext("en_US"))
            warn_box.controls = [
                ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=13, color=pal.muted),
                        ft.Text(i.message, size=11, color=pal.muted, expand=True)],
                       spacing=6)
                for i in report.warnings
            ]
            save_button.disabled = False
            confirm_button.disabled = not report.ok
            confirm_button.tooltip = ("Fix the highlighted fields first"
                                      if not report.ok else
                                      "Read the sentence above, then confirm")
            try:
                page.update()
            except Exception:
                pass

        def text_field(key: str, label: str, *, hint: str = "",
                       width: Optional[int] = None, numeric: bool = False) -> ft.Column:
            if numeric:     # amounts and prices read 1,000,000 once typed; `_decimal` strips the commas
                fields[key] = number_field(label, "", hint_text=hint, dense=True, on_change=revalidate,
                                           border_radius=RADII["sm"], width=width)
            else:
                fields[key] = ft.TextField(
                    label=label, hint_text=hint, value="", dense=True,
                    on_change=revalidate, border_radius=RADII["sm"], width=width)
            error_slots[key] = ft.Text("", size=11, color=pal.error, visible=False)
            return ft.Column([fields[key], error_slots[key]], spacing=2)

        def dropdown(key: str, label: str, options: list[tuple[str, str]], *,
                     width: Optional[int] = None) -> ft.Column:
            # Flet 0.85 names the dropdown callback `on_select`; `on_change`
            # is a TypeError at construction, not a silent no-op.
            fields[key] = ft.Dropdown(
                label=label, value=None, dense=True, width=width,
                on_select=revalidate, border_radius=RADII["sm"],
                options=[ft.dropdown.Option(key=k, text=t) for k, t in options])
            error_slots[key] = ft.Text("", size=11, color=pal.error, visible=False)
            return ft.Column([fields[key], error_slots[key]], spacing=2)

        # -- build the controls, then seed them from the rule being edited
        name_c = text_field("name", "Rule name", hint="How you will recognise it")
        symbol_c = text_field("symbol", "Instrument code")
        market_c = dropdown("market", "Market", list(markets.options()))
        side_c = dropdown("side", "Direction",
                          [(s.value, s.value.title()) for s in Side])
        size_mode_c = dropdown("size_mode", "Size is a",
                               [(SizeMode.QUANTITY.value, "Share count"),
                                (SizeMode.NOTIONAL.value, "Cash amount")])
        size_value_c = text_field("size_value", "Size", numeric=True)
        order_kind_c = dropdown("order_kind", "Order type",     # "Market" alone would read as the venue
                                [(OrderKind.MARKET.value, "Market order"), (OrderKind.LIMIT.value, "Limit order")])
        limit_price_c = text_field("limit_price", "Limit price",
                                   hint="Only for a limit order", numeric=True)
        logic_c = dropdown("logic", "Conditions must",
                           [("all", "All be true (AND)"),
                            ("any", "Any be true (OR)")])
        max_triggers_c = text_field("max_triggers", "Max times this rule may fire")
        max_order_c = text_field("max_order_amount", "Max amount per order", numeric=True)
        max_daily_c = text_field("max_daily_amount", "Max amount per day", numeric=True)
        cancel_after_c = text_field("cancel_after",
                                    "Cancel unfilled order after (s)")

        rule = draft["rule"]
        fields["name"].value = rule.name
        fields["symbol"].value = rule.symbol
        fields["market"].value = rule.market or None
        fields["side"].value = rule.side.value if rule.side else None
        fields["size_mode"].value = rule.size_mode.value if rule.size_mode else None
        fields["size_value"].value = group_digits(str(rule.size_value)) if rule.size_value is not None else ""
        fields["order_kind"].value = rule.order_kind.value if rule.order_kind else None
        fields["limit_price"].value = group_digits(str(rule.limit_price)) if rule.limit_price is not None else ""
        fields["logic"].value = "all" if rule.require_all_conditions else "any"
        fields["max_triggers"].value = ("" if rule.limits.max_triggers is None
                                        else str(rule.limits.max_triggers))
        fields["max_order_amount"].value = ("" if rule.limits.max_order_amount is None
                                            else group_digits(str(rule.limits.max_order_amount)))
        fields["max_daily_amount"].value = ("" if rule.limits.max_daily_amount is None
                                            else group_digits(str(rule.limits.max_daily_amount)))
        fields["cancel_after"].value = ("" if rule.cancel.after_seconds is None
                                        else str(rule.cancel.after_seconds))

        # -- conditions editor
        condition_host = ft.Column(spacing=8)

        def render_conditions() -> None:
            condition_host.controls = []
            for index, entry in enumerate(conditions):
                def on_cmp(e, i=index):
                    conditions[i]["comparator"] = _enum(
                        Comparator, getattr(e.control, "value", None))
                    revalidate()

                def on_level(e, i=index):
                    conditions[i]["level"] = e.control.value
                    revalidate()

                def on_remove(_e, i=index):
                    if len(conditions) > 1:
                        conditions.pop(i)
                    else:
                        conditions[0] = {"comparator": None, "level": ""}
                    render_conditions()
                    revalidate()

                condition_host.controls.append(ft.Row([
                    ft.Text("Last price", size=12, color=pal.muted, width=76),
                    ft.Dropdown(
                        value=entry["comparator"].value if entry["comparator"] else None,
                        dense=True, expand=True, on_select=on_cmp,
                        border_radius=RADII["sm"],
                        options=[ft.dropdown.Option(key=c.value,
                                                    text=COMPARATOR_LABEL[c])
                                 for c in Comparator]),
                    ft.TextField(value=entry["level"], dense=True, width=140,
                                 hint_text="price", on_change=on_level,
                                 border_radius=RADII["sm"]),
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                  on_click=on_remove, tooltip="Remove"),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))

            condition_host.controls.append(ft.Button(
                "Add condition", icon=ft.Icons.ADD,
                on_click=lambda _e: (conditions.append(
                    {"comparator": None, "level": ""}),
                    render_conditions(), revalidate())))
            error_slots["conditions"] = error_slots.get(
                "conditions", ft.Text("", size=11, color=pal.error, visible=False))
            condition_host.controls.append(error_slots["conditions"])

        render_conditions()

        # -- actions
        def do_save(_e) -> None:
            candidate = collect()
            saved = store.save(draft["rule"].edit(**{
                k: getattr(candidate, k) for k in
                ("name", "symbol", "market", "side", "size_mode", "size_value",
                 "order_kind", "limit_price", "conditions",
                 "require_all_conditions", "limits", "cancel")
            }))
            editing["rule"] = None
            toast(f"Saved as {STATUS_STYLE[saved.status][0].lower()}.")
            refresh()

        def do_confirm(_e) -> None:
            candidate = collect()
            report = validate(candidate)
            if not report.ok:
                revalidate()
                return

            def yes(_):
                saved = store.save(draft["rule"].edit(**{
                    k: getattr(candidate, k) for k in
                    ("name", "symbol", "market", "side", "size_mode",
                     "size_value", "order_kind", "limit_price", "conditions",
                     "require_all_conditions", "limits", "cancel")
                }).confirm())
                page.pop_dialog()
                editing["rule"] = None
                toast("Confirmed. Activate it on the list when you are ready.")
                refresh()

            caps = candidate.limits
            cap_lines = []
            if caps.max_triggers is not None:
                cap_lines.append(f"at most {caps.max_triggers} time(s)")
            if caps.max_order_amount is not None:
                cap_lines.append(f"at most {caps.max_order_amount:,} per order")
            if caps.max_daily_amount is not None:
                cap_lines.append(f"at most {caps.max_daily_amount:,} per day")

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Is this what you meant?"),
                content=ft.Column([
                    _summary_text(candidate, size=14, color=pal.text, selectable=True),
                    ft.Text("Limits: " + ("; ".join(cap_lines) if cap_lines
                                          else "none set"),
                            size=12, color=pal.muted),
                    ft.Text("Confirming does not arm it. You activate the rule "
                            "on the list, and the engine only acts while armed.",
                            size=11, color=pal.muted),
                ], spacing=10, tight=True),
                actions=[
                    ft.Button("Keep editing",
                              on_click=lambda _e: page.pop_dialog()),
                    ft.Button("Confirm", on_click=yes,
                              style=ft.ButtonStyle(bgcolor=pal.accent,
                                                   color=pal.on_accent)),
                ],
            )
            page.show_dialog(localized(dialog))

        def do_cancel(_e) -> None:
            editing["rule"] = None
            refresh()

        save_button = ft.Button("Save draft", icon=ft.Icons.SAVE_OUTLINED,
                                on_click=do_save)
        confirm_button = ft.Button("Review & confirm",
                                   icon=ft.Icons.FACT_CHECK_OUTLINED,
                                   on_click=do_confirm,
                                   style=ft.ButtonStyle(bgcolor=pal.accent,
                                                        color=pal.on_accent))
        actions_row.controls = [
            ft.Button("Discard", on_click=do_cancel), ft.Container(expand=True),
            save_button, confirm_button,
        ]

        def group(title: str, hint: str, *controls: ft.Control) -> ft.Control:
            return card(ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=pal.text),
                ft.Text(hint, size=11, color=pal.muted),
                ft.Container(height=4),
                *controls,
            ], spacing=6))

        blocks: list[ft.Control] = [
            ft.Row([
                section("Edit rule" if rule.name else "New rule",
                        subtitle="Every field is blank until you fill it."),
                ft.Container(expand=True),
            ]),
        ]
        if rule.is_confirmed:
            blocks.append(notice(
                "This rule is already confirmed. Changing a condition, size or "
                "limit returns it to draft and you will confirm it again.",
                "accent", icon=ft.Icons.EDIT_NOTE))

        blocks.extend([
            group("What and where",
                  "The instrument this rule watches.",
                  ft.ResponsiveRow([
                      ft.Container(name_c, col={"xs": 12, "md": 6}),
                      ft.Container(symbol_c, col={"xs": 12, "md": 3}),
                      ft.Container(market_c, col={"xs": 12, "md": 3}),
                  ], spacing=12, run_spacing=4), plan_note),
            group("When it fires",
                  "Conditions are compared against the last traded price.",
                  ft.Container(logic_c, width=240), condition_host),
            group("What it does",
                  "The order placed when the conditions hold.",
                  ft.ResponsiveRow([
                      ft.Container(side_c, col={"xs": 12, "md": 3}),
                      ft.Container(size_mode_c, col={"xs": 12, "md": 3}),
                      ft.Container(size_value_c, col={"xs": 12, "md": 3}),
                      ft.Container(order_kind_c, col={"xs": 12, "md": 3}),
                      ft.Container(limit_price_c, col={"xs": 12, "md": 4}),
                  ], spacing=12, run_spacing=4)),
            group("Limits",
                  "Ceilings this rule may never cross. Leave blank for none — "
                  "blank means no ceiling, not a safe default.",
                  ft.ResponsiveRow([
                      ft.Container(max_triggers_c, col={"xs": 12, "md": 4}),
                      ft.Container(max_order_c, col={"xs": 12, "md": 4}),
                      ft.Container(max_daily_c, col={"xs": 12, "md": 4}),
                      ft.Container(cancel_after_c, col={"xs": 12, "md": 6}),
                  ], spacing=12, run_spacing=4)),
            card(ft.Column([
                ft.Text("In plain language", size=14, weight=ft.FontWeight.W_600,
                        color=pal.text),
                preview,
                warn_box,
            ], spacing=8)),
            actions_row,
        ])
        revalidate()
        return blocks

    refresh()
    return body
