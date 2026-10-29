"""QUANTGEN — the operator's quantitative finance research application.

Built on the NEXTGEN base (its rule engine, simulated order book and KRX data
layer survive intact; the skill cockpit moved to TRADEGEN on 2026-10-23) and
upgraded with the thing the client build was contractually forbidden from
having: an opinion. Three new equity surfaces —

  * **Quant Lab** — Monte Carlo simulation (GBM, Merton jump-diffusion, block
    bootstrap) calibrated on daily history, with VaR/CVaR and a percentile fan.
  * **Portfolio** — Markowitz optimization, risk parity, and the efficient
    frontier, solved with scipy on aligned histories.
  * **Signals** — a weighted technical composite with dissent shown, and a
    costed backtest of the same idea against buy-and-hold.

— and, for the FICC desk the operator is training for, five more:

  * **Macro** — the cross-asset sheet (curve, real yields, breakevens, credit,
    dollar, vol) with z-scores, a regime read, and the daily / weekly report.
  * **Rates** — Treasury curve bootstrap, Nelson-Siegel, PCA, swap and swaption
    pricing (Black-76 / Bachelier), short-rate simulation (Vasicek, CIR, HW).
  * **Bonds** — price/yield, duration, convexity, DV01, key-rate DV01, carry and
    roll-down, curve scenarios, futures hedge ratio.
  * **FX** — CIP forwards and basis, Garman-Kohlhagen Greeks, RR/BF smiles with
    a SABR fit, and a G10+KRW carry basket with a no-lookahead backtest.
  * **Structuring** — principal-protected notes, reverse convertibles,
    dual-currency deposits and steepener notes, each with a hedge sheet.

Every result carries two layers of written analysis: a deterministic local
narrative (always), and Claude deep analysis when ANTHROPIC_API_KEY is set.
gs_quant powers realized-vol/drawdown analytics offline and can open a Marquee
session when GS credentials exist. This is a personal build: not a client
deliverable, not for commercial distribution.

TWO FIXES INHERITED FROM NEXTGEN REMAIN LOAD-BEARING
----------------------------------------------------
1. `page.on_resize` — Flet 0.85 does not define `on_resized`; assigning it is
   silently accepted and never fires.
2. Views are built once and cached, so a running simulation or armed engine
   survives a tab switch.
"""
from __future__ import annotations

import flet as ft

import config
from core.app_paths import assets_directory
from core.theme import BREAKPOINTS, RADII, TRANSITION_MS, active, set_mode
from core.engine.feed import QuoteFeed
from core.engine.runtime import EngineRuntime
from core.rules.store import RuleStore
from data.krx import KRXGateway
from ui.bonds_page import build_bonds_page
from ui.crypto_page import build_crypto_page
from ui.derivatives_page import build_derivatives_page
from ui.etf_page import build_etf_page
from ui.fx_page import build_fx_page
from ui.strategy_lab_page import build_strategy_lab_page
from ui.krx_page import build_krx_page
from ui.macro_page import build_macro_page
from ui.portfolio_page import build_portfolio_page
from ui.quant_lab_page import build_quant_lab_page
from ui.rates_page import build_rates_page
from ui.structuring_page import build_structuring_page
from ui.rules_page import build_rules_page
from ui.signals_page import build_signals_page
from ui.trading_page import build_trading_page
from ui.settings_page import build_settings_page
from ui.research_home import build_home_page, build_library_page, build_system_page

LOCALE = "en"

NAV = (
    ("macro", "Macro", ft.Icons.PUBLIC_OUTLINED),
    ("rates", "Rates", ft.Icons.SSID_CHART_ROUNDED),
    ("bonds", "Bonds", ft.Icons.RECEIPT_LONG_OUTLINED),
    ("fx", "FX", ft.Icons.CURRENCY_EXCHANGE_OUTLINED),
    ("structuring", "Structuring", ft.Icons.LAYERS_OUTLINED),
    ("derivatives", "Derivatives", ft.Icons.STACKED_LINE_CHART_OUTLINED),
    ("etf", "ETF", ft.Icons.INVENTORY_2_OUTLINED),
    ("crypto", "Crypto", ft.Icons.CURRENCY_BITCOIN),
    ("lab", "Strategy Lab", ft.Icons.SCIENCE_OUTLINED),
    ("quant", "Quant Lab", ft.Icons.TROUBLESHOOT_OUTLINED),
    ("portfolio", "Portfolio", ft.Icons.PIE_CHART_OUTLINE),
    ("signals", "Signals", ft.Icons.CANDLESTICK_CHART_OUTLINED),
    ("trading", "Execution", ft.Icons.SPEED_ROUNDED),
    ("rules", "Rules", ft.Icons.RULE_FOLDER_OUTLINED),
    ("krx", "KRX", ft.Icons.SHOW_CHART_ROUNDED),
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED),
)


# Existing page keys stay stable; these groups only change navigation.
WORKSPACES = (
    ("home", "Research Home", ft.Icons.HOME_OUTLINED, ("home",)),
    ("markets", "Markets", ft.Icons.PUBLIC_OUTLINED,
     ("macro", "rates", "bonds", "fx", "derivatives", "etf", "crypto", "krx")),
    ("build", "Build & Test", ft.Icons.SCIENCE_OUTLINED,
     ("quant", "lab", "signals", "structuring", "trading")),
    ("risk", "Portfolio & Risk", ft.Icons.PIE_CHART_OUTLINE, ("portfolio",)),
    ("library", "Research Library", ft.Icons.FOLDER_OPEN_OUTLINED, ("library",)),
    ("system", "System", ft.Icons.SETTINGS_OUTLINED, ("system", "rules", "settings")),
)


def main(page: ft.Page) -> None:
    page.title = "QUANTGEN"
    page.padding = 0
    page.fonts = {"QG Interface": "fonts/qg-interface.otf"}
    page.theme = ft.Theme(font_family="QG Interface", color_scheme_seed="#194C40")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.min_width = 320
    page.window.min_height = 620
    set_mode("light")
    pal = active()
    page.bgcolor = pal.bg

    gateway = KRXGateway()

    # Trading system. Constructed here so the engine outlives page navigation:
    # a rule set and a running evaluation loop must not be torn down because
    # the operator looked at another tab.
    rule_store = RuleStore()
    engine = EngineRuntime(rule_store, QuoteFeed(gateway))

    current = {"page": "home"}
    cache: dict[str, ft.Control] = {}

    content = ft.AnimatedSwitcher(
        content=ft.Container(), duration=TRANSITION_MS,
        reverse_duration=TRANSITION_MS, expand=True,
    )

    # ------------------------------------------------------------------ views
    def build(name: str) -> ft.Control:
        if name == "home":
            return build_home_page(page, navigate=navigate)
        if name == "library":
            return build_library_page(page, navigate=navigate)
        if name == "system":
            return build_system_page(page, navigate=navigate)
        ficc = {"macro": build_macro_page, "rates": build_rates_page,
                "bonds": build_bonds_page, "fx": build_fx_page,
                "structuring": build_structuring_page,
                "derivatives": build_derivatives_page, "etf": build_etf_page,
                "crypto": build_crypto_page, "lab": build_strategy_lab_page}
        if name in ficc:
            return ficc[name](page, on_open_settings=lambda: navigate("settings"))
        if name == "quant":
            return build_quant_lab_page(page,
                                        on_open_settings=lambda: navigate("settings"))
        if name == "portfolio":
            return build_portfolio_page(page,
                                        on_open_settings=lambda: navigate("settings"))
        if name == "signals":
            return build_signals_page(page,
                                      on_open_settings=lambda: navigate("settings"))
        if name == "trading":
            return build_trading_page(page, engine,
                                      on_open_rules=lambda: navigate("rules"),
                                      on_open_settings=lambda: navigate("settings"))
        if name == "rules":
            return build_rules_page(page, rule_store,
                                    on_changed=lambda: cache.pop("trading", None))
        if name == "krx":
            return build_krx_page(page, gateway, locale=LOCALE,
                                  on_open_settings=lambda: navigate("settings"))
        return build_settings_page(page)

    def navigate(name: str, *, rebuild: bool = False) -> None:
        # Execution must reflect state that changed elsewhere; everything else
        # keeps its live view so a pipeline survives a tab switch.
        if rebuild or name in {"trading", "library"}:
            cache.pop(name, None)
        if name not in cache:
            cache[name] = build(name)
        if name == "home":
            cache[name].render()  # refresh session observations without abandoning an in-flight fetch
        current["page"] = name
        content.content = ft.Container(cache[name], padding=16 if state["compact"] else 28, expand=True)
        render_nav()
        page.update()

    # -------------------------------------------------------------------- nav
    def brand():
        return ft.Row([
            ft.Container(ft.Image(src="branding/f1-symbol.svg", width=34, height=34,
                                  semantics_label="QUANTGEN F1 Open Horizon"),
                         padding=3, bgcolor="#F7F5F0", border_radius=8),
            ft.Column([ft.Text("QUANTGEN", size=16, weight=ft.FontWeight.W_600, color=pal.text),
                       ft.Text("RESEARCH WORKSPACE", size=9, color=pal.muted)], spacing=2),
        ], spacing=10)

    nav_host = ft.Column(spacing=5)
    state = {"compact": False}
    labels = {key: (label, icon) for key, label, icon in NAV}
    labels.update(home=("Research Home", ft.Icons.HOME_OUTLINED),
                  library=("Research Library", ft.Icons.FOLDER_OPEN_OUTLINED),
                  system=("Project status", ft.Icons.INFO_OUTLINED))
    # Execution's existing simulated engine is unchanged; its label is explicit.
    labels["trading"] = ("Execution · simulated", ft.Icons.SPEED_ROUNDED)
    workspace_title = ft.Text("Research Home", size=13, color=pal.muted)

    def nav_button(label, icon, route, *, selected=False, indent=False, modal=False):
        def click(e):
            if modal:
                page.pop_dialog()
            navigate(route)
        return ft.TextButton(
            ft.Row([ft.Icon(icon, size=17, color=pal.accent if selected else pal.muted),
                    ft.Text(label, size=12 if indent else 13, color=pal.accent if selected else pal.text,
                            weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                            expand=True)], spacing=10),
            on_click=click, data={"route": route}, tooltip=label,
            style=ft.ButtonStyle(bgcolor=pal.accent_soft if selected else ft.Colors.TRANSPARENT,
                                 shape=ft.RoundedRectangleBorder(radius=10),
                                 padding=ft.Padding(24 if indent else 12, 10, 10, 10)),
            width=196, height=42)

    def nav_controls(*, modal=False):
        controls = []
        for key, title, icon, routes in WORKSPACES:
            selected = current["page"] in routes
            controls.append(nav_button(title, icon, routes[0], selected=selected, modal=modal))
            if selected or modal:
                if len(routes) > 1:
                    for route in routes:
                        label, child_icon = labels[route]
                        controls.append(nav_button(label, child_icon, route,
                                                   selected=current["page"] == route,
                                                   indent=True, modal=modal))
        return controls

    def render_nav() -> None:
        nav_host.controls = nav_controls()
        workspace_title.value = next(title for _, title, _, routes in WORKSPACES
                                     if current["page"] in routes)

    def open_menu(e=None):
        page.show_dialog(ft.AlertDialog(
            title=brand(), content=ft.Column(nav_controls(modal=True), spacing=4,
                                             scroll=ft.ScrollMode.AUTO, width=240, height=480),
            actions=[ft.TextButton("닫기", on_click=lambda e: page.pop_dialog())],
            bgcolor=pal.surface, inset_padding=16))

    rail = ft.Container(
        content=ft.Column([brand(), ft.Container(height=12),
                           ft.Text("WORKSPACES", size=10, color=pal.muted), nav_host,
                           ft.Container(height=16),
                           ft.Text("Personal research\nEvidence before decisions", size=11, color=pal.muted)],
                          spacing=12, scroll=ft.ScrollMode.AUTO),
        width=224, padding=14, bgcolor=pal.surface)
    mobile_bar = ft.Container(ft.Row([
        ft.IconButton(ft.Icons.MENU_ROUNDED, on_click=open_menu, tooltip="작업공간 메뉴", data="mobile-menu"),
        brand(),
    ], spacing=6), padding=ft.Padding(8, 8, 8, 8), bgcolor=pal.surface, visible=False)
    desktop_bar = ft.Container(ft.Row([
        workspace_title, ft.Text("PERSONAL RESEARCH", size=10, color=pal.muted),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.Padding(28, 16, 28, 12))
    separator = ft.VerticalDivider(width=1, color=pal.border)

    def resize(e=None) -> None:
        compact = (page.width or 1200) < BREAKPOINTS["compact"]
        if compact == state["compact"] and e is not None:
            return
        state["compact"] = compact
        rail.visible = not compact
        separator.visible = not compact
        mobile_bar.visible = compact
        desktop_bar.visible = not compact
        if isinstance(content.content, ft.Container):
            content.content.padding = 16 if compact else 28
        render_nav()
        page.update()

    # Flet 0.85 uses on_resize; keep cached views/engine across resize and navigation.
    page.on_resize = resize
    page.add(ft.Row([
        rail, separator,
        ft.Column([mobile_bar, desktop_bar, content], expand=True, spacing=0),
    ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH))
    resize()
    navigate(current["page"])
    # v2 M8: governance-chain check + missed decisions, once per process, off the UI thread (rulings 3.13; T-OBS-02/05).
    try:
        __import__("core.skills.macro_daily", fromlist=["on_app_start"]).on_app_start(background=True)
    except Exception:
        pass


if __name__ == "__main__":
    ft.run(main, assets_dir=assets_directory())
