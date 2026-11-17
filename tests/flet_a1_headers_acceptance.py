"""Bounded A1 table headers: synthetic controls, no providers or mutable stores."""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import fields
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import flet as ft
from core.i18n import LocaleContext
from core.ficc.data import synthetic_curve_panel
from core.ficc.macro import MacroRow, MacroSheet, Regime
from ui import bonds_page, fx_page, krx_page, macro_page, rates_page, structuring_page
from ui.localization import literal_text, table_header, translate_controls


def walk(value, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(value, ft.Control) or id(value) in seen:
        return
    seen.add(id(value))
    yield value
    for field in fields(value):
        if field.name.startswith("_"):
            continue
        child = getattr(value, field.name)
        if isinstance(child, (list, tuple)):
            for item in child:
                yield from walk(item, seen)
        else:
            yield from walk(child, seen)


def page():
    return SimpleNamespace(qg_locale=LocaleContext("en_US"), update=lambda: None,
                           run_thread=lambda fn: fn())


def select(root, label, value):
    next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == label).value = value


def click(root, label):
    next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == label).on_click(None)


def cell_values(table):
    return [[cell.content.value for cell in row.cells] for row in table.rows]


class FletA1HeadersTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch("requests.sessions.Session.request",
                                      side_effect=AssertionError("No provider API")))

    def capture_analysis(self, module):
        payloads = []

        def panel(*args, payload_fn, **kwargs):
            payloads.append(payload_fn())
            return ft.Text("Offline analysis fixture")

        self.stack.enter_context(patch.object(module, "analysis_panel", side_effect=panel))
        return payloads

    def inert_charts(self, module, *names):
        for name in names:
            self.stack.enter_context(patch.object(module.fcharts, name,
                                                  side_effect=lambda *a, **k: ft.Text("Chart fixture")))

    def roundtrip(self, root, english, korean, *, table_index=0, payloads=None):
        tables = [c for c in walk(root) if isinstance(c, ft.DataTable)]
        self.assertGreater(len(tables), table_index,
                           [c.value for c in walk(root) if isinstance(c, ft.Text)])
        table = tables[table_index]
        self.assertEqual([c.label.value for c in table.columns], english)
        rows = deepcopy(cell_values(table))
        inputs = [(c, c.value) for c in walk(root) if isinstance(c, (ft.TextField, ft.Dropdown))]
        originals = deepcopy(payloads)
        for _ in range(2):
            for locale, expected in (("ko_KR", korean), ("en_US", english)):
                translate_controls(root, LocaleContext(locale))
                self.assertEqual([c.label.value for c in table.columns], expected)
                self.assertEqual(cell_values(table), rows)
                self.assertEqual([(c, c.value) for c, _ in inputs], inputs)
                self.assertEqual(payloads, originals)
        self.assertEqual([c.label.data["qg_table_header"]["source"] for c in table.columns], english)
        return table

    def test_context_and_literal_markers_preserve_colliding_values(self):
        header = table_header("Account", ko="계정과목")
        literals = [literal_text(v) for v in ("Account", "Price", "2026-11-06", "1,234.56", "사용자 Price")]
        user = ft.TextField(label="Price", value="Account")
        unmarked = ft.Text("Price")
        root = ft.Column([header, *literals, user, unmarked])
        for _ in range(2):
            translate_controls(root, LocaleContext("ko_KR"))
            self.assertEqual(header.value, "계정과목")
            self.assertEqual(unmarked.value, "가격")  # Existing unmarked behavior remains.
            self.assertEqual(user.value, "Account")
            self.assertEqual([c.value for c in literals],
                             ["Account", "Price", "2026-11-06", "1,234.56", "사용자 Price"])
            translate_controls(root, LocaleContext("en_US"))
            self.assertEqual(header.value, "Account")
            self.assertEqual(unmarked.value, "Price")

    def test_structuring_legs_and_hedges_do_not_translate_report_rows(self):
        cases = [
            (["Leg", "Kind", "Value", "Detail"], ["구성요소", "유형", "값", "상세"]),
            (["Instrument", "Quantity", "Unit", "Rationale"], ["상품", "수량", "단위", "근거"]),
        ]
        for en, ko in cases:
            with self.subTest(headers=en):
                rows = [["Account", "Price", "1,234.56", "Provider / 사용자 원문"]]
                original = deepcopy(rows)
                self.roundtrip(structuring_page._table(en, rows), en, ko, payloads=rows)
                self.assertEqual(rows, original)

    def test_rates_and_fx_unselected_tables_retain_default_behavior(self):
        for module in (rates_page, fx_page):
            with self.subTest(module=module.__name__):
                root = module._table(["Price"], [["Price"]])
                table = next(c for c in walk(root) if isinstance(c, ft.DataTable))
                self.assertIsNone(table.columns[0].label.data)
                self.assertIsNone(table.rows[0].cells[0].content.data)
                translate_controls(root, LocaleContext("ko_KR"))
                self.assertEqual(table.columns[0].label.value, "가격")
                self.assertEqual(cell_values(table), [["가격"]])

    def test_krx_five_provider_tables_keep_raw_values_and_accounting_context(self):
        cases = [
            ("daily", "daily", ["date", "open", "high", "low", "close", "volume"],
             ["Date", "Open", "High", "Low", "Close", "Volume"],
             ["일자", "시가", "고가", "저가", "종가", "거래량"]),
            ("filings", "filings", ["date", "title", "filer", "receipt_no"],
             ["Date", "Report", "Filer", "Receipt"], ["일자", "보고서명", "제출인", "접수번호"]),
            ("financials", "financials", ["statement", "account", "this_term", "prev_term"],
             ["Statement", "Account", "This term", "Prev term"],
             ["재무제표 구분", "계정과목", "당기", "전기"]),
            ("snapshot", "market_snapshot", ["ticker", "name", "market", "close", "change_pct", "volume", "market_cap"],
             ["Code", "Name", "Market", "Close", "Chg %", "Volume", "Mkt cap"],
             ["종목코드", "종목명", "시장 구분", "종가", "등락률", "거래량", "시가총액"]),
            ("indices", "indices", ["name", "level", "change", "change_pct"],
             ["Index", "Level", "Change", "Chg %"], ["지수명", "지수", "전일 대비", "등락률"]),
        ]
        for dataset, method, keys, en, ko in cases:
            with self.subTest(dataset=dataset):
                # Deliberate collisions with recognized catalog entries and raw numeric/date text.
                values = ["Price", "Account", "1,234.56", "2026-11-06", "Source", "Provider", "사용자 값"]
                response = [dict(zip(keys, values))]
                gateway = Mock()
                gateway.status.return_value = [{"provider": "Fixture", "ready": True}]
                getattr(gateway, method).return_value = SimpleNamespace(ok=True, data=response, source="Fixture")
                root = krx_page.build_krx_page(page(), gateway)
                select(root, "Data", dataset)
                click(root, "Run")
                table = self.roundtrip(root, en, ko, payloads=response)
                self.assertEqual(cell_values(table), [values[:len(keys)]])
                getattr(gateway, method).assert_called_once()

    def test_macro_sheet_headers_and_provider_labels_roundtrip(self):
        row = MacroRow("fixture", "Price", "Account", "level", 1234.56, "2026-11-06",
                       1.0, None, -2.0, 3.0, 0.75, 0.9, "Source")
        sheet = MacroSheet("2026-11-06", (row,), Regime("flat", "neutral", "flat", "flat", "flat", "Fixture"),
                           {"Source": 1}, ())
        payload = {"rows": [{"label": "Price", "group": "Account", "last": 1234.56}]}
        payloads = self.capture_analysis(macro_page)
        self.inert_charts(macro_page, "macro_z_chart")
        self.stack.enter_context(patch.object(macro_page.config, "ficc_provider_status", return_value=[]))
        self.stack.enter_context(patch.object(macro_page, "macro_sheet", return_value=sheet))
        self.stack.enter_context(patch.object(macro_page, "daily_brief", return_value=payload))
        self.stack.enter_context(patch.object(macro_page.insights, "narrate_macro", return_value="Fixture"))
        root = macro_page.build_macro_page(page())
        select(root, "Data source", "synthetic")
        click(root, "Refresh")
        self.assertEqual(payloads, [payload])
        table = self.roundtrip(root, list(macro_page._COLUMNS),
                               ["분류", "지표", "최근값", "1일", "1주", "1개월", "3개월",
                                "z점수 (1년)", "백분위 (1년)", "출처"], payloads=payloads)
        self.assertEqual(cell_values(table)[0][0:3], ["Account", "Price", "1,234.56"])

    def test_bond_scenarios_use_display_headers_without_payload_mutation(self):
        panel = synthetic_curve_panel(days=30, seed=42)
        self.stack.enter_context(patch.object(bonds_page, "load_treasury_curve", return_value=panel))
        self.inert_charts(bonds_page, "scenario_chart")
        payloads = self.capture_analysis(bonds_page)
        root = bonds_page.build_bonds_page(page())
        select(root, "Tool", "scenarios")
        select(root, "Curve source", "synthetic")
        click(root, "Run")
        self.assertEqual(len(payloads), 1)
        self.roundtrip(root, ["Scenario", "Shock", "New price", "P&L", "P&L %"],
                       ["시나리오", "금리 충격", "새 가격", "손익", "손익률 %"], payloads=payloads)
        self.assertIn("scenarios", payloads[0])

    def test_rates_curve_dynamic_lookback_preserves_numbers_and_payload(self):
        self.stack.enter_context(patch.object(rates_page, "load_treasury_curve",
                                             return_value=synthetic_curve_panel(days=30, seed=42)))
        self.inert_charts(rates_page, "curve_chart", "curve_history_chart", "pca_chart")
        payloads = self.capture_analysis(rates_page)
        root = ft.Column(rates_page._run_curve(page(), source="synthetic", method="bootstrap", lookback=7))
        self.assertEqual(len(payloads), 1)
        self.roundtrip(root, ["Tenor", "Zero", "DF", "Par", "1y fwd", "Chg 7d"],
                       ["만기", "무이표 금리", "할인계수", "파 금리", "1년 선도금리", "7거래일 변화"],
                       payloads=payloads)
        self.assertEqual(payloads[0]["lookback"], 7)

    def test_fx_synthetic_option_and_carry_headers_keep_payloads(self):
        self.inert_charts(fx_page, "smile_chart", "carry_bar_chart", "carry_equity_chart")
        payloads = self.capture_analysis(fx_page)
        cases = [
            ("option", ["Point", "Strike", "Vol", "Spot delta"], ["구분", "행사가격", "변동성", "현물 델타"]),
            ("carry", ["Pair", "Ccy", "Spot", "Rate", "USD rate", "Carry", "3m vol", "Carry/vol", "3m mom", "Score"],
             ["통화쌍", "통화", "현물환율", "금리", "USD 금리", "캐리", "3개월 변동성", "캐리/변동성 비율", "3개월 모멘텀", "점수"]),
        ]
        for kind, en, ko in cases:
            with self.subTest(tool=kind):
                root = fx_page.build_fx_page(page())
                select(root, "Tool", kind)
                select(root, "Data source", "synthetic")
                count = len(payloads)
                click(root, "Run")
                self.assertEqual(len(payloads), count + 1)
                self.roundtrip(root, en, ko, payloads=payloads)


if __name__ == "__main__":
    unittest.main()
